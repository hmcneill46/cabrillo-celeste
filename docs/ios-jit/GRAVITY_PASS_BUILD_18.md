# Build 18 physical acceptance — 12 September 2026

Build 18 passes on the owner's iPhone 15 Pro Max / iOS 26.5. The source and native archives, packaged 200 managed assemblies, generated script identity and installed seven ZIPs match the delivered frozen build. No reimport was needed.

The VM checker now verifies every one of the 8,192 16 KiB pages in each 128 MiB region. All 26 native checks pass, including separate writable/executable aliases and execution across both arenas. Eleven game checks pass. The debugger is detached before execution.

Original GravityHelper 1.2.28, LuaCutscenes 0.2.13 and MaxHelpingHand 1.40.9 execute in the authored gravity room. Evidence records 2,278 inverted frames, 1,613 inverted grounded frames, 1,346 ceiling-platform contacts and 2,000 normal-gravity frames after inversion. Lua begins, waits, resumes and ends once without skipping; it walks Madeline 21 pixels. The retained run survives a 33.592-second background interval and post-resume jumps. All five tracked workers finish, the main managed thread detaches, and the app remains alive after Finish.

The existing game library verifies 1,158,665,183 bytes in 1.936 seconds. Settings and slot zero survive; the mod sidecar counter advances from 23 to 36 with actual YAML readback. Export occurs 15.013 seconds after PASS. Final usage is 149,422,080 / 268,435,456 bytes in 2,358 allocations, 19,378 owned JIT completions and 1,967 patches. There are zero failed/unowned JIT methods, managed errors or patch rejections. Peak sampled physical footprint is 1,853,737,320 bytes; this is a functional test, not a performance benchmark.

The exact raw export is privately retained in `.build/ios-jit/device-evidence/2026-09-12/build-18-results/`, 72,126,895 bytes, SHA256 `1e650528718367ef51cbc6d8e714cfa4c0480426932c1f5df53aa5738be90b54`. `validate.py` verifies it against the IPA and recursive frozen snapshot and writes `validation.json`. The session is `cb6d10e2-d4b9-4b47-a5e4-f7141c8734f3`.

Next gate: the complete pinned Strawberry Jam dependency set, then its original Beginner lobby and Bing map, retaining build 18 as the accepted fallback. The full original ZIP set is 1,237,284,560 bytes, exceeding the 1 GB cloud handoff allowance. Keep those downloads on the owner device; do not upload or split the full set across cloud kits. Full SJ, other devices and public distribution remain unaccepted.
