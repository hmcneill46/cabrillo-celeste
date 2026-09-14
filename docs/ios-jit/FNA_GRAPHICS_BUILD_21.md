# Build 20 session stop and build 21 graphics fix

**12 September physical follow-up:** build21 reached the Beginner lobby, then
stopped loading Paint's intro because MonoMod emitted a static-field read for
literal `Celeste.Decal.Root` during EeveeHelper reflection. The prior FNA method
error is absent. There is no session timer; JIT preparation passed. Build21 is
not accepted for clean map play/save. See [build22's diagnosis and fix](LITERAL_FIELDS_BUILD_22.md)
and [the validated phone evidence](BUILD_21_SESSION_STOP_EVIDENCE.json).

12 September 2026. Build 21 **0.11.1 (21)**, ID `launcher-compat-20260912-21`.
Build 19 remains the accepted fallback. Physical build 21 acceptance is pending.

## What stopped the phone session

Ordinary play has **no intended session time limit**. The supplied build 20
export matches the delivered IPA and source identity exactly. At 18:24:15 BST,
FrostHelper 1.80.1's lava rendering reached a managed graphics method absent from
our older FNA assembly: `GraphicsDevice.GetRenderTargetsNoAllocEXT`.

The event order proves a `MissingMethodException` during `Frame`, followed by the
native frame-failure handler and return to the launcher. This happened 438.381 s
after game startup and 18.865 s after entering the Beginner lobby. It was not
an intended finish, a JIT timeout, or exhausted JIT code space. The owner did not
misconfigure this run.

The log records 26 native checks passing, all 54 selected ZIPs present, all 56
selected/built-in metadata identities verified, successful landscape game
presentation, 25,073 completed frame callbacks and three successful managed
resumes. It includes SJ prologue, the GM lobby and the Beginner lobby. Those
resumes do not establish the requested 30-second background test.

Code reservations were 205,930,496 / 536,870,912 bytes, leaving 330,940,416 bytes.
The native footprint sample was 4,103,524,440 bytes; this is an observation at
failure, not evidence of an OS memory termination or a performance benchmark.

The app remained alive, but the shutdown result was incomplete (`stopped=false`,
managed result 3). A clean final save/readback and fresh-process SJ save reload
are **not established by this export**. Ordinary game save workers had run, but
that is insufficient to claim the latest session progress was saved.

The bounded logger preserved the complete exception and relevant milestones:
107,586 events counted, 830 retained events, 908 sync checkpoints, 2,342,871-byte
export. No storage error is reported. This is not a lossless event trace.

Private evidence: `.build/ios-jit/device-evidence/2026-09-12/build-20-results/`.
Raw export SHA256: `0e73de44254a715def9d886fded99ad06c5471ad2a74ed4b25708e0220cba13b`.
The independent `validate.py` binds the diagnostic to the delivered build and
checks the ordered failure events. Its compact result is
[BUILD_20_SESSION_STOP_EVIDENCE.json](BUILD_20_SESSION_STOP_EVIDENCE.json).

## Fix and compatibility boundary

New isolated source: `experiments/ios-jit/launcher-compat/`. Build 20 and earlier
source/artifact/symbol snapshots remain intact. This adds the standard FNA API
using its existing render-target state: null queries return the count; supplied
buffers must fit the active bindings; unused tail entries are preserved; queries
do not allocate. The behavior follows the pinned
[FNA implementation](https://github.com/FNA-XNA/FNA/blob/76b1aef1fd0fa913ac53726fab9d230291c15327/src/Graphics/GraphicsDevice.cs#L1132)
and [official extension documentation](https://fna-xna.github.io/docs/5%3A-FNA-Extensions/#getrendertargetsnoallocext).

The builder accepts only the reviewed FNA input hash, emits one method and
checks all 5,243 existing method bodies, 4,469 field definitions, assembly
identity/references and embedded resources remain unchanged. Repeating the
patch produces identical bytes; different/already-patched input is rejected.
No native entry point is added. The Mono archives, native renderer, game IL,
original SJ ZIPs and compatibility caches retain their accepted behavior.

FNA input SHA256: `dfd000f1a1eff08d41451099c63a9de9363047a6c0025812fb9ff19d8d53ed6d`.
FNA output SHA256: `e89f3b998229e04a6e596e548498e57214d23d97f753b633ea0d59c0bdfab79b`.

Build 21 also checks the new API with an actual active render target and the
backbuffer at game startup. The launcher retains and displays the first managed
error, records whether stopping came from Finish, start, frame, resume or a game
loop ending, and says recent progress may be unsaved after an incomplete finish.
It does not promise recovery of a failed runtime or permit a second game in the
same process. There is no new time limit.

## Verification

- All 3,222 direct FNA member references across 49 original helper assemblies
  resolve after the patch. The baseline has exactly one missing member: the
  method in this crash. Three runtime-provided multidimensional array operations
  are counted separately. This scan does not cover reflection, every runtime
  path, every dependency API or arbitrary future mods.
- 33 real-Mono/Metal checks cover 0–4 targets, null/exact/oversized/undersized
  output buffers, preserved bindings/tails, zero bytes allocated by 10,000 warm
  queries, the original FrostHelper holder saving/restoring 0/1/4 targets and
  actual GPU readback after switching targets.
- The original Beginner-lobby FrostHelper lava component is rendered in the
  desktop test. Its own code calls the new API twice, restores the gameplay
  render target and produces nonempty GPU pixels. Only its temporary test
  position changes, then is restored. Original mod DLLs/ZIPs are unchanged.
- Full SJ lobby/Bing/music/hooks/save/resume passes on the real Mono host using
  the exact adapter/FNA bytes in this IPA. Separate fresh processes pass with
  the example enabled and disabled while SJ is disabled. Test saves stay local.
- Native mod import/dependency tests and bounded logger replay/metrics controls
  pass. Simulator and XCUITest receipts, script/native-request matching, package
  checks and delivery state are recorded in the linked evidence ledger.

The desktop graphics fixture is external to the app and never packaged. Its
loading path is guarded to macOS. A successful desktop render is **not physical
ARM64 proof**; the owner must repeat the failed route on the phone.

The initial simulator smoke attempt found the earlier UI test's tiny example
ZIP, correctly reporting 54 mods rather than the fixture's expected 53. Only
that hash-verified self-authored simulator ZIP was removed before rerunning;
phone files and product code were unaffected.

## Owner handoff and next gate

Unsigned IPA: `artifacts/ios-jit/launcher-compat-20260912-21/CelesteJITEverest-unsigned.ipa`.
Size: **23,115,371 bytes**. SHA256: `412ed592d21d0752802ce49bb3407b22b5e0732792541f5d8d12d8c38f2c7ba0`.
Executable/dSYM: `UUID: BA5C4346-ABF6-3E2F-ABAA-8AF8C6DD5B55`.
Adapter: `aa7916aeab31cac8e04f752ef7e94efa48e34e379589c617a501eb3fabc6fb36`.

iCloud folder: **Celeste JIT Tests / 0.11.1-build-21**. All eight files
(23,132,160 bytes total) are confirmed uploaded by Apple. Phone download and
execution remain unobserved. Read `README-FIRST.txt`.
Update LC1 retaining data, keep LC2 StikDebug, Launch with JIT OFF, saved script
blank and Fix File Picker ON. Use the newly generated inline PID/nonce script.
Keep the full SJ set enabled and regression mode OFF. Repeat the Beginner-lobby
route including lava, then try an ordinary entrance/map, music and controls,
30-second Home/resume, Finish, export and fresh-process save reload. Place
exports in build 21 Results. After a crash, export before another run.

There is no game/mod reimport or new large download. Same shared GameLibrary/v1
and Profiles/sj-first-play. Exact cloud placement/upload status is in
[FNA_GRAPHICS_BUILD_21_EVIDENCE.json](FNA_GRAPHICS_BUILD_21_EVIDENCE.json);
local copying does not alone prove upload or phone download. Retain accepted
build 19 and all Results; superseded cloud IPAs may be removed only after their
local hashes are verified.

This backend compatibility issue takes priority over save-manager/layout-editor
work. After physical acceptance, continue normal map progression and longer
code/memory checks before full-profile backup/restore and native touch editing.
Public original-IL preparation and FMOD redistribution permission remain separate
release gates. This private IPA still contains prepared game IL and native FMOD.
No AOT checkout mutation, commit, push or public distribution was performed.

## Deferred owner direction after this fix

The owner imported SpringCollab2020 and saw missing MemorialHelper 1.0.0
dependency warnings. They want a general Celeste/Olympus-style product: resolve
dependencies with explicit progress, browse popular/new mods, download mods and
dependencies directly, and show a SwiftUI loading screen driven by real Everest
startup progress. Normal UI should not target Strawberry Jam or any particular
mod; retain existing data paths while removing that product framing. Research
the official Olympus/Everest implementations before designing this next stage.

The owner explicitly deferred that work until the current fix is complete.
Build21 is already frozen/uploaded and does not implement those features. For
its immediate graphics regression, disable the incomplete newly imported
SpringCollab mod so preflight allows the previously accepted SJ set to run.
