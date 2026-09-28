#!/usr/bin/env python3
"""Apply exact cooperative startup edits to a fresh private Everest source copy.

Each yield is outside locks and callbacks. Original dependency discovery/order,
recursive delayed loading, return values and exception behavior are retained.
A single archive or mod callback remains an indivisible work unit. The final
delayed pass preserves its reentrancy guard and optional-cycle state while
releasing the list monitor between modules.
"""
import hashlib
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parent


def apply(repo):
    edits = {}

    def change(name, pairs):
        path = repo / name
        before = path.read_bytes()
        text = before.decode("utf-8-sig")
        for old, new in pairs:
            if text.count(old) != 1:
                raise ValueError(f"Unexpected pinned source at {name}: {old[:90]!r}")
            text = text.replace(old, new)
        path.write_text(text)
        edits[name] = {"before": hashlib.sha256(before).hexdigest(), "after": hashlib.sha256(path.read_bytes()).hexdigest()}

    stage = lambda code, key, detail: (code, 'CabrilloLoading.Stage("' + key + '", "' + detail + '");\n            yield return 0;\n            ' + code)
    change("Celeste.Mod.mm/Mod/Everest/Everest.cs", [
        ("internal static void Boot() {", """internal static void Boot() {
            if (CabrilloLoading.Enabled) { CabrilloLoading.Defer(CJITBootSteps()); return; }
            foreach (int step in CJITBootSteps()) { }
        }
        private static IEnumerable<int> CJITBootSteps() {"""),
        stage('Logger.Info("core", "Booting Everest");', "everest", "Preparing Everest"),
        stage("LegacyMonoModCompatLayer.Initialize();", "hooks", "Preparing mod hooks"),
        stage("Flags.Initialize();", "everest", "Checking platform features"),
        stage("Content.Initialize();", "content_index", "Indexing game content"),
        stage("MainThreadHelper.Instance = new MainThreadHelper(Celeste.Instance);", "everest", "Preparing game services"),
        stage("CoreModule core = new CoreModule();", "everest", "Loading Everest Core"),
        stage("LuaLoader.Initialize();", "everest", "Preparing Lua"),
        ("Loader.LoadAuto();", "foreach (int step in Loader.CJITLoadAuto()) yield return step;"),
        stage('Content.Crawl(new MapBinsInModsModContent(Path.Combine(PathEverest, "Mods")));', "maps", "Indexing maps"),
        stage("Queue<string> args = new Queue<string>(Args);", "mod_options", "Applying mod launch options"),
        stage("EverestModuleAssemblyContext._AllContextsLock.EnterReadLock();", "everest", "Completing mod preparation"),
    ])
    change("Celeste.Mod.mm/Mod/Everest/Everest.Loader.cs", [
        ("internal static void LoadAuto() {", """internal static void LoadAuto() {
                foreach (int step in CJITLoadAuto()) { }
            }
            internal static IEnumerable<int> CJITLoadAuto() {
                CabrilloLoading.Stage("mod_index", "Reading the selected mod library");
                yield return 0;"""),
        ("EverestSplashHandler.SetSplashLoadingModCount(files.Length + dirs.Length);", "EverestSplashHandler.SetSplashLoadingModCount(files.Length + dirs.Length);\n                CabrilloLoading.Discover(files.Length + dirs.Length);\n                yield return 0;"),
        ("""foreach (string file in files) {
                    LoadZip(Path.Combine(PathMods, file));
                }""", """foreach (string file in files) {
                    CabrilloLoading.Archive(file);
                    yield return 0;
                    LoadZip(Path.Combine(PathMods, file));
                    CabrilloLoading.ArchiveCompleted(file);
                    yield return 0;
                }"""),
        ("""foreach (string dir in dirs) {
                    LoadDir(Path.Combine(PathMods, dir));
                }""", """foreach (string dir in dirs) {
                    CabrilloLoading.Archive(dir);
                    yield return 0;
                    LoadDir(Path.Combine(PathMods, dir));
                    CabrilloLoading.ArchiveCompleted(dir);
                    yield return 0;
                }"""),
        ("enforceOptionalDependencies = false;", "CabrilloLoading.Stage(\"dependencies\", \"Resolving remaining mod dependencies\");\n                yield return 0;\n                enforceOptionalDependencies = false;"),
        ("Everest.CheckDependenciesOfDelayedMods();", "if (CabrilloLoading.Enabled) { foreach (int step in Everest.CJITCheckDependenciesOfDelayedMods()) yield return step; }\n                else Everest.CheckDependenciesOfDelayedMods();"),
        ("AutoLoadNewMods = false;\n                    return;", "AutoLoadNewMods = false;\n                    yield break;"),
        ("""public static bool LoadMod(EverestModuleMetadata meta) {""", """public static bool LoadMod(EverestModuleMetadata meta) {
                CabrilloLoading.ModuleBeginning(meta);
                bool loaded;
                try { loaded = CJITLoadModCore(meta); }
                catch { CabrilloLoading.ModuleFinished(meta, false); throw; }
                CabrilloLoading.ModuleFinished(meta, loaded);
                return loaded;
            }
            private static bool CJITLoadModCore(EverestModuleMetadata meta) {"""),
        ('Logger.Warn("loader", $"Mod {meta.Name} already loaded!");\n                    return;', 'Logger.Warn("loader", $"Mod {meta.Name} already loaded!");\n                    CabrilloLoading.Skip();\n                    return;'),
    ])
    # The original constructor has no post-Boot work. Deferral only returns after
    # its original constructor and compatibility log; the adapter has no derived
    # constructor body. No Initialize/LoadContent runs until ContinueBoot ends.
    for source in sorted((SOURCE / "upstream").glob("*.cs")):
        path = repo / "Celeste.Mod.mm/Mod/Everest" / source.name
        path.write_bytes(source.read_bytes())
        edits[str(path.relative_to(repo))] = {"added": hashlib.sha256(path.read_bytes()).hexdigest()}
    return edits


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(apply(args.source), indent=2))
