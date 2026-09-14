CELESTE JIT EVEREST — 0.9.0, BUILD 17
GravityHelper + LuaCutscenes + MaxHelpingHand. Small private test IPA.

Build 16 passed on your phone, including the Lua coroutine, moving platform,
saved game/mod data and Home/return. Build 17 tests gravity changes and ceiling
platforms together with Lua. No Celeste download or game reimport is needed.

UPDATE AND TWO NEW ZIPs
1. Close the previous Celeste process. In LiveContainer 1, install
   CelesteJITEverest-unsigned.ipa as an UPDATE of the existing Celeste JIT
   Everest guest, keeping its data container. Do not delete the guest.
   Keep Launch with JIT OFF, launch script blank, and Settings > Fixes >
   Fix File Picker ON. StikDebug stays in LiveContainer 2.
2. Open build 17. Keep your installed game library and FIVE existing test ZIPs.
   Use Import test ZIPs to select ONLY these two new files from this folder:
     GravityHelper-v1.2.28.zip
     CJITGravityProbe-v1.0.0.zip
   The launcher should now show all SEVEN ZIPs ready. The other five ZIPs in
   this folder are identical recovery copies. If previous content or ZIPs are
   unexpectedly missing, export to Results before repairing or reimporting.
3. Tap Enable via LiveContainer 2. Wait for the fresh script to finish and
   detach; this stage prepares more pages and may take longer. Return to the
   SAME Celeste process, then tap Run Celeste + Everest. Keep the app open
   while it checks content and loads the helpers.

GRAVITY ROOM
4. At the title, tap Gravity map in the native overlay. Let Madeline's short
   automatic walk finish. LUA should say waiting for Home / return.
5. Walk right into the red outlined zone. Gravity should flip upwards.
   Move under the wide wooden ceiling platform and stand on its UNDERSIDE
   for about five seconds, until PLATFORM says PASS. Try moving and jumping.
6. Continue right past the red zone. Gravity should return to normal and
   Madeline should land on the floor; wait two seconds. GRAVITY should now
   say PASS. If necessary walk left back into the zone to retry the platform.
7. Go Home for 30 seconds, then return to the SAME game. The retained Lua
   coroutine should finish and LUA should change to PASS. Jump again after
   returning, then wait about ten seconds. LUA, GRAVITY and PLATFORM must pass.
8. Tap Finish. Wait for PASS and another ten seconds, then Export diagnostics:
   Files > iCloud Drive > Celeste JIT Tests > 0.9.0-build-17 > Results
   Tell me whether gravity, the ceiling platform, sound and controls looked
   correct. Keep the saves and imported files for the next update test.

IF SOMETHING FAILS
If it crashes, reopen and EXPORT FIRST before enabling JIT again. Save to
Results and tell me the last visible step. Do not delete saves or reimport
game files to repair a crash. Export includes previous sessions and console.

SCRIPT
Enable supplies the current script automatically. The included .js is a
TEMPLATE; do not run it unchanged. If a manual route is needed, use Export
session script inside this process and import that exact file into StikDebug.
Build 17 uses two 128 MiB arenas. Older builds' scripts cannot prepare it.
Always use this running process's fresh script.

SCOPE
Original GravityHelper 1.2.28, LuaCutscenes 0.2.13 and MaxHelpingHand 1.40.9,
plus our diagnostic room. This is the next Strawberry Jam dependency test;
the full collection is not included. This private app still contains prepared
Celeste IL and linked iOS FMOD; public packaging is a later stage.
