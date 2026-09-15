# Cabrillo cooperative loading — build31

Version0.16.1, `launcher-loading-20260915-31`. Derived from local29 and accepted28;
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

Build with `tools/build_loading_release.py`, using the exact validated build30
managed receipt and fresh directories. `ManagedPayload.json` pins that receipt
and every resource hash. The managed source/capsule recipe lives in the frozen
`launcher-loading` lane; native/runtime inputs are pinned in `Dependencies.json`. See [the report](../../../docs/ios-jit/RESPONSIVE_LOADING_BUILD_31.md)
and [build guide](../../../docs/BUILDING.md) for evidence and limitations.

Physical acceptance is pending. Keep accepted28 and27 as fallbacks. Do not infer
phone responsiveness, JIT or window behavior from host/simulator results.

Build31 is the delivery refinement of the locally packaged build30. It labels
archive/folder counts accurately. The managed build30 payload is reused exactly,
including cooperative dependency loading; its public sources remain frozen in
`launcher-loading`. Use `tools/build_loading_release.py` and the verified managed
receipt. The new native source and identity are in this directory.
