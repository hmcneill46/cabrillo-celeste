CABRILLO 0.16.1 / BUILD31 — LOADING SCREEN TEST

This adds real startup stages, mod-archive counts, elapsed time and Loading
details. Celeste opens when its main menu is ready. First loading after an update
can take longer while mods rebuild their caches. A large individual mod can still
pause updates; please note the displayed stage/mod if that happens.

1. In LiveContainer slot1, UPDATE the existing Celeste entry with the build31 IPA.
   Preserve its data container, game files, mods and saves. Keep build28 as fallback.
   StikDebug stays in slot2. Launch with JIT OFF, saved script blank,
   Fix File Picker ON. Close the old game process and open build31.
2. Use the app's fresh PID-specific inline JIT request as usual. Detach StikDebug
   before returning to Run. No new standalone script is needed.
3. Run your usual large enabled mod set, such as Strawberry Jam. Open and close
   Loading details while loading. Check the current stage, real counts and elapsed
   time, then the transition into the actual Celeste menu. Note long pauses,
   missing/blank screens, lost input or anything that does not fit in landscape.
4. Play briefly, check movement/jump/audio and saves, then use normal main-menu
   Quit. After native return, wait at least five seconds.
5. Close and relaunch for a second run, with a fresh JIT request. Use the same mods
   to check the warm load and saved data. Briefly background and return during
   loading to check that startup resumes and the game opens correctly. Play/Quit
   again and wait five seconds after native return.
6. Export diagnostics to this build's Results folder. ONE export after both runs
   is fine: it also includes recent previous sessions. Tell me what visually passed
   and the stage/mod for any pause. Do not repeat the accepted build28 browser tests.

If startup reports a failure, use Export diagnostics on that screen, then close
and relaunch. If the app becomes stuck, close it once and reopen the native launcher
and export before another test; the previous session's journal is retained.

PHONE LOCATION
Files > iCloud Drive > Celeste JIT Tests > 0.16.1-build-31 > Results

Build30 is a private test, not a public release or an already accepted phone build.
