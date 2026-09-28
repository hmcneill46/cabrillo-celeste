# Build49: keep the shortcut setup text

## Problem and repair

The owner installed48 and exported its bundled LiveContainer shortcut. USB logs
verify that native export, and a phone screenshot shows Configure This Shortcut
using Apple's URL-list editor. Typing disappears almost immediately. The exact
signed48 file reproduces the failure in the actual iOS26.5 simulator Shortcuts app:
after typing `example`, the field restores `cabrillo://shortcut-setup-required`.
The earlier production-view tests did not exercise Apple's import screen.

Revision49 binds the import question to a **blank Text action**. Typed or pasted
input stays in that field. The Home branch passes this text through a URL action
and binds Open URL directly to that typed URL output. An empty answer opens
Cabrillo's setup help. JIT stage links retain their own explicit typed connection;
networking, restoration and native readiness behavior stay the same.

The49 shortcut works with app48 or later. App49 bundles the correction for future
in-app exports. Its only native source differences from48 are the expected asset
revision and export diagnostic revision; all SwiftUI and the47 reducer are exact48.
All199 managed assemblies and16 runtime dependency archives remain exact48.

## Evidence

- The two actual Apple Shortcuts simulator UI tests reproduce48's lost edit, then
  verify49 typed text, paste of the complete encoded app/data link, retention when
  editing ends, Add/Replace import and real URL/Open URL execution. A fixture app
  receives the exact full link, including encoded space, data selection and base64
  inner URL. These tests use signed input files, not a mock import screen.
- The isolated fixture registers the LiveContainer URL schemes in the simulator.
  No phone radios, VPN, StikDebug, JIT or game actions run. This is import and URL
  execution evidence, not physical Home/JIT acceptance.
- An initial execution check waited on the main Shortcuts app for Apple's Allow
  prompt. Inspection located it in `com.apple.ShortcutsUI`; the final test handles
  that real first-use prompt and passes. The template did not change for this.
- 132 native launch controls,50 setup/integrity controls,36 generated branches and
  15 broken typed-URL controls pass. The retained original43 missing-callback
  failure still reproduces. Apple host controls pass36 comparisons, one completion
  check and18 content checks including four original truncation controls.
- Xcode26.6/17F113 builds arm64 with iOS15 minimum. The package audit verifies zero
  bundled game assemblies/assets, all runtime pins and a fresh matching dSYM UUID.
  The unchanged SwiftUI retains48's recorded14 simulator view checks; those were
  not repeated for this template repair. All35–49 frozen manifests still match.

## Package and delivery

- Version: **0.23.1 / build49**, lane `launcher-shortcut-import`.
- IPA: `Cabrillo-0.23.1-build-49-unsigned.ipa`, 18,758,794bytes.
- SHA256: `2db91b2f496f7e7fe92393822a32e17f78be9c2d8c39f0bba30b5c57ab33b7f6`.
- Executable/dSYM UUID: `15560fd35ba93f459b7a9a4d5225c880`.
- All238 captured inputs are frozen in `artifacts/cabrillo-build49-final`.
  New implementation requires50. The [ledger](SHORTCUT_IMPORT_BUILD_49_EVIDENCE.json)
  records input, validation and private evidence hashes.

All seven kit files are confirmed uploaded in
`Celeste JIT Tests/0.23.1-build-49`. All seven also have exact USB readback at
**On My iPhone → LiveContainer → Cabrillo-build49**. The installed app is48;
file staging is separate from installation. The kit includes the repaired
LiveContainer `Cabrillo.shortcut` so the owner can import it immediately on48.
The IPA includes both standalone and LiveContainer files for future in-app exports.
Cloud logical total is995,079,880bytes; no installer was retired
for49, and every Results folder and the working47/46 fallback remain.

## Focused phone check

Cancel the old configuration, tap **Copy launch link again** in Cabrillo's setup
screen, open the49 kit's `Cabrillo.shortcut`, paste into its blank text field and
add it as exactly **Cabrillo**. The owner confirms that the text stays and the
shortcut imports successfully on the phone with app48. That import request is
answered; this closes the reported configuration defect. After import,
add/use its Home icon and confirm it selects the right guest/data and returns with
native JIT ready. The owner can keep48 for this immediate fix; install49 to make
future in-app exports use the correction. Never interrupt an active game to update.

Preserve an independent diagnostic export in49/Results. Alternate provider routes,
another currently selected LC guest, Travel variants, fully out-of-range operation,
normal game Quit, native saves, iPad38 and sustained120Hz remain distinct physical
gates. The physical pass is scoped to the owner-confirmed49 import on app48;
Home/JIT/gameplay and app49 installation are not yet verified. No GitHub write or
public IPA publication is claimed.
FMOD redistribution permission remains unresolved. See the
[setup guide](../HOME_SCREEN_SHORTCUT.md) for the complete supported setup.

## Subsequent cellular Home launch failure —28 September

The owner confirms text retention/import, then reports the same Home timeout with
Wi-Fi disabled through Control Centre and Settings. Both USB journals show app49
with shortcut49 reaching the native Travel connect phase, failing the developer
service check before Airplane Mode and restoring successfully. No JIT request
occurs. This leaves49's import repair accepted while cellular Home/JIT fails. The
source ordering repair and its separate acceptance gate are in
[build50](SHORTCUT_CELLULAR_BUILD_50.md).49's frozen source and artifacts are unchanged.
