CELESTE JIT · 0.12.0 (BUILD 23)
Normal Quit, required iOS support, and touch prompts

Install this as an UPDATE in LiveContainer 1, keeping the existing data container.
StikDebug stays in LiveContainer 2. Your game ZIP, mods and saves stay installed.
No game or mod download is needed for this test.

SETUP
1. Fully close the old Celeste process, then install CelesteJITEverest-unsigned.ipa.
2. LC1: Launch with JIT OFF; saved script blank; Fix File Picker ON.
3. Check Settings: version 0.12.0 (23), iOS support 1.0.0 (ABI 1).
   Keep the accepted working mod set. Leave incomplete imports disabled.
   Strawberry Jam regression test must be OFF. Turn Performance overlay OFF
   to check that the normal game has no permanent Finish panel.
4. Enable via LiveContainer 2. Run the NEW inline StikDebug request, wait for
   detachment, then return to the SAME Celeste process in LC1. Never reuse an
   old script, PID or nonce. Run Celeste.

TEST A — QUIT FROM THE MAIN MENU
5. Check that confirm/back prompts use the touch jump/dash artwork where those
   actions have touch bindings. Open the main menu and select Quit/Exit.
   The usual game fade should lead to a temporary closing screen, then the
   native launcher should say SESSION SAVED. There is no shutdown timeout.
6. Wait 10 seconds at the launcher, then Settings > Export diagnostics >
   Save to Files > iCloud Drive > Celeste JIT Tests > 0.12.0-build-23 > Results.
   Keep each export; it has a unique session identifier.

TEST B — PLAY, SAVE, QUIT AND REOPEN
7. Fully close the app and relaunch; enable JIT using the new inline request.
   Run Celeste, select your existing save, and play a familiar working map.
   Change something easy to recognize (progress, a collectible, or death count).
   Check movement, jump, dash, grab, pause, menus and music.
8. If you have a controller handy: press a controller button and check its
   normal glyphs/hidden touch controls, then touch the screen to switch back.
   An idle connected controller should not repeatedly take the prompts back.
   A physical keyboard can also be checked if available; neither is required.
9. Background for 30 seconds, return and continue for at least 15 seconds.
10. Use Celeste's ordinary Save and Quit to leave the map, then the main-menu
    Quit/Exit to close the game. Wait for SESSION SAVED and 10 seconds, then
    export this session to the same Results folder.
11. Close and relaunch, enable JIT again, and check the same save through the
    normal menus. Check the progress you noted survived. Quit and export again.
    Tell me the map, what persisted, and any prompt or closing-screen issue.

If closing takes unusually long, keep the app open for a minute if possible
and note the stage shown. A background journal records progress independently
of the game loop. It will not kill the session. If you have to force-close,
reopen and export BEFORE enabling JIT; the previous session is kept in history.
A failed session must not be treated as successfully saved.

Quit now replaces the permanent Finish button during normal play. Save and Quit
inside a map still has Celeste's usual meaning: leave the map. The main-menu
Quit/Exit returns to the launcher. There is still ONE game per process: close
and relaunch the app to play again or change code mods. No play-session timer.

Keep build 19 as fallback. Historical Results are preserved. The TEMPLATE script
is for reference, not a reusable JIT request. The small example ZIP is optional
and does not need reimporting. This is a private development IPA containing
prepared game IL and native FMOD; it is not a public distribution build.
