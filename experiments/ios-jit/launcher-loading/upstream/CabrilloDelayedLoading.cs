// Cooperative form of Everest's final delayed-mod pass (Everest MIT license).
// The ordinary recursive CheckDependenciesOfDelayedMods remains unchanged.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace Celeste.Mod {
    public static partial class Everest {
        internal static IEnumerable<int> CJITCheckDependenciesOfDelayedMods() {
            // Retain the original reentrancy guard for the whole pass. RegisterMod
            // must not recursively drain the rest of the list inside one Load.
            // No Monitor or game/graphics callback is held across a yield.
            if (Interlocked.CompareExchange(ref Loader.DelayedLock, 1, 0) != 0)
                yield break;
            try {
                bool enforceTransitiveOptionalDependencies = true;
                while (true) {
                    var entry = CJITNextDelayed(ref enforceTransitiveOptionalDependencies);
                    if (entry == null) yield break;
                    CabrilloLoading.Stage("dependencies", entry.Item1.Name + " " + entry.Item1.Version);
                    yield return 0;
                    lock (Loader.Delayed) {
                        // A mod's own worker may append/register while UIKit runs.
                        // Recheck presence and duplicates after reacquiring the list.
                        int index = Loader.Delayed.IndexOf(entry);
                        if (index < 0) continue;
                        Logger.Info("core", $"Dependencies of mod {entry.Item1} are now satisfied: loading");
                        EverestSplashHandler.IncreaseLoadedModCount(entry.Item1.Name);
                        if (Everest.Modules.Any(mod => mod.Metadata.Name == entry.Item1.Name)) {
                            Logger.Warn("core", $"Mod {entry.Item1.Name} already loaded!");
                            CabrilloLoading.Skip();
                        } else {
                            entry.Item2?.Invoke();
                            Loader.LoadMod(entry.Item1);
                        }
                        Loader.Delayed.RemoveAt(index);
                    }
                    // Original traversal restarts from index zero after a load;
                    // the optional-cycle fallback stays in force for this pass.
                }
            } finally { Interlocked.Decrement(ref Loader.DelayedLock); }
        }
        private static Tuple<EverestModuleMetadata, Action> CJITNextDelayed(ref bool enforce) {
            lock (Loader.Delayed) {
                bool didDelayOptionalDependencies = false;
                for (int i = 0; i < Loader.Delayed.Count; i++) {
                    var entry = Loader.Delayed[i];
                    if (Loader.DependenciesLoaded(entry.Item1)) {
                        if (enforce && checkIfOneOfDependenciesIsDelayedAndCanBeLoaded(entry.Item1.OptionalDependencies,
                            new HashSet<EverestModuleMetadata>() { entry.Item1 })) {
                            didDelayOptionalDependencies = true;
                        } else { return entry; }
                    }
                    if (i == Loader.Delayed.Count - 1 && didDelayOptionalDependencies) {
                        Logger.Warn("core", "Mods with unsatisfied optional dependencies were delayed but never loaded (probably due to circular optional dependencies), forcing them to load!");
                        enforce = false;
                        i = -1;
                        didDelayOptionalDependencies = false;
                    }
                }
                return null;
            }
        }
    }
}
