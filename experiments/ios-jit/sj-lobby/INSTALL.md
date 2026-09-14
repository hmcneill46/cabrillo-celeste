# Build 19 physical test

Follow [README-FIRST.txt](README-FIRST.txt) in the delivered kit (source:
[PHONE_README.txt](PHONE_README.txt)). Update the existing LiveContainer 1 guest,
keep its data, and keep Launch with JIT OFF, saved script blank and Fix File
Picker ON. StikDebug remains in LiveContainer 2.

The shared Celeste library is reused. The new `sj-first-play` profile gets all
52 original pinned Strawberry Jam ZIPs through the explicit Wi-Fi download
button, plus the bundled diagnostic mod. Expect about 1.24 GB of mod downloads
once and a fresh SJ save; earlier profiles remain intact. The iCloud kit
contains only the small unsigned app, template and instructions.

After 53/53 ZIPs are ready, enable a fresh process script (two 256 MiB arenas),
wait for native checks, Run Celeste, then use the SJ lobby and Bing buttons.
Play each for 15 seconds with music. Home 30 seconds, return and jump, play ten
seconds, Finish, wait ten more seconds and Export to
`iCloud Drive/Celeste JIT Tests/0.10.0-build-19/Results`.

After a crash export first, before another JIT request. Keep existing files.
