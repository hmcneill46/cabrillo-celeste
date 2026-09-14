# Build25 physical test

Use [README-FIRST.txt](README-FIRST.txt) in the delivered folder (the source
copy is `PHONE_README.txt`). The unsigned IPA updates the existing LiveContainer
slot 1 app and retains `GameLibrary/v1` and `Profiles/sj-first-play`.

The versioned handoff is `iCloud Drive/Celeste JIT Tests/0.13.0-build-25/`.
Keep Launch with JIT off, its saved script blank, Fix File Picker on, and
StikDebug in LiveContainer 2. The launcher creates the current PID/nonce script;
use its Enable button each fresh process. The included JS is only the template.

Test missing-dependency alerts and an enable-existing plan, then the Updates
page, individual/batch review, cancel/retry when practical, actual play, normal
Quit and fresh-process save reload. Export both sessions to `Results`.
The UI explicitly blocks updates requiring a newer app runtime. Downloads do
not start merely by checking availability or opening the review screen.

The exact local IPA, executable/dSYM identity and inherited runtime hashes are
recorded in `TEST-IDENTITY.json`. Phone acceptance is pending until the exported
build25 sessions are inspected. Build24 is the accepted fallback.
