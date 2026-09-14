CELESTE JIT GAME — 0.5.0 (12)
Private iPhone test. This is real Celeste; Everest/mod ZIPs are not enabled yet.
Everything needed is supplied here. You do not need to download Celeste again.

1. Download the IPA and CelesteJITGame-v0.5.0.dll from this folder.
2. Install the IPA in LiveContainer 1. It is a separate app from the graphics test.
   Keep Launch with JIT OFF and the launch script empty.
   Keep StikDebug available in LiveContainer 2, as before.
3. Open Celeste JIT Game in landscape. Import CelesteJITGame-v0.5.0.dll.
4. Tap Enable via LiveContainer 2. Let its fresh script finish. Return to the
   SAME running Celeste JIT Game. Wait for the native checks to pass.
5. Tap Run Celeste. Initial loading can pause while code is compiled.
   Wait for the title screen. Check that the graphics and music look/sound right.
6. Tap Prologue in the top-right test panel. It starts a fresh Prologue session
   in this app's separate slot 0; existing test progress is retained.
7. Play for at least 20 seconds: left movement circle; blue double-arrow = jump/
   confirm; pink sprint = dash/cancel; fist = toggle grab; top-centre = pause.
   Jump several times. The Prologue does not grant dash immediately.
   The controls reuse the iOS port's touch policy/artwork; layout editing is not
   included in this build. A connected controller hides the touch overlay.
8. Go to the Home Screen for 30 seconds. Return to the SAME running game.
   Move and JUMP again, and play for at least another 10 seconds.
9. Tap Finish in the top-right panel. It waits for loading/saving to settle,
   saves and reads back the settings/save file, removes the hook and returns
   to the launcher. Wait 10 seconds, then Export diagnostics into Results here.
10. Tell me whether the picture, music/sound, movement, multi-touch jumping and
    resume worked. A PASS label cannot verify what you saw or heard.

Optional useful second check after exporting the first run:
- Close the guest normally, reopen it, import the same DLL, and enable JIT with
  a fresh script. Run Celeste again and use its ordinary title/menu save selector
  to check that slot 0 remains. Export that run too, even if stopped early.
- Do not delete the LiveContainer data container when reinstalling.

IF IT CRASHES: reopen this guest and Export diagnostics BEFORE enabling JIT
again. Save the export in this folder's Results. Note the last visible stage.
If available, include the matching iOS crash report as well.

No need to manually install the TEMPLATE.js. The app binds a fresh PID/nonce
script itself. The exported session script remains the manual fallback.
Never reuse a script from another process or attach Xcode while StikDebug is on it.

This private kit includes your owned game files and the supplied iOS FMOD
runtime. Do not redistribute it. The future public launcher will import users'
own game data; FMOD redistribution permission still needs clarification.
