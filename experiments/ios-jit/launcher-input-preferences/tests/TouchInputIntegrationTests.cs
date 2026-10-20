// Private, real SDL/FNA/game integration. Never included in an IPA.
using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using MonoMod.RuntimeDetour;
using System.Runtime.InteropServices;
using Celeste;
using CelesteJIT.Game;
using CelesteIOSFoundation;
using Microsoft.Xna.Framework;
using Monocle;

public static class TouchInputIntegrationTests
{
    [DllImport("CJGraphicsNative")]static extern void CJTestFeatherTouch(int id,float x,float y,int phase);
    [DllImport("CJGraphicsNative")]static extern void CJTestTouchRevision(int revision);
    delegate void UpdateOrig(Player player);
    delegate void UpdateHook(UpdateOrig orig,Player player);
    static Hook observer;
    static bool sawCrouchDash;
    static int stage,ticks,revision=10,checks;static ulong lastFrame=ulong.MaxValue;
    public static bool Complete=>stage==99;
    static Level level;static Player player;static Vector2 position;
    static TouchConfiguration config;
    static CrouchDashModes oldCrouchMode;
    static void Check(bool value,string name){if(!value)throw new Exception("Touch integration: "+name);checks++;Console.WriteLine("REAL_TOUCH_CHECK "+name);}
    static void Finger(int id,float x,float y,int phase)=>CJTestFeatherTouch(id,x/960,y/540,phase);
    static void Save(){File.WriteAllText(Environment.GetEnvironmentVariable("CJIT_TOUCH_CONFIG"),JsonSerializer.Serialize(config,TouchConfiguration.JSON));CJTestTouchRevision(++revision);}
    public static void Run()
    {
        if(stage==99 || !FeatherIntegrationTests.Complete || Engine.Scene is not Level current)return;
        // Wait in original game updates, never interpolated render callbacks.
        if(lastFrame==Engine.FrameCounter)return;lastFrame=Engine.FrameCounter;
        if(stage==0) {
            player=current.Tracker.GetEntity<Player>();if(player==null || player.Dead || !player.OnGround() || current.InCutscene || current.Transitioning || player.StateMachine.State!=Player.StNormal)return;
            level=current;position=player.Position;oldCrouchMode=Settings.Instance.CrouchDashMode;TouchPolicyTests.Run();
            config=TouchConfiguration.Default(960,540,default,false);config.Swipe=true;
            var grab=config.Controls.First(c=>c.Kind=="grab");grab.Shape="rectangle";grab.X=.65;grab.Y=.05;grab.Width=.3;grab.Height=.10;
            config.Controls=config.Controls.Concat(new[]{new TouchControl{Id="crouch",Kind="crouchDash",Shape="rectangle",X=.40,Y=.45,Width=.1,Height=.1},new TouchControl{Id="restart",Kind="quickRestart",Shape="rectangle",X=.40,Y=.60,Width=.1,Height=.1}}).ToArray();
            observer=new Hook(typeof(Player).GetMethod("Update"),(UpdateHook)((orig,p)=>{
                orig(p);
                if(stage==5 && (bool)typeof(Player).GetField("demoDashed",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).GetValue(p))sawCrouchDash=true;
            }));
            Save();stage=1;ticks=0;return;
        }
        if(++ticks<5)return;ticks=0;
        if(stage==1) {
            player.Dashes=1;
            Finger(101,56,436,0);Finger(102,740,320,0);stage=2;
        } else if(stage==2) {
            Check(Input.Jump.Check,"gesture supplies actual held Jump");Check(Input.MoveX.Value==-1,"movement remains left during gesture");
            Finger(102,740,270,1);stage=3;
        } else if(stage==3) {
            Console.WriteLine("REAL_TOUCH_OBSERVE aim="+Input.Aim.Value+" dash="+player.DashDir+" move="+Input.MoveX.Value+" state="+player.StateMachine.State+" dead="+player.Dead+" paused="+level.Paused+" frozen="+level.Frozen);
            Check(player.DashDir.Y<-.9f && Math.Abs(player.DashDir.X)<.01f,"swipe aim survives the game dash startup");
            Check(Input.MoveX.Value==-1,"dash aim leaves actual MoveX alone");
            Check(player.DashDir.Y<-.9f && Math.Abs(player.DashDir.X)<.01f,"original Player dash uses swipe direction");
            Finger(101,56,436,2);Finger(102,740,270,2);stage=4;
        } else if(stage==4) {
            Check(!Input.Jump.Check && Input.MoveX.Value==0,"lifting clears real jump and movement");
            player.StateMachine.State=Player.StNormal;player.Position=position;player.Speed=Vector2.Zero;player.Dashes=1;
            Settings.Instance.CrouchDashMode=CrouchDashModes.Press;
            typeof(Player).GetField("dashCooldownTimer",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).SetValue(player,0f);
            Finger(102,432,270,0);stage=5;
        } else if(stage==5) {
            Check(Input.CrouchDash.Check,"extra binds actual CrouchDash");
            Check(TouchPort.Prompt(Input.CrouchDash)!=null,"enabled crouch dash has its actual touch prompt");
            Check(sawCrouchDash,"original Player recognizes the crouch dash during its normal update");Finger(102,432,270,2);stage=6;
        } else if(stage==6) {
            Finger(102,432,350,0);stage=7;
        } else if(stage==7) {
            Check(level.Paused,"quick restart opens the original game confirmation");
            Finger(102,432,350,2);CJTestTouchRevision(-1);stage=8;
        } else if(stage==8) {
            Check(MInput.Disabled,"native editor blocks game input");
            config.Grab="invert";Save();stage=9;
        } else if(stage==9) {
            Check(!MInput.Disabled,"closing editor restores input polling");
            Check(Input.GrabCheck,"changed touch inverse mode applies within session");
            var menu=level.Entities.OfType<TextMenu>().FirstOrDefault();
            Check(menu!=null,"restart confirmation remains open under native editor");menu.OnCancel?.Invoke();stage=10;
        } else if(stage==10) {
            Check(level.Paused,"cancel from quick restart returns to ordinary pause");
            var menu=level.Entities.OfType<TextMenu>().FirstOrDefault();
            Check(menu!=null && menu.Items.OfType<TextMenu.Button>().Any(b=>b.Label=="Touch controls…"),"ordinary pause menu exposes editor");
            menu.OnCancel?.Invoke();stage=11;
        } else if(stage==11) {
            Check(!level.Paused,"ordinary menu cancel returns to game");
            File.Delete(Environment.GetEnvironmentVariable("CJIT_TOUCH_CONFIG"));CJTestTouchRevision(++revision);
            player.StateMachine.State=Player.StNormal;player.Position=position;player.Speed=Vector2.Zero;TouchPort.Reset();
            Settings.Instance.CrouchDashMode=oldCrouchMode;observer.Dispose();stage=99;Console.WriteLine("PASS_REAL_TOUCH_EDITOR_INPUT checks="+checks);
        }
    }
}
