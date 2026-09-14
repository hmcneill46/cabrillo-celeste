# Build 20 physical test

Follow [PHONE_README.txt](PHONE_README.txt). Update LiveContainer 1 in place,
retain the existing data container and `Profiles/sj-first-play`. Keep StikDebug
in LiveContainer 2, Launch with JIT off, stored script blank, Fix File Picker on.

The app supplies the process-specific StikDebug script. For manual recovery,
Settings → Export current JIT script gives the PID/nonce-bound file. Import it
into the running StikDebug, target the PID shown in Settings, complete the script
and detach, then return to the same running game app. The script template alone
cannot be used. A fresh process always needs a fresh script.

Questions for this test: native portrait launcher/landscape game transition;
original ZIP import and persisted selection; dependency blocking; normal SJ menu
and lobby progression; save reload, controls/music, frame overlay and resume.
Save the export in `0.11.0-build-20/Results`; after a crash export before a retry.

Host and simulator evidence is distinct from physical ARM64/LiveContainer
acceptance. A directory populated on the Mac is not proof of iCloud upload or
phone download; inspect the delivery receipt and report actual observations.
