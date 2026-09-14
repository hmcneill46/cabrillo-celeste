CELESTE JIT · 0.11.2 (BUILD 22)
Constant-field compatibility fix

Build 21 stopped while loading Paint's intro room. MonoMod generated an invalid
read of Celeste.Decal.Root, a constant field, during EeveeHelper's setup.
There is no timed session limit and your JIT setup passed. This update fixes
constant reads in the shared reflection helper and improves JIT error details.
Existing game content, original mod ZIPs and profile saves are reused.

1. Fully close the old Celeste process. Install CelesteJITEverest-unsigned.ipa
   as an UPDATE in LiveContainer 1, retaining the existing data container.
   StikDebug stays in LiveContainer 2.
2. LC1 settings: Launch with JIT OFF; saved script blank; Fix File Picker ON.
3. Settings should show 0.11.2 (22). Use the same accepted full SJ mod set.
   Keep any incomplete SpringCollab import disabled for this regression.
   Set Strawberry Jam regression test OFF and Performance overlay ON.
4. Enable via LiveContainer 2. Complete the NEW process-specific StikDebug
   request, wait for detachment, then return to the SAME running app in LC1.
   The inline script is automatic; never reuse an old PID/nonce script.
5. Run Celeste. Choose your save in the normal menus, enter the Beginner
   lobby, then enter Paint (mosscairn) through its normal lobby entrance.
   Check the intro loads, play for a few minutes and test movement/jump/dash
   and music. If possible, progress beyond the opening room.
6. Go Home for 30 seconds, return and continue playing for at least 15 seconds.
7. Tap Finish. Expect SESSION SAVED. Wait 10 seconds, then Settings > Export
   diagnostics > Save to Files:
   iCloud Drive > Celeste JIT Tests > 0.11.2-build-22 > Results
8. Fully close and reopen, enable JIT again with the new request, and confirm
   your save progress persists. Export this second session separately after
   finishing. Note the map/room reached and any visible issue.

If the session stops, note the displayed error and export before another run.
After a process crash, reopen and export BEFORE enabling JIT. A failed session
may not save its latest progress. Existing saved files are retained.
No game or mod download is required for this update.

There is one game per process. After Finish, close and relaunch for another
session. Ordinary play has no timer. Metrics measure callback timing, including
loading stalls, and are not GPU timings.

Build 19 remains the accepted fallback. All previous Results folders are kept.
The TEMPLATE script is a reference, not a reusable JIT request. The tiny example
ZIP is optional and does not need reimporting. This is a private development IPA
with prepared game IL and native FMOD; it is not ready for public distribution.
