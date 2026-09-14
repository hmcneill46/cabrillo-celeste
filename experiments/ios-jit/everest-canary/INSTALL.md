# Build 13 physical Everest test

Follow **README-FIRST.txt** in the delivered folder. Target: iPhone 15 Pro Max,
iOS 26.5; game in LiveContainer 1, StikDebug in LiveContainer 2. The unsigned
IPA is signed by your existing installation arrangement. Xcode is not needed
on the phone. Keep LiveContainer's Launch with JIT off and script blank.

This private app includes the owner's original Celeste 1.4.0.0 assets and
Everest-prepared game IL, Mono 8.0.28, FNA/Metal and native FMOD 1.10.09. It
accepts the two supplied ZIPs by exact hash. This is a bounded integration
test, not the public game-file importer or a general mod manager.

The new guest bundle is `io.github.hmcneill46.celeste.everest.jit.everest`.
Its private profile is `Documents/Profiles/everest-jit-canary/`; `Mods/` retains
original ZIPs, and `Saves/` retains game and complete Everest sidecars. The
accepted vanilla/AOT apps and build 12 profile remain separate.

Expected evidence: real Everest module registration and assembly context,
map loaded from ZIP, custom entity rendering, On/IL jump hooks including after
resume, native Lua calling managed C#, audio, movement, normal game and mod
saves, clean stop/detach, and saved counter reload in a fresh process.

Use **Test map** after the title, play/jump 20 seconds, Home 30 seconds, return
and jump/play 10 seconds, Finish, wait 10 seconds and export. Repeat in a fresh
process with a fresh JIT request to verify the saved counter. Both logs belong
in `iCloud Drive/Celeste JIT Tests/0.6.0-build-13/Results/` (or the adjacent
LocalSend Results folder). Report visible rendering, sound, controls and the
saved number as well as PASS. On failure export before enabling JIT again.

There are now two **32 MiB** code arenas (64 MiB total). The native executable
and supplied template use identical geometry. Old scripts are incompatible.
The app sends a fresh PID/nonce-bound script automatically through
`livecontainer2://open-url`. The reference template cannot run on its own;
manual use requires **Export session script** from the current process. Never
attach Xcode while StikDebug is attached. Every game run requires a fresh
process; runtime restart/mod replacement during gameplay is deliberately absent.

Strawberry Jam and its helper/LuaCutscenes closure are subsequent tests. A PASS
here does not establish arbitrary native-plugin support, sustained performance,
older-device capacity, controller play or public redistribution rights.
