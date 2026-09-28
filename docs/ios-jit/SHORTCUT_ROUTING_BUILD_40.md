# LiveContainer helper availability — build40 /0.22.1

26 September2026. The owner requested direct phone testing over Wi-Fi and then
connected USB. Build39 is installed and its shortcut reaches Cabrillo, but the
launcher stops at setup before opening the VPN or requesting JIT.

## Observed defect and correction

**Later phone result:**40 is installed with125 save/profile files unchanged.
Automatic now passes host resolution, opens LocalDevVPN and returns to Cabrillo.
It then times out before any JIT request because the legacy lockdown probe is the
wrong endpoint for the current StikDebug flow. Separate [build41](SHORTCUT_TUNNEL_BUILD_41.md)
uses Remote Pairing. The package and all40 inputs remain frozen. The delivery
section below records the earlier pending-installation state.

The build39 console reports that `localdevvpn` is not an allowed query scheme.
Its guest Info.plist contains that scheme, and LocalDevVPN is installed. Under
LiveContainer, `canOpenURL` still uses the installed host's query permissions.
Build39 incorrectly treats that denied query as a missing helper.

Build40 keeps the supported-provider and actual-host-identity gates. Inside
LiveContainer it attempts the normal URL handoff and uses its completion, the
local lockdown reply, and native JIT/detach checks to determine progress. Direct
installs retain declared-scheme availability checks, with a specific missing-app
message. A new setup event records which gate failed without recording scripts.

Apple documents that opening a URL is independent of the query whitelist:
[canOpenURL](https://developer.apple.com/documentation/uikit/uiapplication/canopenurl(_:)).
The reviewed LiveContainer hook passes external availability queries through to
the original API. This change requires no host re-signing or permission changes.

## Identity and verification

- Lane: `experiments/ios-jit/launcher-shortcut-routing`.
- Build: `launcher-shortcut-routing-20260926-40`,0.22.1.
- IPA18,692,903 bytes; SHA256
  `5d7c397848419c7939e32432586857b4e4e318e10eee61e6c4d01ead2017a48f`.
- New executable/dSYM UUID `b1bacaaf7b223bad949b6cd09e16e75c`.
-62 native host controls pass, including denied LC queries, real-host identity,
  unsupported providers and missing helpers for direct installs. The existing36
  generated shortcut branches pass. Receipt: `.build/shortcut40-controls-b`.
- All Swift UI and public dependency sources are exact39. Its four simulator UI
  tests remain prior evidence for those unchanged views; they were not rerun.
- All199 managed assemblies,16 dependency archives, preparation recipe, content
  manifest, JIT script and generated shortcut are exact39. Keep the installed
  **Cabrillo** shortcut; its `cabrillo-39` callback protocol is unchanged.
- Fresh Xcode26.6 compilation and independent package/payload checks pass. All210
  input files are frozen in `artifacts/cabrillo-build40-final`. No39 input changed.
  Further implementation changes require **build41**.
- Original/prepared game code and original assets remain absent from the IPA.
  FMOD redistribution and authorized release SDK access remain blocked. No
  GitHub write or public IPA is authorized or performed.

## Delivery and physical gate

The six-file kit is copied to `On My iPhone/LiveContainer/Cabrillo-build40` and
the complete IPA readback matches. The installer was opened through the normal
LiveContainer URL after closing its idle, unused build39 process. No debugger
was attached. Installation still requires LiveContainer's replacement selection.
The exact current saves and preferences were collected before the update.

The same six-file kit is confirmed uploaded to
`iCloud Drive/Celeste JIT Tests/0.22.1-build-40`. The initial upload check reported
an iCloud account/server error; a later check confirms every file uploaded with
no remaining error. The local and on-phone IPA hashes match.
Results folders and older builds remain intact; total logical size981,226,812
bytes at placement. The delivery receipt retains the confirmed upload result.

Automatic Wi-Fi handoff, native JIT, helper return, Travel and radio restoration,
and game/Quit are pending. Collect persisted logs directly, retain the independent
Results export and request human interaction only for actual system/helper UI.
Do not turn a host test or staged IPA into a phone PASS.

Raw phone evidence stays under `.private/device-evidence/2026-09-26/phone39` and
`phone40`; the public ledger records hashes and scoped outcomes.

## Reproduce

```sh
python3 tools/check_shortcut_routing.py --work .build/new-routing-controls
python3 tools/build_shortcut_routing.py \
  --managed .build/owned-public-managed38-e/receipt.json \
  --native .build/owned-public-native38-e/receipt.json \
  --fmod .build/owned-fmod38-c/receipt.json \
  --work .build/new-routing-native --output artifacts/new-routing-package
```
