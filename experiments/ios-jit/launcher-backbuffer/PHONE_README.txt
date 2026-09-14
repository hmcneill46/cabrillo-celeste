CELESTE JIT · 0.12.1 (BUILD 24)
Metal backbuffer repair — automatic graphics checks, existing game and mods

Install this as an UPDATE in LiveContainer 1, keeping the existing data container.
StikDebug stays in LiveContainer 2. No game or mod downloads are needed.
Build 23 is the fallback. This test keeps its normal Quit and touch support.

SETUP
1. Fully close the previous Celeste process. Install CelesteJITEverest-unsigned.ipa
   from iCloud Drive > Celeste JIT Tests > 0.12.1-build-24.
2. LC1: Launch with JIT OFF; saved script blank; Fix File Picker ON.
3. Confirm Settings shows 0.12.1 (24), iOS support 1.0.0 / ABI 1.
   Keep your existing working mod set and the same save. Leave incomplete imports
   disabled. Keep the Strawberry Jam regression switch OFF for normal play.
4. Enable via LiveContainer 2. Run the NEW inline StikDebug request for this
   process, wait for detachment, then return to the SAME app process in LC1.
   Do not use an old exported script or the TEMPLATE file. Run Celeste.

TEST A — EXISTING SAVE, GRAPHICS AND RESUME
5. Graphics checks now run automatically during startup. There is no additional
   test button. Continue through the normal game menus and open your existing
   save. Check that the progress from your last build 23 session is present.
6. Play a familiar modded map for at least 30 seconds. Check that graphics,
   controls, prompts and music look/sound normal. Note a change you can recognize
   later: progress, a collectible, or the death count.
7. Go Home for 30 seconds, return, and continue playing for at least 15 seconds.
   The log records another backbuffer read after resume automatically.
8. Use Celeste's Save and Quit to leave the map, then main-menu Quit/Exit to
   return to the native launcher. Wait for SESSION SAVED and another 10 seconds.
9. Settings > Export diagnostics > Save to Files > iCloud Drive >
   Celeste JIT Tests > 0.12.1-build-24 > Results. Keep the unique filename.

TEST B — FRESH-PROCESS SAVE RELOAD
10. Fully close and reopen the app. Enable JIT with its NEW inline request.
    Run Celeste and open the same save. Check the change you noted survived.
    Play briefly, Save and Quit, main-menu Quit/Exit, then wait 10 seconds
    at SESSION SAVED and export again to the same Results folder.
11. Tell me which map you played, whether the saved change survived, and any
    visual corruption or long pause. Both session exports are useful.

If it crashes or closes unexpectedly, reopen and export BEFORE enabling JIT.
Historical logs survive independently of Export. If shutdown seems stuck, keep
it open for a minute if possible and note the displayed stage; native heartbeats
record progress. Normal cleanup can take several seconds. No play timer or
forced timeout is introduced. Do not treat an incomplete session as saved.

There is still ONE game per process: fully close/relaunch to play again or change
code mods. No permanent Finish control is shown in normal mode. Performance
metrics are optional and do not measure GPU time. The tiny example mod remains
optional and does not need reimporting. No additional files are required.

This is a private development IPA containing prepared game IL and linked FMOD,
not a public distribution release. Original game/mod ZIPs and save data remain
on the phone; the AOT development checkout is unchanged.
