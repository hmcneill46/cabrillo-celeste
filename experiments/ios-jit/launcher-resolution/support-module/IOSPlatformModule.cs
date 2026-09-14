// Required game-side integration, bundled separately from the runtime adapter.
// UI, JIT, downloads and profile transactions belong to the native host.
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.InteropServices;
using Celeste;
using Celeste.Mod;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Monocle;
using MonoMod.RuntimeDetour;
namespace CelesteIOS;

public enum InputSource { Touch, Keyboard, Controller }
public sealed class PlatformServices
{
    public Action<string,string> Log;
    public Action BindInput;
    public Func<InputSource> InputSource;
    public Func<VirtualButton,MTexture> TouchPrompt;
}
public sealed class IOSPlatformModule : EverestModule
{
    public const string ID="CelesteIOS", ModuleVersion="1.0.0";
    public const int ABI=1;
    private static PlatformServices services;
    private static IOSPlatformModule instance;
    private readonly List<Hook> hooks=new();
    [DllImport("CJGraphicsNative",CallingConvention=CallingConvention.Cdecl)] private static extern int CJSessionOpen(int abi);
    [DllImport("CJGraphicsNative",CallingConvention=CallingConvention.Cdecl)] private static extern int CJSessionRequestQuit(int abi,int origin);
    public IOSPlatformModule() { Metadata=new EverestModuleMetadata {Name=ID,VersionString=ModuleVersion}; }
    public static void Bootstrap(PlatformServices value)
    {
        if(services!=null || value==null || CJSessionOpen(ABI)!=1)throw new InvalidOperationException("iOS support host ABI or process lifetime mismatch.");
        services=value;
        Everest.Events.Everest.OnRegisterModule+=RegisterAfterVanilla;
    }
    private static void RegisterAfterVanilla(EverestModule module)
    {
        if(module.Metadata.Name!="Celeste")return;
        Everest.Events.Everest.OnRegisterModule-=RegisterAfterVanilla;
        instance=new IOSPlatformModule();instance.Register();
        // Same pinned Everest metadata lifecycle as built-in Core/vanilla modules.
        typeof(EverestModuleMetadata).GetMethod("RegisterMod",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(instance.Metadata,null);
        services.Log("everest_ios_support_registered",ID+" "+ModuleVersion+"; ABI="+ABI+"; required bundled module");
    }
    private delegate void ExitOriginal(Game game);
    private delegate void ExitHook(ExitOriginal orig,Game game);
    private delegate MTexture ButtonOriginal(VirtualButton button,Input.PrefixMode mode,string fallback);
    private delegate MTexture ButtonHook(ButtonOriginal orig,VirtualButton button,Input.PrefixMode mode,string fallback);
    private delegate string PrefixOriginal(Input.PrefixMode mode);
    private delegate string PrefixHook(PrefixOriginal orig,Input.PrefixMode mode);
    private delegate bool ControllerOriginal(Input.PrefixMode mode);
    private delegate bool ControllerHook(ControllerOriginal orig,Input.PrefixMode mode);
    public override void Load()
    {
        if(services==null)throw new InvalidOperationException("CelesteIOS must be loaded by the matching iOS host.");
        hooks.Add(new Hook(typeof(Game).GetMethod(nameof(Game.Exit)),(ExitHook)((orig,game)=>{
            if(!ReferenceEquals(game,global::Celeste.Celeste.Instance)){orig(game);return;}
            int accepted=CJSessionRequestQuit(ABI,1);
            services.Log("game_quit_requested","origin=Game.Exit; accepted="+accepted);
            if(accepted==0)throw new InvalidOperationException("The iOS host rejected the Quit request.");
            // Keep frames alive until the host drains UserIO and ends the loop.
        })));
        hooks.Add(new Hook(typeof(Input).GetMethod(nameof(Input.GuiButton),new[]{typeof(VirtualButton),typeof(Input.PrefixMode),typeof(string)}),
            (ButtonHook)((orig,button,mode,fallback)=>mode==Input.PrefixMode.Latest && services.InputSource()==InputSource.Touch
                ? services.TouchPrompt(button) ?? orig(button,mode,fallback) : orig(button,mode,fallback))));
        hooks.Add(new Hook(typeof(Input).GetMethod(nameof(Input.GuiInputPrefix),new[]{typeof(Input.PrefixMode)}),
            (PrefixHook)((orig,mode)=>mode==Input.PrefixMode.Latest && services.InputSource()!=InputSource.Controller ? "keyboard" : orig(mode==Input.PrefixMode.Latest ? Input.PrefixMode.Attached : mode))));
        hooks.Add(new Hook(typeof(Input).GetMethod(nameof(Input.GuiInputController),new[]{typeof(Input.PrefixMode)}),
            (ControllerHook)((orig,mode)=>mode==Input.PrefixMode.Latest ? services.InputSource()==InputSource.Controller : orig(mode))));
        Everest.Events.Input.OnInitialize+=services.BindInput;
    }
    public override void Unload()
    {
        Everest.Events.Input.OnInitialize-=services.BindInput;
        for(int i=hooks.Count-1;i>=0;i--)hooks[i].Dispose();
        hooks.Clear();
    }
    public static void Shutdown() { instance?.Unload(); }
}
