using System.IO.Compression;
using System.Text.Json;
using Mono.Cecil;
using CelesteJIT.Content;

namespace Cabrillo.Preparation;

internal static class InputMatrixTests
{
    private sealed record Fixture(string label, string archive, string prefix, string source, string kind);
    private static int checks;
    private static void Check(bool yes, string label)
    { if (!yes) throw new Exception(label); checks++; Console.WriteLine("PASS_INPUT_MATRIX " + label); }
    private static void Reject(Action action, string label)
    {
        try { action(); }
        catch (Exception e) when (GameCodeStore.Recoverable(e) || e is OperationCanceledException) { Check(true, label); return; }
        throw new Exception("Accepted " + label);
    }
    internal static int Run(string work, string recipe, string root, GameCodeStore.Result baseline)
    {
        var rows = JsonSerializer.Deserialize<Fixture[]>(File.ReadAllText(Path.Combine(work, "fixtures.json")));
        GameCodeStore Store(Action<string> report = null) => new(root, AppContext.BaseDirectory, recipe,
            report ?? (_ => {}), () => false, () => long.MaxValue);
        var content = new ContentStore(Path.Combine(work, "GameContentManifest.json"),
            "30a1c147d1a3ab0aa45762094e393ed7fd69951dd66e5af063447641e0699c46",
            Path.Combine(work, "GameLibrary"), (_, _, _, _) => {}, () => false, () => long.MaxValue);
        var results = new List<object>();
        var generations = new Dictionary<string, string>();
        var steam = rows.First(f => f.kind == "steam");
        string selection = Path.Combine(root, "selected-source.json");
        byte[] before = File.ReadAllBytes(selection);
        bool interruptedAfterAdaptation = false;
        Reject(() => Store(s => { if (s == "Applying Everest to your game code") { interruptedAfterAdaptation = true; throw new IOException("interrupt source switch"); } })
            .Prepare(steam.archive, steam.prefix + "Content/"), "interrupted switch after Steam adaptation");
        Check(interruptedAfterAdaptation, "interruption actually reached adapted Steam code");
        string steamCore = Path.Combine(work, "steam-core.dll");
        NETCoreifier.Coreifier.ConvertToNetCore(Path.Combine(root, "original", steam.source, "Celeste.exe"), steamCore);
        string stagedSteam = Directory.GetDirectories(Path.Combine(root, baseline.Recipe, steam.source), ".incoming-*")
            .Select(p => Path.Combine(p, "Celeste.dll")).Single(File.Exists);
        using (var beforeSteam = ModuleDefinition.ReadModule(steamCore))
        using (var afterSteam = ModuleDefinition.ReadModule(stagedSteam))
        {
            string Body(MethodDefinition m) => string.Join("\n", m.Body.Instructions.Select(i => i.ToString())) + "\n" +
                string.Join("\n", m.Body.Variables.Select(v => v.VariableType.FullName));
            string Key(MethodDefinition m) => m.FullName + "`" + m.GenericParameters.Count;
            var priorBodies = beforeSteam.GetTypes().SelectMany(t => t.Methods).Where(m => m.HasBody)
                .ToDictionary(Key, Body);
            var newBodies = afterSteam.GetTypes().SelectMany(t => t.Methods).Where(m => m.HasBody)
                .ToDictionary(Key, Body);
            Check(priorBodies.Keys.OrderBy(x => x).SequenceEqual(newBodies.Keys.OrderBy(x => x)), "Steam adaptation keeps every method signature");
            var expected = new HashSet<string>(new[] { "Celeste.Achievements.Has", "Celeste.Achievements.Register",
                "Celeste.Stats.MakeRequest", "Celeste.Stats.Has", "Celeste.Stats.Increment", "Celeste.Stats.Local",
                "Celeste.Stats.Global", "Celeste.Stats.Store", "Celeste.Celeste.Update", "Celeste.Celeste.Main", "Celeste.Celeste..cctor" });
            var changed = afterSteam.GetTypes().SelectMany(t => t.Methods).Where(m => m.HasBody && priorBodies[Key(m)] != Body(m))
                .Select(m => m.DeclaringType.FullName + "." + m.Name).ToHashSet();
            Check(changed.SetEquals(expected), "only 11 desktop Steam service method bodies change; all other game IL preserved");
        }
        Check(File.ReadAllBytes(selection).SequenceEqual(before) && Store().Prepare(null, null).Directory == baseline.Directory,
            "interrupted switch retains old edition and prepared game");
        foreach (var row in rows)
        {
            var assets = content.Prepare(row.archive);
            Check(assets.ArchivePrefix == row.prefix + "Content/", row.label + " content root discovered");
            Check(assets.VerifiedBytes == 1158665183L, row.label + " all 1216 asset hashes verified");
            var result = Store().Prepare(row.archive, assets.ArchivePrefix);
            Check(result.Source == row.source, row.label + " exact input set");
            if (generations.TryGetValue(row.source, out string prior))
                Check(result.Reused && prior == result.Directory, row.label + " shares only matching code cache");
            else generations.Add(row.source, result.Directory);
            var warm = Store().Prepare(null, null);
            Check(warm.Reused && warm.Directory == result.Directory && warm.Source == row.source, row.label + " cache without ZIP");
            using (var game = ModuleDefinition.ReadModule(Path.Combine(result.Directory, "Celeste.dll")))
            {
                Check(!game.AssemblyReferences.Any(a => a.Name.Contains("Steamworks")) &&
                    !game.GetTypeReferences().Any(t => t.Namespace == "Steamworks"), row.label + " no desktop Steam dependency");
            }
            using (var companion = ModuleDefinition.ReadModule(Path.Combine(result.Directory, "Celeste.Content.dll")))
                Check(companion.GetTypes().All(t => t.Name == "<Module>") && companion.Resources.Count == 0,
                    row.label + " companion contains no game code/assets");
            Check(GameCodeStore.Hash(File.ReadAllBytes(Path.Combine(result.Directory, "orig/Celeste.exe"))) ==
                  GameCodeStore.Hash(File.ReadAllBytes(Path.Combine(root, "original", row.source, "Celeste.exe"))),
                  row.label + " original IL retained exactly");
            results.Add(new { row.label, row.source, result.Reused, result.Directory, assets.VerifiedBytes });
        }
        Check(generations.Values.Distinct().Count() == 4, "four source sets have independent generations");
        var saved = Store().Prepare(null, null);
        void Bad(string name, Action<ZipArchive> edit, string prefix = "Content/")
        {
            string archive = Path.Combine(work, name + ".zip");
            File.Copy(Path.Combine(work, "original.zip"), archive);
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Update)) edit(zip);
            Reject(() => Store().Prepare(archive, prefix), name);
            Check(Store().Prepare(null, null).Directory == saved.Directory, name + " preserves selection");
        }
        Bad("mixed-steam-fna", z => { z.GetEntry("FNA.dll").Delete(); using var a = ZipFile.OpenRead(steam.archive);
            using var input = a.GetEntry(steam.prefix + "FNA.dll").Open(); using var output = z.CreateEntry("FNA.dll").Open(); input.CopyTo(output); });
        Bad("unknown-companion", z => { z.GetEntry("Celeste.Content.dll").Delete(); using var s = z.CreateEntry("Celeste.Content.dll").Open(); s.WriteByte(1); });
        Bad("unexpected-steam-dll", z => { using var s = z.CreateEntry("Steamworks.NET.dll").Open(); s.WriteByte(1); });
        Bad("duplicate-exe", z => { using var s = z.CreateEntry("Celeste.exe").Open(); s.WriteByte(1); });
        Bad("case-ambiguous-exe", z => { using var s = z.CreateEntry("celeste.exe").Open(); s.WriteByte(1); });
        Bad("symlink-exe", z => z.GetEntry("Celeste.exe").ExternalAttributes = unchecked((int)0xa1ff0000));
        Bad("missing-game", z => z.GetEntry("Celeste.exe").Delete());
        string missingSteam = Path.Combine(work, "missing-steam.zip");
        using (var sourceZip = ZipFile.OpenRead(steam.archive))
        using (var output = ZipFile.Open(missingSteam, ZipArchiveMode.Create))
            foreach (string name in new[] { "Celeste.exe", "Celeste.Content.dll", "FNA.dll" })
            { using var input=sourceZip.GetEntry(steam.prefix+name).Open(); using var target=output.CreateEntry(name).Open(); input.CopyTo(target); }
        Reject(() => Store().Prepare(missingSteam, "Content/"), "Steam binding is required for Steam input recognition");
        Check(Store().Prepare(null, null).Directory == saved.Directory, "missing Steam binding preserves selection");
        Bad("traversal-root", z => {}, "../Content/");
        Bad("changed-game-byte", z => { var entry = z.GetEntry("Celeste.exe"); byte[] bytes; using(var s=entry.Open()) { using var m=new MemoryStream(); s.CopyTo(m); bytes=m.ToArray(); }
            entry.Delete(); bytes[^1] ^= 1; using var output=z.CreateEntry("Celeste.exe").Open(); output.Write(bytes); });
        File.WriteAllText(selection, "{\"schema\":1,\"source\":\"../../unknown\"}");
        Reject(() => Store().Prepare(null, null), "invalid saved source cannot select arbitrary path");
        var recover = rows.Last(); Store().Prepare(recover.archive, recover.prefix + "Content/");
        Check(Store().Prepare(null, null).Source == recover.source, "verified import repairs invalid selection");
        // A pre-53 install has exact saved originals but no selected-source pointer.
        File.Delete(selection);
        var migrated = Store().Prepare(null, null);
        Check(migrated.Source == baseline.Source && migrated.Directory == baseline.Directory,
            "pre-53 original storage migrates without a ZIP");
        File.WriteAllText(Path.Combine(work, "matrix.json"), JsonSerializer.Serialize(new {
            status = "PASS_NINE_ORIGINAL_INPUTS", checks, results, physical_device_tested = false
        }, new JsonSerializerOptions { WriteIndented = true }));
        return checks;
    }
}
