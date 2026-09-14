# Build 24 physical test

Follow [the phone guide](PHONE_README.txt). Update the existing app in
LiveContainer 1 preserving its data; StikDebug remains in LiveContainer 2.
Use a fresh inline JIT request per process. No game or mod import is needed.

The backbuffer check is automatic. Run your existing modded save, play, background
for 30 seconds, resume for 15 seconds, then Save and Quit and main-menu Quit.
Wait for SESSION SAVED, wait ten seconds, and export. Repeat in a new process to
verify the saved change survived. Keep regression mode off.

Save both exports to `iCloud Drive/Celeste JIT Tests/0.12.1-build-24/Results`.
If the app crashes, export from the next launch before enabling JIT again.
Build23 is the fallback. No session timeout, hot unload or restart is added.
This remains a private prepared-IL/FMOD kit; physical build24 acceptance is pending.
