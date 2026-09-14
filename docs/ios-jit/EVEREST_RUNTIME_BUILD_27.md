# Embedded Everest 1.6531.0 — build27

Build27 (`launcher-runtime-20260913-27`, version0.14.0) implements the runtime
upgrade proposed after [build26 acceptance](BUILD_26_INSTALLS_ACCEPTANCE.md).
Its new source lane is `experiments/ios-jit/launcher-runtime`. The target remains
a general Celeste mod launcher. Catalogue browsing, native loading progress,
whole-profile save/settings backups and the touch layout editor remain later
roadmap items. Subsequent physical build27 acceptance is recorded below.

**Subsequent physical acceptance:** [the phone review](BUILD_27_RUNTIME_ACCEPTANCE.md)
now verifies both helper updates and reports, actual1.6531.0, SJ Cassette Cliffs,
background/resume, complete Quit and fresh-process saved-room reload. The local
validation and original delivery notes below retain their historical scope.

## Runtime and compatibility contract

Everest is rebuilt from pinned stable commit
`d72e94f4b9e62b91cbdea674587ed39d53de9550` (1.6531.0). Its real game patch and
MMHOOK assembly are regenerated from the owner's original hash-verified Celeste
IL. The [prior source assessment](EVEREST_RUNTIME_UPGRADE_ASSESSMENT_2026-09-13.md)
records the nine-commit comparison and primary-source snapshots. Runtime changes
are asset-extension interning, repeatable mirror enumeration and guards for dust
effects outside a Level. Five accepted embedded-host source adaptations are
reapplied separately; source/dependency/preparation receipts bind the outputs.

Only four managed assemblies change relative to the accepted game payload:
Celeste.dll, Celeste.Mod.mm.dll, MMHOOK_Celeste.dll and CelesteJITEverest.dll.
The accepted26 CoreLib correction, accepted24 FNA/Metal renderer, MonoMod fixes,
CelesteIOS1.0.0/ABI1 and accepted19 Mono archives remain byte-identical. The
regenerated intermediate FNA includes one new inert PatchDustBurstAttribute and
its constructor. An IL/field/resource/reference comparison verifies that its
5,242 prior methods,4,469 fields and64 resources are unchanged; ship the accepted
FNA with its later graphics fixes, and verify the new game/hook references.

RuntimeIdentity.json is the shared native/managed source for built-in versions,
Everest commit and compatibility-policy revision. Generated Swift/C# feed native
preflight, update planning, Settings and managed registration checks. The actual
Everest VersionString, numeric version and selected module registrations must
match before gameplay proceeds. Diagnostics include the source/manifest identity.
The JIT script and two256MiB arenas are unchanged; every process still needs a
fresh inline PID/nonce request and only one game session runs per process.

## Cached update availability

Schema2 fingerprints built-in versions and app-managed ZIP pins, plus the policy
revision. A legacy/mismatched cached availability result is recomputed against the
current policy using its already verified index. This applies with automatic
checks disabled, during automatic failure backoff and while offline. It preserves
index timestamps, installed choices, verified downloads and hash caches; it does
not pretend a new network fetch occurred. Reopening a matching cache reuses it.
Manual Check,24h idle Updates visits,1h failure backoff and review-before-install
remain unchanged. Final planning/apply independently validate compatibility.

Current ExtendedVariantMode0.51.0 and MaxHelpingHand1.40.10 require1.6531.0 and
are now eligible. Compatible installed releases are still retained until the user
reviews an update. Verified older entries remain fallbacks for a future case that
needs them; they are neither app-managed pins nor forced downgrades. Genuinely
newer unsupported requirements remain blocked with no Update/apply action.

## Local validation and phone handoff

The final machine-readable [evidence ledger](EVEREST_RUNTIME_BUILD_27_EVIDENCE.json)
records exact receipts, assembly/IPA identities and delivery state. Native tests pass real four-mod updates with exact reports:

| Mod | Before | After |
| --- | --- | --- |
| EeveeHelper |1.12.5|1.12.6|
| FrostHelper |1.80.1|1.80.2|
| ExtendedVariantMode |0.50.5|0.51.0|
| MaxHelpingHand |1.40.9|1.40.10|

A fresh original SpringCollab2020 install selects current compatible helpers,
validates original archive metadata/hashes and retains unknown save data. Cache
upgrade/downgrade/legacy/offline/opt-out/backoff/pin controls, blocked direct
commands, cancellation, journal interruption and unknown-file preservation pass.
Actual Mono/Metal Spring Starjump gameplay and a fresh-process saved-session
reload pass with37 support/input and30 reflection checks per run. The external
host fixture enters the map directly; it does not prove lobby-door progression.
Phone26 separately established normal Spring menu/lobby/Starjump progression.
The six final host cases pass: fresh Spring, saved Spring session reload, Paint
with all four updated helpers, the full original SJ lobby/Bing/Frost graph,
main-menu Quit without a save slot, and repeated Quit during queued mod saves.
All record zero JIT failures,37 support/input checks and30 reflection checks.
Paint completes its original Lua intro and GPU readback; Frost passes33 API/lava
checks. Both Quit cases finish all eight shutdown stages. The four-case matrix
runs with Metal API validation enabled; the two Spring runs do not request it.
The code-capacity totals are x64 host observations, not ARM64 phone estimates.

The new runtime source controls verify actual1.6531.0 registration, both Dust
methods returning safely outside a Level, and repeated mirror enumeration. The
Spring fixture also executes both Dust paths inside the real Level. The full
original107-check backbuffer repair proof is inherited only for the unchanged
FNA/native graphics implementation, alongside these new game-level checks.
Native validation includes555 planner/hash/index checks,20 installer controls,
7 scheduling controls,26 runtime-cache controls,5 blocked-operation checks,
5 real HTTPS checks,9 journal crash/rollback cases and3 unknown-change controls.
Simulator, final package and delivery states are recorded in the evidence ledger.
Never infer ARM64 phone acceptance or an AOT performance comparison from them.

The final fresh-review live fetch timed out twice; host curl independently timed
out connecting to the same community metadata server. Those failed attempts are
retained. The final UI test uses the actual official index captured earlier,
seeded only into the external simulator profile, and exercises the production
hash-verified cache fallback. It verifies the current helper versions, the review
action and no transaction before approval. This is distinct from a successful new
live fetch. The app's no-cache timeout screen preserved all original files and
offered retry. Online checks may need to be retried while that server is
unreachable; no index snapshot or test transport was added to the phone payload.

The small private IPA goes to `iCloud Drive/Celeste JIT Tests/0.14.0-build-27/`.
Use the kit's README-FIRST.txt: update the existing LC1 app retaining data,
verify the new runtime, review the two newly eligible updates, export the report,
play/background/resume/Quit, then reopen and export fresh-process save reload.
StikDebug stays in LC2. No content/mod reimport or manual template edit is needed.
Preserve26 and24 fallbacks and all Results. No GitHub writes, commits, pushes or
AOT-checkout mutations occurred. Prepared game IL and linked FMOD still make
this a private kit; public preparation/redistribution gates remain open.


Original delivery snapshot: 23496679 bytes across 7 files, all confirmed uploaded.
IPA 23476359 bytes; SHA256 `d251a33ee8b08dae94d08d7fe31ac9c3385b919d996fac7843644081a9d2dc45`;
UUID: 39E4D88A-33C1-3D2A-A927-A74C1D024EB4. All224 build source inputs match the frozen source
and simulator package. Phone download/execution remain unobserved. The seven
files include the unsigned IPA, phone README, install guide, reference script,
notices, TEST-IDENTITY.json and checksums. No game/mod ZIP handoff is required.
