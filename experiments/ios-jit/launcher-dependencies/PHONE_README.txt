CELESTE — PRIVATE TEST BUILD 25
Version 0.13.0 (25) • Dependencies + mod updates

FILES → ICLOUD DRIVE → Celeste JIT Tests → 0.13.0-build-25
Install CelesteJITEverest-unsigned.ipa into LiveContainer slot 1 as an
UPDATE of the existing Celeste app. Keep its data. Your game files, mod
ZIPs and saves are reused; no game or mod ZIP needs to be imported again.

Keep LiveContainer: Launch with JIT OFF, saved script blank, Fix File
Picker ON. StikDebug stays in LiveContainer 2. Start with a fresh app
process. Downloads and mod choices are made BEFORE starting Celeste.

1. TEST DEPENDENCY REVIEW (no large download)
   In Mods → Installed, find GravityHelper and turn it off briefly.
   Tap Play → Run Celeste: an alert should explain the missing dependency.
   Open Mods → Resolve dependencies. It should offer to enable the existing
   compatible GravityHelper ZIP. Apply the reviewed change. If other
   dependencies are missing, read the entire plan before applying it.
   Do not enable an incomplete SpringCollab import just for this quick test.

2. TEST UPDATES
   Open Mods → Updates. An idle visit checks automatically if the last
   successful check is over 24 hours old. Check for updates also works
   manually. Settings lets you disable automatic checks.
   You should see installed/latest versions and individual Update buttons.
   At preparation time the compatible updates were EeveeHelper 1.12.6 and
   FrostHelper 1.80.2 (about 1.4 MB together). Two other published updates
   require Everest 1.6531.0 and should explain why they are unavailable;
   this app keeps its accepted Everest 1.6458.0 runtime.
   Choose one individual update and review it. Cancel/Done before applying
   once to check that nothing changes. Then choose Update all for the
   available compatible updates, review, and Download and install.
   If the downloads are long enough, Cancel once and retry. Completed,
   verified files are kept. Keep the app in the foreground on Wi-Fi.
   Actual ZIP metadata may require a second review: this is intentional.
   Disabled mods stay disabled. Previous ZIPs are retained, initially hidden
   behind “Show retained previous archives”; Enable all leaves them alone.
   Any conflict should stop the plan and explain the requirement. Do not
   force-enable an unsupported version. Export diagnostics if blocked.

3. PLAY AND SAVE
   Return to Play → Enable via LiveContainer 2. Run the NEW inline request
   in StikDebug, wait for success and detach, then return and Run Celeste.
   The template JS in this folder is reference material; do not use an old
   PID-specific script or a script from another build/process.
   Confirm existing progress is present. Play a familiar map for a few
   minutes; Paint is a useful helper regression if convenient. The logs
   record the map and room, so there is no need to identify them manually.
   Save and Quit from the map, then use Quit/Exit at the main menu. Wait
   for the native launcher and session-saved result, then another 10 seconds.
   Settings → Export diagnostics → this folder → Results.

4. FRESH-PROCESS CHECK
   Close the app in the app switcher and relaunch. Check that mod versions,
   enabled choices and the Updates page survive. Visiting Updates again
   should reuse today's result rather than repeatedly fetching the index.
   Enable JIT with another NEW request, run, and verify saved progress.
   Quit normally and export a second diagnostic to Results.

If something fails: export before enabling JIT or starting another session.
For a visual/UI problem, a brief description or screenshot helps; logs
already record download hashes, plans, installation receipts and game state.
Keep Export as the iCloud fallback. One game session per process remains.

Build24 remains available in 0.12.1-build-24 as the accepted fallback.
This is a private test kit, not a public distribution package.
