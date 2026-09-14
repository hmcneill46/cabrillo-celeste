// Binding-free adapter for the proven iOS touch policy and attributed artwork.
// Layout editing/preferences and Files UI remain later product work.
using System.IO;
using System.Runtime.InteropServices;
using Celeste;
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
    private static TouchInteractionState state;
    private static TouchControlLayout layout;
    private static readonly double[] metrics=new double[7];
    private static Texture2D circle,jump,dash,grab,grabbed,pause,journal;
    private static readonly List<Texture2D> owned=new();
    public static int Presses,Releases;
    public static bool Visible {get;private set;}
    public static bool ControllerConnected {get;private set;}
    public static bool Grab => Visible && (state?.Grab ?? false);
    private static bool Enabled => Entry.IsPhone || Environment.GetEnvironmentVariable("CJIT_TEST_TOUCH")=="1";
    public static void Bind()
    {
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
        foreach(var axis in new[]{Input.Aim,Input.Feather,Input.MountainAim})
            axis.Nodes.Add(new TouchJoystick());
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
    private sealed class TouchJoystick : VirtualJoystick.Node
    {
        public override Vector2 Value => Visible && state != null ? new Vector2(state.MoveX,state.MoveY) : Vector2.Zero;
    }
    public static void Update()
    {
        if(!Enabled || CJGamePresentation(metrics)!=1) return;
        double width=metrics[0],height=metrics[1];
        var safe=new SafeAreaMetrics(metrics[2],metrics[3],metrics[4],metrics[5]);
        if(!safe.IsValidFor(width,height) || width<=height) return;
        bool changed=state==null || layout.Width!=width || layout.Height!=height || layout.SafeArea!=safe;
        if(changed) {
            layout=TouchControlLayout.Create(width,height,safe,metrics[6]!=0,1);
            if(state==null)state=new(layout);else state.UpdateLayout(layout);
            Entry.Mark("game_touch_layout","points="+width+"x"+height+"; safe="+safe+"; source=shared iOS policy; grab=toggle");
        }
        bool connected=false;for(int i=0;i<4;i++)connected |= GamePad.GetState((PlayerIndex)i).IsConnected;
        if(connected!=ControllerConnected){state.Reset();ControllerConnected=connected;}
        Visible=TouchVisibilityPolicy.IsVisible(TouchControlVisibility.Automatic,connected);
        state.BeginFrame();
        var touches=TouchPanel.GetState();Span<int> active=stackalloc int[TouchInteractionState.MaximumTouches];int count=0;
        foreach(var touch in touches) {
            TouchPhase phase=touch.State==TouchLocationState.Pressed?TouchPhase.Pressed:touch.State==TouchLocationState.Released?TouchPhase.Released:TouchPhase.Moved;
            if(phase!=TouchPhase.Released && count<active.Length)active[count++]=touch.Id;
            if(phase==TouchPhase.Pressed)Presses++;if(phase==TouchPhase.Released)Releases++;
            if(!Visible)continue;
            var point=new TouchPoint(touch.Position.X*width/Math.Max(1,TouchPanel.DisplayWidth),touch.Position.Y*height/Math.Max(1,TouchPanel.DisplayHeight));
            var haptic=state.Apply(touch.Id,phase,point,true);
            if(haptic!=TouchHapticAction.None)CJGameHaptic((int)haptic);
        }
        state.ReleaseMissingOwners(active[..count]);
    }
    public static void Reset() {state?.Reset();}
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
        circle=Texture(data);jump=Icon("jump");dash=Icon("dash");grab=Icon("grab-ungrabbed");grabbed=Icon("grab-grabbed");pause=Icon("pause");journal=Icon("journal");
    }
    public static void Render() {
        if(!Visible || state==null || Monocle.Draw.SpriteBatch==null)return;
        EnsureTextures();var device=global::Celeste.Celeste.Instance.GraphicsDevice;
        var previous=device.Viewport;
        device.Viewport=new Viewport(0,0,device.PresentationParameters.BackBufferWidth,device.PresentationParameters.BackBufferHeight);
        Monocle.Draw.SpriteBatch.Begin(SpriteSortMode.Deferred,BlendState.AlphaBlend,SamplerState.LinearClamp,DepthStencilState.None,RasterizerState.CullNone);
        DrawCircle(layout.Movement,circle,new Color(150,170,195)*0.25f);
        var center=state.MovementCenter;
        var nub=new TouchCircle(new TouchPoint(center.X+state.MoveX*28,center.Y+state.MoveY*28),22,22);
        DrawCircle(nub,circle,new Color(200,220,245)*0.6f);
        Action(layout.Jump,jump,state.Jump,new Color(124,219,255));
        Action(layout.Dash,dash,state.Dash,new Color(255,104,146));
        Action(layout.Grab,state.Grab?grabbed:grab,state.Grab,new Color(220,200,120));
        DrawRect(layout.Pause,pause,Color.White*0.7f);DrawRect(layout.Journal,journal,Color.White*0.7f);
        Monocle.Draw.SpriteBatch.End();device.Viewport=previous;
    }
    private static void Action(TouchCircle shape,Texture2D icon,bool held,Color color) {
        DrawCircle(shape,circle,color*(held?0.65f:0.2f));
        DrawCircle(shape with{Radius=shape.Radius*0.76},icon,Color.White*(held?1:0.7f));
    }
    private static void DrawCircle(TouchCircle shape,Texture2D texture,Color color)=>DrawRect(new TouchRect(shape.Center.X-shape.Radius,shape.Center.Y-shape.Radius,shape.Radius*2,shape.Radius*2),texture,color);
    private static void DrawRect(TouchRect r,Texture2D texture,Color color) {
        var p=global::Celeste.Celeste.Instance.GraphicsDevice.PresentationParameters;
        var rect=new Rectangle((int)(r.X*p.BackBufferWidth/layout.Width),(int)(r.Y*p.BackBufferHeight/layout.Height),(int)(r.Width*p.BackBufferWidth/layout.Width),(int)(r.Height*p.BackBufferHeight/layout.Height));
        Monocle.Draw.SpriteBatch.Draw(texture,rect,color);
    }
    public static void Dispose() {Reset();foreach(var t in owned)t.Dispose();owned.Clear();}
}
