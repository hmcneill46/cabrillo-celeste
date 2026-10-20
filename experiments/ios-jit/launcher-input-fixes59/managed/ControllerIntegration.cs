// Follow the exact SDL controller selected by FNA; Apple/SDL connection order
// is not interchangeable with the game's player index. No second input backend.
using System.Reflection;
using Celeste;
using CelesteIOS;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Monocle;
using MonoMod.RuntimeDetour;
using SDL2;
namespace CelesteJIT.Game;
public static class ControllerIntegration
{
    private static readonly FieldInfo devices=typeof(GamePad).Assembly.GetType("Microsoft.Xna.Framework.SDL2_FNAPlatform",true)
        .GetField("INTERNAL_devices",BindingFlags.Static|BindingFlags.NonPublic) ?? throw new MissingFieldException("FNA SDL controller handles");
    private static readonly List<Hook> hooks=new();
    private static IntPtr device;
    private static int player=-1;
    private static bool active,suspended,resumePending;
    private static Color lastColor,lastReported;
    private static int reportedPlayer=-1;
    private static bool hasColor;
    private static string automatic="xb1";
    private delegate string PrefixOriginal(Input.PrefixMode mode);
    private delegate string PrefixDetour(PrefixOriginal orig,Input.PrefixMode mode);
    private delegate void LightOriginal(PlayerIndex index,Color color);
    private delegate void LightDetour(LightOriginal orig,PlayerIndex index,Color color);
    public static void Install() {
        hooks.Add(new Hook(typeof(Input).GetMethod(nameof(Input.GuiInputPrefix),new[]{typeof(Input.PrefixMode)}),
            (PrefixDetour)((orig,mode)=>{
                string value=orig(mode);
                if(!string.IsNullOrEmpty(Input.OverrideInputPrefix) || (mode==Input.PrefixMode.Latest && TouchPort.Source!=InputSource.Controller) || value=="keyboard")return value;
                return ResolvePrefix(TouchPort.Configuration?.ControllerPrompts??"automatic",device!=IntPtr.Zero?automatic:value);
            })));
        hooks.Add(new Hook(typeof(GamePad).GetMethod(nameof(GamePad.SetLightBarEXT)),(LightDetour)((orig,index,color)=>{
            if((int)index==Input.Gamepad){lastColor=color;hasColor=true;}
            orig(index,color);
            ReportLight((int)index,color);
        })));
    }
    public static string ResolvePrefix(string mode,string detected)=>mode switch {
        "xbox"=>"xb1","playstation"=>"ps4","switch"=>"ns","stadia"=>"stadia",_=>detected};
    private static IntPtr Device(int index) {
        var values=(IntPtr[])devices.GetValue(null);
        return values!=null && index>=0 && index<values.Length?values[index]:IntPtr.Zero;
    }
    // The pinned SDL types 11–13 are Joy-Con; the pinned C# binding stops at PS5.
    public static string DetectPrefix(SDL.SDL_GameControllerType type,string guid,string fallback)=>type switch {
        SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_PS3 or SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_PS4 or SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_PS5=>"ps4",
        SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_PRO or (SDL.SDL_GameControllerType)11 or (SDL.SDL_GameControllerType)12 or (SDL.SDL_GameControllerType)13=>"ns",
        SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_XBOX360 or SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_XBOXONE=>"xb1",
        (SDL.SDL_GameControllerType)9=>"stadia",
        _=>guid=="d1180094"?"stadia":fallback};
    // Native suspends game ticks before SDL's focus events can be polled. Both
    // lost/gained events may therefore finish before the next input update.
    public static void Suspend() {suspended=true;active=false;}
    public static void Resume() {
        if(!suspended)return;
        suspended=false;resumePending=true;
    }
    public static void Update() {
        int index=Input.Gamepad;var current=Device(index);bool foreground=!suspended && Engine.Instance.IsActive;
        bool changed=player!=index || device!=current, resumed=!active && foreground;
        active=foreground;if(!changed && !resumed && !resumePending)return;
        if(changed || resumed) {
            player=index;device=current;reportedPlayer=-1;
            if(current==IntPtr.Zero){automatic="xb1";return;}
            var type=SDL.SDL_GameControllerGetType(current);string guid=GamePad.GetGUIDEXT((PlayerIndex)index);
            string legacy=guid is "4c05c405" or "4c05cc09"?"ps4":guid is "7e050920" or "7e053003"?"ns":"xb1";
            automatic=DetectPrefix(type,guid,legacy);
            Entry.Mark("game_controller_identity","player="+index+"; name="+SDL.SDL_GameControllerName(current)+"; type="+type+"; guid="+guid+"; prompts="+automatic+"; light="+GamePad.GetCapabilities((PlayerIndex)index).HasLightBarEXT);
        }
        // Celeste sets level colours at particular scene changes. Replay its
        // last requested colour after a late connection, player change or resume.
        if(foreground && current!=IntPtr.Zero) {
            resumePending=false;
            if(hasColor)GamePad.SetLightBarEXT((PlayerIndex)index,lastColor);
        }
    }
    private static void ReportLight(int index,Color color) {
        var target=Device(index);
        if(target==IntPtr.Zero || (reportedPlayer==index && color==lastReported))return;
        reportedPlayer=index;lastReported=color;
        Entry.Mark("game_controller_light","player="+index+"; rgb="+color.R+","+color.G+","+color.B+"; supported="+(SDL.SDL_GameControllerHasLED(target)==SDL.SDL_bool.SDL_TRUE));
    }
    public static void Dispose(){foreach(var hook in hooks)hook.Dispose();hooks.Clear();device=IntPtr.Zero;player=-1;active=suspended=resumePending=hasColor=false;lastColor=lastReported=default;reportedPlayer=-1;automatic="xb1";}
}
