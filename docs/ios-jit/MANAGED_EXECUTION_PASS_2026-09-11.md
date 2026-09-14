# Build 6 managed JIT pass and direct USB diagnostics — 11 September 2026

**The physical G1 canary passes on the owner's iPhone 15 Pro Max, iOS 26.5,
inside LiveContainer 1 with StikDebug in LiveContainer 2.** Build 6 executes all
eight managed stages, detaches its Mono worker cleanly, presents PASS, remains
alive and returns in the same process after backgrounding. The build 5 cleanup
abort is corrected on the actual device.

**Direct USB log collection also works without an Export action.** The canary
already persists its event stream and native console in its guest Documents
folder. Export remains available for iCloud/share and disconnected testing;
the owner explicitly asked to preserve that fallback.

## Verified physical result

The owner's export was retrieved from LocalSend's
`Celeste JIT Tests/0.2.2-build-6/Results` over USB. The raw logs were independently
retrieved from LiveContainer and compared with it. Evidence confirms the exact
delivered build metadata and source hashes, **Canary-v0.2.2.dll** identity, fresh
host process, correct inline LC2 request, successful preparation and verified
debugger detach before generated code runs.

| Observation | Result |
| --- | --- |
| Build | `managed-canary-20260911-06`, version 0.2.2 (6) |
| Device | iPhone16,2 / iPhone 15 Pro Max, iOS 26.5 / 23F77 |
| LiveContainer 1 and 2 | Installed metadata independently confirms version 3.8.9 |
| StikDebug | 3.1.9 remains the previous reported value; not independently remeasured |
| Native preparation/execution | 26 checks pass; all 512 prepared pages execute |
| Managed stages | All eight pass with the actual values below |
| JIT completion events | 628, representing 570 distinct method-name strings and 518 entry addresses |
| Code allocation | All observed JIT ranges fit recorded allocations; zero compiler/out-of-arena failures |
| Native imports | All 21 resolution events succeed |
| Mono cleanup | `managed_worker_detached`, `managed_thread_cleared=true` |
| Launcher completion | `g1_managed_pass`, `managed_result_presented`, foreground `managed_post_run_alive` |
| Foreground after PASS | 20.15 seconds before backgrounding |
| Background/return | 21.73 seconds, same process, CS_DEBUGGED retained, debugger detached |
| Persistence | No storage error; raw events agree with the exported event sequence |

| Managed stage | Actual = expected |
| --- | ---: |
| NativeImports | 353 |
| Arithmetic | 324514299 |
| SwitchTable | 1109 |
| Dynamic | 1081 |
| DynamicSwitch | 516 |
| GenericAbi | 4885 |
| ExceptionsAndGC | 367 |
| ThreadAndCallback | 372 |

The end-of-stage profiler record has 612 JIT completion events, with positive
evidence for imported arithmetic and both emitted dynamic methods. The final
total includes subsequent managed thread-exit work. Counts are events, not
unique compiled methods. All eight fixture entries have verified Mono JIT-info
records in prepared executable memory.

This accepts the **bounded G1 managed-runtime canary** and its clean return/resume
on this device and configuration. The app did not invoke another managed test
after resuming; that scenario, longer stress/reboot/failure cases, MonoMod hooks
and gameplay remain separate validation work. No performance claim is made.

## Direct collection from LiveContainer

The actual file-sharing path is:

```text
Files / On My iPhone / LiveContainer / Data / Application /
3C268B63-02B6-… / Documents / Diagnostics /
    session-<launch-uuid>.jsonl
    console-<launch-uuid>.txt
```

The verified UUID and signed host bundle identifier are stored in the private
retrieval receipt. Do not assume that a guest data UUID survives reinstalling
or switching containers. Collection uses the installed **LiveContainer host**
identifier through House Arrest `VendDocuments` / AFC, then reads the known
guest directory. It does not request an independently installed canary app
container, which does not exist in this arrangement.

The raw session contains **1,274 events / 734,119 bytes**; the full console is
**1,103,693 bytes**. The export contains 1,273 current-session events. Every
exported event matches the raw prefix exactly; the extra raw event is a later
background transition. The raw console is more complete than the export's
128 KiB console tail. Both raw files were read twice and hashes verified while
stable. No phone file was changed, app launched or debugger attached.

The persisted events were created throughout the run before the later export
event. Inspection of `CJLog` confirms the files open at launch and each event
is appended and synced independently of Export. A second collection using the
new reusable tool obtained the same raw files without opening or depending on
the exported bundle. This establishes the future no-export workflow; the
owner's export remains useful as the independent comparison in this test.

The [USB collector and usage guide](../../experiments/ios-jit/device-tools/README.md)
select the verified phone, validate guest/session identity, preserve previous
local snapshots and store checksums. It reads only one session and its console
from the specified canary Diagnostics folder. An incomplete final record after
a crash is retained and reported separately. The session and console are
separate stable reads, not an atomic cross-file snapshot. User-entered version
preferences remain in the optional export and are not read by this tool.

For future tests, the owner can leave the phone connected and accessible to
the paired Mac and report that the run is finished. Fetch the raw logs before
requesting another launch or JIT attempt. If USB is unavailable, use **Export
diagnostics** and save/share to LocalSend or iCloud. Keep that button and flow.

## Evidence and next implementation gate

Raw evidence, original source snapshot, reproducible validator, transfer
receipts and the independently verified collector output are private under:

`.build/ios-jit/device-evidence/2026-09-11/build-6-pass/`

Input identities, acceptance details and retrieval hashes are recorded in
[the evidence ledger](MANAGED_EXECUTION_PASS_2026-09-11_EVIDENCE.json). The
[preceding report](BUILD_5_EXECUTION_AND_BUILD_6.md) explains the cleanup fix.
The delivered IPA/DLL and existing phone kits are unchanged by this follow-up.

The next implementation gate is **real MonoMod Hook/ILHook** against the pinned
Mono runtime: original-call chains, hook ordering, removal/re-addition, emitted
replacement code, writable-alias patching, instruction-cache synchronization
and execution after background/return. Successful dynamic methods alone do not
demonstrate detour compatibility. Celeste/Everest integration follows those
checks; the current IPA remains a runtime canary.

The AOT checkout and user game inputs were not modified. No commit, push or
GitHub write was made. Export functionality was preserved without app changes.
