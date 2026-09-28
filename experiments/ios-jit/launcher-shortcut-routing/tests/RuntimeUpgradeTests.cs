// External host fixture. Never packaged or loaded on iOS.
using System;
using System.Linq;
using Celeste;
using Celeste.Mod;
using Celeste.Mod.Helpers;
using CelesteJIT.Game;
using Microsoft.Xna.Framework;
using Monocle;

public static class RuntimeUpgradeTests
{
    sealed class FreezeProbe : Entity { public int Count; public override void Update() { Count++; } }
    static bool springRequested, springPlayed;
    static void Check(bool value, string detail) {
        if (!value) throw new InvalidOperationException("Runtime upgrade: " + detail);
        Console.WriteLine("RUNTIME_UPGRADE_PASS " + detail);
    }
    public static void Run() {
        Check(Everest.VersionString == "1.6580.0-cjit-082e21b", "actual rebuilt Everest source/version");
        Check(Everest.Modules.Single(m=>m.Metadata.Name=="Everest").Metadata.Version==new Version("1.6580.0"), "actual registered numeric version");
        Check(!(Engine.Scene is Level), "dust scene-transition control starts outside Level");
        Dust.Burst(Vector2.Zero, 0f, 1, null);
        Dust.BurstFG(Vector2.Zero, 0f, 1, 0f, null);
        Check(true, "both new Dust guards return safely outside a Level");
        var mirrors=ModUpdaterHelper.GetAllMirrorUrls("https://gamebanana.com/mmdl/870370");
        var first=mirrors.Cast<string>().ToArray();
        Check(first.Length>0 && first.All(s=>s.Contains("870370")) && first.SequenceEqual(mirrors.Cast<string>()), "upstream mirror enumerable supports repeated enumeration");
        var scene = new Scene();
        var tagged = new FreezeProbe { Tag = TagsExt.FreezeFrameUpdate };
        var inactive = new FreezeProbe { Tag = TagsExt.FreezeFrameUpdate, Active = false };
        var ordinary = new FreezeProbe();
        scene.Add(tagged); scene.Add(inactive); scene.Add(ordinary); scene.Entities.UpdateLists();
        scene.FreezeFrameUpdate();
        Check(tagged.Count == 1 && inactive.Count == 0 && ordinary.Count == 0, "freeze frame updates only active tagged entities");
        scene.Paused = true; scene.FreezeFrameUpdate();
        Check(tagged.Count == 1, "paused scene suppresses freeze frame updates");
        using var module = Mono.Cecil.ModuleDefinition.CreateModule("CursorControl", Mono.Cecil.ModuleKind.Dll);
        var method = new Mono.Cecil.MethodDefinition("CursorControl", Mono.Cecil.MethodAttributes.Public|Mono.Cecil.MethodAttributes.Static, module.TypeSystem.Void);
        var il = method.Body.GetILProcessor();
        il.Emit(Mono.Cecil.Cil.OpCodes.Nop); il.Emit(Mono.Cecil.Cil.OpCodes.Ldc_I4_1); il.Emit(Mono.Cecil.Cil.OpCodes.Pop); il.Emit(Mono.Cecil.Cil.OpCodes.Nop); il.Emit(Mono.Cecil.Cil.OpCodes.Ret);
        using var context = new MonoMod.Cil.ILContext(method);
        var cursor = new MonoMod.Cil.ILCursor(context) { Index = 2 };
        Check(cursor.TryGotoPrevBestFit(MonoMod.Cil.MoveType.Before, instr => instr.OpCode == Mono.Cecil.Cil.OpCodes.Nop) && cursor.Index == 0,
              "single-predicate previous-best-fit cursor moves backward");
        Console.WriteLine("PASS_REAL_EVEREST_6580_SOURCE_CONTROLS");
    }
    public static void TickSpring() {
        if (Environment.GetEnvironmentVariable("CJIT_HOST_SPRING") != "1") return;
        const string sid="SpringCollab2020/1-Beginner/Lichtbaulb";
        if(!springRequested && Engine.Scene is Overworld world && world.Current is OuiTitleScreen && CelesteJIT.Game.Platform.RunThreadActiveCount==0 && !UserIO.Saving) {
            var prior=UserIO.Load<SaveData>("0");
            SaveData.Start(prior ?? new SaveData { Name="Madeline" },0);
            var area=AreaData.Get(sid) ?? throw new InvalidOperationException("Original Spring Starjump not loaded");
            var saved=SaveData.Instance.CurrentSession_Safe;
            bool resume=saved!=null && saved.Area.GetSID()==sid;
            if(Environment.GetEnvironmentVariable("CJIT_HOST_EXPECT_SPRING_RESUME")=="1") Check(resume,"fresh process reloads the saved Spring session");
            Console.WriteLine("SPRING_SESSION_LOAD existing="+(prior!=null)+"; resumed="+resume+"; sid="+sid+"; room="+saved?.Level);
            springRequested=true;
            Engine.Scene=new LevelLoader(resume?saved:new Session(new AreaKey(area.ID)));
        }
        if(springRequested && !springPlayed && Engine.Scene is Level level && level.Tracker.GetEntity<Player>()!=null) {
            Check(level.Session.Area.GetSID()==sid,"original Spring Starjump gameplay");
            foreach(var pair in new[]{("ExtendedVariantMode","0.51.0"),("MaxHelpingHand","1.40.10")})
                Check(Everest.Modules.Single(m=>m.Metadata.Name==pair.Item1).Metadata.Version==new Version(pair.Item2),"current helper registered: "+pair.Item1+" "+pair.Item2);
            Dust.Burst(level.Tracker.GetEntity<Player>().Position,0f,2,null);
            Dust.BurstFG(level.Tracker.GetEntity<Player>().Position,0f,2,0f,null);
            Check(true,"normal Level dust still executes");
            springPlayed=true;
            Console.WriteLine("PASS_REAL_SPRING_STARJUMP_CURRENT_HELPERS sid="+sid+"; room="+level.Session.Level);
        }
    }
}
