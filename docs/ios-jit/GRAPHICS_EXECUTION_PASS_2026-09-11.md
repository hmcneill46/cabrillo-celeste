# Build 11 physical FNA/Metal graphics pass

11 September 2026. The owner reports the visible test passed. The exported
build 11 diagnostics independently confirm real JIT FNA rendering, touch,
background/resume, the retained MonoMod render hook and clean shutdown.
**Accept the bounded graphics bridge; full Celeste/Everest gameplay is still pending.**

| Check | Physical result |
| --- | --- |
| Exact build/DLL/script/source snapshot | Match delivered 0.4.1 (11) |
| Native checks | 26 passed, debugger detached |
| Managed JIT completions | 3,974, all reported code ranges owned |
| Real frames | 3,758 draws / 3,759 frame callbacks |
| Touch | 24 presses and 24 releases |
| Background interval | 53.487 seconds; same PID after return |
| Frames after return | 2,562 |
| Graphics assertions | All 10 passed |
| Hook patches | 7, none rejected |
| Reset/callback regressions | Pending-clear reset, startup pool completion and suppressed-Draw recovery passed |
| Shutdown | Game/resources disposed, hook removed, worker/main threads detached, PASS UI/export |
| Runtime errors | No JIT, ownership, managed, hook or allocation failure |
| Code reservations | 4,685,824 / 33,554,432 bytes, 46 reservations |
| Peak sampled physical footprint | 182,748,128 bytes; not a gameplay/performance benchmark |

The automatic startup regression and actual first-frame orientation reset both
completed. This confirms the build 10 callback-lifetime correction on the target
iPhone 15 Pro Max / iOS 26.5 in LiveContainer 1, with StikDebug in LiveContainer 2.
The next step is a separate real Celeste baseline with retained lifetime,
content, FMOD, input and isolated saves, before introducing Everest/mods.

The owner exported 1.334 seconds after the PASS result instead of waiting the
requested 10 seconds. Consequently the five-second post-run liveness marker is
absent. Clean return, successful export and owner visual confirmation establish
bounded acceptance; longer post-stop liveness was not measured. No repeat IPA is
needed just for this timing deviation. Controller input was optional and absent.
Reported container/debugger preferences are not freshly queried version metadata.

Untouched export (12,386,284 bytes), extracted current events/console and the
validator are preserved at
`.build/ios-jit/device-evidence/2026-09-11/build-11-pass/`.
SHA256: `80593a97bcc3d6617e8ad97c95e85348ffb29b698802fb6da62dac4f8c0443b1`.
Older failed sessions in the export remain historical; the current console has
no native crash. [Evidence](GRAPHICS_EXECUTION_PASS_2026-09-11_EVIDENCE.json).

Keep the accepted build 11 source, paired FNA3D patch, symbols, kit and snapshots
immutable. New game work uses separate source/staging and a new version. No
commits, pushes, GitHub writes or modifications to the active AOT checkout.
