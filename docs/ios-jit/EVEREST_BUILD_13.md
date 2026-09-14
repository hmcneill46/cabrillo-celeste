# Build 13: real Everest and normal mod ZIPs

11 September 2026. **Host integration passes; physical Everest acceptance is
pending.** This is the first unsigned IPA in this lane containing actual
Everest, a native Lua runtime and an importer for two ordinary test mod ZIPs.
See [the evidence ledger](EVEREST_BUILD_13_EVIDENCE.json), the private artifact
folder `artifacts/ios-jit/everest-canary-20260911-13/`, and
[the physical instructions](../../experiments/ios-jit/everest-canary/INSTALL.md).
Delivery/upload state is recorded separately from execution acceptance.

## What is ready

**Celeste JIT Everest 0.6.0 (13)** is a separate guest with bundle identifier
`io.github.hmcneill46.celeste.everest.jit.everest`. The IPA is 890,087,879 bytes
(about 890 MB). The complete nine-file handoff is 890,186,809 bytes, within the
owner's 1 GB limit. It contains the owner's original game assets; it remains
a private physical test, not a public redistributable launcher.

The native launcher imports `CJITCodeCanary-v1.0.0.zip` and
`CJITTestMap-v1.0.0.zip`, verifies their hashes, keeps the ZIPs intact in its
private profile, prepares JIT through LiveContainer 2/StikDebug, then starts
Celeste and Everest. The game/adapter DLLs are bundled now; no external game
DLL import is required. **Test map** loads `CJITCanary/FirstSteps` through
Everest's real content system. Its custom entity draws “CODE MOD ACTIVE” and
the normal-hook, IL-hook and prior saved-jump counters.

`Documents/Profiles/everest-jit-canary/` holds Mods, Cache and Saves, including
full Everest module sidecars. The first normal save uses Everest's UserIO
coroutine; its resulting YAML sidecar is deserialized and checked. A second
process must read back the prior counter. Mod changes/runtime restart still
require a new process. Export diagnostics remains available after completion
and on recovery from a previous crash.

## Preparation and shared components

The independent source root is `experiments/ios-jit/everest-canary/`; all
generated inputs, source clones, tools, game IL and native libraries stay in
ignored `.build/ios-jit/everest-*`. No edits/builds went into the active AOT
checkout `/Users/harrymcneill/Projects/celeste-ios`. No commit, push, remote
repository change or publication was made. The local branch remains
`codex/ios-jit-feasibility-audit` at audit base
`b65bedd20016dc3482d7702d7f0a9707bc2b1479`.

The pipeline builds [Everest 1.6458.0](https://github.com/EverestAPI/Everest/tree/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00),
its pinned MonoMod, NLua and libraries in a new source tree. The original
owner-provided Celeste.exe passes its original SHA256 check. NETCoreifier,
the actual MonoMod patcher, HookGen and legacy hook relinker prepare real
Celeste/FNA/MMHOOK assemblies. The desktop MiniInstaller is not run against
owner originals. This replaces build 12's reconstructed game with original IL;
on-device original-game preparation/import remains future product work.

The accepted custom Mono **8.0.28** native archives/alias patch are reused.
Managed AOT and the managed interpreter remain disabled. The accepted FNA
external callback lifecycle and paired build 11 native FNA3D/Metal patch are
retained. The shared pure touch policy/artwork now connects through Everest
input nodes. There is one UIKit/SDL game lifetime and one Celeste-owned FMOD
system. No .NET Apple managed bindings, AOT Everest helpers or static cutscene
substitutes are loaded.

Everest dependencies were rebuilt using the accepted seven MonoMod hosting
source corrections, rather than substituting the old ten-DLL fixture bundle.
The app packages 168 platform framework DLLs and 32 Everest/game/adapter DLLs.
`Celeste.Mod.mm.dll` is required at runtime for genuine mod relinking, even
though its pre-merge types are excluded from adapter compilation.

## Compatibility issues found and corrected

1. **Embedded content paths.** Everest wraps the initial ContentManager.
   Setting the outer wrapper's root afterwards leaves the inner loader pointed
   at the wrong directory. Set the real asset root before Content.Initialize
   wraps it. The failure was a missing MonocleDefault.xnb, not missing assets.
2. **Native metadata.** Converting the unavailable optional FMOD DSP CPU query
   to ordinary IL requires clearing Cecil's PInvokeImpl flag *after* assigning
   null PInvokeInfo. The opposite order leaves an absent ImplMap row and
   crashed Mono during Commands' reflection scan. Written metadata is now
   re-read and checked. The optional query returns ERR_UNSUPPORTED; ordinary
   FMOD imports use the actual static libraries.
3. **FNA interface.** The accepted FNA predates TextInputEXT.IsTextInputActive.
   A narrow added method queries actual SDL state. A Cecil check resolves all
   411 ordinary FNA member references used by the patched game/hook surface;
   CLR-provided array accessors are excluded explicitly. Renderer behavior is
   unchanged by this addition.
4. **Native BCL services and Lua.** ZIP reading needs the matching native .NET
   compression shim, and relinker checksums need Apple cryptography. Both use
   static libraries from the same 8.0.28 iOS pack. [Lua 5.4.8](https://www.lua.org/ftp/)
   is source-built and checksum-verified to match the pinned KeraLua 1.4.7
   binding; the native resolver exposes its 126 declared imports. The real
   Everest NLua context calls a managed function and returns 42. Lua's own C
   interpreter is separate from the disabled managed IL interpreter. External
   process execution reports unsupported on iOS.
5. **Generated hooks across assembly contexts.** Everest loads/relinks the
   code ZIP into its real [EverestModuleAssemblyContext](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Module/EverestModuleAssemblyContext.cs).
   MonoMod's generated Cecil assembly initially could not resolve that already
   loaded mod assembly. A resolver limited to generated DMD requesters reuses
   a unique, exact full assembly identity from an Everest context. It performs
   no disk loads and refuses ambiguous identities. Normal metadata, dependency
   loading, ZIP relinking and module registration remain Everest's. General
   same-name collisions, context collection and mod hot reload are unproven.
6. **Movement precision.** [Everest's Player precision patch](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Patches/Player.cs)
   widens acceleration coefficients to double but leaves DeltaTime as a single
   operand. On pinned host Mono, this mixed-width IL multiplication produced
   zero: movement did not accelerate and jump velocity did not approach gravity.
   The initial Prologue and test-room runs caught this. A generated IL probe
   reproduces 0 versus the expected 15.000001 for 900 × (float)(1/60).
   Explicitly widening the second operand and narrowing the result to the
   float parameter produces 15.000001. Twenty recorded Player precision sites
   now make these conversions explicit, preserving double intermediate
   arithmetic. Actual room movement, landing and subsequent jumps pass.
   The probe also runs on the phone; no general Mono floating-point fix or
   exhaustive gameplay-equivalence claim is made.
7. **Retained process lifetime.** The upstream worker scheduler's reversed
   disposal guard left its idle worker alive. The isolated correction allows
   cancellation/join; worker methods own autorelease pools with finally cleanup.
   Embedded startup disables desktop updates/Discord/splash subprocesses and
   the automatic new-mod watcher. The dedicated test profile skips the desktop
   onboarding wizard. Shutdown waits for normal saving while continuing frames,
   disposes graphics/audio/hooks, and returns to the native UI cleanly on host.

Raw host failures and intermediate observations are retained under
`.build/ios-jit/everest-host-test/`. They are development findings, not phone
crashes or user-procedure errors.

## Verification and limits

The final **cold-profile** host run uses the pinned cooperative-GC Mono runtime,
real desktop SDL/FNA3D/Metal, owner game assets, real Everest and the two normal
ZIPs. It reaches the title and test room, draws the custom entity, exercises
760+ level frames, movement/jumps, both hook kinds, suspend/resume, normal save
sidecars and clean detach. The mod counter is 2 before resume, 3 after; save
readback is 0 → 3. A prior fresh-process warm-profile run reads 5 and writes 8.
NSZombieEnabled was requested and actual **Metal API Validation Enabled** is
present. Worker pool count reaches zero; no JIT or managed errors occur.

Cold host use: **14,849 JIT completions, 223 chunks, 9,662,143 code bytes**.
These are host figures, not iOS memory/performance results. The app now reserves
two **32 MiB** JIT arenas (64 MiB total) to allow headroom over the larger Everest
closure. No late expansion, executable reclamation or restart is promised.
The matching packaged native protocol descriptor and script were checked with
4,096 acknowledged page writes and detach. Old 64 KiB, 4 MiB and build 12's
16 MiB requests, stale identity and wrong PID are rejected by the mock test.
No real debugger command is sent by that validation.

Simulator checks pass exact ZIP import, Run disabled without JIT, native console
capture, 800 persisted/rendered events, export and previous-session recovery.
The final package passes ZIP CRC, exact content/IL/native/source hashes,
1,294 game/FNA/FMOD static imports plus 126 Lua imports, retained callback API,
external dSYM matching, no provisioning profile and **no executable signature**.
Desktop-only native APIs present in dependency assemblies are not claimed as
iOS-supported. Host FMOD reports 1.10.14; the phone links 1.10.09.

Physical iOS execution, this larger JIT geometry, NLua callback ABI, touch/mod
rendering, background audio and fresh-process mod saves must pass on the phone.
Neither host nor simulator substitutes for that test. No repeat of accepted
build 12 is requested. This canary accepts only its two exact ZIPs.

## Physical handoff

Use **Files → iCloud Drive → Celeste JIT Tests → 0.6.0-build-13**.
The nine-file kit is copied and locally checksum-verified, with README-FIRST,
INSTALL, both ZIPs, the unsigned IPA, script template and Results folder.
The owner first confirmed the download was in progress, then explicitly
reported **the IPA finished downloading** through iCloud. Game execution has
not been reported. No host checksum readback of that iCloud phone copy occurred.

The Mac's metadata API still reports an iCloud account-access error despite
that completed phone download. Preserve both observations; do not report a
failed phone delivery from the host error or infer successful game execution.
The redundant direct Wi-Fi transfer was stopped after the owner's iCloud
confirmation/preference; eight small LocalSend files had been verified, but
that route is not a complete alternative kit. See `handoff-status.json`,
`icloud-owner-download-confirmation.json` and the private transfer/cleanup
receipts in the artifact folder. iCloud is the default for future handoffs.
The redundant 726,663,168-byte LocalSend `.uploading` file was subsequently
removed through the verified target's document service; other files were
untouched (`phone-partial-cleanup.json`).

Install this separate guest in LC1 with Launch with JIT OFF/script blank;
StikDebug stays in LC2. Import both intact ZIPs, use the fresh enable-JIT
button, then Run Celeste + Everest and Test map. After movement/jumps/dashes,
background/resume and Finish/PASS, export into this folder's Results. A second
fresh-process run must retain the saved counter. Follow README-FIRST for
timings and recovery: after a crash, export before another JIT request.

## Next after the physical result

Review both phone exports and visual/audio/control observations first. On a
failure, collect the preserved session/console before another JIT request,
match the exact build/ZIP/script hashes and symbolicate with the external dSYM.
Direct LiveContainer Documents collection remains possible once this new
guest's data UUID is identified; retain Export for iCloud recovery.

After this gate, prioritize [persistent content import and a small IPA](CONTENT_IMPORT_NEXT.md)
for build 14 if the device result is clean. The owner requested that transfer
improvement before sending more large game/mod kits. Then load the real SJ
helper dependency closure and exercise an
actual LuaCutscenes script/coroutine in a small room before the Beginner lobby
and Bing. The current Lua callback is not a full cutscene acceptance test.
SJ's pinned 52 archives total 1,237,284,560 compressed bytes, exceeding the
current total handoff limit; use owner imports or resolve a larger concrete
transfer. Keep native FMOD mod-bank compatibility, memory pressure and
cross-helper hooks visible as separate gates. Public game import, arbitrary
profiles/dependency UI, save manager and selective AOT optimization follow
compatibility evidence; the working AOT lane remains independent.

## Exact artifact identity

- IPA SHA256: `33f75af49dfbf64e2e3a948b25fb94acf4de4ada56a38b236a8c05abaed13942`
- Mach-O/dSYM UUID: `D4A8C72A-0615-3971-B447-EFAAF0A5E4A8`
- Adapter SHA256: `375cfce7f57e4433e778f1e4044f51987ecbdf078cccf28f99311a38c31d68c6`
- FNA SHA256: `dfd000f1a1eff08d41451099c63a9de9363047a6c0025812fb9ff19d8d53ed6d`
- Script template SHA256: `952cc7dc55ab7eff2a8395990aaf7e20a06474deb592d932a4671834d5609717`
- Code ZIP SHA256: `d30cc5b1d28d7821764fb18a35a182aa808cee56f4d0c4c778d9fa7bd4ef450b`
- Map ZIP SHA256: `d373b83f85603bee3e5e73cf5742d5ba2d68746376e7ef391d23c949402eba02`

The app generates the actual PID/nonce-specific session script; the template
alone is not runnable. Preserve delivered files and the build-13-ready private
snapshot. Any source/package correction requires a new versioned kit.

The private snapshot contains **4,900 unique SHA256-verified files**: 140 build
sources, five pinned upstream source trees, accepted FNA/renderer sources,
native archives and objects, Lua sources, original and patched game IL,
packaged app data excluding duplicated Content, matching external symbols,
host regressions/failures/profile saves, simulator exports and protocol checks.
The exact IPA retains the full Content; its hash is verified separately.
`source-snapshot-receipt.json` records every preserved path/hash and commit.

## Cloud retention

During this handoff the owner requested iCloud as the future default and removal
of old large test files. Nine superseded IPAs (builds 4–12, each over 10 MB)
were removed from the local iCloud tree after verifying exact preserved local
copies by SHA256: **967,202,714 bytes**. Previous Results and small files remain;
each affected folder has an INSTALLER-ARCHIVED note. Original artifact receipts
still record their historical deliveries. Cloud-server deletion acknowledgement
is separate from the verified local removals, recorded in
`artifacts/ios-jit/everest-canary-20260911-13/icloud-cleanup-receipt.json`.
