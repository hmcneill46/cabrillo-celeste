# Cabrillo responsive loading — build31

15 September2026. **Phone backend/gameplay checks pass; loading UX needs refinement.**
The [phone review](BUILD_31_LOADING_REVIEW.md) supersedes the original pending
phone labels below. Two complete build31 runs confirm main-thread UI pauses and
a17.7-second hidden game-loading sequence; build32 addresses their presentation.

Original build31 implementation/delivery record: Build31 is0.16.1 / `launcher-loading-20260915-31`. Build28 remains the
accepted fallback and27 is preserved. Build29 is local preparation; build30 is
an immutable local loading intermediate. None of those old Results folders change.

## User-visible result

Run now opens a native loading screen with real stage text, the current archive
or module, elapsed time and expandable details. It counts processed archives and
folders separately from module-load attempts, successful loads, failures,
duplicates and pending dependencies. Uncounted phases show an indeterminate
indicator. A count is not an estimate of total time remaining.

The screen covers the game until a real frame has reached `OuiTitleScreen`.
Its window accepts loading-detail taps while allowing SDL to retain focus.
The normal game menu, game controls and existing save/Quit flow then take over.
File preparation retains cancellation. A partially initialized game that fails
shows an error and Export diagnostics; a fresh process is required to retry.
That path does not call save/Stop on an incompletely initialized game.

## Scheduling and compatibility

The pinned Everest constructor finishes at Boot. Its body is deferred into a
main-thread iterator before game initialization/content loading can run. Native
CADisplayLink invokes `Entry.Start` again when it returns3 (pending);1 means the
retained external frame loop can start. Each callback returns through the existing
Mono GC boundary and finishes the FNA graphics callback/autorelease pool.

Boot phases and each selected archive/folder have explicit yield boundaries.
The final delayed-mod pass also yields before each module. It keeps the original
reentrancy guard and optional-cycle decision for the whole pass, while releasing
the list monitor before yielding. Callbacks execute with the original list lock;
ordinary recursive dependency calls remain unchanged. No graphics/mod callback
is moved to an arbitrary worker and production never pumps a nested UIKit loop.
Native scheduling waits while the application is inactive.

The first complete SJ test exposed a37.46-second final dependency batch. Splitting
that pass preserved all106 module begin/end reports in exactly the same order.
The new pass was also compared with the pinned original algorithm for required
chains, optional/transitive cycles, unresolved/mismatched dependencies, duplicates,
recursive callbacks and thrown failures. Its guard is released on completion or
failure and no list monitor crosses a yield.

**Remaining limit:** an individual archive, mod callback or game initialization
call is still indivisible. With a fresh SJ mod cache, the StrawberryJam2021 module
operation took18.09 seconds on this Mac. With that cache warm, the longest step
was4.99 seconds in game-content initialization. A single slow operation can still
pause native interaction/elapsed updates. This is a first cooperative loading
implementation, not a guarantee of uninterrupted responsiveness for arbitrary
mods. The phone gate must assess the actual experience and exported slow steps.

## Local evidence

Full receipts and private logs are linked by hash in the
[evidence ledger](RESPONSIVE_LOADING_BUILD_31_EVIDENCE.json).

| Check | Result |
| --- | --- |
| Managed build from Cabrillo inputs | PASS; four assemblies rebuilt,197 preserved |
| FNA semantic comparison | PASS; accepted shipped FNA bytes retained |
| Prepared Celeste comparison | Same identity, assembly-reference set and all resources; changes confined to Everest/loading types and their generated iterators/closures |
| Cooperative/progress contract | PASS; thread ownership, multi-module counts, exceptions, closed presentation, malformed reports and bounded retention |
| Delayed-dependency comparison | Eight cases match the pinned original order and pending/failure outcomes |
| Small profile, cold/warm content | Both PASS;28 startup calls, Cateline, Memorial Helper and the code canary; real Metal gameplay, save/readback, suspend/resume and eight-stage Quit/detach |
| Real multi-module ZIP | PASS; four archives produce five successful module loads |
| Deliberately throwing mod | PASS; original exception and failed count retained, no false ready or invalid shutdown |
| Full Strawberry Jam, fresh mod cache | PASS;53 archives/modules,52 required SJ identities,144 startup calls, original lobby/Bing gameplay, audio, hooks, saves and Quit |
| Full Strawberry Jam, warm mod cache | PASS; identical module order, fresh process,144 calls, gameplay/save/Quit; longest step4.99s |
| Native UI and window policy | Four XCUITests on each iPhone17ProMax and iPadPro11 simulator: rotation, live details, file cancellation, error Export and game focus/handoff |
| Device compile/package | Fresh arm64 compilation and independent package/symbol checks; exact identity in ledger |

The small-profile final cold/warm maximum steps were0.735/0.463 seconds on the
host. These runs are scheduling/regression evidence, not controlled performance
benchmarks or phone timing claims. Host integration uses pinned Mono8.0.28 x64,
a16KiB code-allocation model and Metal. It does not test iOS JIT aliases, UIKit
lifecycle on a physical device or hardware touch. Simulator game windows are
explicit external fixtures; no fixture transport is added to the IPA.

Managed and native builds run with access to the two old projects and the owner's
original-files folder denied, and writes to `.private` denied. The capsule is an
explicit pinned dependency. No source/binary fallback to another checkout occurs.

## Package and diagnostics

Verified IPA: **23,859,068 bytes**, SHA256
`369ca8a970dd0eadce1b6ba67d2a0277072731fd625823717e2b46c82246cd4c`.
Executable/dSYM UUID: `4337244A-22F8-31EA-BE60-55DB41E3F3AA`.
Output: `artifacts/cabrillo-build31`;61 compiled sources. Four actual-package
negative controls reject stale identity, changed managed bytes, changed compiled
JIT protocol and mismatched symbols. The kit is uploaded to iCloud with matching verified bytes.
The total test directory is713,086,841 bytes, within the owner's1GB limit.
Phone download/execution is unconfirmed. No commit or GitHub write was made.

The build31 native lane is `experiments/ios-jit/launcher-loading-release`.
`ManagedPayload.json` pins the exact validated build30 managed receipt/resources;
the underlying managed source remains frozen in `launcher-loading`.
`tools/build_loading_release.py` and `tools/verify_loading_release.py` require
that receipt, fresh metadata/UUIDs and matching external dSYM. Build31 corrects
archive/folder wording after build30 was packaged; its managed bytes are identical.
The guest bundle identifier, executable name and existing Documents/profile paths
are preserved. Native runtime, renderer/audio libraries and bundled support
module are unchanged. Public distribution remains gated by original IL and FMOD.

`startup_progress` retains the last report for each phase after the event ring
wraps. `startup_step` records the phase/detail before the callback and the next
phase after it. `startup_continuations_finished` retains the eight slowest steps
and maximum duration. `startup_window_handoff` records readiness and native state.
The catalogue still must quiesce with zero active requests before managed startup.

## Phone gate

Use the short [phone guide](../../experiments/ios-jit/launcher-loading-release/PHONE_README.txt).
Default destination: `iCloud Drive/Celeste JIT Tests/0.16.1-build-31`.
Delivery/upload state is recorded in the ledger; local placement alone does not
prove upload, phone download or execution.

Update the existing LiveContainer slot1 entry, preserve data and keep StikDebug
in slot2. Use Launch with JIT OFF, blank saved script, Fix File Picker ON, and a
fresh PID-specific inline request on each process. Detach before Run.

Use a familiar large mod set, inspect loading details/stages/long pauses, check
main-menu handoff, brief play/audio/save and normal Quit with five seconds of
native return. Repeat after a fresh launch/JIT request for the warm load and
background/return behavior. One Export diagnostics after both runs is sufficient
if it retains both sessions; save it in build31 Results and report visual outcomes.
No repetition of accepted28's browser suite is requested. If a fault occurs,
review it before backup/restore feature work. Whole-profile backup with staged
restore/rollback follows loading acceptance, then the full touch editor.
