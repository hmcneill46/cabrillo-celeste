# Native Celeste JIT launcher — build 20

Build 20 keeps the accepted build19 runtime/renderer and adds a native SwiftUI
launcher, ZIP catalogue/dependency preflight, persistent mod choices, normal play,
bounded structured diagnostics and optional callback frame metrics.

Read [the build report](../../../docs/ios-jit/LAUNCHER_BUILD_20.md), the root
[AGENTS.md](../../../AGENTS.md), and [phone instructions](PHONE_README.txt).

Build inputs are private and ignored. Use Xcode 26.6. `build_runtime.py` and
`build_mods.py` only verify read-only build19 dependencies. Do not mutate accepted
lanes. `native-dependencies.json` pins ZIPFoundation and the CYaml parser vendored
by Yams; `build_native.py` verifies pins and records source/library hashes.

Run `build_managed.py`, `tests/build_example_mod.py`, native library/service tests,
the full SJ and normal enabled/disabled host tests, simulator smoke and real UI
tests, then `build.py` and `tests/check_package.py`. The latter binds package
bytes to the accepted native archives and current test adapter. Some copied
historical tests remain references; their accepted build19 receipts are inherited
only when their implementation/input hashes are unchanged.

No public distribution, commit or push is authorized. The IPA still contains
prepared original game IL and private FMOD; owner content assets are imported
once, and original mod ZIPs remain profile-owned. Arbitrary ZIP import is not an
all-mod compatibility claim. The touched source lane and output stages are
`launcher*`; the separate AOT checkout is read-only.
