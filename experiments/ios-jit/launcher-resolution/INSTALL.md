# Build26 physical test

Use `README-FIRST.txt` in the kit (source: [PHONE_README.txt](PHONE_README.txt)).
The unsigned IPA updates the existing LiveContainer slot 1 app, retaining
`GameLibrary/v1`, `Profiles/sj-first-play`, saves and original ZIPs.

Handoff: `iCloud Drive/Celeste JIT Tests/0.13.1-build-26/`.
Keep Launch with JIT off, saved script blank, Fix File Picker on; StikDebug
stays in LiveContainer 2. Enable JIT with the new inline PID/nonce request each
process. The included JS is a reference template. Installs and reports need no JIT.

Test Spring dependency review/install, cancellation and retained downloads when
practical, precise blocked update rows and actual old/new update reports. Do not
wipe a working profile: the host tests separately cover a fresh original map.
Export after each report you want inspected, because the next installation
replaces the last-attempt report. Committed transaction receipts also persist.
Then check gameplay, background/resume, normal Quit and fresh-process save reload.

The exact IPA, executable/dSYM identity and unchanged runtime hashes are in
`TEST-IDENTITY.json`. Physical build26 acceptance requires the exported sessions;
local validation alone is not phone acceptance. Build24 remains the fallback.
