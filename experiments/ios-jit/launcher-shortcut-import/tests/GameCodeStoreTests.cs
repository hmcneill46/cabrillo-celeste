using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Diagnostics;
using System.Text.Json;

namespace Cabrillo.Preparation;

public static class StoreTests
{
    private static int checks;
    private static void Check(bool condition, string text)
    { if (!condition) throw new Exception(text); Console.WriteLine("PASS_CODE_STORE " + text); checks++; }
    private static void Reject(Action action, string text)
    {
        try { action(); } catch (Exception e) when (GameCodeStore.Recoverable(e) || e is OperationCanceledException) { Check(true, text); return; }
        throw new Exception("Accepted " + text);
    }
    public static int Run(int unused)
    {
        try
        {
            string work = Environment.GetEnvironmentVariable("CABRILLO_PREPARATION_PROBE"), root = Path.Combine(work, "GameCode");
            string recipe = Path.Combine(work, "OwnedGameRecipe.json"), zip = Path.Combine(work, "original.zip");
            bool cancel = false; long space = long.MaxValue;
            var store = new GameCodeStore(root, AppContext.BaseDirectory, recipe,
                s => Console.WriteLine("PREPARATION_STAGE " + s), () => cancel, () => space);
            Reject(() => store.Prepare(null, null), "missing original rejected");
            cancel = true; Reject(() => store.Prepare(zip, "Content/"), "cancellation before import"); cancel = false;
            space = 1; Reject(() => store.Prepare(zip, "Content/"), "low storage preserves originals"); space = long.MaxValue;
            var interrupted = new GameCodeStore(root, AppContext.BaseDirectory, recipe,
                s => { if (s == "Applying Everest to your game code") throw new IOException("simulated interruption"); },
                () => false, () => long.MaxValue);
            Reject(() => interrupted.Prepare(zip, "Content/"), "interrupted preparation leaves no active generation");
            Check(!Directory.GetFiles(root, "active.json", SearchOption.AllDirectories).Any(), "no partially prepared pointer");
            string scratch = Directory.GetDirectories(root, ".incoming-*", SearchOption.AllDirectories).Single();
            string unknownScratch = Path.Combine(Path.GetDirectoryName(scratch), ".incoming-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(unknownScratch);
            File.Copy(Path.Combine(scratch, "preparation-owner.json"), Path.Combine(unknownScratch, "preparation-owner.json"));
            File.WriteAllText(Path.Combine(unknownScratch, "unknown.txt"), "preserve");
            var timer = Stopwatch.StartNew(); var cold = store.Prepare(zip, "Content/");
            Check(!Directory.Exists(scratch), "recognized interrupted scratch recovered");
            Check(File.ReadAllText(Path.Combine(unknownScratch, "unknown.txt")) == "preserve", "unknown interrupted files preserved");
            double seconds = timer.Elapsed.TotalSeconds;
            Check(!cold.Reused, "cold preparation");
            Check(!AppDomain.CurrentDomain.GetAssemblies().Any(a => a.GetName().Name == "Celeste"), "game not loaded prematurely");
            File.WriteAllText(Path.Combine(cold.Directory, "owner-unknown.txt"), "preserve");
            timer.Restart(); var warm = store.Prepare(null, null);
            Check(warm.Reused && warm.Directory == cold.Directory, "warm cache without ZIP");
            double warmSeconds = timer.Elapsed.TotalSeconds;
            string modifiedRecipe = Path.Combine(work, "modified-recipe.json");
            var descriptor = JsonSerializer.Deserialize<GameCodeStore.Recipe>(File.ReadAllText(recipe));
            descriptor.tools["FNA.dll"] = new string('0', 64);
            File.WriteAllText(modifiedRecipe, JsonSerializer.Serialize(descriptor));
            Reject(() => new GameCodeStore(root, AppContext.BaseDirectory, modifiedRecipe, _ => {}, () => false, () => space), "mismatched preparation tool rejected");
            string badZip = Path.Combine(work, "bad.zip");
            using (var output = ZipFile.Open(badZip, ZipArchiveMode.Create)) {
                using var entry = output.CreateEntry("Celeste.exe").Open(); entry.WriteByte(1);
            }
            Reject(() => store.Prepare(badZip, "Content/"), "new invalid ZIP rejected despite valid cache");
            Check(store.Prepare(null, null).Directory == cold.Directory, "failed replacement retains active generation");
            // Corrupt the active prepared game; it must be rebuilt from owned originals.
            File.WriteAllText(Path.Combine(cold.Directory, "Celeste.dll"), "corrupt");
            var repaired = store.Prepare(null, null);
            Check(!repaired.Reused && repaired.Directory != cold.Directory, "damaged cache rebuilt from originals without ZIP");
            Check(File.ReadAllText(Path.Combine(cold.Directory, "owner-unknown.txt")) == "preserve", "unknown files retained");
            Check(store.Prepare(null, null).Directory == repaired.Directory, "rebuilt generation committed atomically");
            string original = Path.Combine(root, "original", cold.Source, "Celeste.exe");
            File.WriteAllText(original, "corrupt");
            Reject(() => store.Prepare(null, null), "damaged original requires original ZIP");
            var restored = store.Prepare(zip, "Content/");
            Check(restored.Reused && restored.Directory == repaired.Directory, "original reimport preserves valid prepared cache");
            Check(Directory.GetDirectories(Path.GetDirectoryName(original), "*").Length == 0, "original inputs remain flat");
            AssemblyAudit.Write(Path.Combine(repaired.Directory, "Celeste.dll"), Path.Combine(work, "game-audit.json"));
            AssemblyAudit.Write(Path.Combine(repaired.Directory, "MMHOOK_Celeste.dll"), Path.Combine(work, "hooks-audit.json"));
            File.WriteAllText(Path.Combine(work, "result.json"), JsonSerializer.Serialize(new { status="PASS_OWNED_GAME_STORE", checks, cold_seconds=seconds, warm_seconds=warmSeconds, prepared=repaired.Directory, source=cold.Source, recipe=cold.Recipe }));
            Console.WriteLine("PASS_OWNED_GAME_STORE checks=" + checks + " cold=" + seconds + " warm=" + warmSeconds);
            return 1;
        }
        catch (Exception error) { Console.WriteLine(error); return 0; }
    }
}
