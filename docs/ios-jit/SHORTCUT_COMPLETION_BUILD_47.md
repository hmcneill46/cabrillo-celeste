# Finish Home Screen launch after native JIT — build47

26 September2026. Cabrillo0.22.4 in `launcher-shortcut-completion`, paired with the
unchanged, signed shortcut46. Private owner testing only; no GitHub write or
public IPA distribution is authorized. FMOD remains the distribution gate.

## 28 September: USB evidence and five fresh phone launches

Direct collection verifies installed build47 and recovers the previously missing
phone journals. The owner authorized as much remote shortcut testing as possible.
Five fresh launches pass on the iPhone15ProMax/iOS26.5 with app47 and shortcut46:

| Test | Starting state | Result | Launch to ready |
| --- | --- | --- | --- |
| Automatic, owner starts | Wi-Fi and VPN connected | Native JIT ready, radio switches untouched | 25.9s |
| Travel, owner starts | Wi-Fi and VPN connected | JIT and restoration pass | 27.7s |
| Travel, remotely started | Wi-Fi and VPN connected; both LC processes closed | JIT and restoration pass | 28.3s |
| Travel, remotely started | Wi-Fi off, cellular on, VPN disconnected | VPN setup, offline tunnel, JIT and restoration pass | 53.2s |
| Automatic, remotely started | Wi-Fi off, cellular on, VPN disconnected | Selects Travel; VPN setup, offline tunnel, JIT and restoration pass | 31.8s |

Every run records26 native checks, a known detached debugger and foreground return.
All four Travel runs receive the correct prepare/isolate/restore receipts, clear
the durable recovery record and show “JIT is ready. Your networking preset is
restored.” The extra JIT-stage Shortcuts callback is absent in every run, directly
exercising47's completion correction. A repeated Home launch after readiness keeps
the same process and does not issue a second JIT request or radio transaction.

The two cellular-start tests use LocalDevVPN's supported disable URL and the
unchanged shortcut's network actions to establish the starting state. Screenshots
verify VPN Disconnected and cellular4G before launch; native journals verify no
Wi-Fi address at selection. Preparation enables Wi-Fi and may rejoin the nearby
network. These passes do **not** establish operation entirely outside Wi-Fi range.
The restore preset is Wi-Fi on/cellular on; other presets remain untested physically.

### Earlier failure and recovery

The recovered27 September Automatic/cellular-start journal successfully prepares
the VPN, verifies its tunnel in Airplane Mode and passes native JIT. It then opens
Shortcuts for restoration, backgrounds, and receives no restore receipt. This
locates the reported failure **after JIT**, during restoration. A subsequent fresh
process reads the retained recovery record, receives its restore receipt and
clears it without granting JIT to that new process. A separate late JIT callback
is rejected in an idle process. Those are real device recovery/stale-callback
observations, separate from the five new launches above.

The original missing restore receipt has not been reproduced or explained. Both
successful and failed Travel runs lack the JIT callback, so its absence alone is
not a demonstrated cause. No speculative fix or48 package was made. Keep the
failed journal alongside the passes; do not describe this as a repaired defect.
Recovered47 game runs establish startup/gameplay observations but no normal
Quit/native-return acceptance. The older acceptance gates remain distinct.

### Remote control and retained state

USB log/file access, native screenshots and ordinary process control work.
CoreDevice URL launches initially time out, then work after the completed Travel
run; this does not establish why connectivity changed. Three fresh launches and
the repeated-ready check are subsequently driven remotely. No second debugger is
attached. Idle launchers/helpers are closed only after the native detach result;
no active game is terminated.

Remote touchscreen control reports that it needs iOS27. Accessibility activation
has no observed effect. A locally built UI-test runner cannot install because
the free development profile already has three apps. No existing app is removed.
Changing Travel/Automatic therefore needs the owner's Settings taps. The first
USB preference-file edit reads back as Travel but the running app retains cached
Automatic; it is not counted as a Travel test. The owner subsequently changes the
setting through the UI and restores Automatic before the final run.

All125 saved files (683,136 bytes) have exact before/after hashes; launcher
preferences return to their original values. Private evidence and screenshots
are under `.private/device-evidence/2026-09-28/phone47-*`, referenced by the ledger.
Independent46/47 Results folders are still empty; preserve the independent export
gate without requesting another passed run merely for an export. A fresh host
review passes132 native controls,36 shortcut branches,12 rejected broken URL
connections and the original43 failure control. All221 frozen47 inputs match.

Launching plain LiveContainer reopened YouTube, as the owner explained. That is
not a reproduced Cabrillo-shortcut failure. Source review also notes that46's Home
URL uses generic `open-url`, which forwards to the current guest; selection from
another LC guest remains an untested scenario for the next implementation review.

## Historical27 September: owner confirms the Wi-Fi completion check

The owner reports that47 with shortcut46 works with Wi-Fi and LocalDevVPN already
connected. Home Screen launch finishes with “JIT is ready for this running app.
Wi-Fi and cellular settings were left unchanged.” This closes the owner-visible
spinner/false-timeout check for that path. Installation and execution are
owner-reported; fresh47 device metadata/journals have not yet been collected.
Both46 and47 Results folders were empty at this review.

The next owner-planned check starts a fresh Automatic process with Wi-Fi off,
cellular on and LocalDevVPN disconnected. Automatic should choose Travel, perform
VPN setup, use Airplane Mode for JIT and restore the chosen radio preset. The
prepare stage briefly enables Wi-Fi as well as cellular; a nearby known network
may reconnect during preparation. Keep that start-state test separate from a
run entirely outside Wi-Fi coverage. Travel/recovery and47 game/normal Quit
remain pending. No new implementation or package is needed for these checks.

## Problem and resulting behavior

The exact imported46 shortcut opens Cabrillo and StikDebug, returns automatically
and shows green native JIT readiness. The owner also starts Celeste successfully.
However, app43's Home Screen indicator keeps spinning and eventually says JIT was
not confirmed. A Wi-Fi screenshot records both conflicting statuses. Fresh journal
collection timed out; the owner result and screenshot are scoped evidence.

The launch reducer also requires the JIT stage's Shortcuts callback before accepting
the native result. A missing callback reproduces the observed spinner and false
timeout in the actual43 reducer. Build47 completes that stage after current-process
native execution checks pass and the debugger is known to be detached. The caller
still advances only while Cabrillo is foreground. A callback or foreground return
alone cannot grant JIT.

The JIT stage in shortcut46 opens the helper, waits briefly and finishes; it changes
no radio settings. Therefore, waiting for that extra receipt does not protect a
pending network write. Travel still starts its restoration stage, keeps durable
recovery information and requires the correct restoration receipt before clearing
it. Missing or incorrect radio-stage callbacks continue to fail closed. Late JIT
callbacks cannot change a completed launch or a newer restoration stage.

Diagnostics now record whether the JIT callback arrived separately from native
verification. All other native implementation, SwiftUI, managed payload and native
dependency archives remain43-identical. New metadata and UUID identify47 honestly.

## Validation

`tools/check_shortcut_completion.py` passes132 native launch controls,36 generated
shortcut branches and12 rejected broken URL connections. It also compiles the
same focused tests against the original43 reducer and requires the missing-callback
case to fail, confirming the control exercises the reported defect.

The new cases cover Wi-Fi and Travel without a JIT callback, absent native results,
an attached debugger, late success/cancel/error callbacks, exactly-once restoration,
retained recovery until its receipt and no later120-second false timeout. Existing
tunnel, cancellation, recovery, process/token and helper-discovery controls pass.
The exact46 Apple condition/completion/content receipts remain separately retained;
they are not rerun as a claim of47 device acceptance. SwiftUI sources are unchanged.

```sh
python3 tools/check_shortcut_completion.py --work .build/shortcut47-controls-new
python3 tools/build_shortcut_completion.py \
  --managed .build/owned-public-managed38-e/receipt.json \
  --native .build/owned-public-native38-e/receipt.json \
  --fmod .build/owned-fmod38-c/receipt.json \
  --work .build/shortcut47-new --output artifacts/cabrillo-build47-new
```

Package identity, frozen-input/runtime comparisons and delivery status are recorded
in [the47 ledger](SHORTCUT_COMPLETION_BUILD_47_EVIDENCE.json). Retain all historical
artifacts and Results. No47 phone installation or physical pass is implied by
compilation. Further implementation after packaging requires48.

## Remaining owner checks

Keep installed47 and shortcut46 named exactly Cabrillo. No new import or repeat of
the passed Wi-Fi/cellular-start runs is needed solely for an export. Remaining
physical scenarios are listed above. When playing next, use normal main-menu Quit
and keep independent diagnostics in47's Results. Older native save-manager,
iPad38 and sustained120Hz gates remain separate. If restoration stalls again,
preserve its visible screen and journal before retrying.
