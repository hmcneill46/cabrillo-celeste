# Build 9: physical hooks and resume accepted

**Result: PASS for bounded G2 on the owner's iPhone 15 Pro Max, iOS 26.5.**
The exported session verifies actual MonoMod `Hook` and `ILHook` execution under
Mono ARM64 JIT, including fresh managed work after backgrounding. This permits
the next game-integration stage; it does not establish Celeste/Everest gameplay
or arbitrary mod compatibility.

The immutable build is `hook-canary-20260911-09`, version 0.3.2 (9). Its build
metadata, external HookCanary DLL, script template and 80-file source snapshot
match the delivered kit. The request targeted the actual LiveContainer process
through LiveContainer 2, with the debugger detached before execution.

| Captured check | Result |
| --- | --- |
| Native execution | 26 checks, all 2,048 prepared pages |
| Initial managed canary | All eight G1 stages |
| Hook/ILHook assertions | 42 passes plus two completion markers |
| Executable patches | 108 verified patches, no rejection |
| JIT completion | 2,989 events; 2,724 distinct entry addresses; every range owned |
| Worker cleanup | Two clean detachments, managed thread cleared |
| Background and resume | 65.299 seconds; same process, retained and fresh hooks |
| New work after resume | 16 new JIT events, 21 patches, new DynamicMethod |
| Final UI/liveness | PASS presented, alive in foreground 5.237 seconds later |
| Code reservation high water | 13,959,168 / 33,554,432 bytes, 87 allocations |
| Failures / storage errors | None |

Coverage includes original calls with altered arguments, explicit chain order,
undo/reapply/disposal, combined Hook and ILHook, instance receivers, large struct
returns, floating struct arguments/results, documented generic-hook rejection,
closed generic execution, exceptions, GC, and 64 calls from a managed worker.
Both retained hooks survived backgrounding; removal restored the original
methods, and new hooks and a new DynamicMethod executed after return.

The owner went Home 4.907 seconds after the initial PASS rather than waiting
the requested 10. The first five-second timer therefore ran in the background.
This is recorded as a timing deviation, not silently counted as foreground
liveness. The subsequent 65-second background, new managed resume invocation,
clean second detach and foreground liveness establish the bounded gate without
requiring another identical phone test.

The 13.3 MiB measurement is reserved executable-code space, not total resident
memory. It confirms that build 9 fixes this canary's capacity failure, but says
nothing about full-game or large-mod budgets. No code reclamation, arbitrary
unloading, concurrent hook mutation or long-session performance acceptance is
implied. LiveContainer 3.8.9 and StikDebug 3.1.9 remain carried-forward values;
this export does not independently remeasure their installed versions.

The untouched 9,933,410-byte export and a repeatable validator are preserved at
`.build/ios-jit/device-evidence/2026-09-11/build-9-pass/`. Export SHA-256:
`f1d44cdfae2f42c6b25872997cbe28813dc385e5ee5043efc3f1caeef30723f3`.
The shareable [evidence ledger](HOOK_EXECUTION_PASS_2026-09-11_EVIDENCE.json)
contains derived results; raw sessions/console remain private. iCloud delivery
initially lagged, then the results appeared in the correct build 9 folder.
No device debugger attachment or phone mutation was needed for this review.

The next integration uses a native launcher with one UIKit lifecycle and one
embedded Mono runtime, plus JIT-compiled FNA against the pinned static Metal
libraries. A small graphics/input/resume test can exercise that boundary within
the authorized iCloud handoff size before importing over 1 GB of Celeste content.
All five native libraries have rebuilt in the isolated JIT directory and match
the accepted native output lock. The working AOT checkout and delivered probe
source, IPAs, symbols and results remain separate.
