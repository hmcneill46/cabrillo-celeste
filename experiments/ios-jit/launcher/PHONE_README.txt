CELESTE JIT · 0.11.0 (BUILD 20)
Native launcher, mod library and normal play

Install CelesteJITEverest-unsigned.ipa as an UPDATE in LiveContainer 1.
Keep the existing app data. Do not delete the app or its data container.
Your Celeste content, full Strawberry Jam ZIPs and saves are reused.
StikDebug stays in LiveContainer 2.

LiveContainer 1 settings: Launch with JIT OFF; saved script blank;
Fix File Picker ON. Fully close the previous game process first.

TEST 1 — LAUNCHER AND IMPORT (no JIT needed yet)
1. Open the app upright. Check the Play / Mods / Settings tabs and rotate
   between portrait and landscape. Your existing game files should be found.
2. In Mods, tap Import mod ZIPs and select CJITLauncherExample-v1.0.0.zip
   from this build 20 iCloud folder. It is a tiny independent test code mod.
   Your existing 52 SJ mods should already be present; don't download them again.
3. Search GravityHelper and turn it OFF. The dependency warning should explain
   that Strawberry Jam needs it; Run must be unavailable. Turn it back ON.
4. Search CJITLauncherExample and turn it OFF. Close the app in the app switcher,
   relaunch it, and check that it is still OFF. Turn it back ON for the game test.
   Keep the whole SJ set enabled. Don't use 'Disable all' for this play test.

TEST 2 — NORMAL STRAWBERRY JAM PLAY
5. Settings: Performance overlay ON; Strawberry Jam regression test OFF.
6. In Play, Enable via LiveContainer 2. Complete the fresh StikDebug request,
   wait for it to detach, then return to the SAME running app in LC1.
   The app generates the correct PID/nonce script; no manual script is needed.
7. Run Celeste. The game should switch to landscape. Use Celeste's normal
   menus and your existing save slot. Check the previous save is recognised.
   Select Strawberry Jam and the Beginner lobby through the game menus.
8. Play for a few minutes. If possible enter a map through an ordinary lobby
   entrance, then jump/dash and check controls and music. Note the map's name.
   The normal mode has no forced SJ lobby/Bing test shortcuts.
9. Go Home for about 30 seconds. Return, move and jump, then play a little more.
   The overlay should resume with a fresh measurement window.
10. Tap Finish. Expect 'SESSION SAVED'. Wait 10 seconds, open Settings,
    Export diagnostics, and Save to Files in:
    iCloud Drive > Celeste JIT Tests > 0.11.0-build-20 > Results
    Include a short note about menus, map played, save retention and any UI issue.

After Finish, close and relaunch the app to play again or change code mods.
There is one game/runtime per process. No reimport is needed on relaunch.
If you can, reopen the save in another fresh JIT session to check progress persists.

If anything crashes: reopen and Export diagnostics FIRST, before enabling JIT
or trying another game run. The export includes bounded prior-session excerpts.
For a StikDebug error also keep its displayed script log.

Frame metrics: rolling last 600 callbacks (about 10 s at 60 fps), including
loading stalls. 'Frame ms' is elapsed time inside the game frame callback,
including waits; it is not GPU timing. 1% low averages the slowest 1% intervals
and needs 120 samples. Home/pausing resets the window.

You may import other normal Everest mod ZIPs. The launcher checks dependencies,
versions, duplicates and supported iOS compatibility pins. Successful import
cannot establish that every mod, desktop plugin or map will work on iOS.
New versions of GravityHelper, CollabUtils2 and FemtoHelper need compatibility
review before enabling them. Original ZIPs and disabled mods remain in the app.

This remains a private development IPA with prepared game IL and native FMOD.
Public game-IL preparation / redistribution are separate unfinished work.
The included TEMPLATE script is a reference, not a reusable PID-bound request.
Build 19 is kept as the accepted fallback. No commits or GitHub upload were made.
