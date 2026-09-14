# Build 17: GravityHelper with LuaCutscenes and MaxHelpingHand

Build 16 passed the physical Lua/moving-platform/save/resume test. This stage
adds original GravityHelper 1.2.28 and a new CJITGravityProbe room, retaining
the existing game library, five ZIPs and save files. Import only the two new
ZIPs. Source and generated outputs for accepted builds remain unchanged.

GravityHelper's optional CelesteNet type is eagerly resolved by Mono before
its module-presence guard runs. The exact pinned ZIP receives a separate,
hash-keyed compatibility copy of Everest's relinked assembly. Only two call
sites change: type resolution occurs after checking the optional module.
Original ZIPs, optional-integration bodies and upstream caches are preserved.
The actual optional CelesteNet integration is not tested by this stage.

The accepted build 16 Mono archives are reused exactly. The new native/script
geometry is two 128 MiB arenas, 256 MiB total, sized from the measured gravity
profile with 16 KiB-page host modeling and conservative alias-allocation replay.
The phone still has to establish ARM64 code usage and physical gameplay.

Outputs use `.build/ios-jit/sj-gravity*` and
`artifacts/ios-jit/sj-gravity-20260912-17`. `build_runtime.py` only verifies the
accepted runtime; it does not rebuild or modify it. Build the managed adapter
and test ZIPs, then run the real Mono graphics, compatibility and capacity
checks before `build.py`, simulator smoke, request-protocol and package checks.

See [the phone guide](PHONE_README.txt) and
[the report](../../../docs/ios-jit/GRAVITY_HELPER_BUILD_17.md).
