# Build 23 physical session acceptance

The owner's iPhone 15 Pro Max / iOS 26.5 export matches the delivered build23
metadata exactly. Both recorded build23 sessions finish normally: original
main-menu Quit, then modded gameplay and Quit. Each completes all eight stages,
managed-thread detachment, `graphics_bridge_pass`, native result presentation
and the five-second post-run heartbeat. No recorded JIT/managed errors or patch
rejections. See [the evidence](BUILD_23_SESSION_ACCEPTANCE_EVIDENCE.json).

The played session has 56 enabled ZIPs / 59 registered metadata identities and
14,726 frames. It visits the Beginner gym, lobby and `asteriskblue` rooms a-01
through a-10. Settings and slot 1 (56 deaths, 160,790 serialized bytes) read back;
the mod sidecar reads prior counter 320 and writes/reads 403. Touch-to-controller
activity is recorded. Closing Game.Dispose takes 7.99 seconds after gameplay
and 4.79 seconds from the title. Full Quit-to-native-result times are 9.10 and
5.88 seconds. The independent heartbeats work throughout cleanup.

The export contains two build23 processes, followed by separate historical
build22 journals. There is no third process reloading the latest counter 403.
Existing prior progress loads successfully; carry the new-save reload and
background/resume check into build24 instead of asserting they already happened.
Keyboard and controller-disconnect transitions were not recorded. No watchdog
termination or urgent new shutdown failure is supported by this evidence.

Proceed with the isolated Metal backbuffer increment in
`experiments/ios-jit/launcher-backbuffer`, version 0.12.1 (24). Build23 is the
complete-shutdown fallback; preserve all its sources/artifacts and every Results
folder. The AOT checkout and all original game/mod files remain read-only.
No commits or remote writes.
