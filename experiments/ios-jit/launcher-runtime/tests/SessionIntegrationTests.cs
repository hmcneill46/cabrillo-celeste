// Desktop-only integration, executed on the real game draw thread and never bundled.
using System;
using System.Linq;
using Celeste;
using Celeste.Mod;
using CelesteIOS;
using CelesteJIT.Game;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using Monocle;
public static class SessionIntegrationTests
{
    private static bool complete;
    private static int checks;
    private static void Check(bool value,string description) {
        if(!value)throw new InvalidOperationException("Session integration: "+description);
        checks++;Console.WriteLine("SESSION_CONTRACT_PASS "+description);
    }
    public static void Run(GraphicsDevice device)
    {
        RuntimeUpgradeTests.TickSpring();
        if(complete || GFX.Gui==null || Input.Jump==null)return;
        complete=true;
        ReflectionFlagsTests.Run();
        RuntimeUpgradeTests.Run();
        var module=Everest.Modules.Single(m=>m.Metadata.Name==IOSPlatformModule.ID);
        Check(module is IOSPlatformModule && module.Metadata.Version==new Version(1,0,0),"required support registered once before user mods");
        var policy=new InputSourcePolicy();
        Check(policy.Current==InputSource.Touch,"touch default");
        policy.Observe(false,false,false,true);Check(policy.Current==InputSource.Touch,"idle connection does not steal prompts");
        policy.Observe(false,false,true,true);Check(policy.Current==InputSource.Controller,"controller activity wins");
        policy.Observe(true,false,false,true);Check(policy.Current==InputSource.Touch,"touch recovers with a connected pad");
        policy.Observe(false,false,false,true);Check(policy.Current==InputSource.Touch,"idle pad stays idle");
        policy.Observe(false,true,false,true);Check(policy.Current==InputSource.Keyboard,"keyboard activity wins");
        policy.Observe(false,false,true,true);policy.Observe(false,false,false,false);Check(policy.Current==InputSource.Touch,"unplugged active controller restores touch");
        policy.Observe(true,true,true,true);Check(policy.Current==InputSource.Touch,"simultaneous touch priority");
        Check(TouchPort.Source==InputSource.Touch,"actual game default input source");
        foreach(var button in new[]{Input.Jump,Input.Dash,Input.Grab,Input.Pause,Input.MenuJournal,Input.MenuConfirm,Input.MenuCancel,Input.Talk}) {
            var glyph=TouchPort.Prompt(button);
            Check(glyph!=null && ReferenceEquals(glyph,Input.GuiButton(button,Input.PrefixMode.Latest,"controls/keyboard/oemquestion")),"actual patched GuiButton uses shared glyph");
            Check(glyph.Width==80 && glyph.Height==80,"stock-sized centered glyph canvas");
            Color[] pixels=new Color[80*80];glyph.Texture.Texture.GetData(pixels);
            Check(pixels.Any(c=>c.A>200) && pixels[0].A==0 && pixels[79].A==0 && pixels[6320].A==0 && pixels[6399].A==0,"real Metal glyph pixels and transparent corners");
        }
        Check(TouchPort.Prompt(Input.CrouchDash)==null,"unbound crouch dash does not get a fabricated touch glyph");
        Check(!ReferenceEquals(Input.GuiButton(Input.Jump,Input.PrefixMode.Attached,"controls/keyboard/oemquestion"),TouchPort.Prompt(Input.Jump)),"explicit hardware binding display remains original");
        Check(Input.GuiInputPrefix(Input.PrefixMode.Latest)=="keyboard" && !Input.GuiInputController(Input.PrefixMode.Latest),"touch is not a fake gamepad");
        Console.WriteLine("PASS_REAL_IOS_SUPPORT_AND_TOUCH_GLYPHS checks="+checks);
    }
}
