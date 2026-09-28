# Home Screen launch — build39 /0.22.0

26 September2026. Local implementation and private delivery requested by the
owner. No GitHub write or public IPA publication is authorized. Read the
[phone setup and test guide](../HOME_SCREEN_SHORTCUT.md).

## Delivered implementation

**26 September phone review:** build39 and the shortcut are installed. Direct
Wi-Fi collection and a remote Shortcuts launch confirm the guest receives
`cabrillo://launch`, but its setup preflight rejects LocalDevVPN before any
VPN/JIT handoff. The native console reports that the app is not allowed to query
`localdevvpn`. The guest's Info.plist declares it; LiveContainer's installed host
controls that query permission. This is a build39 integration defect, not missing
LocalDevVPN. A separate build40 fixes the preflight; all39 inputs stay frozen.
The dated delivery and host validation below remain historical, not phone passes.

`launcher-shortcuts-20260926-39` adds a native launch coordinator and an importable,
Apple-signed **Cabrillo.shortcut**. The default variant opens Cabrillo through
LiveContainer1; a separately signed variant supports a directly installed app.
Both use the same shortcut name; import only the applicable variant.

- Cold/warm `cabrillo://launch` and recovery URLs work through app and scene
  delegates, including LiveContainer's retained cold-launch URL. Duplicate launch
  requests coalesce. A used game process requires restart; a process with verified
  JIT skips the handoff. This does not automatically start Celeste.
- The host bundle identifier comes from LiveContainer's retained **real host
  bundle**, while the target remains Cabrillo's current PID. StikDebug's reviewed
  source uses that bundle only to foreground the existing process with
  `kill_existing=false`. Guest bundle/data identity is unchanged. If the real host
  context cannot be resolved, automatic launch stops at setup.
- LocalDevVPN is started only if its local device endpoint does not answer.
  The bounded, off-main-thread probe sends an unauthenticated lockdown `QueryType`
  to10.7.0.1:62078 and requires `com.apple.mobile.lockdown`. This verifies a usable
  local service, not the other app's private NEVPNManager status, DDI or pairing.
- Automatic mode keeps radio switches when en0 has a usable address, otherwise
  uses Travel. Travel records recovery before requesting radio changes, verifies
  the endpoint before Airplane Mode and again after Wi-Fi is switched off, then
  sends the fresh PID/mailbox-bound inline JIT script.
- The same shortcut has four native-requested stages: prepare, isolate, JIT
  handoff and restore. Success, cancellation and error callbacks route back to the
  correct host. Each stage has a fresh random token and a matching receipt. Because
  LiveContainer unwraps only its `url` parameter, the receipt is inside that guest
  URL rather than relying on Shortcuts' appended outer `result` parameter.
- The JIT stage's two-second foreground-return fallback does not grant readiness.
  Completion requires both return of that Shortcuts invocation and the existing
  native memory checks after verified debugger detach. This avoids starting a
  restore shortcut concurrently with the preceding handoff shortcut.
- Travel restores a configurable Wi-Fi/cellular preset with Airplane Mode off.
  Exact prior radio switches cannot be read using the available Shortcuts actions.
  The record survives process death; a new process restores it before a new launch.
  A radio-stage timeout retains recovery without starting concurrent radio writes.
  Cancellation keeps the tunnel while a delayed helper attach may still occur.
  Failed restoration retains the record and a recovery button.
- The native UI exposes status, cancel/recovery and networking preferences.
  Profile changes and game launch are blocked during automation/recovery. Existing
  manual JIT controls remain available outside that transaction. No debugger,
  networking action or game execution is placed in the simulator preview.

The signed shortcut generator uses standard Shortcuts actions, not the StikDebug
Enable JIT AppIntent: that intent cannot accept Cabrillo's fresh PID and inline
script. LocalDevVPN's delayed URL return is never treated as tunnel readiness.
The workflow cannot dismiss first-use iOS prompts or StikDebug's external-request
confirmation, restore a killed process in the background, or initialize offline
DDI/pairing assets that have not been prepared. These are explicit setup/recovery
boundaries, not claimed passes.

## Exact runtime and packaging

- The199 managed assemblies, all16 native dependency archives, preparation recipe,
  content manifest and JIT script template are exact38. No original/prepared
  Celeste code or original assets are bundled. Frozen38 inputs remain untouched.
- Reuse the exact managed `.build/owned-public-managed38-e/receipt.json`, native
  `.build/owned-public-native38-e/receipt.json`, and FMOD
  `.build/owned-fmod38-c/receipt.json`. Their hashes are locked in the39 lane's
  `Dependencies.json`; the builder rejects substitutions.
- `tools/build_shortcuts.py` compiles a fresh iOS15+ native launcher with Xcode26.6.
  It validates those receipts, audits the game-free payload, and produces a new
  executable/dSYM UUID. It does not restore a historical UUID or copy an executable.
- Final artifact: `artifacts/cabrillo-build39-final/`.
  IPA18,692,002 bytes; SHA256
  `dcf55b9d891f1c98a0885e798e638a49bf54700032f67a83cbdabdfd19a7a2a0`.
  UUID `750fa3a8d4143f3fb813053143dca898`.
  The210 recorded input files and source archive are frozen there. New
  implementation changes require **build40**.
- Eleven kit files are confirmed uploaded to
  `iCloud Drive/Celeste JIT Tests/0.22.0-build-39`. A second copy was staged over
  Wi-Fi at `On My iPhone/LiveContainer/Cabrillo-build39`; staging is not installation
  or execution. The existing Cabrillo guest/data container is retained for update.
- FMOD redistribution and authorized release CI SDK access remain unresolved.
  `release/current.json` and the published workflow remain on the frozen38
  development configuration. No GitHub run has tested39 and no public IPA was made.

## Validation and remaining phone gates

-54 native host controls pass: ordering, current-process tokens, replay/reordering,
  tunnel-before-JIT, post-Airplane recheck, actual JIT/detach gating, early helper
  returns, delayed attachment/cancellation, storage failure, timeout and restart
  recovery, failed cleanup and URL wrapping. Receipt:
  `.build/shortcut39-controls-b/receipt.json`.
-36 generated shortcut branches pass a strict host interpreter, including both
  launch variants, each stage and all restore presets. This validates emitted
  control flow; it is not execution by iOS Shortcuts.
-Four XCUITests pass using production shortcut views, including active/cancel,
  restore toggles, waiting-detach controls and recovery in portrait/landscape with
  larger text. Receipt/screenshots: `.build/shortcut39-ui-b/`. Initial fixture
  checks exposed the spinner's accessibility grouping and imprecise switch taps;
  the spinner now has an explicit accessible identity, and tests tap the switch.
-Fresh iOS compilation, payload/archive audits, matching dSYM, exact38 runtime
  comparison and frozen34–39 source checks pass. The public3407-file inventory,
 20 Python build/release controls and actionlint1.7.12 pass. A local CI step now
  runs the shortcut host controls; no GitHub execution is claimed. Signed shortcut files are actual
  `shortcuts sign --mode anyone` outputs, with readable action JSON alongside.
-Phone Wi-Fi discovery and Cabrillo file access pass. The owner is asked to update
  the existing guest and test Automatic on Wi-Fi first, then Travel in a fresh
  process. Helper return, actual Shortcuts action execution, offline tunnel
  survival, final radio states and39 gameplay/Quit are **pending**. The independent
  diagnostic export remains required alongside direct collection.

While preparing39, the collected38 journal verifies real cold owned-game
preparation15.368s, direct adapter binding, first-frame/readback and Strawberry Jam
Grandmaster lobby `GM-main`. This is a scoped38 phone runtime observation. The
journal ends backgrounded; it does not close cached preparation, normal Quit,
native-return, visual review, full native saves or sustained120Hz gates. Journal
SHA256 `d2a376677a13b2257fc2a3175b3d5629610091aacd86272a594bdb4a570c77c3`;
raw evidence stays private under `.private/device-evidence/2026-09-26/phone39`.

The broader32 fallback and each earlier lane's distinct acceptance remain intact.
The iPad's38 first/cached run is still separate from this phone observation.

## Reproduction

```sh
python3 tools/check_shortcut_launch.py --work .build/shortcut-controls-new
python3 tools/check_shortcut_ui.py --work .build/shortcut-ui-new --device SIMULATOR_UDID
python3 tools/build_shortcut_files.py --output .build/shortcut-files-new --sign
python3 tools/build_shortcuts.py \
  --managed .build/owned-public-managed38-e/receipt.json \
  --native .build/owned-public-native38-e/receipt.json \
  --fmod .build/owned-fmod38-c/receipt.json \
  --work .build/shortcut-native-new --output artifacts/shortcut-package-new
```

Source research pins: StikDebug `5e3e1bc91efb0dbec784be5a81e377d3ed355a40`;
StikJIT `5d732f94b871031704ef6f580a313e8d99d80ec1`; LiveContainer
`4dbe0f9a626de801184a42c0be8d2cb105058e3d`; LocalDevVPN
`af3fd697803ada4ac2b8d518358f5ab0a534844c`; Cherri
`d96eee9c7768649d441df0166b68a7e3c742690c`. Primary links are in the setup guide.
These current-source observations are not proof of the installed helpers' versions.
