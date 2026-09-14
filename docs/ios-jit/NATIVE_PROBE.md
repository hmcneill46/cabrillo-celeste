# First native JIT probe — implementation and device handoff

Date: 10 September 2026. Build: `native-probe-20260910-01`.

**Latest result:** [build 2 passed native execution on the target phone](NATIVE_EXECUTION_PASS_2026-09-11.md)
three times, including background/return. Build 3 corrects debug-symbol
packaging. This document's original delivery details remain historical.

**Follow-up, 11 September:** the [first physical report and corrected 0.1.1
probe](DEVICE_TEST_2026-09-11.md) identify a VM-range validation bug. The original
handshake and detach worked, but execution stopped before generated code ran. The
historical delivery/host evidence below applies to build 1.

**Status: unsigned native IPA available for the first physical test. Device
execution is pending.** This advances the [feasibility audit](FEASIBILITY_AUDIT.md)
from a compile-only ABI experiment to an installable diagnostic. It does not
establish a managed JIT, Celeste launch or mod compatibility.

The owner confirmed an iPhone 15 Pro Max / iOS 26.5, with the probe installed in
**LiveContainer 1** and **StikDebug already running inside LiveContainer 2**.
The exact LiveContainer/StikDebug versions remain to be captured. The guide and
app use that two-container arrangement rather than assuming a standalone
StikDebug installation.

## Why this is the next step

Before investing in a custom .NET allocator or adapting MonoMod, establish that
this actual host process can execute code written after installation, modify
it coherently and continue executing it after the debugger detaches. The
result identifies whether a failure is in process targeting, debugger/page
preparation, memory aliasing, cache coherence or execution itself.

A complete Celeste mod test would combine these unresolved parts with a runtime
port, hook backend, platform bridge and Everest integration. The native probe
keeps useful startup/recovery behavior available before any generated code
runs. It needs no game files, FMOD SDK or .NET installation. The existing
vanilla/AOT projects and the active `/Users/harrymcneill/Projects/celeste-ios`
checkout were not modified or used as writable staging.

## Delivered implementation

Source is in [experiments/ios-jit/native-probe](../../experiments/ios-jit/native-probe/README.md).
The local delivery is under `artifacts/ios-jit/native-probe-20260910-01/`:

- `CelesteJITProbe-unsigned.ipa`: ARM64 native UIKit application, bundle ID
  `io.github.hmcneill46.celeste.everest.jit.probe`, minimum iOS 26.0.
- `INSTALL.md`: complete owner-specific install/test/recovery instructions.
- `celeste-jit-probe-TEMPLATE.js`: matching script source, also embedded in the
  app. The app generates and sends a complete script for each running process.
- `build-receipt.json`, `SHA256SUMS.txt`, build log and Mach-O load commands.
- `CelesteJITProbe.app.dSYM`, original-repository license and provenance notes.

The source builder uses Xcode 26.6 (`17F113`) and iPhoneOS SDK 26.5 through a
per-command `DEVELOPER_DIR`. It verifies the lack of `LC_CODE_SIGNATURE`, an
embedded provisioning profile and a `_CodeSignature` directory before packing
the conventional `Payload/*.app` IPA. No global Xcode setting was changed and
no commit, push, remote repository change or publication was made.

## Mailbox handshake and two-container flow

This first physical probe uses a small **M1 mailbox** instead of entering
`brk #0xf00d`. A debugger flag alone cannot identify the script that is attached,
and a breakpoint issued with no matching handler risks stopping/crashing the
app before it can export useful information. A native app can start without
JIT and publish its own data address to the explicitly selected debugger.

```mermaid
sequenceDiagram
    participant P as Probe in LiveContainer 1
    participant S as StikDebug in LiveContainer 2
    participant D as Device debugserver
    P->>P: Start native UI and persistent log
    P->>P: Create PID + random nonce + mailbox request
    P->>S: livecontainer2 open-url envelope, script-data + actual PID
    S->>D: Attach to requested PID
    S->>D: Read and validate mailbox identity
    S->>D: Allocate two RX regions and prepare every page
    S->>D: Write checked response to mailbox, read it back
    S->>D: Detach
    P->>P: On return, verify response and detached trace state
    P->>P: Create RW aliases; write, invalidate, execute and patch
    P->>P: Report native PASS/failure and export diagnostics
```

The app sends a standard `stikdebug://enable-jit?pid=…&script-data=…` request
inside LiveContainer 2's base64 `open-url` envelope. It omits the guest bundle
identifier. StikDebug's inspected URL handler supports a PID without a bundle
ID, and avoids its bundle-return/relaunch step in that case. The owner returns
to the existing first-container process using the app switcher. Both containers
must remain distinct and StikDebug must already be running in slot 2.
[StikDebug URL handler and dispatch](https://github.com/StikDebug/StikDebug/blob/94bc9e8cf3b41f32f125f046abf33d913f4e1b2d/StikDebug/Views/HomeView.swift),
[LiveContainer incoming/outgoing URL handling](https://github.com/LiveContainer/LiveContainer/blob/3afa9eb9a53625e9b8bd8b932e5785fd716ad5ae/TweakLoader/UIKit%2BGuestHooks.m).

This means **Launch with JIT is OFF for this particular probe**. It must first
run native code to publish its mailbox. The ordinary LiveContainer procedure
for an app needing JIT before startup is documented separately in
[LiveContainer's JIT guide](https://livecontainer.github.io/docs/guides/jit-support).
Do not mechanically apply that prelaunch flow to this implementation.

The mailbox is 96 bytes: magic/version, random 128-bit nonce, PID, requested
arena length, and the script-written status/addresses/length/version/error.
The script compares the complete 48-byte request header and requires a pristine
waiting response before allocating anything. It rejects stale PID/nonce,
malformed/short remote replies, reused requests, invalid/overlapping allocations,
rejected page writes and failed read-back. Wrong identity causes detach without
memory writes. A partial preparation failure records a phase where possible,
attempts detach and requires a fresh app process before retry.

The script uses the documented debugserver allocation/page preparation behavior:
`_M<size>,rx`, then debugger writes to each 16 KiB page. Unlike the inspected
batch helper, it checks **each individual page-write reply** and the final
mailbox writes. The app prepares two 64 KiB regions, not an oversized speculative
runtime reservation. Source basis:
[StikJIT integration](https://github.com/stikdebug/StikJIT/blob/3623e725876f76aecb0520582ad6194bacb15d39/INTEGRATION.md),
[StikJIT script host](https://github.com/stikdebug/StikJIT/blob/3623e725876f76aecb0520582ad6194bacb15d39/Sources/ScriptRunner.swift).

No code is generated/executed until the app observes the matching response,
can read its trace state, confirms no debugger is attached, and confirms
`CS_DEBUGGED`. This last flag is diagnostic/precondition evidence, not a PASS.
The app uses `vm_remap` for distinct mappings, sets the alias to RW, and queries
both mappings to require RX and RW respectively. There is no RWX fallback,
interpreter fallback, broad signal handler or hidden precompiled “success” path.
Dynamic constants are selected at runtime and emitted as machine instructions.

The original `brk #0xf00d` ABI compile experiment remains separate and has still
not executed on the phone. M1 is a useful native-bootstrap option, not yet a
decision to replace every future runtime allocation with a debugger round trip.
If the runtime can suballocate from prepared arenas, this handshake may be
reusable; exhausted-arena growth still needs an explicit strategy.

## Device checks and evidence

The app tests:

1. Exact region bounds and distinct RX/RW aliases after debugger detach.
2. Byte sharing across aliases and generated random integer return values.
3. Rewriting instructions, flushing data cache and invalidating instruction cache.
4. Execution from every prepared page and the end of both regions.
5. Integer argument/return ABI and a generated indirect branch to another arena.
6. Execution on a second worker thread.
7. 128 sequential code rewrites and 16,384 calls without concurrent patching.
8. An owner-triggered repeat after background/foreground in the same process.

The generated branch is **not MonoMod**. This test says nothing about managed
method identity, original-call chains, exception/unwind metadata, generic/struct
ABIs, GC, hook removal, imported DLLs, FNA/SDL, game performance or Strawberry
Jam. Those remain later gates from the audit.

Native JSON-lines logs are synced before potentially failing execution stages.
The share export contains build/source/template/session-script hashes, OS and
hardware, actual PID/kernel process name, code-sign flags, trace observations,
VM errors/protections, stage/check results and entered version information.
It includes up to five prior sessions so reopening after termination can
recover the last stage. Pairing records, credentials, UDIDs, arbitrary host
paths and game content are not collected.

A separate system crash report may still be necessary for the exact fault.
Use the actual first-container process and a non-attaching console when
StikDebug is active. The full [physical procedure](../../experiments/ios-jit/native-probe/INSTALL.md)
explains what to send. The provided summarizer reports the evidence in an export
without converting a simulator success or incomplete log into a physical PASS.

## Host validation and remaining limits

Validation is recorded in `NATIVE_PROBE_EVIDENCE.json` and the local delivery
receipts. It comprises device cross-compilation, unsigned-package inspection,
15 fake-debugserver protocol cases, ARM64 assembler comparison, simulator
startup/layout, actual diagnostic serialization and previous-session recovery.
The simulator build disables JIT requests and generated-code execution.

There has been **no physical run**, so the intended LiveContainer 1 → 2 URL
route, installed StikDebug's behavior, iOS 26.5 page preparation/alias behavior,
actual code execution and background survival are hypotheses to test. The
inline request is about a few kilobytes of source encoded twice; if an installed
URL handler rejects its length or encoding, the app can export the exact
session script and send a shorter PID + imported-script-name request instead.

A native PASS on the requested container configuration is valuable G0 evidence;
it does not complete every broader G0 hardening case. Standalone signed-device
execution, wrong-script/cancel/reboot cases and region-growth policy remain to
be assessed as needed. Do not immediately declare the entire audit's gates
complete from a green label.

## Decision after the owner test

- No script reply: inspect route, installed versions, script import, pairing/DDI
  and actual PID before touching the CLR.
- Preparation error: inspect the numbered phase and rejected remote operation.
- VM protection/alias failure: investigate the native allocator model on this
  iOS/device/host combination. Preserve the original failure evidence.
- Execution/cache failure: use the last stage, memory metadata and crash report
  to narrow the native issue before runtime work.
- Native PASS plus background repeat: proceed to a custom managed-runtime
  canary that loads an unseen DLL and demonstrates actual native managed-JIT
  emission, then real MonoMod `Hook`/`ILHook` semantics.

The runtime recommendation remains provisional modern Mono with an explicit
Apple executable allocator, measured against its compatibility risks. No
off-the-shelf .NET iOS flag was introduced, and the AOT product remains an
independent development lane.
