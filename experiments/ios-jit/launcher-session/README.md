# Native Celeste JIT launcher — build 23

This isolated lane adds required `CelesteIOS.dll` (module 1.0.0, host ABI 1),
normal game Quit, queued-save-aware shutdown and shared touch glyphs. It retains
build22's original game/mod inputs, MonoMod literal correction, FNA extension,
Mono archives, renderer, profile paths and JIT protocol. Delivered lanes are
immutable. The active AOT checkout is read-only.

Read [the report](../../../docs/ios-jit/SESSION_FOUNDATION_BUILD_23.md),
[the roadmap](../../../docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md),
[AGENTS.md](../../../AGENTS.md), and [phone instructions](PHONE_README.txt).

The host bootstraps the support module after vanilla registration and before
user mods. Its exact YAML identity cannot be supplied by a user ZIP. The module
hooks Game.Exit to issue a versioned native command, preserving frames until
Everest's queued save coroutine settles. Stop returns 3 to request another save
frame, 4 to yield between teardown stages, and 1/2 for complete/incomplete.
Native return requires all stages plus successful thread detach and no errors.
Diagnostic event names never issue commands. No process kill or timeout is used.

Native UI owns closing presentation and exports. A background heartbeat reads
only atomic native counters, so a long managed callback leaves inspectable
progress. Game/graphics disposal stays on its required thread. One game per
process remains the contract. Mod loading progress, dependency downloads, profile
backup UI and the touch editor are separate roadmap increments.

Use Xcode 26.6 via DEVELOPER_DIR. Build `build_managed.py`, native dependencies
with `build_native.py --target host|ios|simulator`, and
`tests/build_example_mod.py`. Test the production mod parser, native services,
actual Mono/Metal title Quit, repeated Quit during queued saves, full-SJ play and
fresh-process save readback; render actual support glyphs in the host test. Build
device and simulator packages, run smoke/XCUITest, then `tests/check_package.py`
and the unchanged JIT protocol checks. The package gate binds exact app inputs,
new tests and inherited unchanged compatibility evidence. Freeze the source and
artifact receipts before delivery; never regenerate a delivered kit in place.

Private inputs and outputs remain ignored. No public distribution, commit or
push is authorized. Assets are owner-imported; prepared game IL and linked FMOD
remain private development limitations. Arbitrary mod compatibility is still
per-mod. The known Metal backbuffer-read issue is a separate next backend fix.
