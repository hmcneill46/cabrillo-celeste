using System;
using System.Linq;
using System.Reflection;
using Celeste.Mod;
using Microsoft.Xna.Framework;
using Celeste;
using Monocle;
namespace CelesteJIT.Game;
public static class StrawberryJam
{
    public const string Lobby = "StrawberryJam2021/0-Lobbies/1-Beginner";
    public const string Bing = "StrawberryJam2021/1-Beginner/Bing_Over_Google";
    public static readonly (string name,string version)[] RequiredModules = {
        ("AdventureHelper", "1.6.0"),
        ("Anonhelper", "1.1.1"),
        ("BGswitch", "1.2.2"),
        ("Batteries", "1.1.4"),
        ("BounceHelper", "1.14.1"),
        ("BrokemiaHelper", "1.8.5"),
        ("CanyonHelper", "1.1.6"),
        ("CavernHelper", "1.3.7"),
        ("CherryHelper", "1.8.2"),
        ("CollabUtils2", "1.13.4"),
        ("ColoredLights", "1.2.0"),
        ("CommunalHelper", "1.25.5"),
        ("ContortHelper", "1.5.5"),
        ("CrystallineHelper", "1.17.2"),
        ("DJMapHelper", "1.13.4"),
        ("DisposableTheo", "1.0.6"),
        ("EeveeHelper", "1.12.5"),
        ("EmHelper", "1.3.0"),
        ("ExtendedVariantMode", "0.50.5"),
        ("FactoryHelper", "1.4.1"),
        ("FancyTileEntities", "1.6.2"),
        ("FemtoHelper", "1.15.22"),
        ("FlaglinesAndSuch", "1.6.80"),
        ("FrostHelper", "1.80.1"),
        ("FurryHelper", "1.0.6"),
        ("GravityHelper", "1.2.28"),
        ("HonlyHelper", "1.7.5"),
        ("IsaGrabBag", "1.7.3"),
        ("JackalHelper", "1.7.7.1"),
        ("JungleHelper", "1.4.10"),
        ("LuaCutscenes", "0.2.13"),
        ("LunaticHelper", "1.1.1"),
        ("MaxHelpingHand", "1.40.9"),
        ("MoreDasheline", "1.7.1"),
        ("OutbackHelper", "1.7.3"),
        ("PandorasBox", "1.0.49"),
        ("SafeRespawnCrumble", "1.2.1"),
        ("Sardine7", "1.2.0"),
        ("ShroomHelper", "1.2.10"),
        ("SorbetHelper", "1.9.2"),
        ("SpirialisHelper", "1.0.8"),
        ("StrawberryJam2021", "1.0.12"),
        ("StrawberryJam2021Assets", "1.0.1"),
        ("StrawberryJam2021AudioA", "1.0.4"),
        ("StrawberryJam2021AudioB", "1.0.0"),
        ("StrawberryJam2021AudioC", "1.0.1"),
        ("TwigHelper", "1.6.0"),
        ("VivHelper", "1.14.10"),
        ("VortexHelper", "1.2.19"),
        ("XaphanHelper", "1.0.79"),
        ("YetAnotherHelper", "1.2.5"),
        ("memorialHelper", "1.0.4"),
    };
    private static int lobbyFrames, bingFrames, resumes, afterResume;
    private static bool lobbyReported, bingReported, particlesChecked;
    private static bool lobbyAudio, bingAudio;
    public static void Resume() { resumes++; }
    public static bool Observe(bool finishing)
    {
        if (Engine.Scene is Level level && level.Tracker.GetEntity<Player>() != null)
        {
            if(!particlesChecked)
            {
                var assembly=Everest.Modules.First(m=>m.Metadata.Name=="FemtoHelper").GetType().Assembly;
                var flags=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;
                ParticleType Particle(string type,string field)=>(ParticleType)assembly.GetType("Celeste.Mod.FemtoHelper.Entities."+type,true).GetField(field,flags).GetValue(null);
                var water=Particle("GenericWaterBlock","Dissipate");
                if(water==null || water.Color!=Calc.HexToColor("81F4F0")*0.25f || water.LifeMin!=Booster.P_Burst.LifeMin || water.LifeMax!=Booster.P_Burst.LifeMax || Particle("TheContraption","_steam2")==null || Particle("LimitRefill","_pGlow")==null || Particle("BoundRefill","_pGlow")==null || Particle("EvilTheoCrystal","PImpact")==null)
                    throw new InvalidOperationException("Original Femto particle initialization/value check failed.");
                particlesChecked=true;Entry.Mark("sj_femto_particles_pass","Original public/private/readonly fields initialized after game GFX; source particle properties and transformed color match.");
            }
            string target=level.Session.Area.SID==Lobby?"event:/sj21_BegLobby":level.Session.Area.SID==Bing?"event:/sj21_bingovergoogle":null;
            if(target!=null && Audio.CurrentMusic==target && Audio.CurrentMusicEventInstance!=null && Audio.CurrentMusicEventInstance.getPlaybackState(out var playback)==FMOD.RESULT.OK && playback==FMOD.Studio.PLAYBACK_STATE.PLAYING)
            {
                if(level.Session.Area.SID==Lobby && !lobbyAudio){lobbyAudio=true;Entry.Mark("sj_lobby_audio_pass",target);}
                if(level.Session.Area.SID==Bing && !bingAudio){bingAudio=true;Entry.Mark("sj_bing_audio_pass",target);}
            }
            if (level.Session.Area.SID == Lobby) lobbyFrames++;
            if (level.Session.Area.SID == Bing) bingFrames++;
            if (resumes > 0) afterResume++;
            if (lobbyFrames >= 120 && !lobbyReported) { lobbyReported=true; Entry.Mark("sj_lobby_pass", Lobby); }
            if (bingFrames >= 120 && !bingReported) { bingReported=true; Entry.Mark("sj_bing_pass", Bing); }
        }
        bool pass=lobbyFrames>=120 && bingFrames>=120 && resumes>0 && afterResume>=120 && particlesChecked && lobbyAudio && bingAudio;
        if (finishing) Entry.Mark(pass ? "sj_play_checks_pass" : "sj_play_checks_incomplete", "lobbyFrames="+lobbyFrames+"; bingFrames="+bingFrames+"; resumes="+resumes+"; afterResume="+afterResume+"; particles="+particlesChecked+"; lobbyAudio="+lobbyAudio+"; bingAudio="+bingAudio);
        return pass;
    }
}
