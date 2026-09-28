# Cold helper launch and typed shortcut output — build43

26 September2026. Cabrillo0.22.3 / build43, lane `launcher-shortcut-guests`,
with shortcut revision43. This is private owner testing; no GitHub write or public
IPA publication is authorized. FMOD remains the public distribution gate.

## Observed failure

The correctly named42 shortcut passes its comparisons on the real phone and runs
its JIT branch. App41's local Remote Pairing hello passes in21ms. The helper URL
opens LiveContainer2's My Apps screen without selecting StikDebug; no JIT script
or native checks execute. Stop and Output then has no background completion
callback. Foregrounding Shortcuts later returns an error to Cabrillo, which fails
safely without radio changes. See [the42 review](SHORTCUT_FILES_42.md).

An actual Mac Shortcuts run with a harmless editor URL also produces empty output.
The output action expects a text token string; the raw attachment is ignored or
becomes literal Text in the isolated engine. That is a separate proven defect;
whether it fully explains the phone callback stall remains a physical test gate.

## Changes

- Discover the unique shared StikDebug guest through `LCSharedUtils.appGroupPath`
  and `LiveContainer/Applications`. Read its actual bundle-folder name and selected
  data folder, supporting LiveContainer's original-bundle metadata. Match both
  the StikDebug bundle identity and URL scheme. Reads are bounded; missing,
  ambiguous, malformed or external symlink entries cannot dispatch a request.
- Use `livecontainer2://livecontainer-launch` with `bundle-name`, optional
  `container-folder-name` and base64 `open-url`. This selects a cold helper and
  forwards to the same running guest when already open. LiveContainer's own
  locked-app or switch-app confirmations remain in control. The inner fresh PID,
  inline script and actual Cabrillo host return identity are unchanged.
- Check helper discovery before changing radios or preparing a fresh JIT request.
  Standalone StikDebug and TrollStore keep their direct routes. A standalone
  Cabrillo without access to LC's shared group must choose standalone StikDebug.
- Revision43 retains42's six explicit text comparisons and corrects all four
  Stop and Output fields to `WFTextTokenString` with a variable attachment range.
  Action ordering, radio presets and callback protocol `cabrillo-39` remain intact.
- Log only allowlisted callback stage/outcome labels, without callback URLs,
  script contents or tokens. Existing native memory, detach and recovery gates
  still decide readiness; a shortcut receipt cannot grant JIT.

Primary integration source: LiveContainer commit
`4dbe0f9a626de801184a42c0be8d2cb105058e3d`,
[app-list launch handling](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/LiveContainerSwiftUI/Views/AppList/LCAppListView.swift),
[guest URL handling](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/TweakLoader/UIKit%2BGuestHooks.m)
and [shared app metadata](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/LiveContainer/LCSharedUtils.m).
These source observations do not substitute for testing the installed helper.

## Validation and package

-109 native host controls pass, including18 new discovery/guest-routing checks.
-36 generated branches pass for both shortcut variants and radio restore choices.
-53 isolated Apple WorkflowKit controls pass:36 condition cases (12 original
  missing-parameter controls) and17 output cases (8 exact receipt outputs,
  8 original missing-output controls and one literal control). Only If, Comment
  and Stop and Output actions are allowed; no network/radio/URL actions or library
  writes occur. Input substitutes for dictionary action output in these fixtures.
- The first combined host fixture crashed on a missing expected condition in an
  output-only case. The second assumed the original field always produces literal
  Text; in the combined engine it produces empty text instead. The final negative
  control requires the original to lose the receipt, and the positive control
  requires exact receipt output. Failed fixtures are retained, not counted as passes.
- iOS15 arm64 compilation and package verification pass with Xcode26.6.
  All199 managed assemblies and16 dependency archives are exact41. SwiftUI sources
  remain exact41; unchanged UI tests were not rerun. No Celeste game code/assets
  are bundled. Public runtime inputs and explicit FMOD receipt remain pinned.
- IPA18,697,274 bytes, SHA256
  `8a3594a4bad7eddd61e8e2fded22726cb745f48ba273d900be9561203a6fc202`.
  Fresh executable/dSYM UUID `ec31fbfc79a63175b28d936dbb64bcb3`.
  All212 captured inputs are frozen in `artifacts/cabrillo-build43-final`;
  35–42 frozen-input comparisons pass. Further implementation requires44.

## Delivery and physical gates

The eight-file kit is staged at `On My iPhone/LiveContainer/Cabrillo-build43`;
full USB readback of every file matches, including IPA and both Apple-signed
shortcuts. The current125 save/profile files were backed up and match the41
readback. The owner confirms both updates; installed BuildInfo/data identity and125 save hashes
are verified, as are all46 actions in the single named Cabrillo shortcut.

The same kit is placed at `Celeste JIT Tests/0.22.3-build-43`. All eight files are confirmed uploaded after the initial temporary iCloud
account/server error cleared; the upload receipt is retained. Only the superseded40 cloud IPA was removed after
verifying its retained exact local original. All Results and accepted32 remain;
logical cloud contents are981,350,840 bytes after placement.

### First actual43 phone run

The owner allowed both Open prompts. Session `f1769b89-5b7e-4108-a632-1d8fd7864f6a`
(PID21378) passes the VPN hello in80ms, discovers the actual shared StikDebug guest
and opens it from a cold LC2 process. Owner observation and screenshot agree that
StikDebug then remains idle. Mailbox stays1, with no tracing, native JIT checks or
game execution. The system log starts Stop and Output at11:53:36 London time but
records no completion. A later error callback at11:56:13 is accepted and the
session fails safely; Automatic had changed no radios and requires no recovery.
Correct output serialization therefore did not resolve the whole callback problem.

Cabrillo was foregrounded normally while preserving the same PID. The owner tapped
**Enable via LiveContainer 2** with StikDebug already running. This direct request
returns automatically, turns the native status green and starts Celeste. The same
journal verifies mailbox2, `cs_debugged=1`, `traced=0`,26 native passes and14 graphics
passes. It reuses prepared game code in0.095s, quiesces catalogue requests to zero,
reveals the first rendered/readback frame and reaches `OuiTitleScreen` with zero
reported runtime failures. A later collection (`before-shortcut44.jsonl`) verifies
ten paired menu touches, normal Quit, profile save readback, complete stage8
shutdown and a delayed native heartbeat. No level input is observed. This is a
scoped manual warm JIT/menu/Quit pass;43's cold Automatic shortcut remains failed.

No competing debugger was attached. Private evidence includes
`automatic-b`, `return-b` and `native-retry-*` under the phone43 evidence folder.
The successful continuation is retained as `warm-native-success.jsonl`.

[Shortcut44](SHORTCUT_FILES_44.md) separates helper startup from the single JIT
request and avoids Stop and Output. It is packaged and delivered for testing;
its local controls do not establish a physical cold-launch or callback fix.

The subsequent44 test exposes long plain-text URL truncation and an LC decoding
exception. [Shortcut45](SHORTCUT_FILES_45.md) corrects the typed URL handoff.
Next: verify imported45, then fresh-process Automatic, Travel/network restoration
and game/Quit.
Keep independent diagnostics exports and the older native save-manager, cached
preparation, iPad38 and sustained120Hz gates separate. Do not attach a debugger
alongside StikDebug. Private logs are under `.private/device-evidence/2026-09-26`.

## Reproduction

```sh
python3 tools/check_shortcut_guests.py --work .build/new43-native-controls
python3 tools/check_shortcut_files43.py --work .build/new43-apple-controls
python3 tools/build_shortcut_files43.py --output .build/new43-shortcuts --sign
python3 tools/build_shortcut_guests.py \
  --managed .build/owned-public-managed38-e/receipt.json \
  --native .build/owned-public-native38-e/receipt.json \
  --fmod .build/owned-fmod38-c/receipt.json \
  --work .build/new43-build --output artifacts/new43-build
```

Use fresh paths. The Apple host controls require macOS WorkflowKit; they are not
part of the iOS app or portable public CI. This source has not been pushed.
