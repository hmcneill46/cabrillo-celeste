using System;
using System.Linq;
using System.Runtime.Loader;
using Celeste;
using Celeste.Mod;
using Celeste.Mod.Entities;
using Celeste.Mod.MaxHelpingHand.Entities;
using Microsoft.Xna.Framework;
using Monocle;

namespace CJITSJHelpers;

// Ordinary diagnostic mod; the two original helper ZIPs are never modified.
public sealed class HelperProbeModule : EverestModule
{
    public static int Frames, RenderFrames, ResumeSignals;
    public static int LuaBegins, LuaWaits, LuaResumes, LuaEnds, LuaSkipped;
    public static int LuaBeginFrame, LuaWaitFrame, LuaResumeFrame, LuaEndFrame;
    public static double LuaStartX, LuaWalkX;
    public static int PlatformContacts;
    public static float PlatformMinX = float.MaxValue, PlatformMaxX = float.MinValue, CarriedDistance;
    public static int HelperEntityFrames, HelperFramesAfterResume;
    public static string ContextName;

    public override void Load()
    {
        ContextName = AssemblyLoadContext.GetLoadContext(GetType().Assembly)?.Name;
        Console.WriteLine("CJIT_SJ_HELPERS loaded; context=" + ContextName);
    }

    public override void Unload() => Console.WriteLine("CJIT_SJ_HELPERS unloaded");

    // Native host only supplies the lifecycle observation; Lua must resume its
    // own retained coroutine, call this method and finish the real cutscene.
    public static void NotifyResume() => ResumeSignals++;

    public static int LuaCheckpoint(string phase, double x, double y)
    {
        switch (phase)
        {
            case "begin": LuaBegins++; LuaBeginFrame = Frames; LuaStartX = x; break;
            case "waiting": LuaWaits++; LuaWaitFrame = Frames; LuaWalkX = x; break;
            case "resumed": LuaResumes++; LuaResumeFrame = Frames; break;
            case "end": LuaEnds++; LuaEndFrame = Frames; break;
            case "skipped": LuaSkipped++; break;
            default: throw new InvalidOperationException("Unknown Lua checkpoint: " + phase);
        }
        Console.WriteLine("CJIT_SJ_LUA phase=" + phase + "; frame=" + Frames + "; x=" + x + "; y=" + y);
        return 42;
    }

    public static bool LuaWalkPassed => LuaBegins == 1 && LuaWaits == 1 && LuaWaitFrame - LuaBeginFrame >= 10 && LuaWalkX - LuaStartX >= 20;
    public static bool LuaResumePassed => LuaWalkPassed && ResumeSignals > 0 && LuaResumes == 1 && LuaEnds == 1 && LuaSkipped == 0 && LuaResumeFrame > LuaWaitFrame;
    public static bool PlatformPassed => PlatformContacts >= 30 && PlatformMaxX - PlatformMinX >= 64 && CarriedDistance >= 16 && HelperEntityFrames >= 120;

    public static string Summary() =>
        "luaBegin=" + LuaBegins + "; luaWait=" + LuaWaits + "; luaResume=" + LuaResumes + "; luaEnd=" + LuaEnds +
        "; luaSkipped=" + LuaSkipped + "; walkDelta=" + (LuaWalkX - LuaStartX) + "; coroutineFrames=" + (LuaResumeFrame - LuaWaitFrame) +
        "; platformContact=" + PlatformContacts + "; platformTravel=" + (PlatformMaxX - PlatformMinX) + "; carriedDistance=" + CarriedDistance + "; helperFrames=" + HelperEntityFrames + "; afterResume=" + HelperFramesAfterResume +
        "; rendered=" + RenderFrames + "; resumes=" + ResumeSignals;

    public static void Validate()
    {
        if (!LuaResumePassed || !PlatformPassed || RenderFrames < 120 || HelperFramesAfterResume < 120)
            throw new InvalidOperationException("SJ helper room incomplete: " + Summary());
    }
}

[CustomEntity("CJITSJHelpers/status")]
public sealed class HelperStatus : Entity
{
    private float previousPlayerX;
    private bool wasRiding;
    public HelperStatus(EntityData data, Vector2 offset) : base(data.Position + offset) { Depth = -1000001; }

    public override void Update()
    {
        base.Update();
        if (!(Scene is Level level)) return;
        HelperProbeModule.Frames++;
        Player player = level.Tracker.GetEntity<Player>();
        if (player == null || player.Dead) return;
        var platform = level.Entities.OfType<MultiNodeMovingPlatform>().FirstOrDefault();
        if (platform != null) HelperProbeModule.HelperEntityFrames++;
        if (HelperProbeModule.ResumeSignals > 0) HelperProbeModule.HelperFramesAfterResume++;
        bool riding = platform != null && player.OnGround() && player.CollideCheck(platform, player.Position + Vector2.UnitY);
        if (platform != null)
        {
            HelperProbeModule.PlatformMinX = Math.Min(HelperProbeModule.PlatformMinX, platform.X);
            HelperProbeModule.PlatformMaxX = Math.Max(HelperProbeModule.PlatformMaxX, platform.X);
        }
        if (riding)
        {
            HelperProbeModule.PlatformContacts++;
            if (wasRiding && Input.MoveX.Value == 0 && HelperProbeModule.LuaWalkPassed)
                HelperProbeModule.CarriedDistance += Math.Abs(player.X - previousPlayerX);
        }
        wasRiding = riding;
        previousPlayerX = player.X;
    }

    public override void Render()
    {
        base.Render();
        if (!(Scene is Level level)) return;
        HelperProbeModule.RenderFrames++;
        Vector2 at = level.Camera.Position + new Vector2(12, 57);
        Draw.Rect(at.X - 4, at.Y - 3, 270, 32, Color.Black * 0.72f);
        string lua = HelperProbeModule.LuaResumePassed ? "PASS" : HelperProbeModule.LuaWalkPassed ? "waiting for Home / return" : "starting";
        string platform = HelperProbeModule.PlatformPassed ? "PASS" : "stand on moving platform";
        ActiveFont.DrawOutline("LUA: " + lua, at, Vector2.Zero, Vector2.One * 0.18f, Color.White, 1, Color.Black);
        ActiveFont.DrawOutline("PLATFORM: " + platform, at + new Vector2(0, 14), Vector2.Zero, Vector2.One * 0.18f, Color.White, 1, Color.Black);
    }
}
