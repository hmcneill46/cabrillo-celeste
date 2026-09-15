# Cabrillo cooperative loading — build30

Version0.16.0, `launcher-loading-20260915-30`. Derived from local29 and accepted28;
all original delivered sources and artifacts remain immutable.

The native screen shows real preparation/boot/content stages, archive counters,
module results, elapsed time and expandable details. `Entry.Start` returns3
while pending and1 on completion. UIKit advances it on the main CADisplayLink.
Everest boot, archive scanning and the final delayed-module pass yield at explicit
boundaries. The final pass retains its reentrancy guard and optional-cycle state,
and releases the list monitor before each yield. Ordinary recursive dependency
calls and each mod's own Load stay synchronous. No arbitrary game/graphics worker
or nested UIKit event loop is introduced. A single mod can still block a step.

The native window stays above the game until the real title menu is observed,
while its window subclass lets SDL retain focus. Failure during partial startup
keeps Export diagnostics and requires a fresh process. It cannot run the normal
save/Stop sequence on a game that has not finished initialization.

Build with `tools/build_loading_managed.py` then `tools/build_loading.py`, using
an explicit managed receipt and fresh directories. The private managed capsule
is pinned in `ManagedDependencies.json`; native/runtime inputs remain pinned in
`Dependencies.json`. See [the report](../../../docs/ios-jit/RESPONSIVE_LOADING_BUILD_30.md)
and [build guide](../../../docs/BUILDING.md) for evidence and limitations.

Physical acceptance is pending. Keep accepted28 and27 as fallbacks. Do not infer
phone responsiveness, JIT or window behavior from host/simulator results.
