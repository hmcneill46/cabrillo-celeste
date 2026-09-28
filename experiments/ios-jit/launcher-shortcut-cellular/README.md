# Cabrillo 0.23.2 — cellular shortcut launch (build50)

Travel checks the selected local VPN route, enables Airplane Mode, then verifies
the Remote Pairing service before requesting JIT. Earlier builds waited for that
service while cellular was still active, which can prevent reaching isolation.
The route check does not grant JIT or replace the post-isolation service check.
Recovery remains durable until the matching restoration receipt arrives.

Keep the existing revision49 shortcut. Both bundled Apple-signed files are exact49;
no shortcut reimport is needed. All199 managed assemblies,16 dependency archives
and SwiftUI sources remain exact49. Native execution and debugger detach remain
mandatory. Host checks are separate from physical cellular acceptance.

See docs/ios-jit/SHORTCUT_CELLULAR_BUILD_50.md and docs/HOME_SCREEN_SHORTCUT.md.
Public IPA distribution still requires FMOD permission; no publication authorized.
