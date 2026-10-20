# Cabrillo build56 · SwiftUI touch editor

Build56 /0.27.0 adds the SwiftUI touch layout editor and optional tap-and-swipe
controls to build55's repaired game preparation. Public workflows still select52.

- Fresh public build: `tools/build_release56.py`, developer-owned FMOD SDK.
- Managed payload: `tools/build_touch_editor_managed.py`.
- Package compiler: `tools/compile_release56.py`; `release/app56` identity.
- Input/geometry controls: `tools/check_touch_policy.py`.
- Real-game host: `tools/check_touch_editor_host.py`.
- Original Motion Smoothing: `tools/check_touch_editor_motion.py`.
- Actual SwiftUI simulator controls: `tools/check_touch_editor_ui.py`.
- User guide: `docs/TOUCH_CONTROLS.md`.
- Evidence: `docs/ios-jit/TOUCH_EDITOR_BUILD_56.md`.

The launcher, Files import/export and in-game editor are SwiftUI. The gameplay
overlay and stable multitouch input remain on the existing SDL/FNA game path.
No original/prepared Celeste game code, original assets, FMOD SDK components or
signing material is bundled. Keep the existing data container and shortcut49.

The portrait editor retains detailed choices. Landscape shows the entire display
at actual size, with a 16:9 game-image guide and a movable compact toolbar.
Coordinates cover the full display; safe insets guide defaults, never limit edits.
