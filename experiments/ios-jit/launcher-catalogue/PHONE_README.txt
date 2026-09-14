CELESTE — NATIVE MOD BROWSER
0.15.0 (build 28) · Everest 1.6531.0

Files: iCloud Drive → Celeste JIT Tests → 0.15.0-build-28

INSTALL
1. Download CelesteJITEverest-unsigned.ipa from this folder.
2. Update the existing Celeste app in LiveContainer slot 1. Keep its data.
   Keep Launch with JIT OFF, its saved JIT script blank, and Fix File Picker ON.
   StikDebug stays in LiveContainer slot 2.
3. Fully close Celeste's previous process and reopen. Settings should say
   0.15.0 (28), with Everest 1.6531.0. No game/mod reimports are needed.

TEST THE BROWSER FIRST — NO JIT NEEDED
4. Open Mods → Browse. Scroll the cards and load another page. Try Newest,
   Most downloaded and Most liked. Open Categories → Maps → Standalone.
   Check portrait/landscape browsing and that pictures and text fit.
5. Search for “Memorial Helper”. Search shows up to 20 closest name matches
   across all categories. This helper is on a Tools page but can be installed
   because its archive is an actual Everest mod. Open its details and review.
   If already installed, it should reuse that ZIP. If disabled, enabling it
   is shown for review. No duplicate download should be necessary.
6. For a small real download, search “Cateline” and open Cateline. Its current
   file is cateline-010.zip, version 0.1.0, about 17 KB. Review installation,
   then Download and install if the plan is clear. Check the report lists the
   actual installed version and enabled result. Existing saves and compatible
   mods should remain. If already installed, reuse is expected.
7. Open a page with several files, such as the 2020 Spring Community Collab.
   Choose files should jump to the choices. Separate map/audio/extra files
   are listed with their sizes. Select only what you want and review the plan;
   you can tap Done without downloading. Nothing installs before confirmation.
8. Optional offline check: return to Browse, temporarily turn Wi-Fi/mobile data
   off, and tap the refresh arrow. Previously visited results should remain with
   an offline message. An unvisited search should show an error with Retry.
   Play/Installed should remain usable. Turn networking back on afterwards.

PLAY
9. Return to Play. Tap Enable via LiveContainer 2, complete StikDebug's fresh
   PID-specific inline request, and return to the same running Celeste app.
   No new standalone script is needed. Export Script remains a fallback and
   produces the correct request for this process; do not reuse an older one.
10. Run Celeste with your existing mods. Enter your usual map and play briefly.
    Check controls, audio and saving. Cateline adds cat ears and a tail; check
    its appearance if enabled. You may disable it before a later session.
11. Use the game's normal main-menu Quit to return to the launcher. In-map
    Save and Quit returns to the game menu first. Close and relaunch the app
    before another game session; each process needs its own JIT request.

RESULTS
12. Settings → Export diagnostics → save to this folder's Results subfolder.
    Include an export after browsing/installing and one after playing/quitting.
    On a crash, reopen and export before starting another game. Screenshots of
    any awkward layout or unexpected message are also useful in Results.

The browser uses the Celeste catalogue used by Olympus and live GameBanana
details. Search and sorted browsing have different scopes, shown on screen.
Only indexed compatible files can be installed directly. Previous/unindexed
files are linked on GameBanana for manual ZIP import. All ZIPs are verified
before installation. Runtime requirements and iOS compatibility pins still apply.

This is a private test IPA. Keep build27 as the accepted fallback. Do not delete
the app's data or prior Results. No public distribution is authorized yet.
