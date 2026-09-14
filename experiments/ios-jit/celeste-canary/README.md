# Celeste JIT game baseline

Separate successor to the physically accepted build 11 graphics canary. Preserve
all accepted G1/G2/graphics sources, inputs and artifacts. This directory does not
build into the independent AOT checkout. No Git commits/pushes are authorized.

`managed-build.py` validates the supplied game, restores pinned ILSpy 8 on an
isolated .NET 6.0.36 tool runtime, verifies the canonical raw source hash, applies
the existing library/BCL fixes and narrow JIT-platform adaptations, then builds
untrimmed Celeste IL using the existing private .NET 8.0.422 SDK. The .NET 6 tool
is a build dependency, not the in-app runtime. All game source remains ignored.
`touch-derive.py` carries the existing Stage 24D2 logical input extension; the
actual pure touch policy and icon sources are reused without edits.

The FNA DLL and FNA3D archive are the exact accepted build 11 pair. Do not rebuild
or modify `.build/ios-jit/graphics-managed` or `graphics-native-build11` here.
FMOD comes from the owner's exact iOS 1.10.09 SDK, staged privately using the
repository's native preparation script. The one unavailable DSP CPU diagnostic
returns `ERR_UNSUPPORTED`, as in the accepted iOS port. FMOD uses CoreAudio.

`tests/check_host_graphics.py` runs real Celeste using pinned cooperative Mono 8,
FNA/Metal and the owner's desktop FMOD. Per-callback autorelease pools remain a
regression requirement. Host finger snapshots exercise the same FNA touch-slot
mapping and game controls; they are explicitly simulated input, not proof of
physical touches. Test title, Prologue, actual hooked jumping, XML save/readback,
resume and main-thread detach. The host's FMOD 1.10.20 differs from device 1.10.09.

`build.py` packages the private owner-content device kit or native launcher-only
simulator app. The simulator cannot execute this iOS Mono JIT payload. Use
`tests/simulator_smoke.py`, then `tests/check_request_protocol.py`, then
`tests/check_package.py`. Capture an exact immutable source/symbol snapshot and
verify the iCloud upload before delivering a new kit. The external DLL is bound
to BuildInfo by SHA256; mismatched builds are rejected before runtime startup.

See [product reuse/distribution](../../../docs/ios-jit/IOS_REUSE_AND_DISTRIBUTION_2026-09-11.md).
This private reconstructed game is not the final on-device original-IL Everest
patch pipeline or a publicly distributable game binary. Build 12 is pending
physical acceptance; desktop results must not be promoted to device claims.
