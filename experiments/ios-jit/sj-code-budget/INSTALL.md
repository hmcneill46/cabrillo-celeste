# Build 16 physical test

Update the existing LiveContainer 1 guest and preserve its data. Keep Launch
with JIT OFF, script blank, and Fix File Picker ON. StikDebug is in slot 2.
Game files and all five ZIPs should already be installed; no imports are needed.

Follow [PHONE_README.txt](PHONE_README.txt): enable the current process's JIT,
run Celeste, Helper map, Lua walk, moving-platform contact/carry, jumps,
Home for 30 seconds, return and jump again, both helper checks, Finish,
wait ten seconds and Export to `0.8.1-build-16/Results` in the iCloud test folder.
Export first after a crash before trying another JIT run.
