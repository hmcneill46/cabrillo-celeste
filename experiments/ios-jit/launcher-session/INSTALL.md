# Build 23 physical test

Follow [the phone guide](PHONE_README.txt). Update the existing LiveContainer 1
app while preserving its data container; StikDebug remains in LiveContainer 2.
Use a fresh inline JIT request each process. No game or mod reimport is needed.

Test the original main-menu Quit without entering a save, then normal modded
play, save-and-quit, main-menu Quit, and a fresh-process save reload. Expect
SESSION SAVED only after queued saves, managed shutdown and native return pass.
Normal play has no permanent Finish panel. The separate regression mode retains
its test buttons; keep it off for this test. Touch/controller/keyboard prompts
follow recent input; only actions actually bound to touch receive touch glyphs.

Exports go to `iCloud Drive/Celeste JIT Tests/0.12.0-build-23/Results`.
After a crash or forced close, reopen and export before enabling JIT again.
A journal heartbeat records shutdown stage and runtime counters without imposing
a timeout. The template script cannot replace the fresh PID/nonce request.

This remains a private kit with prepared original game IL and native FMOD.
Mac and simulator checks do not establish physical build23 acceptance.
