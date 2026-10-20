// Private host fixture against the user's prepared game. Never packaged.
using System;
using System.Reflection;
using System.Linq;
using Celeste.Mod;
using System.Runtime.InteropServices;
using Celeste;
using CelesteIOSFoundation;
using CelesteJIT.Game;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Monocle;

public static class FeatherIntegrationTests
{
    [DllImport("CJGraphicsNative")] static extern void CJTestFeatherTouch(int id,float x,float y,int phase);
    [DllImport("CJGraphicsNative")] static extern void CJTestFeatherKey(int down);
    const BindingFlags Private = BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public;
    static int stage, ticks, checks;
    static Player player;
    static Level level;
    static Vector2 position, speed;
    static readonly Action<VirtualJoystick,Vector2> SetInput = (Action<VirtualJoystick,Vector2>)typeof(VirtualJoystick)
        .GetProperty("Value").GetSetMethod(true).CreateDelegate(typeof(Action<VirtualJoystick,Vector2>));
    static void Field(string name, object value) => typeof(Player).GetField(name,Private).SetValue(player,value);
    static void Check(bool value,string name) { if(!value)throw new Exception("Feather: "+name);checks++;Console.WriteLine("FEATHER_CHECK "+name); }
    static void Finger(Vector2 point,int phase,int id=101) => CJTestFeatherTouch(id,point.X/960,point.Y/540,phase);
    static Vector2 Screen(Vector2 world) { var p=FeatherTouch.WorldToPoint(level,world,960,540);return new((float)p.X,(float)p.Y); }
    static bool Near(Vector2 a,Vector2 b) => Vector2.Distance(a,b)<0.02f;

    public static void Run(GraphicsDevice device)
    {
        // Host-only: do not throttle because another Mac app has focus.
        global::Celeste.Celeste.Instance.InactiveSleepTime=TimeSpan.Zero;
        if(stage==99 || Engine.Scene is not Level current || current.Paused || CelesteJIT.Game.Platform.RunThreadActiveCount!=0 || Engine.DeltaTime<=0)return;
        if(stage==0) {
            player=current.Tracker.GetEntity<Player>();if(player==null || !player.OnGround())return;
            level=current;position=player.Position;speed=player.Speed;
            FeatherTouchTests.Run();
            var oldCamera=level.Camera.Position; var oldZoom=level.Zoom; var oldTarget=level.ZoomTarget; var oldFocus=level.ZoomFocusPoint;var oldPadding=level.ScreenPadding;
            bool oldMirror=SaveData.Instance.Assists.MirrorMode;
            try {
                level.Camera.Position=new Vector2(200,300); level.Zoom=level.ZoomTarget=1; level.ScreenPadding=0;
                SaveData.Instance.Assists.MirrorMode=false;
                var v=Engine.Viewport;
                var center=new TouchPoint((v.X+v.Width/2.0)*960/device.PresentationParameters.BackBufferWidth,
                                          (v.Y+v.Height/2.0)*540/device.PresentationParameters.BackBufferHeight);
                var expectedCenter=Vector2.Transform(new Vector2(160,90),Matrix.Invert(level.Camera.Matrix));
                if(Environment.GetEnvironmentVariable("CJIT_MOTION_RENDERER")!=null) {
                    var module=Everest.Modules.Single(m=>m.Metadata.Name=="MotionSmoothing");
                    expectedCenter-=(Vector2)module.GetType().GetMethod("GetCameraOffset",BindingFlags.Static|BindingFlags.Public).Invoke(null,null);
                }
                Check(Near(FeatherTouch.PointToWorld(level,center,960,540),expectedCenter),"viewport center maps to rendered camera center");
                foreach(bool mirror in new[]{false,true}) foreach(float zoom in new[]{1f,1.7f}) foreach(float padding in new[]{0f,12f}) {
                    SaveData.Instance.Assists.MirrorMode=mirror;level.Zoom=level.ZoomTarget=zoom;level.ZoomFocusPoint=new(180,70);level.ScreenPadding=padding;
                    var world=new Vector2(375,412);var point=FeatherTouch.WorldToPoint(level,world,852,393);
                    Console.WriteLine("FEATHER_MAPPING mirror="+mirror+" zoom="+zoom+" padding="+padding+" point="+point+" world="+world+" actual="+FeatherTouch.PointToWorld(level,point,852,393));
                    Check(Near(world,FeatherTouch.PointToWorld(level,point,852,393)),"zoom/padding/mirror world round trip");
                    var right=FeatherTouch.WorldToPoint(level,world+Vector2.UnitX*10,852,393);
                    Check(mirror?right.X<point.X:right.X>point.X,"mirror points in the visible direction");
                }
            } finally {level.Camera.Position=oldCamera;level.Zoom=oldZoom;level.ZoomTarget=oldTarget;level.ZoomFocusPoint=oldFocus;level.ScreenPadding=oldPadding;SaveData.Instance.Assists.MirrorMode=oldMirror;}
            player.Position=level.Camera.Position+new Vector2(160,85);
            Check(player.StartStarFly(),"real feather flight starts"); Field("starFlyTransforming",false);Field("starFlyTimer",100f);
            var update=typeof(Player).GetMethod("StarFlyUpdate",Private);
            foreach(var input in new[]{Vector2.Zero,Vector2.UnitX,new Vector2(.2f,0)}) {
                Field("starFlyLastDir",Vector2.UnitX);Field("starFlySpeedLerp",0f);player.Speed=new Vector2(190,0);SetInput(Input.Feather,input);
                for(int i=0;i<90;i++) update.Invoke(player,null);
                float expected=input==Vector2.Zero?91:input.X==1?190:140;
                Check(Math.Abs(player.Speed.Length()-expected)<.1f,"original feather speed for input "+input+" = "+expected);
            }
            player.Speed=new Vector2(91,0); SetInput(Input.Feather,Vector2.Zero);
            Finger(Screen(player.Center+new Vector2(50,-20)),0);
            stage=1; ticks=0; return;
        }
        // Observe the real SDL -> FNA -> TouchPort -> MInput -> Player path.
        // Allow render-only callbacks without advancing these checks too early.
        if(++ticks<8)return;ticks=0;
        Check(!player.Dead && player.StateMachine.State==Player.StStarFly,"flight survives input sequence");
        var actual=Input.Feather.Value;
        if(stage==1) {
            Check(FeatherTouch.Enabled?actual.X>.8f && actual.Y<-.1f:actual==Vector2.Zero,"fresh screen press obeys toggle");
            Finger(Screen(player.Center+new Vector2(-50,-10)),1);stage=2;
        } else if(stage==2) {
            Check(FeatherTouch.Enabled?actual.X<-.8f:actual==Vector2.Zero,"drag follows moving finger continuously");
            Finger(Screen(player.Center),2);stage=3;
        } else if(stage==3) {
            Check(actual==Vector2.Zero,"release clears the game feather input");
            Console.WriteLine("FEATHER_FLIGHT_COAST speed="+player.Speed+" position="+player.Position+" transforming="+typeof(Player).GetField("starFlyTransforming",Private).GetValue(player));
            Finger(Screen(player.Center+new Vector2(0,-60)),0);stage=4;
        } else if(stage==4) {
            Check(FeatherTouch.Enabled?actual.Y<-.8f:actual==Vector2.Zero,"second fresh gesture works");
            Finger(Screen(player.Center),3);stage=5;
        } else if(stage==5) {
            Check(actual==Vector2.Zero,"missing SDL finger is released");
            Finger(new Vector2(166,436),0);stage=6;
        } else if(stage==6) {
            Check(FeatherTouch.Enabled?actual.X<0:actual.X>.8f,"toggle off retains the ordinary feather joystick");
            Finger(new Vector2(166,436),2);CJTestFeatherKey(1);stage=7;
        } else if(stage==7) {
            Check(!TouchPort.Visible && actual.X>.8f,"keyboard takes over without touch overriding its input");
            CJTestFeatherKey(0);Finger(Screen(player.Center+new Vector2(40,0)),0);stage=8;
        } else if(stage==8) {
            Check(TouchPort.Visible && (FeatherTouch.Enabled?actual.X>.8f:actual==Vector2.Zero),"fresh touch recovers from hardware input");
            Finger(Screen(player.Center),2);
            player.StateMachine.State=Player.StNormal;player.Position=position;player.Speed=speed;TouchPort.Reset();
            stage=99;Console.WriteLine("PASS_FEATHER_REAL_GAME enabled="+FeatherTouch.Enabled+" checks="+checks);
        }
    }
}
