# Build 17 physical test

Update the existing LiveContainer 1 guest and preserve its data. Keep Launch
with JIT OFF, script blank, and Fix File Picker ON. StikDebug is in slot 2.
Keep installed Celeste content and the five old ZIPs; import only
`GravityHelper-v1.2.28.zip` and `CJITGravityProbe-v1.0.0.zip` (seven total).

Follow [PHONE_README.txt](PHONE_README.txt): enable this process's JIT,
run Celeste, Gravity map, Lua walk, red gravity zone, stand on the underside
of the ceiling platform, leave the zone for normal gravity, Home 30 seconds,
return and jump again, all three helper checks, Finish, ten-second wait and
Export to `0.9.0-build-17/Results` in the iCloud test folder.
Export first after a crash before trying another JIT run.
