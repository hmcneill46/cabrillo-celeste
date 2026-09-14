# Celeste JIT Probe — first physical test

Build: `native-probe-20260911-03` · app version `0.1.2 (3)` · mailbox protocol `M1`.

**Packaging correction:** build 3 removes the accidental debug-symbol bundle
from inside the IPA. Build 2 passed three native-memory runs on the target
phone, including two after approximately 30 seconds in the background. The
native source and StikDebug script are unchanged in this build. Your existing
build 2 results already establish that success; a full repeated native test is
not required just for this packaging correction.

For a brief installation check, import build 3 while preserving the existing
data container and confirm that the dSYM signing error is gone. If it still
appears, send the exact path; do not delete the data container. The full JIT
procedure below remains available if you want to run this fresh installation.

This small handoff uses **Files → iCloud Drive → Celeste JIT Tests →
0.1.2-build-3**. Download files using their cloud icons if needed. The handoff
message states whether cloud upload was confirmed; placing files in the Mac's
iCloud folder alone does not establish a phone download. Import the versioned
IPA from that folder into LiveContainer 1 and replace the earlier probe while
preserving its data container. Start a fresh probe process and check that it
displays `native-probe-20260911-03`.

This is a small **native executable-memory probe**, with no game content, .NET,
Everest or mods. It answers whether the memory arrangement needed by a future
JIT runtime works on your **iPhone 15 Pro Max / iOS 26.5**, inside **LiveContainer
1**, with **StikDebug running inside LiveContainer 2**.

The IPA was built with Xcode 26.6 / iPhoneOS SDK 26.5. Its ARM64 executable has
no code signature or provisioning profile. LiveContainer performs the guest
installation/signing; debug access depends on the actual LiveContainer 1 host.
The simulator checks the interface and diagnostics only. Build 2 has a physical
native-memory PASS; build 3's installation check is pending.

## Files

The phone folder contains `CelesteJITProbe-0.1.2-build-3-unsigned.ipa`,
`README-FIRST.txt`, this guide and `SHA256SUMS.txt`. The IPA contains the matching
script and everything needed for this test. The full local artifact folder on
the Mac calls the same IPA `CelesteJITProbe-unsigned.ipa` and also retains its
build receipt, notices, dSYM for crash investigation and script template.

**You normally do not import a script.** The app contains the matching script
and fills in the current PID, mailbox address and a random launch token. Its
button sends that complete script to StikDebug in LiveContainer 2.

The supplied `TEMPLATE.js` deliberately refuses to attach if run by itself. A
script exported by the running app is complete but is valid only for that app
process. Do not substitute `universal.js`, a MeloNX script or a previous
launch's script. Do not install the template as LiveContainer's JIT launch
script.

## Preparation

1. Keep your working StikDebug setup in **LiveContainer 2**. Enable LocalDevVPN,
   connect as you normally do, and let StikDebug finish pairing/DDI preparation.
   Use your existing pairing record; nothing in this test needs you to send it
   to anyone.
2. Leave StikDebug **running in slot 2**, then switch to **LiveContainer 1** and
   import `CelesteJITProbe-0.1.2-build-3-unsigned.ipa` using its normal IPA import
   button (or `CelesteJITProbe-unsigned.ipa` from the full local kit).
3. For **Celeste JIT Probe only**, leave **Launch with JIT OFF** and leave its
   **JIT Launch Script empty**. Keep LiveContainer's normal signing and tweak
   loader enabled. This probe starts natively, creates its request, and then
   asks the second container to prepare memory. It intentionally uses a
   different order from a normal app that needs JIT before it can start.
4. Launch the probe in the ordinary first container, without multitasking or a
   LiveProcess extension for this first test. Do not open a second copy. The
   screen should say **READY FOR BASELINE**, with a PID and build ID.
5. Scroll to **Record LiveContainer / StikDebug versions** and enter the version
   and build of each if known. Enter `LiveContainer 2` for the debugger's
   installation. These details will be included in the exported report.

The primary button uses `livecontainer2://open-url` to forward a
`stikdebug://enable-jit` request. That route is present in the inspected
LiveContainer source. It requires the ordinary `livecontainer2` URL scheme and
StikDebug already running there. If your installed version handles it
differently, the failure and fallback below will help us identify that.

## Test A: baseline, then JIT

1. Before enabling JIT, tap **Export diagnostics** and save the JSON to Files.
   Rename this copy `baseline.json` if useful. It should open the share sheet;
   this establishes that recovery/export works without generated code.
2. Return to the probe and tap **Enable via LiveContainer 2**. It should switch
   to the already-running StikDebug in slot 2. Accept StikDebug's own request
   confirmation if it displays one.
3. Wait for the script log. A successful preparation ends with:

   ```text
   [CJIT-M1] PREPARED + DETACHED. Switch back to the existing probe. Only its execution tests can report PASS.
   ```

   This message means memory preparation finished; it is not an execution PASS.
   StikDebug may also print its own completion or connection-cleanup messages.
4. Use the app switcher to return to the **existing probe in LiveContainer 1**.
   Do not terminate/relaunch it or press a launcher action that replaces its
   running process. The PID must still match the request. Its native checks
   start automatically once the reply is valid and the debugger has detached.
5. The desired result is **PASS · NATIVE MEMORY**. Tap **Export diagnostics**
   again and save/send that JSON. Also copy or capture StikDebug's script log,
   including the `[CJIT-M1]` lines and any errors.

The checks cover two separate 64 KiB regions, RX/RW mapping protections, writes
visible through both aliases, random generated return values, changed machine
instructions and cache invalidation, every prepared page and each region's
last instructions, integer arguments, a generated branch between regions,
another worker thread, and 16,384 calls across 128 sequential code rewrites.
All generated-code execution is **after debugger detach**.

## Test B: keep the same process, background and return

If Test A passes:

1. Switch away from the probe for approximately 15 seconds, then return to the
   same running instance.
2. Tap **Run memory checks again**. It should pass using the existing memory
   regions, without another StikDebug request.
3. Export diagnostics again. Both runs and the background/foreground events
   are included in this session's JSON.

A fresh process requires a fresh JIT request. The app makes no promise that JIT
survives termination. A device reboot also requires the usual StikDebug/DDI
setup again. A reboot test can wait until we inspect A and B.

## Fallback: import the launch-specific script

Use this if switching to StikDebug works but the inline script does not arrive,
or StikDebug reports it cannot decode the script. The fallback sends a much
shorter URL while preserving the exact target PID.

1. In the still-running probe, tap **Export session script (manual setup)** and
   save the resulting `celeste-probe-PID…-….js` to Files. Keep its exact name.
2. Switch to StikDebug in LiveContainer 2. In **Scripts**, choose **Import** and
   select that `.js`. It does not need to become the global default script.
3. Return to the same probe in slot 1. Tap **Use imported script in LiveContainer
   2**. This sends the current PID and exact imported filename to StikDebug.
4. Follow Test A from the script-log step. If StikDebug says the script was not
   found, check the filename/import and return its log. Its generic green JIT
   message alone is not a PASS for this test.

If the slot-2 URL itself does not open, first launch StikDebug there manually,
return to the same probe and try the button once more. If it still fails, stop
there and send the diagnostics plus exact container/debugger versions. Do not
attach to slot 2's own PID or guess a guest bundle identifier.

If either app process was restarted during these steps, regenerate and import
the new script. An old request should refuse the wrong PID/launch token. After
a reported script preparation failure, export the logs and use a fresh probe
process for another attempt.

## Failure and log recovery

| Visible result | What to return |
| --- | --- |
| READY FOR BASELINE, before JIT | Baseline JSON; native startup succeeded only |
| NO PREPARATION REPLY YET | JSON and StikDebug log; no generated code ran |
| WAITING FOR DEBUGGER DETACH | Stop the StikDebug session if stuck; export both logs |
| COULD NOT VERIFY DETACH | JSON; the app refuses to execute if it cannot establish trace state |
| SCRIPT PREPARATION FAILED | JSON plus the numbered script phase and complete script log |
| FAIL · CHECK THE LOG | JSON; the first `check_fail` identifies the failing native condition |
| PASS · NATIVE MEMORY | JSON and script log, then perform Test B |
| App closes during checks | Reopen **without JIT**, export immediately, and include the host crash log if available |

The app syncs its JSON-lines log to disk before each dangerous execution stage.
On reopening, **Export diagnostics** includes the current session and up to
five previous sessions. A last `about_to_execute_…` event with no matching
result helps locate a fault. An interrupted session is not automatically a
confirmed crash.

Raw logs are also in the probe's **Documents/Diagnostics** folder. If the share
sheet fails, browse that guest data container through LiveContainer/Files and
copy its `session-….jsonl` and any `.diagnostics.json` exports. Do not delete or
reimport the app's data container before recovering logs. LiveContainer's file
picker compatibility option is only worth changing if a picker actually fails.

For a native crash, iOS Settings → Privacy & Security → Analytics & Improvements
→ Analytics Data may contain a matching **LiveContainer 1 host** `.ips` report;
match the timestamp/PID. If it is available, include it. A report may be named
for the container instead of CelesteJITProbe. The dSYM in the delivery folder
is retained for investigation.

Optional Mac capture: open Console, select the connected/unlocked phone and
start streaming. Filter for `CelesteJITProbe` or the PID shown in the probe.
Its `NSLog` messages have a `[CelesteJITProbe]` prefix. Use a non-attaching
console; do not attach Xcode/LLDB to the same process while StikDebug is in use.
If log streaming is unavailable, the in-app export is the primary method.

Please return:

- The final diagnostic JSON; the baseline copy is useful too.
- StikDebug's script log, including failures.
- Whether the first run and the background/return rerun passed; mention any
  process restart or fallback used.
- Exact LiveContainer 1/2 and StikDebug versions/builds if not entered in-app.

Diagnostics omit pairing records, tokens, device UDIDs and arbitrary system
paths. They do include this app's PID, transient memory addresses, hardware/OS,
build hashes, entered version text, and test results. If attaching a separate
system crash/console report, sharing just the relevant report is sufficient.

## What happens after this test

A native PASS permits work on the next probe: an embedded managed runtime
actually JIT-compiling an imported DLL, followed by real MonoMod hooks. It does
not establish C# execution, unwinding/GC/generic ABI support, Celeste startup,
mod loading, Strawberry Jam compatibility or game performance. The original
breakpoint-based JIT26 ABI is also not exercised by this mailbox probe.

Source behavior checked against [StikDebug's PID/script URL handler](https://github.com/StikDebug/StikDebug/blob/94bc9e8cf3b41f32f125f046abf33d913f4e1b2d/StikDebug/Views/HomeView.swift),
[LiveContainer's URL forwarding](https://github.com/LiveContainer/LiveContainer/blob/3afa9eb9a53625e9b8bd8b932e5785fd716ad5ae/TweakLoader/UIKit%2BGuestHooks.m),
and the [StikJIT integration protocol](https://github.com/stikdebug/StikJIT/blob/3623e725876f76aecb0520582ad6194bacb15d39/INTEGRATION.md).
The installed-version/device behavior is what this handoff asks you to test.
