using System;
using System.Diagnostics;
using System.Threading;
using Celeste.Mod;
using Newtonsoft.Json;

namespace CelesteJIT.Game;

internal static class Startup
{
    internal static bool PresentationFinished { get; private set; }

    internal static void Report(string phase, string detail)
        => ReportEverest(phase, detail, -1, -1);

    internal static void ReportEverest(string phase, string detail, int completed, int total)
    {
        bool enabled = CabrilloLoading.Enabled;
        Entry.Mark("startup_progress", JsonConvert.SerializeObject(new {
            abi = CabrilloLoading.ABI, phase, detail,
            completed, total,
            archives_processed = enabled ? CabrilloLoading.ArchivesProcessed : 0,
            archives_total = enabled ? CabrilloLoading.ArchivesTotal : -1,
            module_attempts = enabled ? CabrilloLoading.ModuleAttempts : 0,
            modules_loaded = enabled ? CabrilloLoading.ModulesLoaded : 0,
            load_failures = enabled ? CabrilloLoading.LoadFailures : 0,
            skipped = enabled ? CabrilloLoading.Skipped : 0,
            delayed = enabled ? CabrilloLoading.Delayed : 0,
            managed_thread = Thread.CurrentThread.ManagedThreadId,
            monotonic_seconds = Stopwatch.GetTimestamp() / (double)Stopwatch.Frequency
        }));
    }

    internal static void Ready()
    {
        if (PresentationFinished) return;
        PresentationFinished = true;
        Report("ready", "Celeste is ready");
        CabrilloLoading.FinishPresentation();
    }
}
