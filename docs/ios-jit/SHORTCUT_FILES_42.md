# Explicit text comparisons — shortcut revision42

26 September2026. Revision42 replaces the signed shortcut only; app41 /0.22.2
stays installed. No42 IPA is produced. No GitHub write or public IPA is authorized.

## Physical failure and correction

App41 passes the real phone's `10.7.0.1:49152` Remote Pairing hello and creates its
fresh JIT request. The original39 shortcut then stops before StikDebug opens.
iOS records `ConditionalAction Code=1`, `WFActionIndex=4`; the editor displays
“Please choose a value for each parameter in this action.” Its generic dictionary
value does not expose the text comparison parameter.

`tools/build_shortcut_files42.py` explicitly coerces the six stage/radio-choice
comparison variables to `WFStringContentItem`. The home/has-value condition stays
the same. Action order, networking commands, fresh JIT URL, callback receipt and
name **Cabrillo** remain compatible with41 and protocol `cabrillo-39`.

## Validation and limits

-36 generated branch controls pass for both LC and standalone variants.
-36 isolated comparisons execute in Apple's macOS WorkflowKit conditional engine:
  matching/nonmatching inputs pass, and all12 original comparisons reproduce the
  same missing-parameter error as iOS. Each fixture substitutes text input for a
  dictionary-output reference and checks the engine's truth result. It permits
  only If/Comment actions, writes no shortcut library and changes no radios.
- The first host fixture tried counting comments as branch effects; Apple's
  controller reports both comments, so it is not a valid branch oracle. The final
  fixture checks the actual conditional truth value. No failed fixture is a pass.
- Loading the full ActionKit into a local test executable is platform-restricted;
  that approach was stopped. The final fixture uses WorkflowKit's conditional
  engine only. Actual iOS URL/radio/stage execution still requires physical tests.
- This closes a gap in39's Python-only shortcut validation, which interpreted the
  intended conditions but did not validate Apple's parameter typing.

Receipt: `.build/shortcut42-controls-b/receipt.json`. All six source/dependency
inputs are frozen in `artifacts/cabrillo-shortcut42-final`. No application source
or runtime payload changes. Further implementation uses identity43.

## Delivery and device gate

Apple-signed files are staged in `On My iPhone/LiveContainer/Cabrillo-shortcut42`.
The default file is25,304 bytes, SHA256
`900ff3b7872d891ad9978220088d863a86991d2ad3e06e5ab10ab9d4feb1ec35`;
full phone readback matches. The standalone variant is25,266 bytes, SHA256
`51b41f51a4dda77df78899fb75911ffe6bf528e48f7e02e9027ea49802086d3b`.
The five-file iCloud kit is at `Celeste JIT Tests/shortcut-42`; consult its upload
receipt. No old Results are removed.

The owner confirms replacement of the shortcut. After collecting41's failed,
untraced state with no game or StikDebug execution, its process was closed and a
fresh Automatic launch requested remotely. Inspect the latest physical ledger
before treating Automatic, Travel/recovery or game/Quit as passed. Preserve the
independent diagnostics export alongside direct collection.

```sh
python3 tools/check_shortcut_files42.py --work .build/new-shortcut-condition-checks
python3 tools/build_shortcut_files42.py --output .build/new-shortcut-files --sign
```

## Correctly named42 phone execution

The owner removed old Cabrillo and renamed42 to Cabrillo; scoped read-only synced
shortcut inspection confirms its contents. The next fresh41 session reaches the
correct JIT branch. iOS logs show the new comparisons pass, Open URL runs, the
two-second delay completes and Stop and Output starts. The screenshot shows
LiveContainer2's app list, not its StikDebug guest. No JIT or game gate passed.
The native loopback hello passes again in21ms; no radio settings were changed.

The generated `livecontainer2://open-url` only forwards to a running guest; the
explicit `livecontainer-launch` route is required to select a cold helper. The
shortcut also emits a bare variable attachment into Stop and Output's text field.
An actual Mac Shortcuts execution with a harmless editor URL completes with an
empty output. Isolated Apple engine checks distinguish that field from a proper
text token string, which returns the supplied receipt. The phone's background
output step had no callback; foregrounding Shortcuts later returns an error.
The precise contribution of output typing to that callback stall remains to be
verified on the phone. These findings allocate43;42 and app41 stay frozen.
