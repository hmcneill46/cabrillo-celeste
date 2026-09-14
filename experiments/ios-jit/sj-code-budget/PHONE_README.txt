CELESTE JIT EVEREST — 0.8.1, BUILD 16
Code allocation fix for the build 15 startup crash. Small private IPA.

Your build 15 export confirmed JIT, all five mod ZIPs and cached game files.
Mono ran out of its code arena before reaching the title. Build 16 reduces
ordinary code chunks from 256 KiB to 64 KiB on your phone, keeping the same
128 MiB budget and earlier helper fixes. Physical helper gameplay is pending.

UPDATE — NO GAME OR MOD IMPORT NEEDED
1. Close the previous Celeste process. In LiveContainer 1, install
   CelesteJITEverest-unsigned.ipa as an UPDATE of the existing Celeste JIT
   Everest guest, keeping its data container. Do not delete the guest.
   Keep Launch with JIT OFF, launch script blank, and Settings > Fixes >
   Fix File Picker ON. StikDebug stays in LiveContainer 2.
2. Open build 16. It should find the installed game library and all FIVE
   test ZIPs. Leave Import game ZIP and Import test ZIPs alone. If anything
   is unexpectedly missing, export to Results before repairing/reimporting.
   The ZIPs in this folder are unchanged recovery copies only. The save you
   deliberately deleted does not need restoring.
3. Tap Enable via LiveContainer 2. Wait for this process's fresh script to
   finish and detach. Return to the SAME Celeste process, then tap Run
   Celeste + Everest. Keep the app open as it checks content and loads mods.

HELPER ROOM
4. At the title, tap Helper map in the native overlay. Let Madeline's short
   automatic walk finish. LUA should say waiting for Home / return.
5. Stand on the wide moving platform for about five seconds until PLATFORM
   says PASS. It must move and carry Madeline. If you fall to the safe floor,
   jump back onto it. Move and jump a few times using the touch controls.
6. Go Home for 30 seconds, then return to the SAME game. The retained Lua
   coroutine should finish and LUA should change to PASS. Jump again after
   returning, then wait about ten seconds. Both LUA and PLATFORM must pass.
7. Tap Finish. Wait for PASS and another ten seconds, then Export diagnostics:
   Files > iCloud Drive > Celeste JIT Tests > 0.8.1-build-16 > Results
   Tell me whether the platform, sound and controls looked correct.

IF SOMETHING FAILS
If it crashes, reopen and EXPORT FIRST before enabling JIT again. Save to
Results and tell me the last visible step. Do not delete saves or reimport
game files to repair a crash. Export includes previous sessions and console.

SCRIPT
Enable supplies the current script automatically. The included .js is a
TEMPLATE; do not run it unchanged. If a manual route is needed, use Export
session script inside this process and import that exact file into StikDebug.
Never reuse a previous process's script. Geometry remains two 64 MiB arenas.

SCOPE
Original LuaCutscenes 0.2.13 and MaxHelpingHand 1.40.9 plus our diagnostic room.
GravityHelper's optional CelesteNet integration is a separate pending fix.
Full Strawberry Jam is not yet accepted. This small private app still contains
prepared Celeste IL and linked iOS FMOD; public packaging is a later stage.
