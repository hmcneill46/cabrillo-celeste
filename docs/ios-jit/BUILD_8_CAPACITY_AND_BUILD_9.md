# Build 8: real hooks ran, then the code budget ran out

11 September 2026. Retest: **hook-canary-20260911-09, version 0.3.2 (9)**.

The owner's build 8 procedure was correct. The corrected JIT protocol worked,
all eight managed stages passed, and **21 real MonoMod hook assertions passed**.
The process then exhausted the canary's fixed 8 MiB code arena while compiling
a generated struct-hook method. This is partial physical hook evidence;
**the complete G2 gate is not accepted**, and Celeste gameplay is not implemented.

Build 9 raises the hook canary's capacity to **32 MiB**, provides its matching
StikDebug script, logs code reservations at hook stages, and stops with a
specific diagnostic if another allocation fails. The six-file test kit is
**10,906,448 bytes** at **iCloud Drive → Celeste JIT Tests → 0.3.2-build-9**.
All files and Results were confirmed uploaded without error at
**2026-09-11 10:38:29 UTC**. Phone download/installation remains unobserved.

See [the evidence ledger](BUILD_8_CAPACITY_AND_BUILD_9_EVIDENCE.json) and
[the complete phone procedure](../../experiments/ios-jit/hook-canary/INSTALL.md).

## What the exported crash proves

The export contains a fresh recovery launch and the crashed build 8 session
among its previous sessions. The persisted console contains the native and
managed stack traces. Its build metadata matches the delivered receipt;
the imported DLL and bundled script hashes match. It records the expected
LC1 → LC2 route, correct 4 MiB requests, successful preparation and detach,
and native execution before Mono started. There is no observed setup error.

| Observation | Physical build 8 result |
| --- | --- |
| Device | iPhone 15 Pro Max / iPhone16,2, iOS 26.5 (23F77), 16 KiB pages |
| Native checks | 26 passed, including execution across both prepared arenas |
| Managed baseline | All eight G1 stages passed |
| Hook assertions | 21 passed; no failed assertion or rejected code patch |
| Executable hook patches | 54 writes, each backed up, written through RW, flushed and verified |
| JIT completion events | 2,863; all within prepared allocations |
| Distinct compiled entry addresses | 2,617, totaling 963,708 reported code bytes |
| Last completed hook check | Instance-method hook disposal restored the original |
| Last requested compilation | Generated SyncProxy for `Box.Value`, the 32-byte struct-return case |
| Last allocator event | Failed 262,144-byte request after 8,192,000 bytes were reserved |
| Initial hook phase / clean detach / resume | Not reached |

The passed cases include original calls with changed arguments, undo/reapply,
disposal, ordering independent of creation order, removal/reinsertion in a
chain, IL constant changes, combined Hook/ILHook behavior, removal of an ILHook
while its Hook remained installed, and instance `this`/original semantics.
The struct-return result is **unknown**: allocation failed during compilation,
before that assertion ran. Later ABI, exception/GC, worker and resume tests
also remain unverified on the phone.

## Root cause and its limits

The allocator rounds each reservation to 16 KiB and keeps it for the process
lifetime. Mono's ordinary code manager chooses a minimum of 16 pages per
chunk: **256 KiB on this phone**. Generated assemblies create additional code
managers. The captured sequence includes 29 successful 256 KiB reservations,
plus 36 small reservations rounded to pages. Their total reserved space is
8,192,000 bytes. Only 196,608 aggregate bytes remain, insufficient for the next
contiguous 262,144-byte request. This is exhaustion of our prepared code
budget, not evidence that the phone ran out of general RAM.

The captured native stack enters `mono_codegen`. The matching build 8 dSYM
maps its return address to `mini.c:2135`; the actual IPA disassembly places
that address immediately after thunk-area initialization and before the
code-pointer null check. Source confirms `cfg->thunks = code + offset` and
`memset` happen before `g_assert(code)`. The allocator had returned NULL, so
the thunk initialization used an invalid address and triggered SIGSEGV.

Symbolication uses the 16 KiB-aligned guest load address inferred from five
consistent named console frames and the exact delivered symbols. No new OS
crash report or debugger attach was required: the allocation failure is also
reproduced with the actual C allocator on the host. Preserve this distinction
from independently reading the OS image list or CPU fault registers.

Private raw evidence and analysis live under
`.build/ios-jit/device-evidence/2026-09-11/build-8-crash/`: the untouched export,
extracted events and console, validation, symbolication receipt and actual
binary disassembly. Build 8's original IPA, dSYM and 73-file source snapshot
are preserved. Do not publish the raw logs.

## Build 9 correction

- `CJHookMemory.h` defines two **16 MiB** arenas. The hook launcher uses this
  value for requests, reply bounds and logging. The Mach-O protocol descriptor
  and package checks verify actual compiled geometry. The G1 mailbox layout
  remains shared; its old 4 MiB capacity constant is not used by this launcher.
- `hook-canary/scripts/celeste-jit-probe.js` requires exactly that new geometry
  and checks **2,048 individual page-write acknowledgments**, mailbox identity,
  reply readback and detach. The app sends a fresh PID/nonce-bound script.
  The earlier managed-canary script stays unchanged.
- `CJHookCodeArena.c` compiles the accepted alias allocator with an event
  wrapper. An allocation failure records `code_allocation_failed`, then
  `jit_code_budget_exhausted`, and aborts before Mono can use NULL. This is a
  terminal diagnostic improvement, **not graceful in-process recovery**.
- Hook stage/patch logs now include reserved bytes, total budget and allocation
  count. The final physical export will show how much capacity the entire
  initial/resume fixture really uses.
- The builder refuses to overwrite a kit with a delivery receipt. Delivered
  symbols and files must remain reproducible; further corrections need a new
  build number and source snapshot.

The Mono 8.0.28 archives, seven-file runtime patch, 168 framework DLLs,
10 MonoMod/Cecil DLLs, native hook patch bridge, GC transition helpers and
external fixture bodies are unchanged. The freshly compiled external
`HookCanary-v0.3.0.dll` has the same SHA-256. AOT and interpreter remain
disabled in this JIT runtime. The accepted G1 source and independent AOT
checkout were not modified.

Increasing capacity is a bounded canary correction. Changing Mono's manager
sizes, pooling generated assemblies or reclaiming code needs separate lifetime,
branch reach, cache and concurrent-execution validation. A game host will
need an explicit capacity policy and measurements with real Everest/mod
profiles. This 32 MiB reservation does not establish that a full game fits.

## Local verification

| Check | Result and scope |
| --- | --- |
| Physical allocation replay | Actual C allocator with host read-only/RW aliases and explicit 16 KiB pages reproduces build 8's failure at request 66 |
| New capacity replay | Three complete 66-request traces fit: 198 allocations, 25,362,432 / 33,554,432 bytes; writes/readback verified under ASan/UBSan |
| Exhaustion guard | Child process emits the terminal budget event and SIGABRT before returning an unusable code pointer |
| Actual pinned host Mono | Eight G1 stages, 42 hook assertions plus two completion markers, 108 patches, two clean native-worker detachments |
| Host capacity observation | 99 code chunks, 4,078,956 cumulative bytes; fourfold scaling and 16 KiB rounding estimates 16,908,288 bytes; planning estimate only |
| Native request/script integration | Simulator runs the shared native builder/binder; exact IPA script completes all 2,048 page writes and detach in a fake debugserver |
| Protocol failures | Sixteen mock cases pass; integration also rejects old build 7/8 capacities, stale nonce and wrong PID |
| Simulator UI | Import, disabled execution without JIT, 800-event persistence/rendering burst, export and previous-session console recovery pass |
| Packaging | Unsigned ARM64 IPA; no embedded dSYM/profile/signature; exact 178 dependency DLLs; test DLL absent from IPA and compiled afterward |

The final host run logged 2,985 JIT events and 1,302,023 compiled bytes. These
counts can vary; the behavioral assertions and address/write validation are
the acceptance criteria. The unchanged alias patch regression was retained
after verifying all of its input hashes; it was not rerun. Host and simulator
checks do not prove physical ARM64 execution, background survival, or game
compatibility.

## Retest and artifact identity

Unsigned IPA:
`artifacts/ios-jit/hook-canary-20260911-09/CelesteJITHooks-unsigned.ipa`

- IPA SHA-256: `ac730cd2847dedce41b93a5de8f6f0a1369e8f53b7c7bb0499e250d9abb5b532`
- DLL SHA-256: `c4256d9f5f6400fe5b23a7b1590c4b343c280a90d882fbce3efb37999dc28157`
- Script SHA-256: `bfd36579c919cd060bb28fa201fa3056b4a7e19793d9d835539bb62abe24b413`
- Executable/dSYM UUID: `3CA3AD77-C8F4-3B16-8D6C-A3ABB1ACD9DF`
- All 80 source files are preserved in
  `.build/ios-jit/device-evidence/2026-09-11/build-9-ready/source-snapshot/`.

Install the versioned IPA from **iCloud Drive/Celeste JIT Tests/0.3.2-build-9**
into LC1 with its old process closed and data preserved. Keep Launch with JIT
OFF and launch script empty; StikDebug stays in LC2. Import the included DLL,
enable through LC2, return for native checks, then run hook tests. After initial
PASS, wait 10 seconds, go Home for 30 seconds, return to the same process and
run resume tests. After final PASS, wait 10 seconds and export into this
folder's **Results**. On a crash, reopen/export before enabling JIT again.

Next acceptance requires the full initial phase, clean detach and visible
liveness, an actual background interval of at least 20 seconds, retained and
fresh hooks plus new DynamicMethod after resume, clean second detach, final
PASS and liveness, and no allocation/patch/JIT errors. Review that evidence
before advancing to the JIT Celeste baseline. No commits, pushes or GitHub
writes were performed.
