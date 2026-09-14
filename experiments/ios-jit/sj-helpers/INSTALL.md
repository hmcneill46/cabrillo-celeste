# Build 15 physical test

Follow [the phone guide](PHONE_README.txt), delivered as README-FIRST.txt.
Update the existing build 14 Everest guest in LiveContainer 1, retain its data,
keep Launch with JIT OFF/script blank and Fix File Picker ON. StikDebug stays
in LiveContainer 2. The app provides its fresh PID/nonce script automatically.

Reuse stored Celeste content and the two old canary ZIPs. Import only the new
LuaCutscenes, MaxHelpingHand and CJITSJHelpers ZIPs. In Helper map, let the real
Lua cutscene walk and wait, ride MaxHelpingHand's moving platform, then go Home
for 30 seconds, return and jump. Require LUA and PLATFORM PASS, Finish, wait
10 seconds and export into `0.8.0-build-15/Results` in the iCloud test folder.

The export must verify the build 14 → 15 update retained the content library
(`reused=True`), original canary ZIPs, settings and current save counter. The
owner intentionally deleted an older save; do not restore it or classify that
choice as loss. Stop and export before repair if retained data is missing.

A new guest can still import the owner's original itch.io Celeste Windows
(FNA) 1.4.0.0 `celeste-win-opengl.zip`; it does not need build 13 extraction.
That is a recovery/fresh-install path, not the requested update test.

The original helper ZIPs remain byte-identical to their pins; Everest performs
normal runtime relinking. GravityHelper's separate optional CelesteNet issue
is documented and excluded. Host/simulator checks are not physical acceptance.
No public distribution or commits have been authorized.
