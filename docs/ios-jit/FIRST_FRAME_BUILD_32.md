# Cabrillo first-frame presentation — build32

15 September2026. **Physically accepted on the target phone.** The
[acceptance review](BUILD_32_ACCEPTANCE.md) supersedes the original pending gate
below; three first-frame handoffs and a complete game/save/Quit run are recorded. Cabrillo0.16.2 / `launcher-first-frame-20260915-32` addresses the
[build31 phone feedback](BUILD_31_LOADING_REVIEW.md). Both31 game/backend runs
passed, but individual main-thread callbacks made loading controls choppy, and
the native title-menu gate hid17.7 seconds of actual game loading frames.

## Result

The native startup display now shows the stage, current archive/module, real
counts and elapsed time directly. Normal game startup has no disclosure control
or scroll view. A full-width bar represents actual archive/folder work while its
total is known. Uncounted phases use a moving activity segment, with a stationary
segment for Reduce Motion. Counts never pretend to estimate total remaining time.
The activity motion runs in Core Animation without per-frame SwiftUI scheduling.
Individual mod/game calls can still pause text and count updates.

The owner permits smooth interaction if it does not sacrifice loading/backend
performance. The fixed display is the scoped solution here: arbitrary mod calls
cannot safely be made preemptible by moving them to an unrelated worker. No
mod-loading work, ordering, thread ownership or scheduling delay changes. File
preparation cancellation and error scrolling/text selection/Export remain usable.

The native cover now yields to Celeste during the first successful Frame callback
that has produced an actual draw and the adapter's existing post-Present GPU
readback. It also requires an active foreground app, a valid same-scene game
window, Metal and successful graphics checks. A successful Start or a Frame that
skips drawing cannot expose the initial render-test surface. Cover touches are
absorbed, SDL keeps focus, and handoff hides the native window in that callback.

There is no wait for `OuiTitleScreen`, extra managed call, extra GPU readback or
new graphics thread. Celeste's own opening fade/loading sequence can now appear
before its menu. The earliest frame may be mostly black as the original fade
begins; private host captures show the opening controls in frame1 and the actual
GameLoader background in frame15. Physical display/audio timing remains the new
gate. An FMOD-ready event is not proof of the exact instant audio became audible.

## Validation

| Check | Result |
| --- | --- |
| Production C frame observer |10 cases pass: correct draw/readback order, ignored worker/wrong-phase/malformed reports and real first frame |
| Replay of both collected build31 runs |Existing evidence makes the new gate eligible at their first Frame return,17.733/17.764s before the old handoff |
| iPhone17ProMax and iPadPro11 simulators |Six XCUITests each: fixed details and rotation, larger text, real activity-layer/Reduce Motion behavior, error Export, file cancellation, window guards/focus/tap isolation and background deferral |
| Early real game images on host |Pinned game/FNA/adapter and established host Mono BCL; GameLoader images before Overworld, then normal main-menu Quit |
| Fresh iOS build |62 source inputs compiled with Xcode26.6 / SDK26.5; new UUID and matching external dSYM |
| Package controls |Five actual mutated IPAs rejected: stale build identity, title-menu gate metadata, managed bytes, compiled JIT protocol and mismatched dSYM |
| Build31 package comparison |All201 managed DLLs byte-identical; only executable, Info.plist, BuildInfo and notices differ |
| Independence |Native build and host observation deny legacy/original-input access and writes to the pinned private capsule |

[The ledger](FIRST_FRAME_BUILD_32_EVIDENCE.json) pins the exact receipts and
private evidence. The host's extra screenshot readbacks are external test code,
absent from the IPA. These runs are functional evidence, not a controlled loading
performance benchmark or a physical iOS window test. Earlier managed scheduling,
dependency order, gameplay/save/Quit checks remain applicable to the unchanged
managed payload; build31 now provides actual phone evidence for those bytes.

## Package and delivery

- Artifact: `artifacts/cabrillo-build32/Cabrillo-0.16.2-build-32-unsigned.ipa`.
- Size: **23,862,241 bytes**.
- SHA256: `86f9de0b51073473e7562ea2ef97073889bf48123a424e8d6f98ec245c65b9f1`.
- Executable/dSYM UUID: `342D1B25-8DE3-39B1-8A53-A40ED579FC01`.
- Native lane: `experiments/ios-jit/launcher-first-frame`.
- Builder/verifier: `tools/build_first_frame.py`, `tools/verify_first_frame.py`.
- Managed dependency: exact `loading-managed30-d` receipt pinned by both31 and32.

The six-file kit is byte-verified and **upload-confirmed** in iCloud
`Celeste JIT Tests/0.16.2-build-32`. An initial upload error cleared on recheck;
all six files now report uploaded with no error. Phone execution is unconfirmed. The test folder
totals742,066,033 bytes, within1GB. No previous installer or Results was removed.
Build28 remains the accepted fallback;27 and31 are preserved. No commit/push occurred.

## Focused phone gate

Follow the [short guide](../../experiments/ios-jit/launcher-first-frame/PHONE_README.txt).
Update slot1 preserving its data; keep StikDebug in slot2, Launch with JIT OFF,
blank saved script and Fix File Picker ON. Use a fresh PID-specific inline request
and detach before Run. Check passive details, early native-to-game presentation,
audio/input, background return and normal save/Quit with five seconds of native
heartbeat. One export is sufficient; it can also include an optional warm run.
No repetition of accepted browser/install tests is requested.

Expected new evidence: `startup_window_handoff` has reason `first_rendered_frame`
and native `first_frame_drawn` / `first_frame_readback_passed` true. Its progress
can still be `game_content` with `ready=false`; that is intentional. The later
`game_menu` event for `OuiTitleScreen` records menu readiness. Once native loading
ends, late managed progress cannot reopen it. Catalogue quiescence still requires
zero active requests before managed startup. Preserve normal Quit and fresh JIT
per process. Whole-profile backup/restore follows this presentation gate, then
the full touch editor.
