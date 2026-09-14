# Build 5 managed execution and build 6 cleanup fix — 11 September 2026

**Later result:** [build 6 passes the complete physical managed-runtime canary](MANAGED_EXECUTION_PASS_2026-09-11.md),
including clean detach, PASS UI and background/return. Its raw logs are directly
retrievable over USB. The remainder records the original build 5 investigation
and build 6 handoff snapshot; pending statements describe that earlier stage.

**The owner's recorded procedure was correct. Build 5 passed all eight managed
tests on the iPhone, then aborted in the native host's Mono worker cleanup.
Build 6 corrects that lifecycle transition and is copied directly onto the
phone for a clean-return and background/resume test.**

Imported IL and Reflection.Emit execution in the intended LiveContainer setup
are now physically established. The crashing return to the launcher prevents
accepting the complete, stable G1 handoff. MonoMod hooks and game execution are
still separate, untested milestones.

## Check of the owner's procedure

The new diagnostics were read from build 5's `Results` folder in iCloud Drive.
The matching `LiveContainer-2026-09-11-090123.ips` was fetched over USB without
attaching a phone debugger. Raw files, the source snapshot, validator and
symbolication remain under the private directory
`.build/ios-jit/device-evidence/2026-09-11/build-5-crash/`.

The current recovery launch contains three events. The relevant prior launch
contains **1,266 events**. Older build 4 sessions are also present and were
excluded from this result. Validation independently checks:

- Embedded build metadata exactly matches delivered **0.2.1 (5)**. Every source
  snapshot hash matches its original build receipt; the old IPA is preserved.
- The imported **Canary-v0.2.1.dll**, 8,704 bytes, has the expected SHA-256
  `55dd2e8c770a047996bcfb24936d3723a81e211eb389176e1b424df8cae33ef2`.
- This is a fresh host process relative to build 4. It starts without
  CS_DEBUGGED or an attached debugger, sends an inline script through
  `livecontainer2://open-url`, and retains the same PID through preparation
  and managed startup. These are recorded observations, not a visual inspection
  of LiveContainer's settings screen.
- The script template hash matches the delivered template. Its reply reports
  success, and the app verifies debugger detach before executing generated code.
- All **26 native checks** pass, including execution on all **512 prepared
  pages** across the two 4 MiB arenas. Managed initialization and finalizer
  initialization both complete, and the imported assembly is loaded.

There is no observed setup or DLL-selection error. The test ran on
**iPhone16,2 / iPhone 15 Pro Max, iOS 26.5 / 23F77**. LiveContainer 3.8.9 and
StikDebug 3.1.9 remain the prior owner-reported versions, not newly measured
application versions.

## Managed execution result

The runtime selected challenge **286** and obtained every expected result:

| Stage | Actual = expected |
| --- | ---: |
| NativeImports | 291 |
| Arithmetic | 324516221 |
| SwitchTable | 1047 |
| Dynamic | 895 |
| DynamicSwitch | 454 |
| GenericAbi | 4017 |
| ExceptionsAndGC | 305 |
| ThreadAndCallback | 310 |

Each imported stage also has a verified Mono JIT-info entry in prepared memory.
The end-of-tests record contains **612 JIT completion events**, with positive
profiler evidence for the imported arithmetic method and both newly emitted
dynamic methods, zero compiler failures and zero out-of-arena JIT ranges.
The recorded total reaches **628 events** while other managed thread-exit work
continues: **570 distinct method-name strings and 518 distinct entry addresses**.
Every observed range independently fits a recorded allocation. Event counts
must not be described as unique method counts.

All **21 native import resolution events** succeed. The build 4 import and
ordinary/dynamic switch regressions therefore pass physically in build 5.
The allocator reserved **851,968 bytes** in seven page-aligned allocations;
their unrounded requests total 786,932 bytes. The abort is unrelated to the
canary's 8 MiB code-memory limit.

## Exact cleanup fault and fix

The native console records:

```text
mono_thread_detach Cannot transition thread ... from STATE_BLOCKING with DO_BLOCKING
```

The OS reports **SIGABRT**, with the triggering thread in the native canary's
dispatch worker. The original dSYM UUID matches the device image:
`ba9e9c45-1891-3955-a8a9-4c0ff31493d6`. Symbolication traces the abort through
`mono_threads_transition_do_blocking`,
`mono_threads_enter_gc_safe_region_unbalanced_with_info`, `mono_thread_detach`
and `CJManagedRun`, after the managed-test evidence event. This is a different
fault from build 4's RX table write.

Under the pinned runtime's cooperative GC, the embedding thread returns from
bootstrap in GC-safe (`STATE_BLOCKING`) mode. The host called
`mono_thread_detach` in that state. The detach routine temporarily enters
GC-unsafe mode for its internal work, restores its incoming mode, then makes
an unbalanced transition to GC-safe mode. Starting already GC-safe therefore
attempts a non-nestable second blocking transition.

Build 6's shared [CJMonoThread.c](../../experiments/ios-jit/managed-canary/src/CJMonoThread.c)
explicitly enters GC-unsafe mode before detach, following the pinned runtime's
own detach-if-exiting pattern. Detach consumes that transition and leaves the
worker GC-safe; there is deliberately no second region-exit call afterward.
The helper checks that the managed thread object has been cleared. It does
not disable runtime checks, suppress the abort, leave the thread attached, or
shut down/reinitialize Mono.

The bootstrap also brackets each managed invocation and returned-object or
exception inspection in a balanced GC-unsafe region. This protects managed
references and restores the caller's mode on success and failure. All eight
fixture bodies are unchanged; build 6 supplies a versioned assembly identity.

New diagnostic events distinguish completion stages:

1. `managed_worker_detach_start`
2. `managed_worker_detached` with `managed_thread_cleared=true`
3. `g1_managed_pass`
4. `managed_result_presented`
5. `managed_post_run_alive`, five seconds after presenting the result

These make a late host failure visible separately from successful managed
execution. AOT/interpreter configuration, the native Mono archive, framework
IL, allocator and StikDebug script match build 5 exactly. The iOS runtime source
patch remains the same seven-file patch; this correction belongs to embedding.

## Local verification

The new [lifecycle regression](../../experiments/ios-jit/managed-canary/tests/check_mono_lifecycle.py)
executes actual **Mono 8.0.28**, built from the same source commit on the Intel
Mac with cooperative GC, AOT and interpreter disabled. The old call reproduces
the exact `STATE_BLOCKING` / `DO_BLOCKING` abort after all eight managed stages.
The shared corrected helper passes bootstrap detach and **160
attach/invoke/detach cycles across five native threads**, covering both GC-safe
and GC-unsafe entry states and reuse of an already detached native thread.

This harness uses the exact physically tested canary DLL and matching **macOS**
Mono framework IL/System.Native. It does not substitute host components into
the IPA. An initial attempt to use iOS framework IL on this x64 host recursed
during bootstrap; using the matching macOS pack resolved that harness error.
Do not treat architecture-specific Mono runtime packs as interchangeable. The
host package's NuGet catalog SHA-512 and source commit were verified and are
pinned in [host-runtime-pin.json](../../experiments/ios-jit/managed-canary/tests/host-runtime-pin.json).

Build 6 cross-compiles with **Xcode 26.6 / 17F113, iPhoneOS SDK 26.5**. Package
validation verifies all build inputs, 168 framework assemblies, notices,
external fixture identity and absence of signatures, provisioning profiles
and embedded dSYMs. Its new 8,704-byte DLL is compiled after IPA packaging,
absent from the IPA and passes **40 host CoreCLR fixture checks**, including
verification that the ordinary switch uses an actual IL switch instruction.

The iOS 26.5 x64 simulator passes import, pre-JIT run gating, export, prior
session/native-console recovery and the 800-event logging burst. Its screenshot
was inspected. It contains no Mono and does not validate the device cleanup
or new post-run events. Prior allocator/switch/script regression evidence is
retained by unchanged input hashes; the actual device is needed for the final
build 6 lifecycle result.

## Files on the phone and physical test

**Files → On My iPhone → LocalSend → Celeste JIT Tests → 0.2.2-build-6**

The six-file kit was copied over USB and **every file was read back from the
phone and checked by SHA-256**. It contains the unsigned IPA, new DLL, README,
full instructions, script template and checksums. A `Results` subfolder is ready.
This confirms file placement; the host did not install or launch the guest IPA.

CoreDevice's `appDataContainer` file listing still fails, but LocalSend's normal
file-sharing service works. Transfer used **House Arrest `VendDocuments` / AFC**
through [pymobiledevice3](https://github.com/doronz88/pymobiledevice3), installed
only in `.build/ios-jit/device-transfer-tools/`. It was restricted to the matched
iPhone 15 Pro Max's LocalSend Documents and known new test paths. No debugger
or phone settings change was involved. Keep pairing material and raw transfer
metadata private; the result receipt contains no UDID or pairing secrets.

An additional local copy exists at
`iCloud Drive/Celeste JIT Tests/0.2.2-build-6`; cloud upload state is recorded
separately in the evidence. The verified LocalSend copy is the primary handoff.

Local unsigned IPA:
`artifacts/ios-jit/managed-canary-20260911-06/CelesteJITCanary-unsigned.ipa`.

| Input | SHA-256 |
| --- | --- |
| IPA 0.2.2 (6) | `5618c57a3d1189d091c577774ddec43e86e36dbd911cf7be14667e7bd64a8cb5` |
| Canary-v0.2.2.dll | `4e29d1b7d7b301e1addd6a99c22002122d1b1ed3933de5afb656e73bc49e6094` |
| Script template, unchanged | `79d53b7c77fd2cfdb6045e1b699c2b8e0eca3822d9cfb98a03556b35d674b72b` |

Fully close the old canary, update the IPA in LiveContainer 1 while keeping
app data, and import `Canary-v0.2.2.dll` from the LocalSend folder. Keep Launch
with JIT OFF and the launch-script field empty. Have StikDebug ready in
LiveContainer 2, enable JIT through the canary, return to the same process and
run the managed test after native PASS. The app supplies its fresh script.

At **PASS · MANAGED JIT**, stay in the foreground for **10 seconds**, switch to
Files or Home for about **20 seconds**, and return to the same canary. Export
diagnostics into the LocalSend `Results` subfolder or send the JSON in chat.
If it crashes, reopen and export before another JIT request. The LocalSend
README/INSTALL copies use the on-phone location; their hashes differ from the
iCloud guides for that reason. IPA, DLL and script bytes are identical.

After a clean physical return/resume result, proceed to actual MonoMod
Hook/ILHook and original-call/removal tests. The native launcher, dynamic code,
GC/ABI/callback primitives now have direct physical evidence; game/native
lifecycle integration and mod compatibility still require their own tests.
There is no gameplay or performance claim yet.

See [the evidence ledger](BUILD_5_EXECUTION_AND_BUILD_6_EVIDENCE.json) for original
input identities, physical observations, host receipts and both transfer states.
The AOT checkout and user game inputs were not modified. Old kits/results were
preserved. No commit, push or GitHub write was made.

## Pinned runtime references

- [Thread attach/detach and detach-if-exiting](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/metadata/threads.c).
- [GC state-transition implementation](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/utils/mono-threads-coop.c).
- [Non-nestable blocking state transition](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/utils/mono-threads-state-machine.c).
- [Exact embedding API signatures](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/utils/mono-threads-api.h).

Runtime references were inspected locally at the recorded immutable commit.
