# Graphics bridge physical test: 0.4.1 (11)

Use the numbered phone guide, `README-FIRST.txt` in the test kit. This stage has its own bundle
ID, `io.github.hmcneill46.celeste.everest.jit.graphics`, and a separate diagnostics
directory. It does not replace the accepted build 9 Hook Canary data.

Build 11 fixes the startup Metal command-buffer lifetime and reset ordering.
Install it over build 10 and import the new DLL; keep the previous results.
The reset and skipped-draw regressions run automatically.

The unsigned IPA contains the native UIKit launcher, the pinned static native
graphics libraries, custom Mono 8.0.28 and untrimmed FNA/MonoMod IL. Import the
separate `GraphicsCanary-v0.4.1.dll` after installation. No Celeste content,
Everest gameplay, FMOD, signing identity or provisioning profile is included.

The primary configuration is iPhone 15 Pro Max / iOS 26.5, graphics app in
LiveContainer 1 and StikDebug in LiveContainer 2. Turn **Launch with JIT OFF**
and leave the LiveContainer launch script **empty**. Record changed container
or StikDebug versions using the launcher's version button.

Enable JIT from inside this app. Its PID/nonce-specific request routes through
`livecontainer2://open-url`. It retains build 9's exact 16 MiB per arena script
and native checks. Wait for the script to complete and detach, return to the
app, then wait for NATIVE PASS before starting graphics. Do not reuse a script
from another launch or another probe. The included template is a reference,
not a directly runnable script.

If forwarding an inline script fails, use **Export session script** in the
current graphics process, save that freshly generated file, and import it into
StikDebug in LiveContainer 2. Return to the graphics launcher and use **Use
imported script in LiveContainer 2**. Select the current PID shown by the app.
Keep the target process alive throughout. Do not attach Xcode simultaneously.

A useful pass needs at least 300 completed game frames, actual touch press and
release, at least 20 seconds in the background, and at least 120 more frames
after returning. The guide asks for longer waits to allow slow startup. The
marker changes to white while touched; a real MonoMod hook supplies its idle
pink colour. GPU texture clear/readback and hook preservation are checked in
code. A controller can move the marker but is optional for this test.

**Finish test** stops the display link, ends the FNA loop, disposes graphics,
removes the hook, detaches the native main thread from Mono, and restores the
launcher. The managed runtime stays alive until the process closes; game
restart and arbitrary mod unloading are not implemented. A partial test still
returns to the launcher and produces diagnostic evidence.

Wait 10 seconds after the result and export to
`iCloud Drive/Celeste JIT Tests/0.4.1-build-11/Results/`. On a crash, reopen and
export before another JIT request. The export includes the previous five
sessions and console tails. USB retrieval remains available when the correct
phone is connected; this new bundle must be selected explicitly.

Please report visible animation, drag/release behaviour, background/resume and
return to the launcher. Logs alone cannot certify what was displayed. Slow
frames while diagnostic JIT logging is active are not a product benchmark.
There is deliberately no audio test in this build.
