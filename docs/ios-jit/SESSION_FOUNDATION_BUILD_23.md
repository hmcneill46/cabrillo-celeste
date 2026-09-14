# Session foundation — build 23

Status: physical title and modded Quit both pass on the owner’s iPhone.
See [the acceptance review](BUILD_23_SESSION_ACCEPTANCE.md) for evidence and
the remaining fresh-save reload check. All local build23 gates previously pass.
The exact final identities and handoff status are in
[the evidence ledger](SESSION_FOUNDATION_BUILD_23_EVIDENCE.json).

## Scope and ownership

Owner approved the first step in the [native launcher roadmap](NATIVE_LAUNCHER_ROADMAP_2026-09-12.md):
a required iOS support module, ordinary Quit, source-aware prompts and observable
shutdown. New lane: `experiments/ios-jit/launcher-session`, app **0.12.0 (23)**,
build ID `launcher-session-20260912-23`. Build22 is immutable; no commit, push or
remote write is authorized or performed. The active AOT checkout is untouched.

Game assets, original mod ZIPs, profile `Profiles/sj-first-play`, shared content
cache, accepted Mono archives, original game IL, build22's MonoMod correction,
FNA extension, native renderer and JIT protocol are retained. No reimport needed.

## Implemented contract

`CelesteIOS.dll` is a separate, bundled Everest module: metadata ID `CelesteIOS`,
version **1.0.0**, native ABI **1**. The app receipt binds its hash to this build.
The host supplies log/input/prompt services before constructing the game. Support
registers immediately after vanilla registration and before user mods, following
the pinned Everest metadata lifecycle. It must be the single expected module
instance at boot. The native importer rejects a ZIP using its reserved identity;
a manually copied conflicting ZIP blocks preflight. Mods can depend on that
exact built-in YAML identity. Settings displays the required support version.

This module owns the game-side Game.Exit and input-prompt hooks. The native host
owns JIT, session state, presentation, downloads and files; runtime compatibility
patches remain in their existing components. There is no hot unload or runtime
restart. A new game still requires a new process and fresh JIT authorization.

Normal main-menu Quit calls the real Celeste fade/exit path. Support turns the
final Game.Exit into an idempotent native command instead of immediately ending
frames. The host accepts that command separately from callback/JIT failures.
An unexpected frame-loop end remains a failure. Diagnostic strings have no
command authority. Duplicate requests cannot start concurrent shutdowns.

Stop advances through these stages, returning control to UIKit between them:

1. Wait for tracked workers and all queued UserIO saves; request a final normal
   save (including settings when no slot is selected), then drain it.
2. Verify settings, selected vanilla save and the test mod's real sidecar readback.
3. End the external loop and run the normal exiting callbacks.
4. Release touch/game textures and finish the graphics callback.
5. Dispose the game, including Everest's audio unload and mod detour teardown.
6. Close platform integrations and verify worker completion.
7. Remove the host's remaining hook.
8. Detach the native managed thread, release the window/audio session and present
   the final native result. The managed stage 8 marker precedes native detachment;
   only `graphics_bridge_pass` plus `graphics_result_presented` completes the gate.

Return code 3 means a save frame is required; 4 means yield without another game
frame; 1/2 are final complete/incomplete results. Native window pointers are
forgotten after Game.Dispose so later staged calls cannot inspect a destroyed
SDL window. Foreground/background handlers avoid restarting graphics/audio after
the game loop has ended. Native audio deactivation notifies other audio sessions.

During pending saves, game save-error dialogs remain usable. Once saves settle,
SwiftUI displays the closing stage. Successful native return says SESSION SAVED;
a failed or incomplete shutdown does not claim success. No timeout, process kill,
forced exit, timer-based gameplay limit or automatic restart was introduced.
Normal play has no permanent Finish panel. The optional regression mode retains
its controls; performance metrics are independent and can be hidden completely.

Touch prompt selection follows recent touch, keyboard or controller activity.
An idle connected pad cannot continually steal focus back from touch. Switching
away resets touch owners/latched state; controller disconnect restores touch.
Known touch actions use the same centered artwork as the existing controls on
stock-size 80×80 prompt canvases. Explicit hardware-binding displays and unknown
mod bindings retain their normal glyphs. Crouch dash has no fabricated touch
prompt until its actual touch binding/editor support is added. This does not
pretend touch is a physical controller or remap user bindings. Hard-coded glyphs
inside individual mods may require additional specific integration later.

## New evidence that changes the next questions

The earlier phone journal ended 9.5 seconds into build22 teardown after successful
save readback. New host stage measurements separate that work: full SJ lobby/Bing
shutdown spent **12.50 seconds inside Game.Dispose / mod-hook removal**; the full
mod set playing vanilla spent **4.60 seconds** there. Both completed all stages,
with no recorded JIT, patch rejection or managed error. These are Mac timings,
not an iPhone performance estimate, and do not prove the old phone process crashed
or explain why it was closed.

This stage still runs on the game thread, so the native spinner can pause while
that callback is busy. It has not been represented as fully responsive/cooperative
hook teardown. A separate native queue writes stage/elapsed-time/atomic runtime
counter heartbeats every two seconds without touching UIKit or imposing a timer.
The phone test now asks the owner to note the stage and wait, then export. If the
phone shows a watchdog, patch-budget failure or excessive delay, bounded batches
of ordinary detour cleanup become an immediate backend follow-up. Do not skip
mod cleanup or move all game/graphics disposal onto a worker to hide the delay.

## Validation

- Actual accepted Mono 8, cooperative GC, no AOT/interpreter: original desktop
  main-menu action including fade and Exit passes without a selected save.
- Repeated real Game.Exit calls while two UserIO saves are queued pass; all
  sidecars settle and native managed-thread detach succeeds.
- A second process reads the same slot and test mod counter **3**, plays, saves
  **6**, and reads **6** back. This tests real save files; the scripted harness
  then starts a new map Session and does not prove exact-room checkpoint resume.
- Full original 52-mod graph plus the bundled code canary passes lobby/Bing,
  suspend/resume, saves and all 33 real FNA/Frost graphics checks. Separate normal
  mode with that full set verifies all 56 metadata identities, actual repeated
  Quit during queued saves and a previously saved profile (counter 3→6).
- Each new host run passes 37 support/input/glyph checks, including real Metal
  texture readback. Physical controller/keyboard switching and phone glyph
  presentation remain device checks; the source-policy truth table is host-tested.
- Production native ZIP/YAML parser: 42 controls, including required support,
  importer and manual-copy override rejection. Native event-store/metrics stress
  test passes 120,096 events, 12,642 allocation records and 802 checkpoints.
- Native ABI runs with address/undefined sanitizers: wrong versions and out-of-
  order stages rejected; 32 concurrent requests yield exactly one initial Quit;
  no reopen or Quit after close. No diagnostic-name command channel exists.
- Build22's 137 literal-field and original/fixed Paint controls are inherited
  only for unchanged MonoMod/FNA/runtime inputs. They are not re-labelled as
  execution of this new session adapter.
- Simulator checks cover native portrait/landscape closing presentation, real
  ZIP picker, persisted selection, missing-dependency and no-JIT launch gates,
  export/recovery, update preservation and generated request geometry. A first
  closing-screen test exposed a parent SwiftUI accessibility identifier masking
  the child stage identifier; the parent identifier was removed. No physical
  JIT/game execution is claimed from a simulator fixture. A cropped app screenshot
  during rotation was unreliable; a separate settled full-screen capture shows
  the complete centered landscape screen, verified alongside the portrait view.

Final IPA SHA256: `32c62731d6c3cec14abbad7449dd1ae6f86615341a00df883d55a2f2b00eee28`.
Executable/dSYM UUID: `36701DB8-1857-3705-936C-444828114F26`.
The payload has 168 framework DLLs plus 33 Everest/host DLLs, including support;
no game content directory, separate test DLL, signature, provisioning profile
or dSYM is inside the IPA. The exact 184 source inputs are recorded.

## Physical acceptance and subsequent work

Use [the phone guide](../../experiments/ios-jit/launcher-session/PHONE_README.txt).
Default kit destination: **iCloud Drive / Celeste JIT Tests / 0.12.0-build-23**.
Install the unsigned IPA as an update in LC1; keep data. StikDebug stays in LC2.
Launch with JIT off, saved script blank, Fix File Picker on, and a new inline
request per process. Original game/mod files remain installed. Keep regression
mode off for normal menu Quit testing. Export each session to this build's Results.

Required phone evidence: main-menu Quit, visible final native result, modded
play/save/Quit, fresh-process progress readback, touch prompts, and optional real
controller/keyboard transitions. Keep build19 fallback and every Results folder.
Only superseded cloud installers may be removed after verifying exact local
copies. The independent Export flow remains available for iCloud and USB use.

After physical session acceptance, investigate the known Metal backbuffer-read
bug in a separate renderer lane before broad installs. Dependency transactions,
neutral/general mod browsing, responsive game loading, complete-profile backup
UI and full-parity SwiftUI touch editing remain sequenced in the roadmap. Update
that order if new device evidence makes teardown or another runtime issue urgent.

The small IPA still contains private prepared game IL and linked FMOD; a fully
public original-IL import/relink/release path and FMOD permission remain separate
release work. No original game assets or large user mod archives are added to
the cloud handoff.

Handoff completed at 20:45 UTC on 12 September 2026. All eight iCloud files
report uploaded and match local bytes. Source snapshot receipt:
`b6a232e9c0595c32d1ab935029d1444890a9d771c7b98757a0649b127904ad6d`,
with build22 as its verified parent. Build22's superseded cloud IPA was removed
only after exact local verification; build19, local symbols/artifacts and every
Results folder remain. No commit or remote source publication was performed.
