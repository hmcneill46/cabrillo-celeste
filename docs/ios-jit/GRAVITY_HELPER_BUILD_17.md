# Build 17: GravityHelper with LuaCutscenes and MaxHelpingHand

12 September 2026. Build 16 is physically accepted. Build 17 addresses the next
known Strawberry Jam helper blocker and supplies a small gravity-room test.
Full Strawberry Jam remains a later integration gate; its locked graph has
52 nodes and has not been exercised together on this iPhone.

[Build 16 acceptance](SJ_HELPERS_PASS_BUILD_16.md) verifies original LuaCutscenes
0.2.13 and MaxHelpingHand 1.40.9 gameplay, retained content/ZIPs, saved counter
15 → 23, 37-second Home/return and clean detach. Actual code reservations are
58,408,960 / 134,217,728 bytes with no runtime errors. The setup was correct.

## Physical follow-up

The phone setup and seven ZIPs were correct, but the app's old 4,096-entry
VM checker stopped after the first 64 MiB of the larger region, following a
successful StikDebug reply/detach. No generated code or managed runtime ran.
[Build 18 corrects this range-validation limit](BUILD_17_VM_LIMIT_AND_BUILD_18.md).
The pending language below records the original build 17 handoff.

## GravityHelper failure and correction

The exact original GravityHelper 1.2.28 ZIP is retained. On this Mono runtime,
GravityHelperModule.Load/Unload eagerly resolve a `typeof(CelesteNetModSupport)`
reference. That optional integration has a field whose type needs CelesteNet.
Resolution fails before the original module-presence check can decide to skip
an absent dependency. A real original-code negative control reproduces the
CelesteNetGravityComponent TypeLoadException on the same packaged adapter and
accepted Mono archive.

`GravityOptionalIntegration.cs` intercepts Everest's LoadRelinkedAssembly only
for the pinned GravityHelper 1.2.28 archive. It verifies the original ZIP hash
and expected instruction shape, then creates a separate compatibility copy
of Everest's relinked IL. Two call sites use the already-loaded GravityHelper
assembly rather than eagerly resolving the optional integration type. The
original ZIP and Everest's own cache stay unchanged. Every type, field, base,
optional integration body and other method body remains present.

The load bridge checks for the actual `CelesteNet.Client` module before
resolving the optional type and invoking GravityHelper's original forced-load
operation. Errors from a present integration propagate. The unload bridge
finds an existing original integration instance and unloads it even if the
optional module has already disappeared; it does not resolve a missing type
merely to discover that no instance exists. This test establishes absence
handling and branch/error policy, not working CelesteNet networking.

The compatibility copy is stored at the profile's
`Cache/CJITCompat/gravity-optional-v1/<input-sha256>/GravityHelper.dll`.
Its bytes are checked on reuse and written through a temporary file followed
by atomic replacement of that cache entry. Everest loads that same file for
both managed IL and retained Cecil metadata. Unsupported version/ZIP/IL shapes
fail explicitly. No fake dependencies, global resolver fallback or swallowed
integration exception is introduced.

Implementation references are the [GravityHelper source](https://github.com/swoolcock/GravityHelper)
and pinned [Everest assembly loader](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Module/EverestModuleAssemblyContext.cs).
The distributed 1.2.28 DLL and pinned Everest source were inspected locally;
current upstream main is not treated as the exact tested binary. Input URLs
and exact original hashes are in
[helper-pins.json](../../experiments/ios-jit/sj-gravity/helper-pins.json).

## Actual room and runtime budget

A new normal Everest mod, CJITGravityProbe 1.0.0, requires the original three
helpers and runs SID `CJITGravityProbe/RuntimeRoom`. The five existing ZIPs stay
unchanged, including CJITSJHelpers; only GravityHelper and CJITGravityProbe
need importing. There is no game-content download or save migration.

LuaCutscenes performs a short automatic walk, waits in its real coroutine,
and finishes only after the native lifecycle reports resume. GravityHelper's
trigger flips gravity inside the red zone and restores it on exit. The player
must collide with the underside of MaxHelpingHand's UpsideDownJumpThru,
return to the ordinary floor and jump after Home/return. Room counters require
actual inverted/normal frames, platform contact, retained Lua completion,
rendered frames and helper execution after resume.

Build 17 reuses the physically accepted build 16 Mono host/iOS archives exactly,
including its 64 KiB ordinary chunk minimum and member-access correction.
No accepted runtime or source is rebuilt in place. Gravity's additional hooks
raise the measured host profile beyond the old 128 MiB arena. The new geometry
is **two 128 MiB arenas, 256 MiB total**, shared by the native app and its
matching StikDebug script. Scripts from older geometries cannot prepare it.
Every running process still requires its own PID/nonce request.

The final real-Mono host run, with 16 KiB pages/granules and ARM64 binding-space
modeling, creates 2,321 chunks: 145,487,856 raw bytes, 147,144,704 rounded bytes.
It still executes x64 code. Actual alias replay counts every created chunk,
even if Mono recycled an address, adds another 1,161 chunks and 16 MiB for
native hooks, and uses 235,569,152 / 268,435,456 bytes without reclamation.
ASan/UBSan, the exact build 15 failure control and terminal exhaustion guard
pass. This is capacity evidence for this profile; physical ARM64 usage and
memory pressure remain device checks, and larger future profiles need new
measurements.

## Verification and evidence

- The final packaged managed adapter passes the complete real Mono/FNA/Metal/
  FMOD test, including compatibility cache reuse, original helper module
  contexts, On/IL hooks, Lua and gravity/platform counters, save reload/write
  3 → 6 and clean detach. There are 229 inverted frames, 169 inverted ground
  frames, 157 platform contacts, 3,228 normal frames after inversion, one Lua
  begin/wait/resume/end, no skip, and 2,383 helper frames after resume.
- Seventeen checks on each of the original and actual Everest-relinked
  GravityHelper assemblies pass under accepted Mono: only two of 2,008 method
  bodies change, type/field shapes and optional bodies remain, absent operations
  never resolve, present operations/errors run, duplicate/tampered inputs fail.
  The original real-code negative control reproduces the startup failure.
- Final native packaging, 200 managed DLL identities, 1,294 game/FNA and 126 Lua
  static native imports, seven original/test ZIPs and the unchanged renderer
  are validated. The IPA contains no Content assets, signature, provisioning
  profile, desktop native library or embedded dSYM. Symbols remain outside it.
- Simulator checks cover all seven ZIPs ready, native staged copy, same-bundle
  update retention, disabled Run without JIT, log burst, export and previous
  console recovery. Exact native-generated requests and the packaged script
  must acknowledge all 16,384 pages and reject stale identities/old geometry.
  Simulator execution does not exercise iOS JIT or mod gameplay.

Exact receipts and pass states are in
[the build evidence](GRAVITY_HELPER_BUILD_17_EVIDENCE.json). Private source,
original/positive control logs, native symbols and dependency snapshots are
preserved under `.build/ios-jit/device-evidence/2026-09-12/build-17-ready/`.
The native bridge now retains `sj_` and `mono_` event names directly so that
phone diagnostics can identify these checks without generic-message parsing.

## Phone handoff

Version **0.9.0 (17)**, ID `sj-gravity-20260912-17`, same existing guest bundle
and `Documents/Profiles/everest-jit-canary`. Local kit:
`artifacts/ios-jit/sj-gravity-20260912-17/`.
Phone folder: `iCloud Drive/Celeste JIT Tests/0.9.0-build-17/`.
The [phone guide](../../experiments/ios-jit/sj-gravity/PHONE_README.txt) includes
the update/import order and failure-export procedure. Delivery evidence
separates local placement, confirmed cloud upload and actual phone download.

Update the existing LC1 guest, preserve its data and keep Fix File Picker ON,
Launch with JIT OFF and its stored script blank. Import only the two new ZIPs;
StikDebug remains in LC2. Enable this process's fresh script, wait for detach,
run Celeste and tap Gravity map. Let Lua walk, enter the red zone, stand on the
ceiling platform's underside, leave the zone and land normally. Home for
30 seconds, return and jump, require LUA/GRAVITY/PLATFORM PASS, Finish, wait
ten seconds and Export to build 17 Results. Export first after any crash
before another JIT request. Keep saves for the next update-retention check.

Physical gravity acceptance is pending. Review actual code allocation totals,
optional-integration event identities, retained old ZIPs/game/save counter,
gravity/platform/Lua checks, detached resume and delayed liveness. If accepted,
expand required SJ helpers toward the Beginner lobby/Bing test. Full SJ,
CelesteNet, older devices, performance comparisons and public original-IL
preparation are separate gates. This private IPA retains prepared game IL and
linked iOS FMOD. The AOT checkout remains read-only; nothing is committed,
pushed or publicly distributed.

Artifact identity: IPA 22,780,995 bytes,
SHA256 `d53c7399946ef11150cbcfdcf2d797865f9175d28e4894dc1ac9f950b8223b40`;
executable/dSYM `UUID: 82EA42B3-CD0A-38B2-8073-A552F044DBF7`.
Script template SHA256 `6b8ab9a65b976441c5d96991f3e26ad1f0c8b5b41d7be1b8db29416486c1f191`.

All 13 kit files (24,567,275 bytes total) have verified local readback and
confirmed iCloud upload. Phone download and physical gravity execution are
pending. Superseded build 14's cloud IPA was removed after its exact local
copy was verified; build 16 and all Results are retained.
