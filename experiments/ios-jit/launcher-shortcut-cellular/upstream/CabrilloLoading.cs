// Added to the private, pinned Everest source by patch_loading.py.
// No desktop splash process or new worker owns game/mod initialization.
using System;
using System.Collections.Generic;
using System.Threading;

namespace Celeste.Mod {
    public static class CabrilloLoading {
        public const int ABI = 1;
        public static bool Enabled { get; private set; }
        public static Action<string, string, int, int> Progress;
        public static int ArchivesProcessed { get; private set; }
        public static int ArchivesTotal { get; private set; } = -1;
        private static int attempts, loaded, failures, skipped;
        public static int ModuleAttempts => Volatile.Read(ref attempts);
        public static int ModulesLoaded => Volatile.Read(ref loaded);
        public static int LoadFailures => Volatile.Read(ref failures);
        public static int Skipped => Volatile.Read(ref skipped);
        public static int Delayed => Everest.Loader.Delayed.Count;
        private static int owner;
        private static IEnumerator<int> boot;

        public static void Enable(Action<string, string, int, int> progress) {
            if (Enabled) throw new InvalidOperationException("Startup is already owned by Cabrillo.");
            owner = Thread.CurrentThread.ManagedThreadId;
            Enabled = true;
            Progress = progress;
        }
        private static void CheckThread() {
            if (Enabled && Thread.CurrentThread.ManagedThreadId != owner)
                throw new InvalidOperationException("Cooperative startup changed its owning thread.");
        }
        internal static void Defer(IEnumerable<int> steps) {
            CheckThread();
            if (boot != null) throw new InvalidOperationException("A game boot is already pending.");
            boot = steps.GetEnumerator();
        }
        public static bool ContinueBoot() {
            CheckThread();
            if (boot == null) throw new InvalidOperationException("No deferred Everest boot.");
            try {
                if (boot.MoveNext()) return true;
                boot.Dispose(); boot = null; return false;
            } catch (Exception error) {
                // Preserve the constructor's detailed error reporting after the
                // boot has moved to explicit continuations.
                try { boot?.Dispose(); } catch (Exception cleanup) { Logger.LogDetailed(cleanup); }
                boot = null;
                Logger.LogDetailed(error);
                throw;
            }
        }
        public static void FinishPresentation() { Progress = null; }
        internal static void Stage(string stage, string detail) {
            var progress = Progress;
            if (!Enabled || progress == null) return;
            CheckThread(); progress(stage, detail, -1, -1);
        }
        internal static void Discover(int total) {
            ArchivesTotal = total;
            ArchivesProcessed = 0;
            Archive("");
        }
        internal static void Archive(string name) {
            var progress = Progress;
            if (!Enabled || progress == null) return;
            CheckThread(); progress("mods", name, ArchivesProcessed, ArchivesTotal);
        }
        internal static void ArchiveCompleted(string name) {
            ArchivesProcessed++;
            Archive(name);
        }
        internal static void ModuleBeginning(EverestModuleMetadata meta) {
            var progress = Progress;
            if (!Enabled || progress == null || meta == null) return;
            // Observe a mod's own thread choices without imposing new affinity.
            // Only the host's iterator/continuation is required to stay on owner.
            Interlocked.Increment(ref attempts);
            progress("mods", meta.Name + " " + meta.Version, -1, -1);
        }
        internal static void ModuleFinished(EverestModuleMetadata meta, bool loaded) {
            var progress = Progress;
            if (!Enabled || progress == null || meta == null) return;
            if (loaded) Interlocked.Increment(ref CabrilloLoading.loaded); else Interlocked.Increment(ref failures);
            progress("mods", meta.Name + " " + meta.Version, -1, -1);
        }
        internal static void Skip() { if (Enabled && Progress != null) Interlocked.Increment(ref skipped); }
    }
}
