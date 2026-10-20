// Stable SDL contacts feed the configurable touch policy. SwiftUI owns editing,
// while the game retains its ordinary virtual inputs and frame timing.
using System.IO;
using System.Text;
using System.Reflection;
using Celeste.Mod;
using System.Runtime.InteropServices;
using Celeste;
using CelesteIOS;
using CelesteIOSFoundation;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using Microsoft.Xna.Framework.Input.Touch;
using Monocle;
namespace CelesteJIT.Game;
public static class TouchPort
{
    [DllImport("CJGraphicsNative",CallingConvention=CallingConvention.Cdecl)] private static extern int CJGamePresentation([Out] double[] values);
    [DllImport("CJGraphicsNative",CallingConvention=CallingConvention.Cdecl)] private static extern void CJGameHaptic(int action);
    [DllImport("CJGraphicsNative")] private static extern int CJTouchRevision();
    [DllImport("CJGraphicsNative")] private static extern int CJTouchRead([Out] byte[] data,int capacity);
    [DllImport("CJGraphicsNative")] private static extern void CJTouchOpenEditor();
    private static ConfiguredTouchState state;
    private static TouchConfiguration config;
    private static int revision=-2;
    private static readonly byte[] configurationBytes=new byte[32768];
    private static bool menuBound,editorWasActive,disabledBeforeEditor;
    private static object context;
    private static bool contextPaused;
    private static readonly Action<VirtualJoystick,Vector2> setAim=(Action<VirtualJoystick,Vector2>)typeof(VirtualJoystick).GetProperty("Value").GetSetMethod(true).CreateDelegate(typeof(Action<VirtualJoystick,Vector2>));
    private static TouchControlLayout layout;
    private static bool presentationReady;
    private static readonly double[] metrics=new double[7];
    private static readonly InputSourcePolicy inputSource=new();
    private static KeyboardState lastKeys;
    private static readonly GamePadState[] lastPads=new GamePadState[4];
    public static InputSource Source => inputSource.Current;
    private static readonly Dictionary<string,MTexture> prompts=new();
    private static Texture2D circle,jump,dash,grab,grabbed,pause,journal,crouchDash,restart,rectangle;
    private static readonly Texture2D[] splitMasks=new Texture2D[4];
    private static readonly List<Texture2D> owned=new();
    public static int Presses,Releases;
    public static bool Visible {get;private set;}
    public static bool ControllerConnected {get;private set;}
    public static bool Grab => Visible && !editorWasActive && Input.GrabCheck;
    internal static TouchConfiguration Configuration => config;
    private static bool Enabled => Entry.IsPhone || Environment.GetEnvironmentVariable("CJIT_TEST_TOUCH")=="1";
    public static void Bind()
    {
        if(!menuBound) {Everest.Events.Level.OnCreatePauseMenuButtons+=PauseMenu;menuBound=true;}
        BindButton(Input.Grab,()=>state.GrabRaw,()=>state.GrabPressed,()=>false);
        BindButton(Input.CrouchDash,()=>state.CrouchDash,()=>state.CrouchDashPressed,()=>state.CrouchDashReleased);
        BindButton(Input.QuickRestart,()=>state.QuickRestart,()=>state.QuickRestartPressed,()=>state.QuickRestartReleased);
        BindButton(Input.Jump,()=>state.Jump,()=>state.JumpPressed,()=>state.JumpReleased);
        BindButton(Input.Dash,()=>state.Dash,()=>state.DashPressed,()=>state.DashReleased);
        BindButton(Input.Talk,()=>state.Jump,()=>state.JumpPressed,()=>state.JumpReleased);
        BindButton(Input.MenuConfirm,()=>state.Jump,()=>state.JumpPressed,()=>state.JumpReleased);
        BindButton(Input.MenuCancel,()=>state.Dash,()=>state.DashPressed,()=>state.DashReleased);
        BindButton(Input.Pause,()=>state.Pause,()=>state.PausePressed,()=>state.PauseReleased);
        BindButton(Input.MenuJournal,()=>state.Journal,()=>state.JournalPressed,()=>state.JournalReleased);
        BindButton(Input.MenuLeft,()=>state.MoveX<0,()=>state.LeftPressed,()=>state.LeftReleased);
        BindButton(Input.MenuRight,()=>state.MoveX>0,()=>state.RightPressed,()=>state.RightReleased);
        BindButton(Input.MenuUp,()=>state.MoveY<0,()=>state.UpPressed,()=>state.UpReleased);
        BindButton(Input.MenuDown,()=>state.MoveY>0,()=>state.DownPressed,()=>state.DownReleased);
        Input.MoveX.Nodes.Add(new TouchAxis(()=>state.MoveX));
        Input.MoveY.Nodes.Add(new TouchAxis(()=>state.MoveY));
        Input.GliderMoveY.Nodes.Add(new TouchAxis(()=>state.MoveY));
        Entry.Mark("game_feather_touch", "enabled="+FeatherTouch.Enabled+"; neutral=vanilla coast; radius_points=16/22");
        foreach(var axis in new[]{Input.Aim,Input.Feather,Input.MountainAim})
            axis.Nodes.Add(new TouchJoystick(ReferenceEquals(axis,Input.Aim)));
    }
    private static void PauseMenu(Level level,TextMenu menu,bool minimal) {
        if(!Enabled || minimal)return;
        menu.Add(new TextMenu.Button("Touch controls…").Pressed(()=>{Reset();CJTouchOpenEditor();}));
    }
    private static void BindButton(VirtualButton button,Func<bool> held,Func<bool> pressed,Func<bool> released)
    {
        button.Nodes.Add(new TouchButton(held,pressed,released));
    }
    private sealed class TouchButton(Func<bool> held, Func<bool> pressed, Func<bool> released) : VirtualButton.Node
    {
        public override bool Check => Visible && state != null && held();
        public override bool Pressed => Visible && state != null && pressed();
        public override bool Released => Visible && state != null && released();
        public override bool Bufferable { get; set; } = true;
    }
    private sealed class TouchAxis(Func<float> value) : VirtualAxis.Node
    {
        public override float Value => Visible && state != null ? value() : 0;
    }
    private sealed class TouchJoystick(bool aim) : VirtualJoystick.Node
    {
        public override Vector2 Value => Visible && state != null ? aim && state.HasDashAim ? new Vector2((float)state.DashAim.X,(float)state.DashAim.Y) : new Vector2(state.MoveX,state.MoveY) : Vector2.Zero;
    }
    public static void Update()
    {
        presentationReady=false;
        if(!Enabled || CJGamePresentation(metrics)!=1) { Reset(); return; }
        int currentRevision=CJTouchRevision();
        if(currentRevision<0) {
            if(!editorWasActive){disabledBeforeEditor=MInput.Disabled;editorWasActive=true;}
            MInput.Disabled=true;Reset();return;
        }
        if(editorWasActive){MInput.Disabled=disabledBeforeEditor;editorWasActive=false;Reset();}
        double width=metrics[0],height=metrics[1];
        var safe=new SafeAreaMetrics(metrics[2],metrics[3],metrics[4],metrics[5]);
        if(!safe.IsValidFor(width,height) || width<=height) { Reset(); return; }
        presentationReady=true;
        bool changed=state==null || revision!=currentRevision || layout.Width!=width || layout.Height!=height || layout.SafeArea!=safe;
        if(changed) {
            FeatherTouch.Gesture.Reset();
            layout=TouchControlLayout.Create(width,height,safe,metrics[6]!=0,1);
            config=TouchConfiguration.Default(width,height,safe,metrics[6]!=0);
            try {
                int length=CJTouchRead(configurationBytes,configurationBytes.Length);
                if(length>0)config=TouchConfiguration.Decode(Encoding.UTF8.GetString(configurationBytes,0,length));
            } catch(Exception e) {Entry.Mark("game_touch_layout_fallback",e.GetType().Name+": "+e.Message);}
            state=new(config,TouchConfiguration.Canvas(width,height,safe));revision=currentRevision;
            InputPreferences.Configure(config);
            FeatherTouch.Configure(config.FeatherTouch ?? (Environment.GetEnvironmentVariable("CJIT_FEATHER_TOUCH")=="1"));
            Entry.Mark("game_touch_layout","points="+width+"x"+height+"; schema=1; controls="+config.Controls.Length+"; grab="+config.Grab+"; swipe="+config.Swipe);

        }
        var touches=TouchPanel.GetState();
        bool touchActivity=false;
        foreach(var touch in touches) {
            touchActivity |= touch.State==TouchLocationState.Pressed ||
                (touch.State==TouchLocationState.Moved && touch.TryGetPreviousLocation(out var prior) && Vector2.DistanceSquared(touch.Position,prior.Position)>1);
        }
        var keys=Keyboard.GetState();bool keyActivity=false;
        if(keys!=lastKeys)foreach(var key in keys.GetPressedKeys())keyActivity |= lastKeys.IsKeyUp(key);
        lastKeys=keys;
        bool connected=false,padActivity=false;
        for(int i=0;i<4;i++) {
            var pad=GamePad.GetState((PlayerIndex)i);var previous=lastPads[i];connected|=pad.IsConnected;
            // Edges and stick motion above the deadzone; connection alone is not input.
            if(pad.IsConnected)padActivity |= pad.Buttons!=previous.Buttons || pad.DPad!=previous.DPad ||
                (pad.ThumbSticks.Left.LengthSquared()>0.09f && Vector2.DistanceSquared(pad.ThumbSticks.Left,previous.ThumbSticks.Left)>0.0025f) ||
                (pad.ThumbSticks.Right.LengthSquared()>0.09f && Vector2.DistanceSquared(pad.ThumbSticks.Right,previous.ThumbSticks.Right)>0.0025f) ||
                (pad.Triggers.Left>0.25f && previous.Triggers.Left<=0.25f) || (pad.Triggers.Right>0.25f && previous.Triggers.Right<=0.25f);
            lastPads[i]=pad;
        }
        ControllerConnected=connected;
        if(config.Visibility=="off")touchActivity=false;
        if(inputSource.Observe(touchActivity,keyActivity,padActivity,connected)) {
            state.Reset();FeatherTouch.Gesture.Reset();Entry.Mark("game_input_source","source="+Source+"; controller_connected="+connected);
        }
        InputPreferences.Observe(Source);
        Visible=Source==InputSource.Touch && config.Visibility!="off";
        var currentLevel=Engine.Scene as Level;
        object currentContext=currentLevel?.Tracker.GetEntity<Player>() ?? (object)Engine.Scene;
        bool paused=currentLevel==null || currentLevel.Paused || currentLevel.Frozen || currentLevel.Transitioning || (currentContext is Player cp && cp.Dead) || MInput.Disabled;
        if(currentContext!=context || paused!=contextPaused) {state.Reset();FeatherTouch.Gesture.Reset();context=currentContext;contextPaused=paused;}
        if(config.Visibility=="off")state.Reset();
        FeatherTouch.Gesture.BeginFrame(FeatherTouch.PlayerInFlight());
        var oldDirection=state.Direction;
        state.MenuMode=currentLevel==null || currentLevel.Paused;
        state.BeginFrame(Engine.DeltaTime);
        Span<int> active=stackalloc int[ConfiguredTouchState.MaximumTouches];int count=0;
        foreach(var touch in touches) {
            TouchPhase phase=touch.State==TouchLocationState.Pressed?TouchPhase.Pressed:touch.State==TouchLocationState.Released?TouchPhase.Released:TouchPhase.Moved;
            if(phase!=TouchPhase.Released && count<active.Length)active[count++]=touch.Id;
            if(phase==TouchPhase.Pressed)Presses++;if(phase==TouchPhase.Released)Releases++;
            if(!Visible)continue;
            var point=new TouchPoint(touch.Position.X*width/Math.Max(1,TouchPanel.DisplayWidth),touch.Position.Y*height/Math.Max(1,TouchPanel.DisplayHeight));
            bool eligible=!state.IsAction(point) && FeatherTouch.InGameArea(point,width,height);
            if(FeatherTouch.Gesture.Apply(touch.Id,phase,point,eligible))continue;
            var haptic=state.Apply(touch.Id,phase,point,!paused || state.MenuMode);
            if(haptic!=TouchHapticAction.None)CJGameHaptic((int)haptic);
        }
        state.ReleaseMissingOwners(active[..count]);
        FeatherTouch.Gesture.ReleaseMissing(active[..count]);
        if(config.DirectionalHaptics && state.Direction!=oldDirection && state.Direction!=TouchDirection.Neutral)CJGameHaptic(4);
    }
    public static void AfterInputUpdate() {
        if(!presentationReady)return;
        InputPreferences.Observe(Source);
        ControllerIntegration.Update();
        if(Visible && state.HasDashAim && !contextPaused) setAim(Input.Aim,new((float)state.DashAim.X,(float)state.DashAim.Y));
        FeatherTouch.AfterInputUpdate(layout.Width,layout.Height);
    }
    public static void Reset() {state?.Reset();FeatherTouch.Gesture.Reset();presentationReady=false;}
    private static Texture2D Texture(Color[] data) {
        var t=new Texture2D(global::Celeste.Celeste.Instance.GraphicsDevice,128,128);t.SetData(data);owned.Add(t);return t;
    }
    private static Texture2D Icon(string name) {
        using var s=typeof(TouchPort).Assembly.GetManifestResourceStream("Celeste.IOSTouchControls."+name+".a8") ?? throw new FileNotFoundException(name);
        var bytes=new byte[128*128];s.ReadExactly(bytes);if(s.ReadByte()!=-1)throw new InvalidDataException(name);
        return Texture(Array.ConvertAll(bytes,a=>new Color(a,a,a,a)));
    }
    private static void EnsureTextures() {
        if(circle!=null)return;
        var data=new Color[128*128];
        for(int y=0;y<128;y++)for(int x=0;x<128;x++){
            byte a=(byte)Math.Clamp((63-Math.Sqrt((x-63.5)*(x-63.5)+(y-63.5)*(y-63.5)))*255,0,255);
            data[y*128+x]=new Color(a,a,a,a);
        }
        circle=Texture(data);rectangle=Texture(Enumerable.Repeat(Color.White,128*128).ToArray());crouchDash=Icon("crouch-dash");restart=Icon("restart");
        for(int n=0;n<4;n++){var mask=new Color[128*128];for(int y=0;y<128;y++)for(int x=0;x<128;x++){bool first=n==0?y<=x:n==1?y+x<=127:n==2?x<64:y<64;mask[y*128+x]=first?Color.White:Color.Transparent;}splitMasks[n]=Texture(mask);}
        jump=Icon("jump");dash=Icon("dash");grab=Icon("grab-ungrabbed");grabbed=Icon("grab-grabbed");pause=Icon("pause");journal=Icon("journal");
    }
    public static MTexture Prompt(VirtualButton button) {
        if(ReferenceEquals(button,Input.CrouchDash) && !(config?.Controls.Any(c=>config.Active(c) && c.Kind=="crouchDash")??false))return null;
        if(ReferenceEquals(button,Input.QuickRestart) && !(config?.Controls.Any(c=>config.Active(c) && c.Kind=="quickRestart")??false))return null;
        // Never invent a generic touch binding for a mod action we cannot trigger.
        string name=ReferenceEquals(button,Input.MenuConfirm) || ReferenceEquals(button,Input.Jump) || ReferenceEquals(button,Input.Talk) ? "jump" :
            ReferenceEquals(button,Input.MenuCancel) || ReferenceEquals(button,Input.Dash) ? "dash" :
            ReferenceEquals(button,Input.Grab) ? "grab-ungrabbed" : ReferenceEquals(button,Input.Pause) ? "pause" :
            ReferenceEquals(button,Input.MenuJournal) ? "journal" : ReferenceEquals(button,Input.CrouchDash) ? "crouch-dash" : ReferenceEquals(button,Input.QuickRestart)?"restart":null;
        if(name==null || global::Celeste.Celeste.Instance?.GraphicsDevice==null)return null;
        if(prompts.TryGetValue(name,out var value))return value;
        using var stream=typeof(TouchPort).Assembly.GetManifestResourceStream("Celeste.IOSTouchControls."+name+".a8") ?? throw new FileNotFoundException(name);
        byte[] alpha=new byte[128*128];stream.ReadExactly(alpha);
        const int size=80;var colors=new Color[size*size];
        for(int y=0;y<size;y++)for(int x=0;x<size;x++) {
            byte a=alpha[Math.Min(127,((y*2+1)*128)/(size*2))*128+Math.Min(127,((x*2+1)*128)/(size*2))];
            colors[y*size+x]=new Color(a,a,a,a);
        }
        var texture=VirtualContent.CreateTexture("CelesteIOS prompt "+name,size,size,Color.Transparent);
        texture.Texture.SetData(colors);value=new MTexture(texture);prompts.Add(name,value);
        Entry.Mark("game_touch_prompt_created","action="+name+"; size=80; shared centered artwork");return value;
    }
    public static void Render() {
        if(state==null || config.Visibility=="off" || (!Visible && config.Visibility!="always") || Monocle.Draw.SpriteBatch==null || editorWasActive)return;
        EnsureTextures();var device=global::Celeste.Celeste.Instance.GraphicsDevice;
        var previous=device.Viewport;
        device.Viewport=new Viewport(0,0,device.PresentationParameters.BackBufferWidth,device.PresentationParameters.BackBufferHeight);
        Monocle.Draw.SpriteBatch.Begin(SpriteSortMode.Deferred,BlendState.AlphaBlend,SamplerState.LinearClamp,DepthStencilState.None,RasterizerState.CullNone);
        if(FeatherTouch.PlayerInFlight() is Player featherPlayer) {
            var centerPoint=FeatherTouch.WorldToPoint((Level)featherPlayer.Scene,featherPlayer.Center,layout.Width,layout.Height);
            DrawCircle(new TouchCircle(centerPoint,FeatherTouchState.CoastRadius,0),circle,new Color(255,221,120)*0.16f);
            if(FeatherTouch.Gesture.HasTarget) {
                DrawCircle(new TouchCircle(FeatherTouch.Gesture.Target,9,0),circle,new Color(255,221,120)*0.32f);
                DrawCircle(new TouchCircle(FeatherTouch.Gesture.Target,3,0),circle,Color.White*0.8f);
            }
        } else {
            var movement=config.Controls.First(c=>c.Kind=="movement");var r=movement.Rect(state.Canvas);
            var center=state.MovementCenter;
            float alpha=(float)(movement.Opacity*config.Opacity/10000.0);
            DrawCircle(new TouchCircle(center,state.MovementRadius,0),circle,new Color(150,170,195)*(.25f*alpha));
            var nub=new TouchCircle(new TouchPoint(center.X+state.MoveX*28,center.Y+state.MoveY*28),22,22);
            DrawCircle(nub,circle,new Color(200,220,245)*(.6f*alpha));
        }
        foreach(var control in config.Controls) {
            if(!config.Active(control) || control.Kind is "movement" or "floating")continue;
            if(control.Kind=="gesture" && FeatherTouch.PlayerInFlight()!=null)continue;
            DrawControl(control);
        }
        Monocle.Draw.SpriteBatch.End();device.Viewport=previous;
    }
    private static void DrawControl(TouchControl c) {
        var r=c.Rect(state.Canvas);float opacity=(float)(c.Opacity*config.Opacity/10000.0);
        if(c.Kind=="split") {
            DrawRect(r,rectangle,(c.Swap?new Color(124,219,255):new Color(255,104,146))*(.16f*opacity));
            DrawRect(r,splitMasks[c.Split],(c.Swap?new Color(255,104,146):new Color(124,219,255))*(.30f*opacity));
            double x=c.Split==0?2.0/3:c.Split==1?1.0/3:c.Split==2?.25:.5;
            double y=c.Split<2?1.0/3:c.Split==2?.5:.25;
            DrawGlyph(r,c.Swap?dash:jump,x,y,opacity);DrawGlyph(r,c.Swap?jump:dash,1-x,1-y,opacity);return;
        }
        if(c.Kind=="gesture") {DrawRect(r,rectangle,new Color(124,219,255)*(.08f*opacity));return;}
        bool held=c.Kind switch {"jump"=>state.Jump,"dash"=>state.Dash,"grab"=>Grab,"pause"=>state.Pause,"journal"=>state.Journal,"crouchDash"=>state.CrouchDash,"quickRestart"=>state.QuickRestart,_=>false};
        var icon=c.Kind switch {"jump"=>jump,"dash"=>dash,"grab"=>Grab?grabbed:grab,"pause"=>pause,"journal"=>journal,"crouchDash"=>crouchDash,"quickRestart"=>restart,_=>null};
        var color=c.Kind=="jump"?new Color(124,219,255):c.Kind=="dash"?new Color(255,104,146):c.Kind=="grab"?new Color(220,200,120):Color.White;
        if(c.Shape=="circle") {
            double radius=Math.Min(r.Width,r.Height)/2;
            DrawCircle(new(new(r.X+r.Width/2,r.Y+r.Height/2),radius,0),circle,color*((held?.65f:.17f)*opacity));
        } else DrawRect(r,rectangle,color*((held?.65f:.17f)*opacity));
        if(icon!=null)DrawGlyph(r,icon,.5,.5,opacity*(held?1:.7f));
    }
    private static void DrawGlyph(TouchRect r,Texture2D icon,double x,double y,float opacity) {
        double size=Math.Min(r.Width,r.Height)*.62;
        if(x!=.5 || y!=.5)size=Math.Min(50,size*.62);
        DrawRect(new(r.X+r.Width*x-size/2,r.Y+r.Height*y-size/2,size,size),icon,Color.White*opacity);
    }
    private static void DrawCircle(TouchCircle shape,Texture2D texture,Color color)=>DrawRect(new TouchRect(shape.Center.X-shape.Radius,shape.Center.Y-shape.Radius,shape.Radius*2,shape.Radius*2),texture,color);
    private static void DrawRect(TouchRect r,Texture2D texture,Color color) {
        var p=global::Celeste.Celeste.Instance.GraphicsDevice.PresentationParameters;
        var rect=new Rectangle((int)(r.X*p.BackBufferWidth/layout.Width),(int)(r.Y*p.BackBufferHeight/layout.Height),(int)(r.Width*p.BackBufferWidth/layout.Width),(int)(r.Height*p.BackBufferHeight/layout.Height));
        Monocle.Draw.SpriteBatch.Draw(texture,rect,color);
    }
    public static void Dispose() {if(menuBound){Everest.Events.Level.OnCreatePauseMenuButtons-=PauseMenu;menuBound=false;}Reset();foreach(var t in owned)t.Dispose();owned.Clear();prompts.Clear();circle=null;jump=null;dash=null;grab=null;grabbed=null;pause=null;journal=null;Visible=false;}
}
