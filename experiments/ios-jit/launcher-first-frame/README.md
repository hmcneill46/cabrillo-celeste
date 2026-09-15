# Cabrillo first-frame presentation — build32

Version0.16.2, `launcher-first-frame-20260915-32`. This native refinement follows
the [build31 phone review](../../../docs/ios-jit/BUILD_31_LOADING_REVIEW.md).
The exact phone-tested managed payload remains pinned in `ManagedPayload.json`;
its frozen source is `launcher-loading`. The native runtime/renderer remain pinned.

Normal startup has a fixed display with stage, current work, actual archive/folder
counts, module/dependency counts and elapsed time. An activity segment represents
uncounted work; its Core Animation motion needs no per-frame SwiftUI scheduling.
Individual thread-affine mod/game calls can still pause status updates. File
preparation cancellation and failure scrolling/Export remain available.

`CJStartupFrame` observes the existing adapter's first draw and post-Present
readback. A successful frame callback, those checks, a valid same-scene game
window and active application are all required for `CJLoadingWindow` to reveal
the game. The native cover absorbs touches and keeps SDL focus until then. There
is no title-menu wait, extra managed call/readback or change to the loader schedule.

Build using `tools/build_first_frame.py --managed .build/loading-managed30-d/receipt.json`
and fresh work/output directories. Verify with `tools/verify_first_frame.py` and
`tools/check_first_frame_package.py`. UI, native frame-observer replay and private
host observations use `tools/check_first_frame_ui.py`,
`tools/check_first_frame_observer.py` and `tools/check_first_frame_host.py`.
Test fixtures stay outside the IPA. See the [build32 report](../../../docs/ios-jit/FIRST_FRAME_BUILD_32.md)
for results, limitations and delivery. No Git publication is authorized.
