# Build 22 physical test

Read [the complete phone guide](PHONE_README.txt). Update the existing app in
LiveContainer 1 without replacing its data container. StikDebug stays in slot 2.
Use a fresh inline JIT request, keep the original accepted mod set, and test the
normal Beginner-lobby entrance to **Paint (mosscairn)**, its intro and subsequent
play, 30-second background/resume, Finish, then a fresh-process save reload.

This build corrects MonoMod constant-field access that stopped build 21 during
EeveeHelper room setup. The earlier FNA extension is retained. No timer is added,
no game/mod reimport is needed, and existing profile paths remain in use.

Save each diagnostic export to `0.11.2-build-22/Results`. If a session fails,
export before retrying; after a process crash export before enabling JIT again.
The template script cannot be reused as a process-specific request.

This is a private development kit with prepared game IL and FMOD. It has not
received physical build22 acceptance. Desktop/simulator checks are separate.
