# Build 20 — native mod launcher and normal play

**12 September physical update:** Normal play reached the Beginner lobby, then
FrostHelper lava rendering stopped on a missing FNA API. This build is not fully
accepted. See [the build21 diagnosis, fix and retest](FNA_GRAPHICS_BUILD_21.md).


Build 19's physical result is accepted. Build 20 is the next private device
candidate: turn the fixed Strawberry Jam test into a useful launcher while
keeping its accepted runtime. This is a foundation for the app, with backend
validation ahead of cosmetic or save-editing work. Physical build20 acceptance
must be recorded separately after the owner tests its exact IPA.

## Evidence that justifies this step

[Build 19 acceptance](STRAWBERRY_JAM_PASS_BUILD_19.md) binds the owner's export to
its exact executable, script, 200 DLLs, source inputs and 16 native archives.
All 26 native and nine game checks passed, with the full original 52-module SJ
set, both Beginner lobby and Bing, music, 139 saved On/IL hook calls, 33.49 seconds
background/resume, clean worker/main detach and no runtime errors. The previous
session in the same export records completion of the direct phone download;
the current session independently verifies all 53 original/own ZIP identities.
Code use was 211,156,992 of 536,870,912 bytes.

That result establishes a usable platform to start building on. It does not
establish every SJ map, long sessions, normal lobby-door progression or a
fresh-process SJ save reload on the phone. The export contains 120,096 current
events and is 126,404,189 bytes; sampled footprint reached 4,334,358,952 bytes.
Logging was an avoidable contributor, but there is no evidence it accounts for
all that memory. The longest frame gap includes loading and is not an in-game
benchmark.

## Implemented in the isolated build20 lane

Source: `experiments/ios-jit/launcher/`; stages `.build/ios-jit/launcher*`;
ID `launcher-20260912-20`, version **0.11.0 (20)**. No AOT-checkout writes,
commits, pushes or public distribution. Preserve accepted build19 as fallback.

The native SwiftUI launcher has Play, Mods and Settings tabs, supports portrait
and landscape, and uses Apple's scene geometry API before creating the game
window in landscape. It keeps the existing `Profiles/sj-first-play` directory
and shared game library. It does not copy or prune mod saves during an update.
The former test screen is retained as internal backend state, with its native
JIT/file-picker/export/lifecycle operations connected to the new front end.

Mods can be imported through Files without starting Mono/JIT. The Swift catalogue
uses pinned ZIPFoundation 0.9.20 and libyaml's C parser vendored by Yams 6.2.2.
The exact commits and source/archive hashes are recorded; no YAML object tags
are instantiated. Metadata is parsed as text, so `1.10` is not treated as a
floating-point `1.1`. Original archive contents are retained. Imports stream to
a same-directory temporary file, hash before publication, validate metadata and
DLL paths, then atomically move into place. Existing identical bytes deduplicate;
different versions are retained separately and cannot silently overwrite a ZIP.
Pinned SJ filenames are recognised by hash. Ordinary imports preserve a safe
basename, adding a hash suffix only for a collision, including metadata-free
asset ZIPs whose filename supplies their Everest identity.

Validation covers required and present optional dependency versions, multiple
modules per ZIP, duplicate names, cycles, declared DLL existence, metadata CRC,
path traversal, symbolic links, duplicate ZIP entries, YAML duplicate keys,
recursive/undefined aliases, multiple documents and size/complexity limits.
The parser bounds metadata to 1 MiB, 20,000 events, depth 32 and 256 anchors;
archives are at most 4 GiB and 100,000 entries; a profile is at most 1,024 ZIPs.
An asset payload's every CRC/format is not eagerly verified by this catalogue;
Everest still owns content loading and relinking. Import success establishes
metadata/storage validity, not general iOS runtime compatibility.

Choices live in `launcher-mod-state.json`, independently of game save files.
At Run, the app rehashes the selected installation and writes Everest's real
`Mods/blacklist.txt` plus `launcher-run.json`. Writes are atomic per file; neither
is consumed for startup until both operations succeed. A later attempt rewrites
both, so interruption between them cannot launch a partially prepared selection.
The managed adapter verifies the selected module versions against actual Everest
registration and rejects missing or unexpected modules. Multiple module classes
sharing one metadata entry (original JackalHelper) remain supported. The
always-enabled internal diagnostic mod is omitted from the user-facing counts.

The explicit Strawberry Jam downloader remains a preset: 52 original ZIPs,
1,237,284,560 bytes, direct download to the phone, verified progress retained on
cancellation. General dependency auto-download, updates and mod profiles are
future work. Downloading does not override stored enable/disable choices.
GravityHelper 1.2.28, CollabUtils2 1.13.4 and FemtoHelper 1.15.22 stay pinned by
original ZIP hash when enabled because they need the known iOS compatibility
work. Other mods may be imported; this is not permission to assume their native
libraries, loader behaviour or APIs are supported.

Normal play now uses Celeste's own menus and accepts a clean saved session
without demanding the two artificial map jumps or background exercise. An
optional **Strawberry Jam regression test** setting retains those stricter tests
and shortcuts. There is still **one runtime/game per process**: changes after a
game require closing and relaunching the app. Saves use the complete existing
Everest profile, its ordinary save coroutine, and the actual selected file slot.
No vanilla-only backup allowlist is introduced.

## Diagnostics and frame measurements

The structured logger aggregates routine JIT, resolution and patch events into
exact per-event counts and bounded first/last samples. It preserves startup
identity, recent events and last named milestones/checks, with explicit eviction
counts. In-memory recent records are capped at 768 / 2 MiB; milestones at 256 /
4 MiB. Journal parts rotate at 4 MiB, retaining current and previous parts.
Non-routine milestones, failures and pre-execution checks are durable; routine
counters are checkpointed at most once per second while traffic continues.

Every code-allocation triple is stored separately as packed little-endian
(address, requested size, total reserved size). Its export has the complete
Base64 trace, hash and record count, capped at 65,536 records with an explicit
overflow count. It must not be called complete if overflow is nonzero. Prior
exports read bounded prefix/tail excerpts from up to three prior sessions and
include console tails; schema 2 reports this retention policy. Native console
and Everest's own log files remain separate; the in-app export reads tails and
does not promise lossless retention of every historic message. Preserve the
full private files and system crash report when investigating a native crash.

Replaying the actual 120,096 build19 events through the production logger under
ASan/UBSan reproduced every one of the 12,642 allocation records exactly, with
**802** sync checkpoints instead of one per event. Rotation, bounded memory,
partial old journal lines, UTF-8 excerpt boundaries and final-error recovery
were exercised. This is a host logger result, not measured phone FPS or an
attribution of all build19 RAM to logging.

The optional overlay reports recent callback FPS, mean wall-clock time inside
the game frame callback and a rolling 1% low. The window is the last 600
intervals; 1% low is the reciprocal of the mean slowest ceil(1% of N) intervals,
with at least 120 samples. Pausing resets the window, so the Home-screen gap is
not a frame stall. Loading/JIT stalls are included. Callback time includes work
and any waits in the call, not a separately measured GPU or pure CPU duration.
The tests include steady 60 Hz, a 200 ms stall and a 33-second pause/reset.
Apple's Metal HUD remains an optional later developer aid.

## Validation and physical handoff

Current private receipts live under `.build/ios-jit/launcher-validation/`, the
native mod-library/service test stages, simulator `smoke/`, UI-test stage, and
`artifacts/ios-jit/launcher-20260912-20/`. Consult
[the evidence manifest](LAUNCHER_BUILD_20_EVIDENCE.json) and final package receipt
for the exact test outcomes, source hashes, IPA hash and executable/dSYM UUID.

The real Mono host tests use the same packaged adapter and accepted runtime:
full SJ lobby/Bing/music/hooks/save/resume; then normal play with the independent
CJITLauncherExample code mod enabled and all SJ mods disabled; then another fresh
process with that example disabled too. Actual Everest registration matches
each selection. Save counters progress 0 → 3 → 6 → 9 across those processes;
the later tests retain and load the prior slot. A host-only command selects a
vanilla test map without changing the phone's normal-menu behaviour.

The small example ZIP is 1,512 bytes and has no reference to the iOS adapter.
It is a normal Everest DLL with a Load log message, suitable for checking real
import/enable/disable, not a synthetic loader result. A separate native test
suite exercises failure cases and the 53-ZIP corpus; simulator tests exercise
native copy/export/old-console recovery, request generation, portrait/landscape
launcher, actual picker taps, dependency warning and fresh-process UI selection.
These do not establish LiveContainer's game-window rotation; that is a phone gate.

The phone kit belongs at `iCloud Drive/Celeste JIT Tests/0.11.0-build-20/`.
Use [the numbered phone guide](../../experiments/ios-jit/launcher/PHONE_README.txt).
Update LC1 in place; no content/SJ reimport is necessary. Keep StikDebug in LC2,
LC1 Launch with JIT off, stored script blank and Fix File Picker on. Test native
selection first, then normal SJ menus, existing save, natural lobby entry, music,
controls, overlay and Home/resume. Export to that folder's Results. After a crash,
export before another JIT request. Keep the exact build19 IPA locally and in
cloud as fallback; remove only superseded large cloud installers after verifying
their local copies, and preserve all Results.

## What is still missing and the recommended order

1. **Accept build20 on the phone**, especially scene rotation, real menu/door
   progression and fresh-process save reload. Investigate any failure before
   adding another UI feature. Longer SJ sessions must measure memory/JIT code
   headroom and crash recovery. The 512 MiB arena has no late growth/reclamation;
   successful first maps are not a guarantee of the entire campaign.
2. **Complete profile backup/restore and recovery.** Snapshot all Everest save,
   settings and sidecar files while the runtime is idle; include identity and
   checksums, preview the replacement, use atomic swap/rollback, and retain the
   previous profile. Do not apply vanilla's four-file/schema restrictions to
   arbitrary mods. Add named profiles only when this storage contract is tested.
3. **Native touch-layout editor.** Reuse the proven touch bindings, safe-area
   math, haptics and background reset policy; edit normalised positions/sizes in
   SwiftUI/UIKit, preview in landscape, provide reset/undo and versioned data.
   The editor can render natively without being limited by Celeste's font/render
   primitives. A shared input model should drive both editor and game hit regions.
4. **Compatibility and installation services.** Better dependency actions,
   explicit update/revert, logs tied to each selection, new helper-version
   verification and broader map/device tests. Only then consider mod catalogues
   and automatic dependency downloads. Never hot-unload arbitrary mod assemblies.
5. **Public release gates remain independent:** on-device preparation/cache of
   owner-imported original Celeste IL, removal of prepared copyrighted game IL
   from the IPA, and resolution of native FMOD distribution/licensing. Build20
   still includes private prepared game IL/FMOD; it is not the public thin-loader
   solution. Do not publish it or infer permission from another port.

The static AOT vanilla/everest/SJ lane remains independent. The accepted AOT
runtime is not used as the hookable game here: Mono JIT still owns game, Everest
and mod assemblies together. Share stable native services/policy ideas through
reviewable source changes later, rather than pointing both builds at live
writable output directories. No commit or remote write is authorised.

## Primary references

- [Everest metadata setup](https://github.com/EverestAPI/Resources/wiki/everest.yaml-Setup)
  and the pinned local `Everest.Loader.cs` / `EverestModuleMetadata.cs`: blacklist,
  ZIP metadata and the exact System.Version-compatible dependency policy.
- [ZIPFoundation](https://github.com/weichsel/ZIPFoundation/tree/0.9.20) and
  [Yams](https://github.com/jpsim/Yams/tree/6.2.2): native ZIP access and the bounded
  C YAML event parser, with pinned source and licence copies in the lane.
- [Apple scene geometry update](https://developer.apple.com/documentation/uikit/uiwindowscene/requestgeometryupdate(_:errorhandler:)):
  supported scene orientation transition, instead of private device-orientation KVC.
- [Apple Metal performance HUD](https://developer.apple.com/documentation/xcode/gaining-performance-insights-with-metal-performance-hud):
  later GPU diagnostics, kept separate from our callback timing measurements.
- [MeloNX](https://git.ryujinx.app/projects/MeloNX): launcher/game separation as a
  design reference. Its local audit clone was inspected; its orientation KVC
  approach was not copied. The current web endpoint serves an anti-bot page.
