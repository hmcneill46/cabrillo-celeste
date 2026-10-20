// Host-only observation of the original released mod under the shipped Mono payload.
using System;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using Celeste;
using Celeste.Mod;
using Microsoft.Xna.Framework.Graphics;
using Monocle;

public static class MotionSmoothingTests {
    sealed class Counter : Entity {
        public int Updates;
        public double Seconds;
        public override void Update() {
            base.Update(); Updates++; Seconds += Engine.RawDeltaTime; totalUpdates++; totalSeconds += Engine.RawDeltaTime;
            if (Math.Abs(Engine.RawDeltaTime - 1.0/60) > 0.0001)
                throw new Exception("Motion Smoothing changed the gameplay update step: " + Engine.RawDeltaTime);
        }
    }
    static bool configured, complete;
    static Counter counter;
    static int draws, firstUpdates, totalUpdates;
    static double totalSeconds;
    static double firstSeconds;
    static readonly Stopwatch clock = new Stopwatch();
    public static void Run(GraphicsDevice device) {
        if (!configured) {
            var module = Everest.Modules.Single(m => m.Metadata.Name == "MotionSmoothing");
            if (module.Metadata.Version != new Version(1,8,0)) throw new Exception("Unexpected mod version");
            object settings = module.GetType().GetProperty("Settings", BindingFlags.Public|BindingFlags.Static).GetValue(null);
            void Set(string name, object value) {
                var property = settings.GetType().GetProperty(name);
                property.SetValue(settings, property.PropertyType.IsEnum ? Enum.Parse(property.PropertyType, (string)value) : value);
            }
            Set("UseMapSettings", false);
            Set("RenderingMode", Environment.GetEnvironmentVariable("CJIT_MOTION_RENDERER"));
            Set("FramerateIncreaseMethod", "Interval");
            Set("FrameRate", int.Parse(Environment.GetEnvironmentVariable("CJIT_MOTION_FPS")));
            Set("GameSpeed", 60.0);
            configured=true;
            Console.WriteLine("MOTION_MOD_CONFIGURED " + module.Metadata.Version + " " + Environment.GetEnvironmentVariable("CJIT_MOTION_FPS") + " " + Environment.GetEnvironmentVariable("CJIT_MOTION_RENDERER"));
        }
        if (complete || !(Engine.Scene is Level level) || level.Paused || level.Tracker.GetEntity<Player>() == null) return;
        // A death reload removes non-global entities without replacing Level.
        // Count across observed counters, recreating only after an attached one
        // is removed; do not duplicate an Add that is still queued.
        if (counter == null || (counter.Scene != level && counter.Updates > 0)) { counter = new Counter(); level.Add(counter); }
        draws++;
        if (draws == 180) { firstUpdates=totalUpdates; firstSeconds=totalSeconds; clock.Restart(); }
        if (draws != 700) return;
        clock.Stop();
        if (totalUpdates <= firstUpdates || totalSeconds <= firstSeconds) throw new Exception("Gameplay did not update: first="+firstUpdates+" final="+totalUpdates+" scene="+(counter.Scene?.GetType().FullName ?? "null")+" same="+ReferenceEquals(counter.Scene,Engine.Scene)+" active="+counter.Active+" levelEntities="+level.Entities.Count);
        // Wall-clock rates are observations on this Mac, not phone performance claims.
        Console.WriteLine("PASS_MOTION_SMOOTHING_REAL_GAME fps="+Environment.GetEnvironmentVariable("CJIT_MOTION_FPS")+
            "; renderer="+Environment.GetEnvironmentVariable("CJIT_MOTION_RENDERER")+"; draws=520; physics_updates="+(totalUpdates-firstUpdates)+
            "; physics_seconds="+(totalSeconds-firstSeconds)+"; wall_seconds="+clock.Elapsed.TotalSeconds+"; fixed_step=60");
        complete=true;
    }
}
