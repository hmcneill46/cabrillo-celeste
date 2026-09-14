# Build 12: real Celeste under the JIT host

11 September 2026. **Celeste JIT Game 0.5.0 (12) now passes its bounded physical
game test.** Read the [phone acceptance](CELESTE_EXECUTION_PASS_2026-09-11.md)
for Prologue/Forsaken City gameplay, audio, saves, hooks and clean resume/stop.
This implementation/delivery report retains the original test instructions and
host evidence. The app does not include Everest or mod ZIP import yet.

The preceding [build 11 graphics result](GRAPHICS_EXECUTION_PASS_2026-09-11.md)
has been reviewed and accepted. The owner used the correct build and passed
the bounded Metal/touch/background/resume test. This new stage preserves that
renderer/runtime pair and adds the actual game in an independent canary.

Machine-readable results and handoff status are in
[the build 12 evidence](CELESTE_BASELINE_BUILD_12_EVIDENCE.json).

## What is implemented

The native launcher initializes one retained game through the custom Mono
8.0.28 runtime after the existing StikDebug handshake. Celeste and FNA remain
untrimmed managed IL and JIT at runtime; UIKit, SDL, FNA3D/Metal and FMOD are
compiled native components. Neither the interpreter nor managed AOT is enabled.
The code arenas, seven-file runtime patch, MonoMod backend and script are
unchanged from the accepted stages.

The launcher supplies absolute content and save roots, owns the UIKit display
link, and forwards lifecycle events to SDL and the managed game. Each native
callback finishes its Metal command-buffer/autorelease-pool work. A real
`Player.Jump(bool, bool)` Hook calls the original method and records execution;
the test requires another hooked jump after resume. This exercises a game
method without changing its gameplay behavior.

The existing iOS port supplies the pure `TouchControlsPolicy` and
`PlatformPolicies`, touch artwork and virtual-input delegate design. The new
binding-free adapter connects FNA touch/controller state to the original game
bindings and native haptics. It keeps safe-area positioning, touch ownership,
eight-direction movement/hysteresis and controller-triggered overlay hiding.
Touch state resets on inactivity or a layout/controller change. The complete
layout editor, preference UI and Save Manager are not included in this stage.

The test panel offers **Prologue** and **Finish**. Prologue waits until the title
has been reached and starts a fresh area-0 session using this app's own slot 0.
Finish waits for game loading and saving to settle while continuing to service
frames; it does not join a GPU-loading worker while blocking the UI thread.
It saves and reads back actual Settings/SaveData XML, stops audio, ends the FNA
loop, disposes resources and the hook, detaches the managed main-thread state,
and returns to the diagnostic launcher. A delayed liveness event follows.

Original game worker threads remain active, with a balanced native autorelease
pool per worker and persistent error logging. The host manages AVAudioSession
activation and forwards suspend/resume to the game's FMOD mixer. The one system
belongs to Celeste; the FNA audio path is disabled for this test.

## Game provenance and build isolation

This private baseline uses the owner's validated **itch.io macOS FNA 1.4.0.0**
installation, not an unvalidated new Linux download. The existing input
validator confirms the original assembly identities and all 1,216 content files.
No separate game download is required for this phone test.

The independent generation step uses pinned ILSpy 8.0.0.7246-preview3 under
an isolated .NET 6.0.36 build-tool runtime. Its canonical 920-file raw source
manifest matches the existing AOT generation baseline exactly:
`db7b722159fbdef8625c81608165aea162957dce956fcd5b16eeceaa1089a273`.
The manifest normalizes decompiler reference HintPaths in `Celeste.csproj`;
the private snapshot also preserves the actual, unnormalized file bytes.
The decompiler runtime is a build tool, not the runtime shipped in the app.

Existing crash fixes and modern library/BCL adaptations apply with zero fuzz.
Narrow JIT-host changes add retained lifecycle, native logging, private paths,
worker pools, touch delegates and static FMOD imports. The legacy binary-save
path remains disabled; normal game XML serialization is retained and tested.
Mono does not support the requested sustained-low-latency GC setting, so the
adapter catches that specific `PlatformNotSupportedException`, records it and
uses Mono's default collector policy. Other failures still propagate to logs.

The phone links the supplied FMOD **1.10.09, build 97915** iOS archives through
CoreAudio, using the game's 1.10.14 (`0x00011014`) managed wrapper.
The one unavailable DSP CPU-usage query returns `ERR_UNSUPPORTED`; all 488
declared remaining FMOD imports resolve. Broader API compatibility and physical
audio behavior still require testing.

An additional inspection of the exact iOS Studio archive confirms that its
system-creation header check masks the low byte and requires `0x00011000`.
The game's `0x00011014` passes that check; the Studio library separately checks
that its linked core reports `0x00011009`. This is a static compatibility check,
not physical audio execution or a blanket guarantee for every API. The actual
host run reports `0x00011014` too. Earlier notes and the frozen canary README
called this 1.10.20 by reading the last byte as decimal; the correct display is
1.10.14 because [FMOD uses binary-coded decimal version digits](https://qa.fmod.com/t/getversion-gives-2-2-21-for-fmod-2-02-15/20432).
This documentation correction does not change the tested game DLL or IPA.

Implementation is under `experiments/ios-jit/celeste-canary/`, with private
staging under `.build/ios-jit/celeste-*`. The accepted G1/G2/graphics inputs are
unchanged. Xcode 26.6 / build 17F113 and the iPhoneOS 26.5 SDK produced the
ARM64 app. The independent `/Users/harrymcneill/Projects/celeste-ios` AOT lane
and the owner's original inputs were not edited. No commit, push or GitHub
write has been performed.

## Verification and its limits

| Check | Observed result | Limit |
| --- | --- | --- |
| Actual game on pinned macOS Mono | Title, Prologue, 760 level frames, movement, two jump-hook calls including one after resume, XML save/readback and clean stop/detach | x64 host execution, not physical iOS |
| Touch integration on host | Original FNA polling and reused input policy drive movement and jumps | Host injects stable SDL finger snapshots; this is not a physical gesture test |
| Native graphics lifetime | The complete game test passes with NSZombieEnabled and confirmed Metal API Validation | Physical background/surface behavior remains pending |
| Native audio on host | Real FMOD initialization and bank loading complete | Host FMOD reports 1.10.14; device uses 1.10.09. Audible output needs owner confirmation |
| Simulator launcher | Exact DLL import, JIT gating, 800-event burst, current/previous-session and console recovery pass | Generated-code paths disabled; share-sheet interaction not automated |
| Exact device package | CRCs, owner-content identities, all 1,294 declared native imports, 168 framework DLLs and 10 MonoMod DLLs verified | Packaging is not device execution |
| Native request and packaged script | Two 16 MiB arenas, 2,048 acknowledged page writes, response/readback/detach; old geometries, stale nonce and wrong PID rejected | Fake debugserver; no real debugger commands sent |

The host records 113 code chunks / 5,062,192 requested bytes and 8,806 JIT
completions. Scaling each chunk fourfold and rounding to 16 KiB gives a planning
estimate of 20,824,064 bytes against the unchanged 33,554,432-byte phone arena.
This is **not a measured iOS requirement or a performance benchmark**. Physical
allocation high water, resident memory, frame pacing and loading cost must be
read from the game run. Larger chapters, Everest and mod-generated methods may
require a different capacity policy. There is no late arena growth or reliable
arbitrary runtime unload/restart in this canary.

The IPA is unsigned and contains no provisioning profile, code signature or
dSYM. The external symbols match native UUID
`4995D4CF-76A3-3619-955C-A62CFC6C09E7`. The exact game DLL is hash-bound to this
IPA; a DLL from another build is rejected. Keep the external DLL with the kit.

## Physical test and files

Primary phone location: **Files → On My iPhone → LocalSend → Celeste JIT Tests
→ 0.5.0-build-12**. All nine files were copied over the existing Apple Wi-Fi
tunnel and read back by SHA-256 at **2026-09-11 18:43:26 UTC**. The host did not
install or launch the IPA. See [the verified Wi-Fi method](WIFI_FILE_HANDOFF_2026-09-11.md).

The kit totals **883,114,836 bytes**, plus `Results`. It includes
the versioned IPA, game DLL, matching script template, phone README, full install
guide, checksums, build receipt and notices. An identical backup is at
**iCloud Drive → Celeste JIT Tests → 0.5.0-build-12**. All nine files and Results
were confirmed uploaded without error at **2026-09-11 18:42:57 UTC**, after a
temporary account-access error. An iCloud download on the phone is unobserved;
the LocalSend copy is already verified on the device. Use `README-FIRST.txt`
and export into the `Results` folder beside those files; the original INSTALL
guide's iCloud Results location remains an alternative.

Local unsigned IPA:
`artifacts/ios-jit/celeste-canary-20260911-12/CelesteJITGame-unsigned.ipa`.
Bundle: `io.github.hmcneill46.celeste.everest.jit.game`. This is a separate guest
from the graphics canary, with saves under
`Documents/Profiles/vanilla-jit-canary/` in its own container.

1. Install `CelesteJITGame-v0.5.0-build-12-unsigned.ipa` in LiveContainer 1.
   Keep **Launch with JIT OFF** and the launch script empty. StikDebug stays in
   LiveContainer 2. Open the game guest in landscape.
2. Import `CelesteJITGame-v0.5.0.dll`, tap **Enable via LiveContainer 2**, and
   let the fresh script finish. Return to the same running guest and wait for
   native checks to pass. The supplied template is not installed manually.
3. Tap **Run Celeste**, wait for the title, and check graphics/music. Tap
   **Prologue** in the top-right panel. Move and jump several times for at
   least 20 seconds. The blue control jumps/confirms, pink dashes/cancels,
   fist toggles grab and top-centre pauses. Prologue does not grant dash immediately.
4. Go Home for 30 seconds. Return to the **same process**, move and **jump**
   again, and play for another 10 seconds.
5. Tap **Finish**, let loading/saving settle, and wait for the launcher result.
   Wait another 10 seconds, then export diagnostics to this folder's `Results`.
   Report picture, audio, multi-touch and resume observations alongside the log.

If it crashes, reopen this guest and **export before enabling JIT again**.
Record the last visible stage; include a matching iOS crash report if available.
Do not attach Xcode concurrently with StikDebug. Export remains available even
when direct USB diagnostics collection can be used later.

After exporting a successful run, an optional second launch can check that the
ordinary game save selector still shows slot 0. Use a fresh JIT handshake and
export that run too; do not delete the guest data container.

## Next development gate

Accept this bounded physical game run before adding Everest. If it passes,
prepare the pinned real Everest game/FNA patches and hook surface, then test
the loader with one small map and one code mod before attempting Strawberry Jam.
Keep original mod ZIPs and complete module save sidecars in separate profiles.

Before repeated large game handoffs, add persistent owned-content import so
native launcher updates do not rebundle all assets. Build 12 deliberately keeps
content inside its private IPA for one self-contained baseline test; it does
not yet migrate that content into a persistent game-install directory. Plan an
explicit migration/import step rather than assuming a LiveContainer app update
will retain the previous app bundle's assets.

The current reconstructed game fixture is private test scaffolding. The planned
public product instead imports owned original game files, prepares and caches
the platform/Everest assemblies, and preserves content across launcher updates.
The itch.io Linux/FNA download is a candidate for that importer, but its exact
archive/layout still needs validation. Asking the owner to pre-copy it now
would not help this self-contained test.

This kit includes owner game content and the supplied iOS FMOD runtime; it is
not a public redistributable launcher. The [reuse and distribution decision](IOS_REUSE_AND_DISTRIBUTION_2026-09-11.md)
records the FMOD permission question, user-import target and save-manager boundary.

Exact inputs are frozen at
`.build/ios-jit/device-evidence/2026-09-11/build-12-ready/`: 2,631 unique input
files, generated and canonical game source, native archives, symbols, packaged
IL/manifests, host logs/executable, simulator and protocol evidence. Game assets
remain in the preserved exact IPA. The delivered builder refuses to overwrite
this build ID; subsequent code changes require a new versioned kit.
