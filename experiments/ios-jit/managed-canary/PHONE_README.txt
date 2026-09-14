CELESTE JIT CANARY — 0.2.2 (BUILD 6)

This tests the managed runtime needed for Celeste + Everest. It is not the game yet.
Build 5 passed all eight tests, then crashed during worker cleanup. Your steps
were correct. Build 6 fixes cleanup and logs the return to the launcher.

1. Download the IPA and Canary-v0.2.2.dll from this folder.
2. Fully close the old canary. Update its IPA in LiveContainer 1, keeping app data.
   Select Celeste JIT Canary.
   Launch with JIT: OFF. JIT Launch Script: EMPTY.
3. Have StikDebug ready in LiveContainer 2 with its usual VPN/connection.
4. In the canary, tap "1. Import Canary DLL" and select Canary-v0.2.2.dll.
5. Tap "2. Enable via LiveContainer 2". Complete StikDebug's request.
   Return to the same running canary. Native memory checks start automatically.
6. At "NATIVE PASS · READY FOR MONO", tap "3. Run managed JIT test".
   Scroll down if needed. Keep the app in the foreground.
7. At "PASS · MANAGED JIT", wait 10 seconds in the foreground. Switch to Files
   or the Home Screen for about 20 seconds, then return to the same canary.
   Do not close/relaunch it or enable JIT again.
8. Tap "Export diagnostics" even if it passes. Send the JSON to Codex, or save it
   in this folder's Results subfolder as before.

If it crashes: reopen and export diagnostics BEFORE enabling JIT again.
Previous sessions and native console logs are included. Do not delete app data.
If it hangs: allow about a minute, then close/reopen and export.

The app sends its own matching script to StikDebug. No manual script setup is
normally needed. Do NOT reuse a script from the older native probe.

Expected finish: "PASS · MANAGED JIT". A failure/crash is also useful evidence.
Read INSTALL.md for manual-script fallback and further details.
