# Build 19 physical Strawberry Jam acceptance

12 September 2026. The original pinned 52-node Strawberry Jam graph passes
on iPhone 15 Pro Max / iOS 26.5. The exact delivered IPA, 160 frozen source
inputs, 16 native libraries, 200 managed assemblies and script match. All
26 native and nine game checks pass. Independent reconstruction of complete
VM trace hashes confirms all 16,384 pages of each 256 MiB region and aliases.

The original Beginner lobby records 4,807 frames and Bing 11,266 frames, with
both original music events playing and original Femto particle checks passing.
The game survives 33.492 seconds in the background, followed by 2,962 level
frames. All 11 tracked workers finish and the main managed thread detaches.
The new SJ profile saves slot 0 with 29 deaths and mod counter 0 → 139, with
actual readback. It remains alive after Finish; export follows PASS by 16.124
seconds. Settings and this SJ slot were new; a fresh-process SJ save reload and
normal lobby-door progression have not yet been accepted.

Final JIT reservation is 211,156,992 / 536,870,912 bytes, in 12,642 allocations;
36,901 owned JIT completions and 12,492 patches have zero runtime errors.
The peak sampled physical footprint is 4,334,358,952 bytes. Maximum frame gap
is 9.428 seconds, including loading; this is not an in-game benchmark. The
120,096-event current trace and 126 MB export identify diagnostic overhead
worth reducing before wider use; do not attribute all footprint to logging.

All 53 ZIPs and the owner-imported 1,158,665,183-byte content library survive
into this process without reimport. Verification takes 1.953 seconds. The
exact raw export is in the private build-19-results evidence folder, SHA256
`fd2fcb8f053af4f752fc18364d84fa63aee51c156fa6c79b3bd578b8f969e606`.
`validate.py` and [the evidence](STRAWBERRY_JAM_PASS_BUILD_19_EVIDENCE.json)
record the checks. Keep build 19 as the accepted fallback.

Next: a persistent, dependency-aware native mod catalogue, ordinary play
sessions, portrait SwiftUI launcher and bounded diagnostics/performance
metrics. Keep the accepted runtime and private preparation inputs immutable.
Original-game IL preparation on the phone and FMOD redistribution permission
remain separate public-release gates. One successful pack/two maps does not
establish compatibility with every map or arbitrary native mod library.
