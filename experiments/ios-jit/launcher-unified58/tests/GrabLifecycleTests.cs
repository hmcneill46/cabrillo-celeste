// Private real-death and cross-map test; never packaged in the application.
using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Runtime.InteropServices;
using Celeste;
using CelesteJIT.Game;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Monocle;
public static class SessionIntegrationTests {
    [DllImport("CJGraphicsNative")]static extern void CJTestTouchRevision(int revision);
    static int stage,checks,ticks,otherArea;static Player oldPlayer;static Session original;static TouchConfiguration config;
    static void Check(bool value,string message){if(!value)throw new Exception("Grab lifecycle: "+message);checks++;Console.WriteLine("GRAB_LIFECYCLE_CHECK "+message);}
    static void Save(){File.WriteAllText(Environment.GetEnvironmentVariable("CJIT_TOUCH_CONFIG"),JsonSerializer.Serialize(config,TouchConfiguration.JSON));CJTestTouchRevision(500+stage);}
    sealed class Press:VirtualButton.Node {public override bool Check=>true;public override bool Pressed=>true;public override bool Released=>false;}
    static void Toggle(){var node=new Press();Input.Grab.Nodes.Add(node);try{Input.UpdateGrab();}finally{Input.Grab.Nodes.Remove(node);}}
    public static void Run(GraphicsDevice graphics) {
        if(stage==99 || ++ticks<3)return;ticks=0;
        if(Engine.Scene is not Level level)return;
        var player=level.Tracker.GetEntity<Player>();if(player==null || player.Dead || level.Paused || level.Transitioning || level.InCutscene)return;
        if(stage==0) {
            original=level.Session;config=TouchConfiguration.Default(960,540,default,false);config.ToggleBehavior="persistent";stage=1;Save();
        } else if(stage==1) {
            Check(Settings.Instance.GrabMode==GrabModes.Toggle,"persistent selects original Toggle");Toggle();Check(Input.GrabCheck,"grab latched before real death");
            oldPlayer=player;stage=2;Check(player.Die(Vector2.UnitY,true)!=null,"original Player death starts");
        } else if(stage==2) {
            if(ReferenceEquals(player,oldPlayer))return;
            Check(Input.GrabCheck,"persistent grab survives actual death and respawn");
            otherArea=AreaData.Areas.First(a=>a.LevelSet=="Celeste" && a.ID>0 && a.ID!=original.Area.ID).ID;
            stage=3;Engine.Scene=new LevelLoader(new Session(new AreaKey(otherArea)));
        } else if(stage==3) {
            if(level.Session.Area.ID!=otherArea)return;
            Check(Input.GrabCheck,"persistent grab survives loading another map");stage=4;Engine.Scene=new LevelLoader(original);
        } else if(stage==4) {
            if(level.Session.Area.ID!=original.Area.ID)return;
            Check(Input.GrabCheck,"persistent grab survives returning to prior map");config.ToggleBehavior="default";stage=5;Save();
        } else if(stage==5) {
            Check(!Input.GrabCheck,"default option clears persistent state");Toggle();Check(Input.GrabCheck,"default toggles before death");oldPlayer=player;stage=6;Check(player.Die(Vector2.UnitY,true)!=null,"default original death starts");
        } else if(stage==6) {
            if(ReferenceEquals(player,oldPlayer))return;
            Check(!Input.GrabCheck,"default grab clears after actual death and respawn");
            File.Delete(Environment.GetEnvironmentVariable("CJIT_TOUCH_CONFIG"));CJTestTouchRevision(599);stage=99;Console.WriteLine("PASS_REAL_GRAB_DEATH_AND_MAPS checks="+checks);
        }
    }
}
