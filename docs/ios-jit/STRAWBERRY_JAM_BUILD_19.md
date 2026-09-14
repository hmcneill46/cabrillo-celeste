# Strawberry Jam first play — build 19, 12 September 2026

Build 18 is physically accepted. Build 19 is the first full original Strawberry
Jam candidate: all 52 pinned release modules load under the real Mono runtime,
and the original Beginner lobby and Bing pass the Mac gameplay test. The
unsigned iPhone IPA is **22,812,410 bytes**. Full SJ iPhone acceptance is pending;
this report does not certify every map, arbitrary mods or normal lobby-door
progression.

## Accepted starting point

[Build 18 acceptance](GRAVITY_PASS_BUILD_18.md) verifies the exact delivered
native executable, all 200 managed assemblies, seven retained ZIPs and the
full memory ranges on the owner's iPhone 15 Pro Max / iOS 26.5. All 26 native
and 11 game checks pass. Gravity/Lua/Max gameplay, a 33.592-second background
interval, post-resume hooks and clean shutdown pass; mod save 23 → 36 is read
back from YAML. Its final code reservation is 149,422,080 / 268,435,456 bytes,
with zero runtime errors. Build 18 remains the accepted fallback.

## Candidate and phone flow

Source is `experiments/ios-jit/sj-lobby/`; private stages use
`.build/ios-jit/sj-lobby*`. Update the existing LC1 guest and retain its data.
The shared `Documents/GameLibrary/v1` remains the source of owner-imported
Celeste content. **No game reimport is needed.** The distinct
`Documents/Profiles/sj-first-play` contains this test's Mods, Cache, settings,
slot XML and complete mod sidecars. It starts a fresh SJ save; earlier helper
profiles are retained without conversion or vanilla save filtering.

The explicit Wi-Fi download button retrieves the original pinned root release
and its full required closure directly from upstream URLs. The 52 ZIPs total
**1,237,284,560 bytes**, so they are not put in the iCloud handoff. A 3,560-byte
CJITCodeCanary is bundled, making **53/53** ready files. Original archive names,
versions, URLs, sizes and SHA256 identities are in `SJReleaseManifest.json`;
the graph fingerprint is
`6afeb30bed9e916a2600c09f6916df97a36131acc4bf9ead6e4222e27823c633`.
[Strawberry Jam's release page](https://gamebanana.com/mods/424541) and
[Everest](https://everestapi.github.io/) are the upstream entry points. This
fixed graph is a reproducible first test, not a general dependency resolver.

Downloads use native URLSession download files, HTTPS redirects, expected
sizes and streaming checksums before an atomic install. Existing good files
survive wrong or truncated imports, cancellation and retries. Completed
archives are reverified and skipped on retry; an interrupted archive restarts.
Keep the app open on Wi-Fi. The native downloader does not require JIT and
disables cellular transfers. Manual import accepts the exact pinned original
ZIPs. Neither route extracts arbitrary archive paths in the native launcher.

After all ZIPs are ready, use a fresh LC2/StikDebug request, wait for detach
and native checks, then Run Celeste + Everest. Use **SJ lobby** and **Bing** in
the overlay, play each with music, Home 30 seconds, return and jump, play ten
seconds, Finish, wait ten seconds and Export to
`iCloud Drive/Celeste JIT Tests/0.10.0-build-19/Results`. The complete steps and
crash recovery are in
[the phone guide](../../experiments/ios-jit/sj-lobby/PHONE_README.txt).

## Compatibility work

Two additional startup failures were reproduced with original release inputs.
Their negative logs and candidate experiments are retained privately under
`.build/ios-jit/sj-lobby-investigation`.

**CollabUtils2 1.13.4:** a compiler-generated delegate cache in the normal lobby
helper referenced optional CelesteNet types, so loading the normal cache on
Mono failed without CelesteNet. The adapter moves that one cache field into
the already-existing optional CelesteNet type in a separate hash-keyed
`Cache/CJITCompat/collab-optional-cache-v1` copy. Exactly four field operands
in two methods change; all field types/flags, optional event handlers and
original guards remain. The original ZIP and Everest relink cache remain
untouched. Unsupported versions/shapes and duplicate application fail.
Original and Everest-relinked input controls each pass 1,073 checks, including
comparison of all 1,062 method bodies. Actual CelesteNet networking remains
untested. The earlier pinned GravityHelper compatibility cache is retained.

**FemtoHelper 1.15.22:** Mono eagerly ran `beforefieldinit` initializers while
Everest installed hooks, before the base game initialized particle templates.
Original GenericWaterBlock, TheContraption and LimitRefill failed. A draft
managed particle-field rewrite was rejected after it exposed additional
private/readonly fields; it is preserved only as an investigation artifact.
The delivered adapter does not rewrite Femto particle IL.

Instead, an isolated copy of the accepted Mono 8.0.28 runtime defers these
initializers until actual static field access. The policy is limited to the
FemtoHelper image and `beforefieldinit` types. Explicit static constructors
and unrelated assemblies retain their old behavior. Three runtime objects
change for this policy (`mini`, `mini-runtime`, `method-to-ir`); a fourth
changes chunk sizing. All 256 other archive members remain identical to the
accepted input. Tests reproduce the old failure and exercise 13 initialization
cases: own-field and instance access, generics, reflection, explicit
RunClassConstructor, exception caching and concurrent first reads. A renamed
unrelated-assembly control retains the original policy. During actual game
play, original public/private/readonly Femto fields and derived particle
properties are checked against initialized game templates. All pass.

## Code capacity and diagnostics

The first complete full-SJ host run at the older 64 KiB chunk floor reserved
638,910,464 rounded bytes, too much for the earlier arena. Reducing the ordinary
floor to **16 KiB**, clamped to OS page/granule and preserving large requests,
dynamic chunks, alignment and ARM64 binding room, reduces the final measured
trace to **183,287,808 bytes**. It contains 10,867 allocations and 33,468 JIT
method completions. These are host sizing observations, not iOS performance
measurements.

Build 19 reserves **512 MiB total**, in **two 256 MiB regions**. The actual alias
allocator replays two entire host traces plus 16 MiB of native hook reserve:
21,990 allocations use 383,352,832 bytes and fit. The exact physical build 15
exhaustion control and terminal failure guard still pass. No arena reclamation,
interpreter fallback or in-process runtime restart is introduced. ARM64 JIT
size and full-SJ device memory/background survival remain phone gates.

The full-range checker from build 18 is unchanged. Every page is still queried,
and complete coverage/uniform permissions remain required. Build 19 retains
first/last VM samples plus a SHA256 trace of every row, instead of thousands
of repeated JSON dictionaries. The production logger traverses 16,384 real
Darwin entries in a sanitizer test; its hash matches an independently encoded
complete trace, while only 16 rows and 2,737 JSON bytes are retained. The VM
suite also rejects a permission fault beyond page 8,192 of a 256 MiB range.
The shared native request and packaged script acknowledge all 32,768 page
writes, reject old geometry, stale nonce and wrong PID, and detach. These
script tests use a fake debugserver and do not claim device execution.

## Validation and identity

The final Mac run uses the exact packaged adapter and isolated host Mono
archive with AOT/interpreter disabled. Everest verifies all 52 module versions,
then renders the real lobby for 540 frames and Bing for 424 frames. Original
music events report FMOD PLAYING in both maps. The retained run records one
suspend/resume, 324 post-resume level frames, live On/IL hooks, settings/slot
readback, mod counter 6 → 9, zero tracked workers at shutdown and clean return.
The accepted FNA renderer is reused. This replay does not enable NSZombie or
Metal API Validation; their earlier renderer evidence remains separate.

Native atomic import/real HTTPS download/reuse/cancel tests, four sets of
6,744 actual Mono chunk-function sizing cases, capacity/VM controls and the
compact VM logger pass with ASan/UBSan where applicable. The simulator exercises
all 53 ZIP imports, 4 MiB native content staging, same-bundle update retention,
800 logged background events, export and prior-console recovery. It cannot
execute the ARM64 JIT. Package validation checks all 160 source inputs, 16 native
libraries, 200 managed DLLs and the 1,294 game/FNA plus 126 Lua static imports.
The IPA has no game assets, original SJ ZIPs, signature, provisioning profile,
Apple managed bindings or dSYM bundle; its symbols are retained separately.

- Build: `sj-lobby-20260912-19`, **0.10.0 (19)**; Xcode 26.6 / build 17F113,
  iPhoneOS SDK 26.5, ARM64 deployment iOS 26.0.
- IPA SHA256: `1a64be05f4454a3dcee601e6b244f7e6a44142ad69a97fa10ee8967500edb180`.
- Executable/dSYM UUID: `C32B2B24-459D-3182-95E9-852A4ACE8370`.
- Adapter SHA256: `7021366bbb27b0ccc80e2f7f8955c4717c8a7932b42135e40873af9b39730091`.
- Final host log SHA256: `136d1ba47335dcbf9a77d275fd82ef372fbdd3cdbe756fc9765ac965f54aada5`.
- Local kit: `artifacts/ios-jit/sj-lobby-20260912-19/`.
- Frozen evidence: `.build/ios-jit/device-evidence/2026-09-12/build-19-ready/`,
  with verified inherited build 18 inputs and exact symbols/control inputs.
- [Evidence ledger](STRAWBERRY_JAM_BUILD_19_EVIDENCE.json) records final receipts,
  snapshot and delivery state. Distinguish local cloud placement, uploaded
  bytes and actual phone download/execution.

This remains a private prepared-game-IL/FMOD test. The public small launcher
still needs original-game-IL preparation on the device and resolved FMOD
redistribution permission. No AOT checkout changes, commits, pushes, messages
to third parties or public distribution were performed. If the phone passes,
the next useful gate is normal lobby transitions/map progression plus another
update/relaunch verifying the new profile's saves and downloaded ZIPs; a broad
map or performance claim requires more evidence.
