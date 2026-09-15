# Build 29: independent startup preparation

Subsequent result on15 September: [build28's phone gate is now accepted](BUILD_28_CATALOGUE_ACCEPTANCE.md).
The dated preparation record below describes the earlier state. Build29 remains
local and has no physical acceptance; its artifacts are unchanged.

15 September 2026. **Build 28 phone acceptance remains pending.** Its expected
Results directory was empty at the start of this work (14 September,
22:59:50 UTC). Build 27 remains the accepted fallback. This report describes a
new local preparation build, not a review of phone execution.

## Scope and identity

| Item | Preparation |
| --- | --- |
| Source lane | `experiments/ios-jit/launcher-startup` |
| Version / number | Cabrillo 0.15.1 (29) |
| Build ID | `launcher-startup-20260915-29` |
| Native changes | Cabrillo Play title; four passive startup phase timings; retention of every phase's begin/end |
| Builder | `tools/build_development.py` |
| Package verifier | `tools/verify_development_build.py` |
| Local IPA | `artifacts/cabrillo-build29-preparation/Cabrillo-0.15.1-build-29-preparation-unsigned.ipa` |
| IPA bytes / SHA256 | 23,802,457 / `12b678058ac4f0622ad6e7782012c05053a06495919e43704c0ba40a7801ae08` |
| Executable / dSYM UUID | `59DA3ED7-75C1-32F8-B74D-1A4783095D3D` |
| Preserved guest identity | `io.github.hmcneill46.celeste.everest.jit.everest`; executable `CelesteJITEverest` |
| Preserved storage | `GameLibrary`, `Profiles/sj-first-play`, all existing settings/saves/sidecars |
| Runtime | Accepted Everest 1.6531.0 / Mono 8 payload and renderer; all 201 managed DLLs reused |
| Feature state | Responsive loading, backup/restore and touch editor remain unimplemented |

Build 28's lane, recipe and delivered bytes remain frozen. Build 29's output is
local; the existing build 28 iCloud kit is still the phone test. No new kit,
reinstall request, scheduled monitor, commit or GitHub write accompanies this work.
The repository's initial local handoff/navigation changes were preserved on
`codex/startup-preparation`.

## Fresh build contract

The new recipe reads only Cabrillo source/vendor files and the hash-locked local
`.private` capsule. It compiles the Swift launcher and ZIP/CYaml dependencies,
native bridge and generated symbol tables, creates icons, generates a current
BuildInfo/native receipt, links once and creates matching symbols. All compiler
and linker paths refer to Cabrillo and the explicit Xcode 26.6 installation.
There is no legacy-path remapping, relink-until-match loop, UUID restoration,
historical build timestamp or ZIP metadata replay.

Version, product and guest identity must agree between `BuildIdentity.json` and
`Info.plist`. The builder refuses old identity, altered pinned inputs, an existing
output, outputs outside their ignored category, traversal and symlink aliases.
It checks source hashes again before packaging. The verifier inspects the
actual arm64/iOS executable, embedded JIT protocol section, absence of a Mach-O
signature, dSYM UUID, app resource hashes, current BuildInfo/native receipt and
the exact preserved managed payload. A physical PASS is never inferred.

The private dependency capsule is reused, not rebuilt from upstream. In particular,
this command cannot rebuild `CelesteJITEverest.dll`, prepared game IL or FNA from
changed managed source. Only the narrow native preparation lane is runnable so
far; the next managed recipe must have its own inputs and stages.

## Revalidated startup boundaries

The current launcher/adapter sources and the **patched build 27 Everest tree at
upstream d72e94f4b9e62b91cbdea674587ed39d53de9550** were read directly. This is the
tree used by the accepted 1.6531.0 dependency, not the older 4bbde91 research
snapshot. A small read-only reference copy with hashes is retained privately in
`.private/startup-preparation/everest-reference`. `Everest.Loader.cs` and
`Everest.cs` contain the already established embedded-platform patches; the
review does not describe them as pristine upstream files. The reference tree
is not a dependency of the new builder.

| Boundary | Actual work / thread | Consequence for loading |
| --- | --- | --- |
| `beginManagedRun` → `prepareForGameWithCompletion` | Native UI initiates catalogue cancellation/drain before `graphics_test_start` | Keep the nested zero-active-request gate; no new catalogue request during the game |
| `prepareManagedContentWithProcessState` | Dispatches allocator/`CJGraphicsPrepare` onto the existing worker | Already separate from UIKit; measure preparation and detachment |
| `CJGraphicsPrepareContent` | Attaches worker to Mono, invokes `ContentLibrary.Prepare`, exits GC region and detaches | Existing file verification/import has real byte/file counts and cancellation |
| `startGraphics` | Main thread; checks foreground state and settles landscape before invoking Start | Keep this foreground/window boundary; elapsed waiting is not loading work completed |
| `CJGraphicsCall("Start")` | Explicitly rejects non-main calls; attaches main to Mono and enters the GC region | Sending SwiftUI updates to this same queue cannot make a synchronous call responsive |
| `Entry.Start` → `Platform.Initialize` | Installs hook/platform services, sets Celeste `_mainThreadId` to the calling thread, disables the desktop splash, loads settings | These calls establish thread identity; do not move the constructor wholesale |
| `new JitGame()` | Patched Celeste constructor calls `Everest.Boot`; Boot sets up content/helpers/core modules/Lua and calls `Loader.LoadAuto` | Archive discovery, content crawling, relinking, dependency processing and module code occur before constructor return |
| `CJITBeginExternalLoop` | FNA calls `DoInitialize`, `BeginRun`, `BeforeLoop` synchronously, with graphics callback cleanup in `finally` | More startup remains after Boot; splitting it requires managed/FNA work and preserving callback lifetimes |
| `Initialize` / `LoadContent` | Celeste original methods, each module's Initialize/LoadContent, graphics/content work | Thread-affine game/mod calls stay ordered; mod count is not elapsed-work percentage |
| Native Start return / first display-link callback | Window/scene/Metal/readback checks, followed by first successful frame | Distinct milestones; neither means all asynchronous game-loader work or gameplay is complete |

Sources: [native lifecycle](../../experiments/ios-jit/launcher-startup/src/main.m),
[Mono attachments](../../experiments/ios-jit/launcher-startup/src/CJGraphicsManaged.m),
[accepted adapter Start](../../experiments/ios-jit/launcher-catalogue/managed/GameEntry.cs),
[platform bootstrap](../../experiments/ios-jit/launcher-catalogue/managed/Platform.cs),
[FNA external loop](../../experiments/ios-jit/graphics-canary/managed/ExternalGameLoop.cs).

### Why the desktop splash counters cannot be copied verbatim

The reviewed d72e94f tree exposes useful sites, but their semantics differ from
successful module completion:

- `Loader.LoadAuto`, lines 181–208, counts eligible ZIP/directory candidates,
  processes them, revisits delayed dependencies, then calls `AllModsLoaded`.
- `LoadZip`, lines 334–344 (and the directory equivalent), expands the total by
  metadata entries minus one for a multi-module package. That is metadata count,
  not archive count or necessarily registered runtime module instances.
- `LoadModDelayed`, lines 478–479, increments the splash count **before**
  `LoadMod` returns. `LoadMod` can return false for an assembly failure. Missing
  files also advance the count, and duplicate entries take different paths.
- `CheckDependenciesOfDelayedMods`, lines 705–713, advances the counter before
  checking for an already registered duplicate and before the real delayed load.
- `LoadMod` uses a `ScopeFinalizer` for `Events.Everest.LoadMod(meta)`, so that
  notification alone is not a successful-return signal.
- `EverestSplashHandler.AllModsLoaded`, lines 115–117, assigns completed equal
  to total. More game/module/content initialization follows.
- `Everest.Register` invokes `module.Load`; module constructors, Load,
  Initialize and LoadContent can perform arbitrary work or fail independently.

A native progress bridge must separately observe candidate discovery, exact
archive/metadata identity, load attempt, successful registration, skip/duplicate,
delayed/unresolved dependency and failure. Preserve return values and exceptions;
never turn the splash's forced finish into successful installation or startup.

## Real milestones and implementation sequence after phone 28

1. **Profile the actual phases.** Build 29 emits begin/end spans for catalogue
   quiescence, runtime preparation, content preparation and managed Start.
   Add managed spans around platform/settings/hook setup, constructor/Boot,
   LoadAuto, per-module callbacks and external-loop initialization in the next
   version. Record actual thread, monotonic duration and outcome. Count these
   as observations, not controlled cold/warm benchmarks yet.
2. **Define the native progress contract.** Keep stage, elapsed time and current
   exact module identity; track archives scanned and metadata/modules separately.
   Totals may be unknown or increase when multi-module metadata is discovered.
   Show determinate counts only within a measured operation; use indeterminate
   presentation for settings, arbitrary mod callbacks and unmeasured content work.
   Bound/coalesce routine progress, retain failures and stage edges. Preserve
   independent Export diagnostics.
3. **Create explicit continuation points.** Prototype a resumable Boot/LoadAuto
   sequence around candidate units and the delayed-dependency queue, preserving
   order, locks, callback timing, hook targets and failure semantics. Inspect
   the current FNA initialization chain before separating its phases. Schedule
   each supported main-thread continuation on the ordinary UIKit queue; do not
   pump a nested run loop. Yielding between modules does not preempt one slow
   module callback, so measure that remaining limit rather than claiming every
   load is responsive.
4. **Move only audited independent work.** ZIP reads/hashes/metadata preparation
   are candidates after verifying their ownership and dependency contracts.
   Existing `ContentLibrary.Prepare` already has an attached worker. Do not
   presume Everest content crawling, relinking callbacks, module registration,
   graphics/window creation or mod code are thread-independent. Any worker
   requires explicit Mono attach/GC-region/detach and bounded owned resources.
5. **Complete the window handoff.** Keep a native screen through real work,
   foreground/background transitions and settled orientation. Hand ownership
   to the game only after the corresponding graphics checks and first-frame
   evidence. Do not queue fake progress behind the existing synchronous Start.
   Cancellation before irreversible initialization differs from a partially
   initialized game; preserve one game per process and the supported shutdown
   or fresh-process recovery path.

Required later evidence: controlled cold/warm loads with unchanged content,
multi-module archives, failed/skipped/delayed loads, actual native animation/input
responsiveness, thread identity and window ownership, background-before-start,
catalogue quiescence, gameplay/audio/save/Quit and fresh-process persistence.
iPad layout and thread design should be considered now; physical tablet acceptance
remains separate. The existing 27 startup observations are not new benchmarks.

## Managed dependency preparation still needed

The retained recipes identify the required flow:

| Task | Reference | New isolated inputs/stages needed |
| --- | --- | --- |
| Adapter-only instrumentation | `launcher-runtime/build_managed.py` | SDK 8.0.422 / net8.0 references; accepted assembly references; exact embedded touch resources; new adapter output and receipt |
| Everest Boot/loader continuation | `launcher-runtime/build_dependencies.py`, `patch_everest_source.py` | Pinned d72e94f and dependency/submodule revisions, recorded embedded patches; SDK 9.0.300 and locked package inputs; new source/build/tool outputs |
| Prepare game/HookGen against changed Everest | `launcher-runtime/prepare_game.py`, `tools/PlatformPatch.cs` | SDK 8.0.422, original owned IL, required preparation tools and exact accepted FNA input; new original/prepared/platform-patched stages |
| FNA external-loop changes if necessary | `graphics-canary/managed-build.py`, accepted backbuffer patch history | Restore only required pinned FNA/interop/source/stock-effect inputs privately; carry build 24 renderer/readback/lifetime fixes and prove unchanged surfaces |

These SDK/build trees are not in the migrated capsule. The native preparation
does not silently use executables or caches in the old checkout. Restore selected
inputs into ignored Cabrillo directories with hashes before porting that flow.
Do not rebuild or replace Mono, CoreLib, native renderer, FMOD, Lua or unrelated
managed libraries as a side effect. Keep ABI 1 reflection, MonoMod literal-field
handling, compatibility pins, minimum versions and actual 1.6531.0 registration.

## Validation record

The accompanying [evidence ledger](STARTUP_PREPARATION_BUILD_29_EVIDENCE.json)
records final command/artifact hashes and local results. Six Python controls cover
output boundaries and rejection of signed, simulator, wrong-architecture,
duplicate-UUID and truncated Mach-O inputs. The native retention test fills the
ordinary ring and checks all eight phase edges survive within existing bounds.
The preparation build uses a sandbox denying reads/writes to all three old/input
directories, with separate denial controls.

All **58 source inputs** compiled and the package/symbol checks passed. Four
additional controls modified the real IPA's BuildInfo, a managed assembly,
compiled protocol and dSYM identity; each was rejected for the intended reason
after updating ordinary archive checksums. All201 managed assemblies and the
original build28 source/IPA hashes remain unchanged. The final Results-folder
check at14 September23:17:24 UTC still found zero files.

The linker emitted the same sysroot and FMOD Objective-C ABI warnings present
in the exact build28 reproduction log. The independent Mach-O check verifies
this output is arm64/iOS26.0 with SDK26.5; no runtime correction or phone result
is inferred from those warnings. The catalogue/installer implementations are
unchanged, so their existing test evidence is retained without repeating the
live-service suite or the successful build27 phone test.

Build/package success establishes native compilation and package integrity only.
No phone run, managed gameplay, improved responsiveness or build 28 acceptance
is claimed by this preparation. Preserve build 29's recorded artifacts; a later
implementation needs a new identity (next unused number after this work: 30).
