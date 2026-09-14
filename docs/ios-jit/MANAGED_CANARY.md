# G1 managed runtime canary — 11 September 2026

**Latest follow-up:** [build 6 physically passes the managed-runtime canary](MANAGED_EXECUTION_PASS_2026-09-11.md),
including all eight stages, clean detach, PASS UI and background/return. Its raw
logs can be collected directly over USB; Export remains available. The rest
of this report is the original build 4 implementation/handoff snapshot;
pending/unproven statements below describe that earlier point in time.

**An unsigned managed-canary IPA is ready for the owner's physical test. Managed
JIT has not yet been demonstrated on the phone.** This is the next step after
the [three successful native-memory runs](NATIVE_EXECUTION_PASS_2026-09-11.md)
and the owner's confirmation that packaging-fixed build 3 installs cleanly.

Build **0.2.0 (4)** contains a custom .NET **8.0.28 Mono ARM64 JIT**, a native
launcher and an imported-DLL test. It does not contain Celeste, Everest,
MonoMod or game assets. Passing this test will justify the real hook canary;
it will not by itself demonstrate game/mod compatibility.

## Deliverable and physical question

Local unsigned IPA:
`artifacts/ios-jit/managed-canary-20260911-04/CelesteJITCanary-unsigned.ipa`

External test DLL: `Canary-v0.2.0.dll` in the same directory. The fixture was
compiled **after** the IPA was packaged, is absent from its payload, and is
copied into the app through the Files picker. There is no embedded fallback
copy. App logs record its SHA-256 before managed startup.

Phone handoff: **Files → iCloud Drive → Celeste JIT Tests → 0.2.0-build-4**.
The six-file handoff is **10,169,637 bytes**, below the owner's 50 MB limit.
Local copy verification, cloud upload status and device download observation
are separate fields in [the evidence record](MANAGED_CANARY_EVIDENCE.json).

The test asks: **Can this custom Mono runtime JIT-compile and execute imported
IL and Reflection.Emit code, after StikDebug detaches from the LiveContainer
host process, using the prepared RX/RW aliases?**

Use the [numbered physical test instructions](../../experiments/ios-jit/managed-canary/INSTALL.md).
Keep the canary in LiveContainer 1 and StikDebug in LiveContainer 2. Launch with
JIT remains OFF and the LiveContainer launch script remains empty. The native
launcher creates and forwards its own process-specific script. This is a new
app identity, `io.github.hmcneill46.celeste.everest.jit.canary`, so the earlier
native probe may remain installed.

## Runtime choice and implementation

The selected canary source is dotnet/runtime tag **v8.0.28**, commit
`46295af5828b062bbbf93a9cef50fd8cb9fbcb09`. Its framework IL and System.Native
archive come from the official **8.0.28 iOS ARM64 runtime package**, whose
NuSpec identifies the same commit. The package SHA-512 was verified. The
isolated .NET SDK **8.0.422** was also verified against Microsoft's published
SHA-512. [Pinned tuple](../../experiments/ios-jit/managed-canary/runtime-pin.json).

This targets the .NET 8 baseline of the audited Everest stable-1.6458.0. The
stock iOS Mono AOT archive is **not** used. Direct CMake cross-compilation builds
the JIT-enabled static runtime, the real marshal IL generator and stubs for the
unused debugger/hot-reload/diagnostics components. The configuration explicitly
disables AOT and the interpreter and retains Reflection.Emit. All 168 matching
framework assemblies, including System.Private.CoreLib, retain IL. The app's
native code, including Mono itself, is compiled ahead of time; managed methods
are the subject of the JIT test.

Xcode is **26.6 / 17F113**, selected per command, with iPhoneOS SDK **26.5** and
minimum OS 26.0. Source, package, SDK, generated headers, caches and runtime
outputs are confined to this JIT checkout's ignored `.build/ios-jit/` root.
The active `/Users/harrymcneill/Projects/celeste-ios` AOT checkout was not changed.

### Executable memory

The earlier M1 mailbox/PID/nonce/detach protocol is preserved, with a new fixed
geometry of **two 4 MiB RX arenas**. StikDebug must acknowledge all **512 page
writes** before publishing success. The app walks the full VM ranges, creates
distinct RW aliases, checks exact RX/RW protections and executes generated code
on every prepared page before offering the managed test. This larger geometry
is not yet physically accepted; old native-probe scripts cannot satisfy it.

The runtime patch keeps code pointers as **RX addresses**, which preserves
branch displacements and managed code-address lookup. Its instruction stores,
literal stores, final method copies, thunk initialization, code-pool reuse and
patch writes translate their destination into the corresponding RW alias.
Cache flushing uses the RW data address and RX instruction address. Temporary
heap emission buffers remain ordinary writable pointers.

Executable allocations use a checked, page-aligned, mutex-protected allocator
in the prepared arenas. Dynamic methods also use this path instead of
executable dlmalloc storage. Allocation failure is logged; code-space growth
and unmapping are intentionally absent from this bounded canary. Mono may
reuse its own freed code chunks, while the backing prepared pages live until
process termination. There is no RWX fallback or signal-based store emulator.

The original six-file source patch was generated against the exact pin, with
original and patched file hashes. Its immutable copy is in the private build 4
source snapshot; the [active patch](../../experiments/ios-jit/managed-canary/runtime-alias.patch)
has since been extended for build 5.
Host testing also identified an upstream signed opcode-literal shift in the
register-branch macro; its unsigned equivalent preserves the bits and permits
the tested emitter paths to pass UBSan. No broader upstream sanitizer claim is
made.

### Embedding and evidence

The native launcher stays responsive while a worker initializes Mono. It
supplies framework assembly paths, trusted-platform-assembly entries and the
same `PINVOKE_OVERRIDE` embedding mechanism used by the upstream Apple host.
A generated table resolves the statically linked System.Native functions
without relying on LiveContainer's global `dlsym` scope. A small explicit native
callback fixture tests managed → native → managed execution.

This canary uses **invariant globalization**. ICU/Apple culture entry points
are intentionally unavailable and remain unresolved if requested. Other game
native dependencies and managed Apple bindings are not integrated yet.

Before every potentially failing stage, the app persists a structured event.
Mono's log/print callbacks and native stdout/stderr are captured. Export includes
the current session, up to five previous sessions and up to 128 KiB of native
console output per session. After a crash, reopen and export before starting a
new JIT request. No additional debugger is needed for the initial run.

The five managed stages are:

| Stage | Evidence sought |
| --- | --- |
| Arithmetic | Imported method compiled by Mono, `MonoJitInfo` matches, code belongs to a prepared allocation, random challenge result matches |
| Dynamic | New Reflection.Emit method executes and its JIT profiler callback records code inside the prepared arenas |
| GenericAbi | Generic identity with mixed integer/long/double struct and homogeneous floating-point struct returns |
| ExceptionsAndGC | Live string array survives collections; a thrown exception crosses a method boundary into a filtered catch and finally |
| ThreadAndCallback | Another managed thread calls a native function and returns through a managed delegate |

The UI only reports managed PASS when all expected results match, imported and
dynamic methods have JIT completion evidence, and no observed JIT code lies
outside prepared allocations or reports a compiler failure. The diagnostic
report must still be reviewed against the delivered build, DLL and script
hashes. A successful method lookup, runtime-feature flag or interpreter result
cannot satisfy this gate. This is one-shot runtime execution; restarting or
unloading Mono in-process is not attempted.

## Completed local verification

- Custom iOS ARM64 JIT runtime and native launcher compile/link successfully.
  The final archive has no code signature, provisioning profile or embedded
  dSYM. Symbols are emitted beside the IPA. All source/runtime/BCL/script input
  hashes match the build receipt, and package integrity checks pass.
- ASan/UBSan host test passes for the actual patched Mono ARM64 emit/patch
  macros using a **read-only** RX view. It verifies RX-based branch displacement,
  separate write alias, ordinary heap buffers, bounds rejection, exhaustion and
  concurrent reservations. The Intel host does not execute these ARM64 bytes.
- **16 fake-debugserver tests pass**, including full preparation, nonce/PID
  rejection, stale requests, response corruption, detach failure and rejection
  of the 500th page write without publishing success.
- **25 fixture logic checks pass** on host CoreCLR 8.0.28, including dynamic
  methods, struct/generic returns, GC/exceptions and native callbacks. This
  validates fixture expectations, not the custom iOS Mono runtime.
- iOS 26.5 **x86_64 simulator** checks pass for startup, the actual DLL import
  handler, disabled managed execution before JIT, export and recovery of a
  terminated prior session and its native console. The screenshot was inspected.
  The simulator app contains no Mono runtime; picker/share-sheet taps were not
  automated. The simulator was shut down afterwards.

Receipts are beside the IPA and summarized in
[MANAGED_CANARY_EVIDENCE.json](MANAGED_CANARY_EVIDENCE.json).

## Next decision

Obtain the owner's physical report for build 4. If it stops during startup,
use the last native/Mono/JIT event and retained console to fix that boundary.
If it passes, build the **actual Hook/ILHook test** using the pinned MonoMod
source and an iOS code-memory backend. Then bring up Celeste/FNA and the native
graphics/audio/lifecycle bridge in this single managed runtime, followed by
Everest and a small mod profile. Strawberry Jam remains later compatibility
work; the AOT lane continues independently.

Still unproven: managed execution on this phone, all runtime code-write paths,
hook installation/original-call chains/removal, larger profiles and late code
growth, full globalization/native-library coverage, game startup, performance,
thermal behaviour and background/resume with a live managed game. The broader
G0 standalone/reboot/failure matrix also remains incomplete.

No commits, pushes or GitHub writes were made. Future integration must preserve
the user's explicit approval requirement.

## Primary implementation references

- [.NET 8.0.28 source](https://github.com/dotnet/runtime/tree/46295af5828b062bbbf93a9cef50fd8cb9fbcb09)
  and [official iOS runtime package](https://www.nuget.org/packages/Microsoft.NETCore.App.Runtime.Mono.ios-arm64/8.0.28).
- [Mono code manager](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/utils/mono-codeman.c),
  [ARM64 emitter](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/mono/mono/arch/arm64/arm64-codegen.h),
  and [Apple embedding template](https://github.com/dotnet/runtime/blob/46295af5828b062bbbf93a9cef50fd8cb9fbcb09/src/tasks/AppleAppBuilder/Templates/runtime.m).
- [Microsoft SDK release metadata](https://builds.dotnet.microsoft.com/dotnet/release-metadata/8.0/releases.json).
- [mono-nx](https://github.com/exelix11/mono-nx) was also considered: its stated
  interpreter/AOT focus does not establish a solution for this native iOS JIT
  gate. No code from it was incorporated.
