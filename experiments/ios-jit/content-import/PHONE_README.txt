CELESTE JIT EVEREST — 0.7.0, BUILD 14
Small app; import your game once. Private test, not a public release.

DOWNLOAD FIRST
From your itch.io Celeste purchase page, download Celeste Windows (FNA),
version 1.4.0.0: celeste-win-opengl.zip. Keep the ZIP unextracted in Files.
This original archive's 1,216 content files were verified on the Mac.
Do not choose Windows (XNA). A build 13 IPA is not required.
Allow about 3 GB free space while importing; installed content is about 1.16 GB.

FIRST TEST — UPDATE THE EXISTING GUEST
1. Finish/close the build 13 game process. In LiveContainer 1, install this
   CelesteJITEverest-unsigned.ipa as an UPDATE of the existing Celeste JIT
   Everest entry, keeping its existing data container. Do not delete that entry
   or create a fresh data container. Keep Launch with JIT OFF and script blank.
   Leave StikDebug in LiveContainer 2.
2. Open it. It should say Build 14 and Both mod ZIPs imported already.
   If the old mod ZIPs are missing, export diagnostics and stop: we need to
   inspect update retention before reimporting or replacing anything.
3. Tap Import game ZIP and select celeste-win-opengl.zip from Files. Wait for
   Game ZIP selected. This stages a copy; your original download stays intact.
4. Tap Enable via LiveContainer 2. Let the fresh script finish and detach.
   Return to the SAME Celeste process. Tap Run Celeste + Everest.
   Keep the app open while it verifies/imports the game, then wait for the title.
   Future launches use the stored game files without selecting a ZIP again.
5. Tap Test map. Check picture, sound and touch controls. The saved counter
   should retain the build 13 result (the supplied log saved 50).
   Move, jump and dash for 20 seconds. Home for 30 seconds, return and jump for
   10 seconds. Finish, wait for PASS and another 10 seconds, then export.
   Save to this folder's Results, with a name ending in first-import.json.

SECOND TEST — CONTENT AND SAVES SURVIVE AN APP UPDATE
6. Close the game process. Install this SAME small build 14 IPA again as an
   update of the SAME guest, retaining its data container. Reopen.
   It should find saved game files and both mod ZIPs. Do not import anything.
7. Enable fresh-session JIT, Run, Test map. Check the saved counter is nonzero
   and retained. Repeat step 5 and export as after-update.json in Results.
   This checks a fresh process plus an actual LiveContainer app update.

CANCEL / IMPORT FAILURE
Cancel import stops copying or verification safely. Select the original ZIP
again to retry; existing game data and saves stay intact. If an archive is
rejected, export diagnostics so I can see the specific mismatch. The original
Files download is preserved. The app deletes only its own staged ZIP after
verification, leaving the installed library for future updates.

IF IT CRASHES
Reopen and EXPORT FIRST before enabling JIT again. Put the log in Results and
report the last screen. Export includes previous-session logs. Keep any script
error output too. Never use an older PID/session script.

SCRIPT
The Enable button supplies the complete current script automatically. The .js
in this kit is only a TEMPLATE. Manual fallback: Export session script inside
this running app, import that exact script in StikDebug, then use the app's
imported-script button. It is tied to the current PID and session.

MODS / SCOPE
The two supplied small mod ZIPs are unchanged from build 13. Existing imports
should persist; the copies are for recovery or an intentional new guest.
Strawberry Jam and arbitrary mod ZIPs are a later test. This small private IPA
still includes prepared Celeste code and linked iOS FMOD. Preparing original
user-owned game code on the phone is a later step toward public distribution.

RESULTS
Files > iCloud Drive > Celeste JIT Tests > 0.7.0-build-14 > Results
Keep the original Celeste ZIP until both tests pass. No build 13 IPA extraction
is required; it remains an optional compatible Content source only.
