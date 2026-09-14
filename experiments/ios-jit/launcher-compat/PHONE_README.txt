CELESTE JIT · 0.11.1 (BUILD 21)
FrostHelper graphics compatibility fix

Build 20 stopped because FrostHelper lava rendering called a missing FNA
function. There is no timed session limit. This build adds that function,
checks it at startup and displays a specific error if a later session fails.
Original game content, mod ZIPs, selected mods and saved files are reused.

1. Fully close the previous Celeste process. Install this IPA as an UPDATE
   in LiveContainer 1, retaining its existing data container.
   StikDebug stays in LiveContainer 2.
2. LC1 settings: Launch with JIT OFF; saved script blank; Fix File Picker ON.
3. Settings should show 0.11.1 (21). Keep the full SJ set enabled. Set
   Strawberry Jam regression test OFF and Performance overlay ON.
4. Enable via LiveContainer 2. Complete the NEW process-specific StikDebug
   request, wait for detachment, then return to the SAME running app in LC1.
   The inline script is automatic. Do not reuse a previous PID/nonce script.
5. Run Celeste. Select your existing save and enter the Beginner lobby using
   the normal game menus. Repeat the route where build 20 stopped, including
   walking far enough to bring the lava into view. Play for a few minutes.
6. If successful, enter a map normally, test movement/jump/dash and music,
   go Home for 30 seconds, return and play a little more. Note the map name.
7. Tap Finish. Expect SESSION SAVED. Wait 10 seconds, then Settings > Export
   diagnostics > Save to Files:
   iCloud Drive > Celeste JIT Tests > 0.11.1-build-21 > Results
8. Close and reopen for a fresh JIT session and verify your save progress
   persists. Export that session separately after finishing.

If the game stops: photograph/note the displayed error and export diagnostics
before another run. After a process crash, reopen and export BEFORE enabling
JIT. Recent progress from a failed session may not have been saved. Previously
saved files are retained. This update needs no game or SJ download.

There is one game per process. After Finish, close and relaunch for another
session. Ordinary play has no timer. The optional metrics include loading
stalls and show callback timing, not GPU timing.

Build 19 remains the accepted fallback. Build 20 results stay in its Results
folder. The TEMPLATE script is a reference, not a reusable JIT request.
This remains a private development IPA with prepared game IL and native FMOD.
