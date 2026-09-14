# Build 16 physical helper acceptance

12 September 2026. The iPhone 15 Pro Max / iOS 26.5 export confirms the code
allocation correction and the bounded LuaCutscenes/MaxHelpingHand room. This
is a physical pass, with GravityHelper and the full Strawberry Jam graph still
outside this build's acceptance. The next candidate addresses GravityHelper.

The 69,499,777-byte export was copied twice-verified from build 16 Results;
SHA256 `1871374023b921ae56dbd64eb89194a24c641c1bdaf4cabf4ff60b87f34e57ec`.
Its exact embedded build matches the unsigned IPA, 200 managed assemblies,
152 frozen source inputs, 16 native libraries and the packaged script. Private
raw export, validator, console and per-session events are retained in
`.build/ios-jit/device-evidence/2026-09-12/build-16-results/`.

The current session is the successful build 16 run. Two earlier build 16
sessions stop during the handoff to StikDebug and do not provide an explicit
failure reason. Older build 15's already-diagnosed allocation crash remains in
the export history and is not counted as a new failure.

All 26 native and nine game checks pass. All five mod ZIPs were retained with
no reimport. Installed content verifies with `reused=True`: 1,158,665,183 bytes
in 1.948 seconds. Existing settings and slot zero load; the canary's persisted
counter loads at 15, then writes and reads back 23. Eight On/IL jump calls match.
The owner deliberately deleted an older save earlier; nothing was restored.

The exact original LuaCutscenes 0.2.13 and MaxHelpingHand 1.40.9 modules load in
their genuine Everest contexts. The selected SID is `CJITSJHelpers/RuntimeRoom`.
Lua records one begin/wait/resume/end, no skip, 33 pixels of walk and a coroutine
retained across the Home interval. The moving platform travels 200 pixels,
records 1,575 player contacts and carries an idle player 1,069 cumulative pixels.
There are 1,167 helper frames after resume and 2,105 rendered helper frames.

The app survives 37.159 seconds on Home, returns detached, completes all six
worker starts/ends and clears the managed main-thread attachment. Native
post-run liveness is observed at 5.185 seconds; export succeeds 15.439 seconds
after PASS. Sampled footprint peaks at 1,504,741,376 bytes. This is a bounded
scene measurement, not a full SJ or older-hardware performance result.

The runtime records 17,172 owned JIT completions, 961 executable patches and
no JIT failures, unowned JIT, managed errors or patch rejections. Total code
reservations finish at 58,408,960 / 134,217,728 bytes. Of 964 allocations, 863
are now 64 KiB; larger requests are still allowed. Build 15 exhausted its pool
before the title. This run physically confirms the smaller-chunk correction.

Build 16's native logger folded `sj_` and `mono_` names into
`graphics_fixture_message`. The payloads survive and the validator checks their
exact helper identities and counters against the pinned adapter logic. The
next build should retain those event names directly for easier future review.

Proceed to GravityHelper's optional CelesteNet type-loading correction and a
real gravity/ceiling-platform room with Lua and MaxHelpingHand. Do not infer
full Strawberry Jam support from these two helpers: the locked graph has 52
nodes. Preserve accepted build 16 source, artifacts, symbols and runtime.
