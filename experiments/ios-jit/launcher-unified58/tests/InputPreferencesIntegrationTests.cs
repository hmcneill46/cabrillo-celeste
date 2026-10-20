// Private integration against the original prepared game and real SDL controller
// backend. The virtual controller is a test device, never a physical-light claim.
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.Json;
using Celeste;
using CelesteIOS;
using CelesteJIT.Game;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Monocle;
using MonoMod.RuntimeDetour;
using SDL2;
public static class InputPreferencesIntegrationTests
{
    [DllImport("CJGraphicsNative")]static extern void CJTestTouchRevision(int revision);
    [DllImport("CJGraphicsNative")]static extern int CJTestController(int operation,int argument);
    static int stage,ticks,checks;static ulong lastFrame=ulong.MaxValue;static TouchConfiguration config;
    static bool originalFeather;
    static Hook grabObserver;
    delegate void GrabOriginal();
    delegate void GrabDetour(GrabOriginal orig);
    static readonly BindingFlags Private=BindingFlags.Static|BindingFlags.NonPublic;
    static void Check(bool value,string name){if(!value)throw new Exception("Input preferences: "+name);checks++;Console.WriteLine("INPUT_PREFERENCE_CHECK "+name);}
    static void Configure(TouchConfiguration value)=>typeof(InputPreferences).GetMethod("Configure",Private).Invoke(null,new object[]{value});
    static void Source(InputSource value) {
        var policy=(InputSourcePolicy)typeof(TouchPort).GetField("inputSource",Private).GetValue(null);
        policy.Observe(value==InputSource.Touch,value==InputSource.Keyboard,value==InputSource.Controller,true);
        typeof(InputPreferences).GetMethod("Observe",Private).Invoke(null,new object[]{value});
    }
    static void Save(){File.WriteAllText(Environment.GetEnvironmentVariable("CJIT_TOUCH_CONFIG"),JsonSerializer.Serialize(config,TouchConfiguration.JSON));CJTestTouchRevision(100+stage);}
    sealed class RawGrab:VirtualButton.Node {
        public bool Down,Edge;
        public override bool Check=>Down;
        public override bool Pressed=>Edge;
        public override bool Released=>false;
    }
    static void GrabContracts() {
        var node=new RawGrab();Input.Grab.Nodes.Add(node);
        // Each synthetic edge represents a new input update, including the
        // original VirtualButton's buffer/consumption lifecycle. Several draws
        // can occur between actual updates under Motion Smoothing.
        void Edge(){node.Down=node.Edge=true;Input.Grab.Update();Input.UpdateGrab();node.Edge=false;}
        void Release(){node.Down=false;Input.Grab.Update();Input.UpdateGrab();}
        try {
            foreach(var mode in new[]{"hold","invert","toggle"}) {
                var p=TouchConfiguration.Default(960,540,default,false);p.Grab=mode;p.ControllerGrab="hold";p.KeyboardGrab="invert";Configure(p);Source(InputSource.Touch);
                Check(Settings.Instance.GrabMode==(mode=="hold"?GrabModes.Hold:mode=="invert"?GrabModes.Invert:GrabModes.Toggle),"actual Celeste setting selects "+mode);
                Input.ResetGrab();node.Down=false;
                Check(Input.GrabCheck==(mode=="invert"),"original idle "+mode);Edge();
                Check(Input.GrabCheck==(mode!="invert"),"original press "+mode);Release();
                Check(Input.GrabCheck==(mode!="hold"),"original release "+mode);
                Input.ResetGrab();Check(Input.GrabCheck==(mode=="invert"),"original reset "+mode);
            }
            config=TouchConfiguration.Default(960,540,default,false);config.Grab="toggle";config.ControllerGrab="hold";config.KeyboardGrab="invert";config.ToggleBehavior="persistent";
            Configure(config);Source(InputSource.Touch);Edge();Release();Check(Input.GrabCheck,"persistent toggle uses original latch");
            Input.ResetGrab();Check(Input.GrabCheck,"persistent preserves original latch across the game's reset entrypoint");
            Source(InputSource.Controller);Check(Settings.Instance.GrabMode==GrabModes.Hold && !Input.GrabCheck,"controller automatically uses original Hold");
            Edge();Check(Input.GrabCheck,"original controller Hold down");Release();Check(!Input.GrabCheck,"original controller Hold released");
            Source(InputSource.Keyboard);Check(Settings.Instance.GrabMode==GrabModes.Invert && Input.GrabCheck,"keyboard automatically uses original Inverse");
            Source(InputSource.Touch);Check(Settings.Instance.GrabMode==GrabModes.Toggle && Input.GrabCheck,"return to touch restores its persistent latch");
            Edge();Release();Check(!Input.GrabCheck,"fresh original grab edge untoggles");
            Edge();Release();Source(InputSource.Controller);Settings.Instance.GrabMode=GrabModes.Invert;Source(InputSource.Keyboard);Source(InputSource.Controller);
            Check(Settings.Instance.GrabMode==GrabModes.Invert && config.ControllerGrab=="invert","ordinary Celeste Options change remembers only that source");
            Source(InputSource.Touch);Check(Settings.Instance.GrabMode==GrabModes.Toggle && Input.GrabCheck,"other source preference and latch survive game Options change");
            var next=TouchConfiguration.Decode(JsonSerializer.Serialize(config,TouchConfiguration.JSON));next.ToggleBehavior="default";Configure(next);config=next;
            Check(!Input.GrabCheck,"returning to default clears persistent grab");Edge();Release();Source(InputSource.Keyboard);Source(InputSource.Touch);Check(!Input.GrabCheck,"default source change does not carry a toggle");
            Edge();Release();next=TouchConfiguration.Decode(JsonSerializer.Serialize(config,TouchConfiguration.JSON));next.Grab="hold";Configure(next);config=next;
            Check(Settings.Instance.GrabMode==GrabModes.Hold && !Input.GrabCheck,"live mode change releases former toggle");
            // No GrabCheck detour is installed: original virtual nodes, including
            // mod-provided nodes, participate in every tested mode above.
        } finally {node.Down=node.Edge=false;Input.Grab.Nodes.Remove(node);Source(InputSource.Touch);}
        foreach(var type in new[]{SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_PS3,SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_PS4,SDL.SDL_GameControllerType.SDL_CONTROLLER_TYPE_PS5})
            Check(ControllerIntegration.DetectPrefix(type,"4c05e60c","xb1")=="ps4","SDL PlayStation family "+type);
        Check(ControllerIntegration.DetectPrefix((SDL.SDL_GameControllerType)13,"","xb1")=="ns","SDL Joy-Con family");
        Check(ControllerIntegration.DetectPrefix((SDL.SDL_GameControllerType)9,"","xb1")=="stadia","SDL Stadia family");
        Check(ControllerIntegration.ResolvePrefix("xbox","ps4")=="xb1" && ControllerIntegration.ResolvePrefix("playstation","xb1")=="ps4","manual prompts override both ways");
    }
    public static void Run() {
        if(stage==99 || stage<0 || !TouchInputIntegrationTests.Complete)return;
        if(lastFrame==Engine.FrameCounter)return;lastFrame=Engine.FrameCounter;
        if(++ticks<3)return;ticks=0;
        if(stage==0) {
            Check(!Enumerable.Range(0,4).Any(i=>GamePad.GetState((PlayerIndex)i).IsConnected),"fixture starts without real hardware controllers");
            // Motion Smoothing intentionally suppresses UpdateGrab between
            // game updates. Run these contracts inside an accepted original
            // UpdateGrab call, below that mod's outer timing hook. Do not
            // bypass or change the mod's timing to make a draw-time test pass.
            grabObserver=new Hook(typeof(Input).GetMethod(nameof(Input.UpdateGrab)),(GrabDetour)(orig=>{
                orig();
                if(stage!=-1)return;stage=-2;
                GrabContracts();originalFeather=FeatherTouch.Enabled;config.FeatherTouch=!originalFeather;stage=1;Save();
            }));
            stage=-1;
        } else if(stage==1) {
            grabObserver.Dispose();grabObserver=null;
            Check(FeatherTouch.Enabled!=originalFeather,"feather changes during original game session");config.FeatherTouch=originalFeather;stage=2;Save();
        } else if(stage==2) {
            Check(FeatherTouch.Enabled==originalFeather,"feather can be changed back without restart");
            Input.SetLightbarColor(new Color(128,200,32));Check(CJTestController(1,0)>=0,"attach real SDL virtual DualSense");stage=3;
        } else if(stage==3) {
            Check(GamePad.GetState(PlayerIndex.One).IsConnected,"FNA receives SDL controller connection");
            Check(TouchPort.Source==InputSource.Touch,"idle controller does not take touch focus");
            Check(GamePad.GetCapabilities(PlayerIndex.One).HasLightBarEXT,"FNA exposes virtual LED capability");
            Check(Input.GuiInputPrefix(Input.PrefixMode.Attached)=="ps4","actual game automatic prompts identify SDL DualSense");
            Check(CJTestController(5,0)>0,"late attachment receives previously requested light colour");
            int expected=((int)(Math.Pow(128/255f,3)*255)<<16)|((int)(Math.Pow(200/255f,3)*255)<<8)|(int)(Math.Pow(32/255f,3)*255);
            Check(CJTestController(4,0)==expected,"original Celeste colour transform reaches SDL LED callback exactly");
            config.ControllerPrompts="xbox";stage=4;Save();
        } else if(stage==4) {
            Check(Input.GuiInputPrefix(Input.PrefixMode.Attached)=="xb1","live Xbox override on PlayStation controller");
            Check(Input.GuiInputPrefix(Input.PrefixMode.Latest)=="keyboard","touch prompts remain touch with manual controller override");
            CJTestController(2,1);stage=5;
        } else if(stage==5) {
            Check(TouchPort.Source==InputSource.Controller,"real controller activity selects controller source");
            Check(Settings.Instance.GrabMode==GrabModes.Invert,"real source switch restores saved controller grab setting");
            Check(Input.GuiInputPrefix()=="xb1" && Input.GuiInputController(),"active controller uses chosen original glyph family");
            CJTestController(2,0);config.ControllerPrompts="playstation";stage=6;Save();
        } else if(stage==6) {
            Check(Input.GuiInputPrefix()=="ps4","manual PlayStation symbols are live");
            Input.OverrideInputPrefix="ns";Check(Input.GuiInputPrefix()=="ns","explicit mod prompt override takes precedence");Input.OverrideInputPrefix=null;
            Input.SetLightbarColor(Color.Red);Check(CJTestController(4,0)==0xff0000,"subsequent original level colour passes through");
            CJTestController(3,0);stage=7;
        } else if(stage==7) {
            Check(!GamePad.GetState(PlayerIndex.One).IsConnected && TouchPort.Source==InputSource.Touch,"disconnect returns to touch");
            Check(Settings.Instance.GrabMode==GrabModes.Hold,"disconnect restores touch's selected original mode");
            Check(CJTestController(1,0)>=0,"reattach virtual controller");stage=8;
        } else if(stage==8) {
            Check(CJTestController(4,0)==0xff0000,"reattachment restores latest game colour");CJTestController(3,0);
            File.Delete(Environment.GetEnvironmentVariable("CJIT_TOUCH_CONFIG"));CJTestTouchRevision(199);stage=99;
            Console.WriteLine("PASS_INPUT_PREFERENCES_REAL_GAME checks="+checks);
        }
    }
}
