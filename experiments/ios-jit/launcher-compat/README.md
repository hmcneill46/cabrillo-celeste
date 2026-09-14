# Native Celeste JIT launcher — build 21

Build 21 adds the standard FNA `GetRenderTargetsNoAllocEXT` method to the
accepted managed FNA assembly. The original FrostHelper 1.80.1 ZIP is unchanged.
All 5,243 existing FNA method bodies, field definitions, references and resources
are preserved. The renderer and Mono archives remain the accepted build19 inputs.
The native error screen now includes the first managed error and explicit stop
origin; a failed session never claims that its latest progress was saved.

Read [the build report](../../../docs/ios-jit/FNA_GRAPHICS_BUILD_21.md), the root
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
