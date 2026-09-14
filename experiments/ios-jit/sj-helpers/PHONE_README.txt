CELESTE JIT EVEREST — 0.8.0, BUILD 15
Real LuaCutscenes and MaxHelpingHand test. Small private IPA.

FILES
CelesteJITEverest-unsigned.ipa
LuaCutscenes-v0.2.13.zip
MaxHelpingHand-v1.40.9.zip
CJITSJHelpers-v1.0.0.zip
The two older CJITCodeCanary / CJITTestMap ZIPs are recovery copies only.
No new Celeste download is needed: this test reuses your build 14 game files.

UPDATE AND CHECK RETENTION
1. Close the old Celeste game process. In LiveContainer 1, install the IPA as
   an UPDATE of the existing Celeste JIT Everest guest, keeping its current
   data container. Do not delete the guest or create a new data container.
   Keep Launch with JIT OFF and the launch script blank. StikDebug stays in
   LiveContainer 2. Keep Settings > Fixes > Fix File Picker ON in LC1.
2. Open build 15. Before importing anything, it should find saved game files
   and show 2/5 test ZIPs (the existing canaries). If either is missing, export
   diagnostics to Results and stop so I can inspect retention before repair.
   The save you deliberately deleted need not be restored. The most recent
   diagnostics saved the canary counter at 12; later play may have raised it.
3. Import the THREE new ZIPs listed above using Import test ZIPs. Select the
   ZIPs themselves, not extracted folders. You can select all three together.
   It should say All 5 test ZIPs ready. Leave Import game ZIP alone.
4. Tap Enable via LiveContainer 2. Wait for the fresh script to finish and
   detach, then return to the SAME Celeste process. Tap Run Celeste + Everest.
   Keep the app open while it verifies stored content and loads the helpers.

HELPER ROOM
5. At the title, tap Helper map in the native overlay. Let Madeline's short
   automatic walk finish. LUA should say waiting for Home / return.
6. Stand on the wide moving platform for about five seconds until PLATFORM
   says PASS. It must move and carry Madeline. If you fall to the safe floor,
   jump back onto it. Then move and jump a few times using the touch controls.
   The canary sign should show the saved counter and matching On / IL counts.
7. Go Home for 30 seconds, then return to this same game. The retained Lua
   cutscene should finish and LUA should change to PASS. Jump a few more
   times, then wait about ten seconds. Both LUA and PLATFORM must say PASS.
8. Tap Finish. Wait for PASS and another ten seconds. Export diagnostics to:
   Files > iCloud Drive > Celeste JIT Tests > 0.8.0-build-15 > Results
   A name such as helpers-after-update.json is useful. Tell me whether the
   moving platform, sound and touch controls looked correct.

IF SOMETHING FAILS
If it crashes, reopen and EXPORT FIRST before enabling JIT again. Save that
export in Results and tell me the last visible step. If a room check stays
pending, export after returning to the launcher; the counters explain why.
Do not reimport game files or delete saves to repair an unexpected failure.
The app's export still includes previous sessions and native console tails.

SCRIPT
Enable supplies the complete current script automatically. The included .js
is only a TEMPLATE and cannot be run unchanged. If a manual route is needed,
use Export session script inside the current process, import that exact file
into StikDebug, then use the imported-script button. Never reuse an old PID's
script. This build uses two 64 MiB arenas (128 MiB total).

SCOPE
This test uses the original LuaCutscenes 0.2.13 and MaxHelpingHand 1.40.9 ZIPs,
plus our original diagnostic room. GravityHelper 1.2.28 exposed an optional
CelesteNet loading incompatibility on the Mac and is saved for a separate fix;
it is not included in this phone test. Full Strawberry Jam follows further
helper coverage. The small private app still contains prepared Celeste IL and
linked iOS FMOD; a public game-free launcher remains a later packaging stage.
