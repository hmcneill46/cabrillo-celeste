// Preferences select Celeste's own GrabMode. Input.UpdateGrab and GrabCheck
// continue to process the game's real bindings, including mod-added nodes.
using System.Reflection;
using System.Runtime.InteropServices;
using Celeste;
using CelesteIOS;
using Monocle;
using MonoMod.RuntimeDetour;
namespace CelesteJIT.Game;
public static class InputPreferences
{
    [DllImport("CJGraphicsNative")] private static extern void CJTouchSetGrabMode(int source,int mode);
    private static readonly FieldInfo latch=typeof(Input).GetField("grabToggle",BindingFlags.Static|BindingFlags.NonPublic)
        ?? throw new MissingFieldException("Celeste.Input.grabToggle");
    private static readonly List<Hook> hooks=new();
    private static readonly bool[] remembered=new bool[3];
    private static TouchConfiguration config;
    private static InputSource source;
    private static GrabModes applied;
    private static bool initialized,forcingReset;
    private delegate void Original();
    private delegate void Detour(Original orig);
    private static bool Persistent => config?.ToggleBehavior=="persistent";
    public static void Install() {
        hooks.Add(new Hook(typeof(Input).GetMethod(nameof(Input.UpdateGrab)),(Detour)(orig=>{Observe(TouchPort.Source);orig();})));
        hooks.Add(new Hook(typeof(Input).GetMethod(nameof(Input.ResetGrab)),(Detour)(orig=>{
            if(!forcingReset && initialized && Persistent && Settings.Instance.GrabMode==GrabModes.Toggle)return;
            orig();
        })));
    }
    static GrabModes Parse(string value,GrabModes fallback)=>value switch {"hold"=>GrabModes.Hold,"invert"=>GrabModes.Invert,"toggle"=>GrabModes.Toggle,_=>fallback};
    static string Stored(GrabModes mode)=>mode switch {GrabModes.Invert=>"invert",GrabModes.Toggle=>"toggle",_=>"hold"};
    static string Mode(TouchConfiguration c,InputSource input)=>input switch {InputSource.Controller=>c.ControllerGrab,InputSource.Keyboard=>c.KeyboardGrab,_=>c.Grab};
    static void SetMode(TouchConfiguration c,InputSource input,GrabModes mode) {
        switch(input){case InputSource.Controller:c.ControllerGrab=Stored(mode);break;case InputSource.Keyboard:c.KeyboardGrab=Stored(mode);break;default:c.Grab=Stored(mode);break;}
    }
    static void ClearLatch() {forcingReset=true;try{Input.ResetGrab();}finally{forcingReset=false;}}
    static void CaptureGameSetting() {
        if(!initialized || Settings.Instance==null || Settings.Instance.GrabMode==applied)return;
        // A change in Celeste's ordinary Options belongs to the source that was
        // active when the option changed, before applying a newly observed source.
        applied=Settings.Instance.GrabMode;
        if(applied is not (GrabModes.Hold or GrabModes.Invert or GrabModes.Toggle))applied=GrabModes.Hold;
        Settings.Instance.GrabMode=applied;SetMode(config,source,applied);remembered[(int)source]=false;ClearLatch();
        CJTouchSetGrabMode((int)source,(int)applied);
        Entry.Mark("game_grab_mode_saved","source="+source+"; mode="+applied);
    }
    internal static void Configure(TouchConfiguration next) {
        if(Settings.Instance==null){config=next;return;}
        CaptureGameSetting();
        var fallback=Settings.Instance.GrabMode;
        foreach(var input in new[]{InputSource.Touch,InputSource.Keyboard,InputSource.Controller})
            if(Mode(next,input)=="game") {SetMode(next,input,fallback);CJTouchSetGrabMode((int)input,(int)fallback);}
        bool changed=initialized && (Mode(next,source)!=Mode(config,source) || next.ToggleBehavior!=config.ToggleBehavior);
        if(initialized)foreach(var input in new[]{InputSource.Touch,InputSource.Keyboard,InputSource.Controller})
            if(Mode(next,input)!=Mode(config,input))remembered[(int)input]=false;
        if(config?.ToggleBehavior!=next.ToggleBehavior)Array.Clear(remembered);
        config=next;
        if(!initialized){source=TouchPort.Source;initialized=true;changed=true;}
        if(changed){ClearLatch();applied=Parse(Mode(config,source),fallback);Settings.Instance.GrabMode=applied;}
    }
    internal static void Observe(InputSource next) {
        if(config==null || Settings.Instance==null)return;
        if(!initialized){Configure(config);return;}
        CaptureGameSetting();
        if(source==next)return;
        remembered[(int)source]=Persistent && applied==GrabModes.Toggle && (bool)latch.GetValue(null);
        source=next;applied=Parse(Mode(config,source),applied);Settings.Instance.GrabMode=applied;
        ClearLatch();
        if(Persistent && applied==GrabModes.Toggle)latch.SetValue(null,remembered[(int)source]);
        Entry.Mark("game_grab_source","source="+source+"; mode="+applied+"; persistent="+Persistent);
    }
    public static void Dispose() {
        if(initialized)ClearLatch();
        foreach(var hook in hooks)hook.Dispose();hooks.Clear();initialized=false;config=null;Array.Clear(remembered);
    }
}
