# Build 4 crash investigation and build 5 retest — 11 September 2026

**Latest result:** [build 6 passes all eight stages, clean cleanup and
background/return](MANAGED_EXECUTION_PASS_2026-09-11.md). This report records
the earlier build 4 investigation and build 5 handoff snapshot.

**Managed framework JIT execution was observed on the owner's phone. The full
imported-DLL canary did not finish initializing. Build 5 fixes the identified
startup faults and is ready for another physical test.** Celeste, Everest and
MonoMod are still later gates.

## Evidence from the phone

The owner saved diagnostics in the build 4 iCloud folder. With the phone now
connected, CoreDevice also retrieved the matching LiveContainer crash report.
No debugger was attached and no StikDebug session was started by the host.

The recovery export contains three current-launch events and two earlier
sessions. The relevant earlier session has **831 events** and matches the
delivered build 4 metadata, imported DLL hash, script template, crash PID and
Mach-O UUID. The original sources were preserved and checked against every
source hash in the build receipt before editing. Raw diagnostics, native
console tails, the `.ips`, symbolication and disassembly remain private under
`.build/ios-jit/device-evidence/2026-09-11/build-4-crash/`.

| Physical observation | Result |
| --- | --- |
| Target | iPhone 15 Pro Max / iPhone16,2, iOS 26.5 / 23F77 |
| LiveContainer / StikDebug | Existing reported values 3.8.9 / 3.1.9; not independently remeasured |
| Prepared memory | Both 4 MiB arenas; generated instructions executed on all 512 pages |
| Native checks | 26 passed, zero failed |
| Managed startup | Debugger detach verified, CS_DEBUGGED set, allocator initialized |
| JIT evidence | 405 completion events; 373 distinct method-name strings; 344 distinct code entry addresses |
| Code ownership | Every reported JIT range independently fits one of the two recorded allocations |
| Reserved code | 524,288 bytes at the crash; not exhaustion of the 8 MiB budget |
| Last compilation started | `System.Resources.ResourceFallbackManager/<GetEnumerator>d__5:MoveNext ()` |
| Final stage | Inside `mono_jit_init_version`; no runtime-init success, imported assembly load or fixture stage result |

The JIT events are not 405 unique methods. Repeated callbacks and distinct
instantiations must not be conflated. The retained managed stack also shows
executing framework methods, including startup/resource/exception code, which
supports actual framework execution rather than compilation alone. This is
useful progress toward G1, but **G1 is not accepted** until imported IL,
Reflection.Emit and the ABI/exception/GC/callback stages pass.

The other earlier session imported the DLL and requested preparation but never
received a completion reply before its background allowance expired. It did
not execute generated code. The export alone cannot establish why that request
did not complete; the later session demonstrates a successful native handoff.

## Crash and startup fixes

The Mono console records the original fault PC as `0x10b7d307c`. The matching
build 4 image UUID is `98800471-1692-32db-b927-cc4169743c34`; its slide maps the PC
to `0x10012f07c`. Symbolication places it in `mono_codegen`; disassembly resolves
the inlined operation to the `MONO_PATCH_INFO_SWITCH` table in
`mono_postprocess_patches`:

```asm
str x9, [x0, x8, lsl #3]
```

That table was allocated in the RX code pool but populated through the RX
pointer. The previous port covered emitted instructions and other code stores
but missed this data table. Build 5 translates the table's write destination
through the RW alias while retaining the RX pointer as the logical address.
The same error existed in the second switch-table phase,
`mono_resolve_patch_target`, where offsets become absolute branch targets.
Both phases are fixed for ordinary and dynamic methods. The patch now changes
seven pinned runtime source files.

There were also **eight failed native import lookups**, all naming
`libSystem.Native`, for `SystemNative_SchedGetCpu`,
`SystemNative_LChflagsCanSetHiddenFlag` and `SystemNative_GetEnv`. The previous
resolver accepted `System.Native` only. The pinned framework's actual Unix
library constant includes the `lib` prefix. This produced initialization
exceptions and entered the resource/culture path in which the switch fault
occurred. Build 5 resolves the exact framework name and its explicit equivalent
aliases to the statically linked table. It records a preflight for all three
observed failing entry points before starting Mono.

The exception path also reached `EventPipeInternal.CreateProvider`, although
this small runtime is built with EventPipe disabled. Build 5 supplies the
framework's `System.Diagnostics.Tracing.EventSource.IsSupported=false` app-context
switch to match that compiled capability. The new managed fixture verifies
the switch and performs an environment-variable lookup through System.Native.
Native console capture and Mono/JIT profiler callbacks remain active. Full
EventSource/performance tracing is a later runtime capability decision.

The OS signal report captures the UI thread in TextKit while `refreshLog`
is running; the original Mono worker fault is identified by the console PC and
matching code. The UI frame does **not** establish a second independent root
cause. Nevertheless, queuing a complete log-layout update for every JIT event
was unnecessary pressure. Build 5 persists every event but renders the log at
most twice a second, skips unchanged snapshots and uses an explicit TextKit 1
log view. Its native-launch console line is compact; full build hashes remain
in the structured diagnostics.

Implementation: [runtime patch](../../experiments/ios-jit/managed-canary/runtime-alias.patch),
[native resolver](../../experiments/ios-jit/managed-canary/src/CJNativeResolver.c),
[managed bootstrap](../../experiments/ios-jit/managed-canary/src/CJManaged.m),
[fixture](../../experiments/ios-jit/managed-canary/fixtures/Canary.cs).

## Verification of build 5

- The regression harness extracts both actual switch cases from the pinned
  runtime. All four unpatched negative controls fault on a read-only RX view:
  two phases × ordinary/dynamic allocation. The patched cases pass ASan/UBSan,
  preserving offsets, eliminated entries and absolute RX targets.
- The actual native-library resolver passes against matching host System.Native
  exports, including all three observed failures, aliases, a real native GetEnv
  round trip, callback lookup and rejection of unknown/null names.
- The existing actual ARM64 emitter/allocator checks pass ASan/UBSan again.
  They validate generated bytes, aliases and bounds; this Intel host does not
  execute the generated ARM64 instructions.
- The external **8,704-byte DLL**, compiled after packaging the IPA and absent
  from it, passes **40 host logic checks**: eight stages × five inputs. Its
  ordinary switch method is inspected to require a real IL `switch` opcode;
  its new DynamicMethod explicitly emits another switch.
- Xcode **26.6 / 17F113**, SDK **26.5**, builds the custom ARM64 JIT runtime and
  unsigned app. The package validator checks source/runtime/framework hashes,
  168 framework DLLs, notices and external fixture identity. The IPA contains
  no code signature, provisioning profile or dSYM; symbols stay beside it.
- iOS 26.5 x86_64 simulator checks pass for import, disabled execution before
  JIT, export, prior-session/native-console recovery, and **800 background log
  events** preserved and rendered by the timer. The screenshot was inspected.
  This UI build contains no Mono; it does not validate device JIT or automate
  the real Files/share-sheet interaction.
- The matching script is unchanged from build 4, which prepared the phone's
  512 pages successfully. Its earlier 16 mock checks remain applicable by
  identical template hash. Runtime changes do not alter mailbox geometry.

Receipts and evidence are in [BUILD_4_CRASH_AND_BUILD_5_EVIDENCE.json](BUILD_4_CRASH_AND_BUILD_5_EVIDENCE.json)
and beside the IPA. Host passes establish these bounded regressions and fixture
expectations, not successful execution of build 5 on the phone.

## Physical handoff and next decision

Open **Files → iCloud Drive → Celeste JIT Tests → 0.2.1-build-5**. The six-file
kit is **10,173,261 bytes**, below the owner's 50 MB limit, and includes the
unsigned IPA, new DLL, numbered instructions, template and checksums. Upload
confirmation and copy identities are recorded in the evidence ledger; actual
phone download is not inferred from cloud upload. A `Results` subfolder is ready.

Local IPA: `artifacts/ios-jit/managed-canary-20260911-05/CelesteJITCanary-unsigned.ipa`.

| Input | SHA-256 |
| --- | --- |
| IPA 0.2.1 (5) | `de3ef2053020d5d536cdbb098883675f838c248ee1e24a664a91a0f6f6c1bba5` |
| Canary-v0.2.1.dll | `55dd2e8c770a047996bcfb24936d3723a81e211eb389176e1b424df8cae33ef2` |
| Runtime patch | `8851379ad30dc56ecbf4cbb8516afda53968a4cee8268a59c7d9e538e5be588b` |
| Script template | `79d53b7c77fd2cfdb6045e1b699c2b8e0eca3822d9cfb98a03556b35d674b72b` |

Follow [INSTALL.md](../../experiments/ios-jit/managed-canary/INSTALL.md). Fully
close the old canary, update it in LiveContainer 1 while preserving app data,
and import **Canary-v0.2.1.dll**. Keep Launch with JIT OFF and the launch-script
field empty. Have StikDebug ready in LiveContainer 2, request JIT from the
canary, return to the same process and run the managed test after native PASS.
The app creates the matching script; the supplied template is not standalone.

Expected managed stages, in order: **NativeImports, Arithmetic, SwitchTable,
Dynamic, DynamicSwitch, GenericAbi, ExceptionsAndGC, ThreadAndCallback**. A PASS
requires correct outputs and profiler evidence for both dynamic methods and
the imported arithmetic method, with no out-of-arena JIT ranges or failures.
Export diagnostics even on success. If it crashes, reopen and export before
another JIT request; save the JSON in this build's `Results` folder. Keep app
data so the failed session's console remains available.

After full physical G1 acceptance, proceed to actual MonoMod Hook/ILHook and
original-call/removal tests, then Celeste/FNA/native lifecycle integration and
Everest. Another startup fault should be diagnosed at its exact stage before
expanding the payload. No performance or arbitrary mod-compatibility conclusion
is supported yet. The bounded arenas, invariant globalization, no runtime
restart/unload and incomplete game-native integration remain deliberate limits.

The AOT checkout and user game inputs were not modified. No commit, push or
GitHub write was made. Old delivered build 4 files and results were preserved.

## Pinned implementation references

- [Original switch offset-table construction](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/mini/mini.c).
- [Original switch-target resolution](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/mini/mini-runtime.c).
- [Framework Unix library names](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/libraries/Common/src/Interop/Unix/Interop.Libraries.cs).
- [EventSource capability switch](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/libraries/System.Private.CoreLib/src/System/Diagnostics/Tracing/EventSource.cs).

These references were inspected in the local clone at the recorded immutable
commit; the crash diagnosis also uses the original binary and external symbols.
