# Build 7 protocol mismatch and build 8 correction

11 September 2026. **The owner's setup was correct. Build 7 contained a native
build configuration error.** Its request asked for two 64 KiB regions while
its bundled StikDebug script required two 4 MiB regions. The script correctly
stopped before debugger attachment. No native JIT, managed test or hook stage
ran in this session. Physical G2 remains pending.

The corrected retest is **hook-canary-20260911-08, version 0.3.1 (8)**.
Read [the installation guide](../../experiments/ios-jit/hook-canary/INSTALL.md)
and [the evidence record](BUILD_7_PROTOCOL_AND_BUILD_8_EVIDENCE.json).

## Captured evidence and root cause

The export is session `78db45e2-dd00-4af6-a8ad-ca601817c37e`, on the expected
iPhone16,2 / iOS 26.5 with 16 KiB pages. It contains 23 current-session events.
The build metadata and all recorded source hashes match the delivered build 7;
the imported `HookCanary-v0.3.0.dll` hash matches the supplied fixture.
The inline route opened successfully through LiveContainer 2 for PID 27856.

The decisive event is `jit_request_created.fields.bytes_per_arena = 65536`.
The screenshot reports **FAIL phase 1: Unsupported request geometry/version**.
The paired script hash is correct, and that script requires `length === 4194304`.
The mailbox stayed in requested state with no script acknowledgment, and the
process remained untraced with CS_DEBUGGED unset in captured samples. The script
performs this validation before issuing `vAttach`, so it could not write a
failure response to an authenticated mailbox at this stage.

Both probe lanes contain a file named `ProbeProtocol.h`. Build 7's new launcher
used an unqualified import and did not have that header in its own source folder.
Its compile command searched `native-probe/src` before `managed-canary/src`, so
it selected the old 64 KiB contract. The earlier managed canary found its own
local header first and was unaffected.

BuildInfo's `bytes_per_arena` was separately hard-coded to 4 MiB. The earlier
report's statement that build 7 retained two 4 MiB requests was therefore wrong:
the script and intended configuration retained that geometry, but the compiled
launcher did not. The package hash checks verified the recorded files, not the
resolved include or generated request. Earlier mock script tests supplied a
handwritten correct request, and simulator UI tests disabled request generation.
Those tests missed the integration boundary.

The full export, photo and preserved build 7 sources remain private under
`.build/ios-jit/device-evidence/2026-09-11/`. The old IPA, DLL, symbols and iCloud
kit are preserved. This correction does not alter the independent AOT checkout
or the accepted build 6 source.

## Correction and verification

`CJHookProtocol.h` now explicitly includes the managed-runtime contract by path
and asserts the required protocol version and region length at compile time.
The launcher uses shared request/mailbox initialization and script-binding
functions. Their compiled protocol descriptor is embedded in the executable's
`__TEXT,__cjprotocol` section and used when constructing the request.

The builder captures the actual compiler dependency file and rejects the old
native header. It reads the compiled descriptor from the Mach-O and requires
protocol 1, 4,194,304 bytes per arena, a 96-byte mailbox and response/error offsets
48/88. Package validation checks those bytes in the final IPA again. Startup
logs include `compiled_jit_protocol`; native request creation also refuses a
compiled-versus-BuildInfo mismatch before opening StikDebug.

The new regression runs the actual shared native request builder and binder
inside the simulator, using a local fixture mailbox and explicit 16 KiB test
page size. It then runs that generated script with the exact script bytes from
the device IPA against a fake debugserver. It compares the sample's compiled
configuration with the ARM64 executable's descriptor. No debugger is attached
and no ARM64 code is executed by this host test.

Captured results:

- The corrected request completes two 4 MiB allocations, **512 distinct
  acknowledged page writes**, response readback, success publication and detach.
- Reprocessing build 7's preserved source with its recorded ARM64 compiler flags
  resolves `CJ_ARENA_LENGTH` to **65536**. Reconstructing that request reproduces
  the exact geometry error with **zero debugger commands**.
- Stale nonce and wrong PID checks reject their requests. All 16 existing
  script failure-path tests also pass.
- Simulator import, disabled execution gates, export, 800-event log burst and
  previous-session/console recovery pass.
- The final unsigned package has the expected ARM64 executable and exact
  178-DLL closure, with no embedded symbols/signature/profile/test fixture.

The Mono archives, framework DLLs, MonoMod/Cecil DLLs, native hook bridge,
managed runtime host, hook fixture and script are unchanged from build 7.
The delivered DLL was rebuilt after IPA packaging and has the same SHA-256:
`c4256d9f5f6400fe5b23a7b1590c4b343c280a90d882fbce3efb37999dc28157`.
The existing actual-Mono hook/alias regression receipts still match all their
source and binary inputs; their host results are retained, not presented as
new phone acceptance. This change addresses preparation, leaving the planned
physical Hook/ILHook and background/resume test intact.

## Retest

Use **iCloud Drive → Celeste JIT Tests → 0.3.1-build-8**. Fully close the old
LiveContainer 1 process and update the canary while preserving data. Keep
Launch with JIT off and its launch script empty. Use StikDebug in slot 2 and
import the supplied `HookCanary-v0.3.0.dll` copy. The app provides a fresh script.
No manual script modification is needed.

After preparation, run the initial hook phase. At its pass, wait 10 seconds,
go Home for 30 seconds, return to the same running process and run the resume
phase. At **PASS · HOOKS + RESUME**, wait 10 seconds and export diagnostics to
this version folder's **Results**. Export on failure too; after a crash reopen
and export before making another JIT request.

The local IPA is
`artifacts/ios-jit/hook-canary-20260911-08/CelesteJITHooks-unsigned.ipa`.
Its exact hash, source snapshot, symbols and confirmed cloud-upload state are
recorded in the evidence JSON. No commit, push, phone install or debugger
attachment was performed by the host for this correction.


**Delivery confirmed:** all six files and the Results directory report uploaded
with no error at **2026-09-11 10:17:18 UTC**. The kit is 10,905,670 bytes and all
copied file hashes match. Phone download/installation of build 8 is unobserved.

- IPA SHA-256: `f6675a9419549ed012f07a1f791c2471227b322de3afc7021e5fb52ea0ffcbf5`
- Matching executable/dSYM UUID: `3BF43DBB-7899-33A5-8CE0-F37F2212EE5B`
- The 73 source files identified by the receipt are preserved under
  `.build/ios-jit/device-evidence/2026-09-11/build-8-ready/source-snapshot/`.
