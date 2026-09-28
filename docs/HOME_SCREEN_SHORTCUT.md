# Open Cabrillo from one Home Screen icon

Use **Cabrillo0.23.2 / build50** with **shortcut revision49**. Keep an already
imported49 shortcut;50 changes the native cellular launch sequence. New installs
use **Settings → Home Screen shortcut → Add Home Screen shortcut**. This is a
private development build. The fresh50 Automatic cellular-start test passes native
JIT, automatic return and restoration, confirmed by USB logs and the owner.
The owner confirms49's phone text entry/import; app47/shortcut46 remains the
fallback with scoped Wi-Fi/Travel passes.

If48 erases text during Configure This Shortcut, use the corrected49 template
bundled with50. Paste the app-generated launch link into its blank Text field.
The separate49-kit file is the LiveContainer template; standalone installations
export their direct template from Cabrillo.

## One-time setup from Cabrillo

1. Install the50 IPA over the existing Cabrillo entry, retaining its data container.
   In LiveContainer, leave JIT **off**, the saved JIT script blank and Fix File
   Picker **on**. Finish an active game with normal Quit before updating.
2. Set up LocalDevVPN once, accepting its VPN configuration and keeping its default
   addresses. Cabrillo uses **10.7.0.1:49152** for the local developer service.
3. Set up the StikDebug installation selected by **Settings → JIT for this device →
   Enable with**. Its pairing, device connection and Developer Disk Image must be
   ready while online. Automatic StikDebug integration needs iOS17.4 or later.
4. Open **Add Home Screen shortcut**. Cabrillo shows its current installation and
   JIT provider. Tap **Save shortcut**; in LiveContainer, the button also copies
   this installation’s exact launch link. Save the file in Files, then tap it.
5. Review the shortcut in Apple Shortcuts. For LiveContainer, paste Cabrillo’s
   copied link into the blank text field when asked. Add the shortcut with the exact name **Cabrillo**.
   Replace an existing copy; do not leave a new **Cabrillo1** alongside the old one.
   The setup screen can copy the link again if needed.
6. Open the shortcut’s details/share menu and choose **Add to Home Screen**.
   Apple requires the import and Home Screen taps; exporting a file does not
   prove it was installed. The setup screen’s Open button opens the named shortcut
   for editing; **Test installed shortcut** actually runs it in Shortcuts.
7. Choose Automatic or Travel and the restore preset in Cabrillo. Test once with
   the device unlocked and allow first-use app/network permissions. For unattended
   requests, StikDebug’s **Confirm External JIT Requests** must be off; this setting
   applies to all external requests to that installation. Keep Auto Quit off while
   testing. No saved Cabrillo debugger script is needed.

### Supported installation choices

| Cabrillo | StikDebug | Setup |
| --- | --- | --- |
| Standalone | Standalone | Signed direct-launch template; uses the current provider setting. |
| LiveContainer1 | Standalone | Paste the app-generated Cabrillo launch link once. |
| LiveContainer1 | LiveContainer2 | Same Home link; Cabrillo discovers the one shared StikDebug guest. |
| Standalone | LiveContainer2 | Also paste StikDebug’s copied LiveContainer launch link into Cabrillo once. |
| LiveContainer2 | Standalone | Uses the actual LC2 host and current data container. |
| LiveContainer2 | LiveContainer2 | Blocked: both apps need to run in separate hosts. |

For the standalone/LC2 combination, hold **StikDebug** in LiveContainer → **Add to
Home Screen → Copy Launch URL**, then paste it into Cabrillo’s setup screen and
save it. Share that StikDebug installation with LC2. The app validates the link
structure; it cannot inspect the helper’s identity from a separate sandbox. That
combination has host routing tests, not an end-to-end phone pass yet.

The Home link includes the actual LiveContainer scheme, Cabrillo guest folder and
current data container. It explicitly selects Cabrillo rather than forwarding the
URL to whichever guest was last active. LiveContainer may require confirmation
when switching a running guest. Repeat setup if Cabrillo moves to another host or
data container. Keep one shortcut named Cabrillo: native network stages call that
name. Switching supported JIT providers in Cabrillo does not require reimporting it.

The icon prepares JIT for **that running process**, then returns ready to choose
Run Celeste. It does not start the game automatically. A process with verified JIT
skips preparation. After Celeste has run and quit, close Cabrillo before another
game session. Existing saves, mods and prepared game files stay in place.

### Signing and customization

Cabrillo bundles two templates signed with Apple’s macOS Shortcuts CLI in
**anyone** mode. The phone verifies and exports the exact signed bytes; it does not
try to sign a modified workflow. Apple’s import question customizes the LiveContainer
Home URL after import. No user PID, pairing data or debugger script is embedded;
Cabrillo supplies each fresh JIT request at runtime. The files are bundled, so the
setup flow does not download a template or depend on a Cabrillo signing server.
See Apple’s [file signing guide](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac),
[import questions](https://support.apple.com/guide/shortcuts/apdf330fd3a0/ios) and
[Home Screen guide](https://support.apple.com/guide/shortcuts/apd735880972/ios).

### Existing phone evidence

USB testing on28 September verifies app47/shortcut46 Automatic on Wi-Fi and four
Travel launches, including Automatic starting on cellular with Wi-Fi and VPN off.
All pass26 native checks detached and restore the configured both-on preset.
One earlier restoration receipt was missing; a later fresh-process recovery passes,
and the stall did not recur. Its cause remains unexplained. These results establish
the retained native coordinator.48 file export is verified, but its import question
loses edits in Apple's URL-list editor.49 fixes that question: the owner confirms
text retention and successful phone import on app48. It also passes actual
simulator import/URL execution checks. Subsequent app49 phone runs start the native
Home flow on cellular but time out before Airplane Mode; both restore successfully.
The same failure occurs with Wi-Fi disabled in Control Centre and Settings.50
changes the pre-isolation gate to check the VPN route. Its fresh phone run passes
all26 native checks detached, returns and restores the preset in31.3seconds.
The owner’s independent50 export is also reviewed and confirmed uploaded; its
current run matches the USB evidence, with the earlier49 failures kept separately.
See the [50 cellular repair](ios-jit/SHORTCUT_CELLULAR_BUILD_50.md), the
[47 report](ios-jit/SHORTCUT_COMPLETION_BUILD_47.md) and
[48 report](ios-jit/SHORTCUT_SETUP_BUILD_48.md) and
[49 repair](ios-jit/SHORTCUT_IMPORT_BUILD_49.md). Keep the working47/46 artifacts.

## Networking

| Mode | What happens |
| --- | --- |
| Automatic | Keeps Wi-Fi/cellular settings when Wi-Fi has an assigned address; otherwise uses Travel. |
| Keep Wi-Fi & cellular | Leaves those switches and Airplane Mode alone; enables/checks LocalDevVPN. |
| Travel · Airplane Mode | Turns Airplane Mode off and Wi-Fi/cellular on, waits for the selected local VPN route, turns Airplane Mode on and Wi-Fi off, verifies the developer service, then enables JIT. |

In Travel, Cabrillo first verifies that the route to10.7.0.1 uses an active tunnel.
It checks the developer service **after Airplane Mode**, following
[StikJIT's cellular sequence](https://github.com/StikDebug/StikJIT/blob/5d732f94b871031704ef6f580a313e8d99d80ec1/INTEGRATION.md).
LocalDevVPN's return callback alone proves neither connection nor readiness.
The Wi-Fi path requires the service reply directly. Both paths then require native
JIT execution and debugger detach. A route, helper opening or completed Shortcuts
action cannot mark JIT ready.

**Travel uses a restore preset**, because the available Shortcuts network actions
do not expose the original on/off state of all three radio switches. After JIT,
Travel turns Airplane Mode off and applies your chosen Wi-Fi and cellular states
(both on by default). It does not claim to remember states it cannot read.
Airplane Mode follows iOS's remembered Bluetooth behavior. LocalDevVPN stays enabled;
this workflow does not disable an existing VPN after launch. A different active
VPN may need to be disconnected before LocalDevVPN can start.

Travel is intended for use away from Wi-Fi after StikDebug's one-time online setup.
It cannot download a missing Developer Disk Image or repair pairing while offline.
The phone tests verify cellular starting state and the Airplane Mode tunnel, but
preparation can reconnect nearby known Wi-Fi. Build50's corrected sequence now passes a fresh cellular-start test. Operation
entirely outside Wi-Fi range and alternate restore presets remain separate gates.

## Interrupted launches

Cabrillo writes its recovery record **before** asking Shortcuts to change radios.
If it restarts, the next Home Screen launch restores that saved preset first,
without treating an old process's JIT as valid. Then use the icon again.

On a recoverable error, it returns to Cabrillo and attempts restoration. It keeps
the tunnel in place while StikDebug may still be attached. If a Shortcuts prompt
or run is stuck, stop it in Shortcuts, return to Cabrillo and tap **Restore
networking**. If the app cannot open, use Control Center to turn Airplane Mode off
and restore Wi-Fi/cellular manually. The recovery record stays until Shortcuts
reports completion; no background app can guarantee cleanup after iOS kills it.

The LiveContainer2 route opens the selected helper with one complete fresh request.
The JIT stage includes a short foreground-return fallback, so a helper
failure should not leave StikDebug on screen. That delay is **not** a JIT success
test. The system may still show its own permission/error UI; report a stranded
screen rather than assuming the launch succeeded.

## Remaining phone checks

The28 September review records five47 launches plus the50 cellular pass and an unchanged
125-file save snapshot. Automatic has been restored in Settings. Do not repeat
those passed runs solely for another log export. Remaining checks include use
entirely outside Wi-Fi range, alternate restore presets, cancellation, launching
while another LiveContainer guest is selected, and normal game Quit after47.
The independent50 export is verified in50/Results. Keep independent exports for
new tests without repeating a passed run solely to create another file.
The original restoration stall remains an intermittent issue to investigate if it
recurs; preserve its on-screen error and logs before retrying.

### Test sequence for an untested setup

1. Keep the phone unlocked. Close Cabrillo and LiveContainer2, tap the new Home Screen icon in
   **Automatic** with Wi-Fi connected. Expect Cabrillo → LocalDevVPN if needed →
   StikDebug → Cabrillo, ending with verified JIT and unchanged radio switches.
2. Close Cabrillo. Choose **Travel** before the next fresh launch, check your
   restore preset, then use the icon again. Expect Wi-Fi to disconnect temporarily,
   then return with the preset applied after JIT. The Mac's wireless connection
   will drop during this test; Cabrillo keeps its log locally.
3. Check that Run Celeste still works. Return through the game's normal Quit.
   Export diagnostics to **0.23.2-build-50/Results**, and report whether each
   helper returned automatically and whether the final network switches matched
   your preset. Keep the independent export even if logs are also collected over Wi-Fi.

## Integration references

Reviewed26 September2026, with source commits recorded in the build39 report:

- [Apple: Shortcuts x-callback-url](https://support.apple.com/guide/shortcuts/use-x-callback-url-apdcd7f20a6f/ios).
- [StikJIT integration guidance](https://github.com/StikDebug/StikJIT/blob/5d732f94b871031704ef6f580a313e8d99d80ec1/INTEGRATION.md): fresh PID/script requests, return bundle identity and cellular/Airplane Mode setup.
- [StikDebug request handling](https://github.com/StikDebug/StikDebug/blob/5e3e1bc91efb0dbec784be5a81e377d3ed355a40/StikDebug/Views/HomeView.swift) and [script-driven app return](https://github.com/StikDebug/StikDebug/blob/5e3e1bc91efb0dbec784be5a81e377d3ed355a40/StikDebug/JSSupport/RunJSView.swift).
- [LocalDevVPN URL handling](https://github.com/jkcoxson/LocalDevVPN/blob/af3fd697803ada4ac2b8d518358f5ab0a534844c/LocalDevVPN/LocalDevVPNApp.swift): starts the VPN and returns after a delay without confirming connection.
- [LiveContainer guest URL handling](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/TweakLoader/UIKit%2BGuestHooks.m).
- [Cherri's network action definitions](https://github.com/electrikmilk/cherri/blob/d96eee9c7768649d441df0166b68a7e3c742690c/actions/network.cherri) and [device actions](https://github.com/electrikmilk/cherri/blob/d96eee9c7768649d441df0166b68a7e3c742690c/actions/device.cherri), used to cross-check the generated Shortcuts plist.
