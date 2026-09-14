CELESTE JIT EVEREST — 0.10.0, BUILD 19
First original Strawberry Jam test: Beginner lobby and Bing.

UPDATE — KEEP YOUR EXISTING CELESTE FILES
1. Close the old Celeste process. Install CelesteJITEverest-unsigned.ipa as an
   UPDATE of the existing Celeste JIT Everest guest in LiveContainer 1.
   Keep its data container. Launch with JIT OFF, stored script blank,
   Settings > Fixes > Fix File Picker ON. StikDebug stays in LiveContainer 2.
2. Open build 19. Your previously imported Celeste game library is reused;
   no game download or reimport is needed. This test has a NEW Strawberry Jam
   profile, so a fresh save is expected. The old helper-test saves/ZIPs remain.
3. On Wi-Fi tap Download missing SJ mods. It downloads the original pinned
   Strawberry Jam release and all dependencies: 52 ZIPs, about 1.24 GB total.
   Keep the app open until 53/53 are ready (52 originals + our tiny test mod).
   Allow a few GB of free phone storage for ZIPs, caches and temporary files.
   Cancel keeps completed verified ZIPs. Tap Download again to continue;
   the interrupted ZIP restarts. No cellular download is enabled.
   You only need this download once. Future updates reuse these files.
4. Tap Enable via LiveContainer 2. Let this process's FRESH script finish
   and detach. Return to the SAME Celeste process. Native checks must pass.
   This version has a larger JIT arena; do not reuse a build 18 script.
5. Tap Run Celeste + Everest. Keep the app open while the full pack loads.
   The first load can take a while; do not repeatedly tap Run or relaunch.

PLAY TEST
6. At the title, tap SJ lobby in the native overlay. Explore the original
   Beginner lobby for at least 15 seconds. Move, jump and listen for music.
7. Tap Bing in the overlay. This is a direct test shortcut into the original
   Bing map. Play for at least 15 seconds; try jumping/dashing and hear music.
   You do not need to complete the map. Natural lobby-door progression is a
   later test; use the buttons for this first reproducible run.
8. While in Bing, go Home for 30 seconds, return to the SAME game and jump
   again. Play at least another ten seconds, then tap Finish.
9. Wait for PASS and another ten seconds. Export diagnostics using Save to
   Files into iCloud Drive > Celeste JIT Tests > 0.10.0-build-19 > Results.
   Tell me whether maps, controls and audio looked/sounded correct. Keep saves
   and downloaded ZIPs for the next update/retention test.

IF SOMETHING FAILS
Export partial results even if checks do not pass. After a crash, reopen and
EXPORT FIRST before enabling JIT again. Save in build 19 Results and describe
what you last saw. Do not delete saves or reimport game files to repair it.
After a download error, retry once on Wi-Fi; completed files remain. If the
same file repeatedly fails, export diagnostics so I can inspect the error.

SCRIPT
Enable forwards the script automatically. The included .js is a TEMPLATE;
do not run it unchanged. For a manual route use Export session script in
this process, then import that exact file into StikDebug. Requests contain
this process's PID, nonce and mailbox. Build 19 prepares two 256 MiB arenas.

SCOPE
The full original pinned pack loads on the Mac under Mono JIT. iPhone full-SJ
compatibility, memory use and gameplay are what this test will establish.
This private small IPA still includes prepared Celeste IL and linked iOS
FMOD. It is not yet the public original-game-IL importer/distribution build.
