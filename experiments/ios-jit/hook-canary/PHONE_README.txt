CELESTE HOOK CANARY — 0.3.2 (BUILD 9)

This tests real MonoMod hooks needed by Everest. Celeste gameplay comes next
once this gate passes. There are two test phases in the SAME running process.

Build 8 ran real Hook and ILHook tests, then exhausted the probe's JIT memory.
Build 9 increases the reserved code budget from 8 MiB to 32 MiB. Your steps
were correct. The test DLL is unchanged; import the included copy again.
The app supplies a NEW matching StikDebug script automatically.

Files: iCloud Drive > Celeste JIT Tests > 0.3.2-build-9
Download the IPA and HookCanary-v0.3.0.dll before starting.

1. Fully close the old canary. Update its IPA in LiveContainer 1, keeping app data.
   The new name is Celeste Hook Canary (it replaces the managed canary).
   Launch with JIT: OFF. JIT Launch Script: EMPTY.
2. Have StikDebug ready in LiveContainer 2 with its usual VPN/connection.
3. Open the canary. Tap "1. Import HookCanary DLL" and select
   HookCanary-v0.3.0.dll from this build 9 folder.
4. Tap "2. Enable via LiveContainer 2". Complete StikDebug's request.
   Return to the same running canary. Native checks run automatically.
5. At "NATIVE PASS · READY FOR MONO", tap "3. Run hook tests".
   Scroll down if needed. Keep the app in the foreground; allow up to 2 minutes.
6. At "HOOKS PASS · BACKGROUND NEXT", wait here 10 seconds.
   Go to the Home Screen for at least 20 seconds (30 is fine), then return
   to the SAME running canary. Do not close it or enable JIT again.
7. At "READY · RUN RESUME TESTS", tap "4. Run resume tests".
   This checks retained hooks and creates fresh hooks after returning.
8. At "PASS · HOOKS + RESUME", wait 10 seconds. Tap "Export diagnostics".
   Choose Save to Files > iCloud Drive > Celeste JIT Tests > 0.3.2-build-9 > Results.
   Let me know when the JSON has saved there, even if everything passes.

If it stops: export diagnostics to Results; note the visible status.
If it crashes: reopen and EXPORT BEFORE enabling JIT again. Previous sessions
and native console logs are included. Keep the app data.
If it hangs: allow 2 minutes, then close/reopen and export.
If the background test was too short: go Home for 30 seconds and return again.

The app supplies the exact fresh StikDebug script. No manual script setup is
normally needed. The separate TEMPLATE.js is reference only, not runnable.
Read INSTALL.md if the usual route fails.
