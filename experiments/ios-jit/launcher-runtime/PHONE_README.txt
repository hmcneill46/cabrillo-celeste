CELESTE — PRIVATE TEST BUILD 27
Version 0.14.0 (27) · Everest 1.6531.0

UPDATE THE EXISTING APP
1. Files → iCloud Drive → Celeste JIT Tests → 0.14.0-build-27.
   Download CelesteJITEverest-unsigned.ipa and import it into LiveContainer 1.
   Update the existing Celeste app, retaining its data. No game/mod reimport.
2. Keep Launch with JIT OFF, the saved script blank, and Fix File Picker ON.
   StikDebug stays in LiveContainer 2. Keep build26 as your fallback.

TEST THE RUNTIME UPDATE AND REPORT
3. Open Settings. It should show 0.14.0 (27) and Everest 1.6531.0.
4. Open Mods → Updates. If cached results appear, ExtendedVariantMode 0.51.0
   and MaxHelpingHand 1.40.10 should now be eligible. Tap Check for updates
   if needed. Availability checks never install anything automatically.
5. Review and update these two helpers. The report should show:
     ExtendedVariantMode 0.50.5 → 0.51.0
     MaxHelpingHand 1.40.9 → 1.40.10
   Other legitimate updates may be listed. Review only the ones you intend.
   Older archives remain disabled; disabled mod choices remain disabled.
6. Reopen the installation report and Export diagnostics to this folder's
   Results subfolder. Installs, reports and Export do not need JIT.

PLAY AND SAVE
7. Generate the new inline request and tap Enable via LiveContainer 2.
   Wait for StikDebug's successful completion and return to Celeste.
   Run the native checks, then Run Celeste. Each fresh process needs a new
   PID/nonce request. The included JS file is only a reference template;
   use the app-generated inline request, not an old saved script.
8. Continue the existing Spring save (Starjump, if that is still your save).
   Check movement, jump, dash, music and progress. Play for a few minutes.
   Background the app for about 30 seconds, return and move/jump again.
9. Use the normal game menus to save and return to the main menu, then Quit
   to return to the native launcher. Wait for the session result, then ten
   seconds more. Export diagnostics into Results with a distinct filename.
10. Close/relaunch Celeste, enable JIT with a fresh request, and run again.
    Confirm the latest save/progress survives. Quit and export this second
    session too. Do not overwrite the first export.

If anything fails, Export before trying another run. The logs include runtime
identity, registered mod versions, installation changes, map/room and shutdown.
No need to repeat the exact map name separately unless it differs from the logs.

Your game files, mods and complete profile stay in the existing data container.
One game session per process remains the current limit. This build does not add
browsing, a new loading screen, backups or the touch layout editor yet.
The IPA is still a private development package with prepared game IL and FMOD.
