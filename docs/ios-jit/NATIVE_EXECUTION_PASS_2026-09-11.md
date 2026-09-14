# Native execution confirmed; signing package corrected

11 September 2026. Physical test: `native-probe-20260911-02`, app 0.1.1 (2).
Packaging correction: `native-probe-20260911-03`, app 0.1.2 (3).

**The supplied reports establish native generated-code execution in the intended
LiveContainer configuration. Proceed to the managed-runtime canary.** They do
not establish managed .NET JIT, MonoMod hooks, Celeste or mod compatibility.

## Captured device result

The phone is the owner's iPhone 15 Pro Max (iPhone16,2), running iOS 26.5.
Owner-entered versions are LiveContainer 3.8.9 and StikDebug 3.1.9. The probe
runs in LiveContainer 1 and StikDebug in LiveContainer 2.

Both exports match the delivered build 2 source hashes, script hash and build
timestamp. They describe one process: the first export is an exact prefix of
the later export. Count **three distinct runs**, with 80 passed checks and no
failed checks in the current session. Old build 1 failures remain correctly
preserved as historical sessions. The current session is no longer duplicated
in the history section.

| Evidence | Verified result |
| --- | --- |
| JIT preparation | One fresh M1 request; valid script response |
| Debugger state | Detached before and after each run; CS_DEBUGGED remains set |
| Prepared memory | Two 64 KiB regions; each spans four 16 KiB VM entries |
| Mappings | Separate RX (5) and RW (3) views, exact permissions throughout |
| Generated instructions | Random return values match; rewritten instructions produce changed results |
| Coverage | All eight prepared pages and both region ends execute |
| Calls | Integer argument/return and generated cross-region branch pass |
| Threads | Generated code executes on a second, distinct worker thread |
| Rewrite stress | 128 rewrites and 16,384 calls per run; 49,152 stress calls total |
| Background/return | 29.776 seconds in the background, followed by two passing reruns |
| Re-preparation | No second JIT request or second set of mappings for those reruns |

The first run has 32 checks; each subsequent run has 24 because initial mapping
creation is reused. Diagnostic storage reports no error. The reports capture
execution results, not just a green UI label or debugger flag.

Raw exports are retained only under ignored
`.build/ios-jit/device-evidence/2026-09-11/build-2-pass/`. Their hashes, the
validated counts and acceptance scope are in the
[evidence ledger](NATIVE_EXECUTION_PASS_2026-09-11_EVIDENCE.json).

This establishes G0's successful native-execution path on the intended target.
It does not finish the entire original G0 matrix: standalone installation,
reboot/re-preparation, device cancellation/wrong-script paths, memory pressure
and long-run behavior remain untested. Native branch/thread tests do not prove
managed unwind, GC, runtime trampolines or hooks, and these small loops are not
a performance comparison with AOT.

## Cause of the LiveContainer signing error

Both original IPAs contain this unintended path:

```text
Payload/CelesteJITProbe.app/CelesteJITProbe.dSYM/Contents/Resources/DWARF/CelesteJITProbe
```

That is a debug-symbol Mach-O (`MH_DSYM`, file type 10), not the executable
(`MH_EXECUTE`, file type 2). Its bundle-relative suffix exactly matches the
owner's signing error. The error was a packaging mistake in this project.
The captured successful launches and test runs show it did not prevent this
particular installation from executing the probe.

The builder compiled Objective-C source and linked with `-g` in one clang
command. A dry run of that exact command with Xcode 26.6 confirms an implicit
`dsymutil` job placing symbols beside the executable, inside the `.app`.
Our separate explicit symbol-output command did not remove that extra bundle.
The earlier signature checks inspected the actual executable but failed to
reject debug symbols elsewhere in the payload.

Build 3 compiles `main.m` to an object before linking, generates only the
explicit external dSYM, and rejects `.dSYM` paths and thin `MH_DSYM` files both
before packaging and inside the resulting ZIP. A regression check rejects the
actual bad build 2 archive and a renamed copy of its debug-symbol file, then
accepts the corrected IPA. The new IPA contains one Mach-O: the app executable.
The retained external symbols' UUID matches that executable.

The native sources, embedded StikDebug script and executable `__TEXT,__text`
instruction bytes match physically tested build 2. The new build is unsigned
and its source hashes and version were verified. This turn did not repeat
unchanged native/VM/mock/simulator tests; validation targets the packaging
change. The owner subsequently confirmed that build 3 downloads and installs without
error. This is owner-reported installation evidence; the detailed native
execution evidence remains the build 2 exports.

## Delivery and next work

Local IPA:
`artifacts/ios-jit/native-probe-20260911-03/CelesteJITProbe-unsigned.ipa`

SHA-256: `f3663787b13b892f46af7322ce146500b8e8d7a63bee025ff795249c96f0a254`.
The IPA is 72,009 bytes. Its phone copy is named
`CelesteJITProbe-0.1.2-build-3-unsigned.ipa`.

The phone handoff folder is **Files → iCloud Drive → Celeste JIT Tests →
0.1.2-build-3**, containing the IPA, short README, full instructions and checksums
(86,420 bytes total). The evidence JSON records the observed cloud-upload state;
after a transient upload error, Foundation confirmed all four files uploaded
at 00:31:37 UTC on 11 September. Actual phone download/installation remains
unobserved. Local copy verification alone is not a phone install result.
Preserve the previous data container when updating. A brief installation check
should determine whether the dSYM warning is gone; a full repeated native run
is not required for this packaging correction.

The next implementation target is G1: a pinned modern Mono runtime/BCL pair,
embedded behind the existing native launcher and verified M1 preparation path.
All runtime-generated code and stubs must use an allocator aware of separate
write/execute addresses and cache flushing. Load a DLL imported after the IPA
was built, JIT its method and a dynamic method, and instrument the compiler/
code-cache path to exclude interpreter or precompiled-fixture explanations.
Then cover generics, struct/floating-point ABI, exceptions, callbacks, managed
threads and GC before adapting actual MonoMod hooks. Keep the runtime and
hook milestones separate from Celeste content and launcher polish.

No AOT checkout writes, commits, pushes or GitHub changes were made.

The owner authorized proceeding to the managed-runtime prototype after the
successful build 3 installation.
