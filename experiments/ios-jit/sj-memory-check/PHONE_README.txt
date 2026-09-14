CELESTE JIT EVEREST — 0.9.1, BUILD 18
Memory-check correction. No game or mod reimports needed.

Your build 17 setup was correct: all seven ZIPs were ready, and StikDebug
reported success and detached. The app stopped cleanly because its memory
checker still allowed only 4,096 entries, half the new arena. Celeste never
started. Build 18 checks the full requested range using the OS page size.

UPDATE — KEEP EVERYTHING
1. Close the previous Celeste process. In LiveContainer 1, install
   CelesteJITEverest-unsigned.ipa as an UPDATE of the existing Celeste JIT
   Everest guest, keeping its data container. Do not delete the guest.
   Keep Launch with JIT OFF, stored script blank, and Settings > Fixes >
   Fix File Picker ON. StikDebug stays in LiveContainer 2.
2. Open build 18. Your game library and all SEVEN ZIPs should be present.
   Do not import anything. ZIPs in this folder are identical recovery copies.
   If anything is unexpectedly missing, export to Results before repairing it.
3. Tap Enable via LiveContainer 2. Let this process's fresh script finish and
   detach. Return to the SAME Celeste process. Native checks should now pass;
   tap Run Celeste + Everest and keep the app open while the helpers load.

GRAVITY ROOM — SAME TEST AS BUILD 17
4. At the title, tap Gravity map in the native overlay. Let Madeline's short
   automatic walk finish. LUA should say waiting for Home / return.
5. Walk right into the red outlined zone. Gravity should flip upwards.
   Move under the wooden ceiling platform and stand on its UNDERSIDE for
   about five seconds, until PLATFORM says PASS. Try moving and jumping.
6. Continue right past the red zone. Gravity should return to normal and
   Madeline should land on the floor. Wait two seconds for GRAVITY PASS.
   If needed, walk left into the zone again to retry the ceiling platform.
7. Go Home for 30 seconds, then return to the SAME game. LUA should change to
   PASS. Jump again after returning, then wait about ten seconds. Require
   LUA, GRAVITY and PLATFORM PASS before tapping Finish.
8. Wait for the final PASS and another ten seconds, then Export diagnostics:
   Files > iCloud Drive > Celeste JIT Tests > 0.9.1-build-18 > Results
   Tell me whether gravity, the platform, controls and sound looked correct.
   Keep your saves and installed content for the next update check.

IF SOMETHING FAILS
If the app stops with an error, export diagnostics. After a crash, reopen
and EXPORT FIRST before enabling JIT again. Save to Results and tell me the
last visible step. Do not delete saves or reimport game files to repair it.

SCRIPT
Enable supplies the current script automatically. The included .js is a
TEMPLATE; do not run it unchanged. If a manual route is needed, Export session
script from this process and import that exact file into StikDebug. Geometry
is unchanged from build 17, but an old process's PID/nonce script is invalid.

SCOPE
This remains the GravityHelper/LuaCutscenes/MaxHelpingHand dependency test
for Strawberry Jam. Full Strawberry Jam is not included. The private IPA
still contains prepared Celeste IL and linked iOS FMOD.
