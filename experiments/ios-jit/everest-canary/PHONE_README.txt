CELESTE JIT EVEREST — 0.6.0, BUILD 13

This is the first real Everest + mod ZIP test. It contains your Celeste files.
Use this private kit only on your devices. Strawberry Jam is not included.

1. Fully close the previous game process. Install CelesteJITEverest-unsigned.ipa
   in LiveContainer 1. It creates a separate Celeste JIT Everest entry.
   Keep Launch with JIT OFF and the LiveContainer script setting empty.
   Leave StikDebug in LiveContainer 2 as before.
2. Open Celeste JIT Everest. Tap Import both mod ZIPs. Select
   CJITCodeCanary-v1.0.0.zip and CJITTestMap-v1.0.0.zip from this folder.
   You can select both together or import one at a time. Do not unzip them.
   The button should say Both mod ZIPs imported. No separate game DLL needed.
3. Tap Enable via LiveContainer 2. Let the generated script finish and detach.
   This build prepares twice the previous code space, so allow it more time.
   Return to the SAME Celeste process. Do not launch a second copy.
4. Tap Run Celeste + Everest. Wait for the title, then tap Test map at the top.
   You should enter a flat room with a CODE MOD ACTIVE sign and counters.
5. Move, jump and dash for at least 20 seconds. Hook and IL counters should
   increase together when you jump. Check the picture, sound and touch controls.
6. Go Home for 30 seconds. Return to the same process, jump several more times,
   play for at least 10 seconds, then tap Finish. Wait for PASS and another
   10 seconds. Export diagnostics into this folder's Results subfolder.
7. Fully close this game process and open it again. The mod ZIPs stay imported.
   Enable JIT again using the NEW session's button/script. Run the test map.
   Its saved counter should now be greater than zero. Repeat steps 5–6 and
   export the second log too. Tell me whether the saved counter survived.

If it crashes: reopen and EXPORT FIRST, before another JIT request. Put the
log in Results and describe the last screen. Export includes previous sessions.
If a script fails, preserve its output too. Do not use a build 12 script.

The supplied .js is a TEMPLATE for reference, not a ready-to-run session script.
Normally the Enable button sends the complete script automatically. Manual
fallback: use Export session script in this running app, import that exact file
in StikDebug, then use the app's imported-script button. It is PID-specific.

Results: iCloud Drive / Celeste JIT Tests / 0.6.0-build-13 / Results
If this kit was copied to LocalSend, its adjacent Results folder also works.
