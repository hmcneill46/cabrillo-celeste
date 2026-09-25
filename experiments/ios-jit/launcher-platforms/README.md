# Build35: iOS15, JIT routes and high refresh

Version0.19.0, `launcher-platforms-20260925-35`. Packaged sources are frozen.

This lane keeps build34’s saves/precision repairs and build32’s first-frame gate.
Seven native libraries are explicitly rebuilt for iOS15; nine compatible archives
stay pinned. `NativePayload.json` and `ManagedPayload.json` identify both derived
receipts. Only the managed adapter changes relative34, moving touch polling to
the actual game input update so extra render frames do not consume tap edges.

Use `tools/build_platforms.py`, `tools/verify_platforms.py`, and
[the build report](../../../docs/ios-jit/PLATFORMS_BUILD_35.md). No historical
UUID or package metadata restoration is used. Device acceptance is separate.
