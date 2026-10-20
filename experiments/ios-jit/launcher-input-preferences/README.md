# Cabrillo build57 · Live input preferences

Build57 / 0.28.0 uses original Celeste grab semantics with preferences per input
method, optional persistent toggling, live feather steering, controller symbol
selection, SDL controller recognition and light-colour replay after connection.
Build56's full-display SwiftUI layout editor is retained. Public workflows select52.

- Fresh public build: `tools/build_release57.py`, developer-owned FMOD SDK.
- Managed payload: `tools/build_input_preferences_managed.py`.
- Package: `tools/compile_release57.py`, `release/app57` identity.
- Geometry/migration: `tools/check_input_preferences_policy.py`.
- Real game: `tools/check_input_preferences_host.py` (explicit pinned host SDL receipt).
- Death/maps: `tools/check_grab_lifecycle_host.py`.
- Motion Smoothing: `tools/check_input_preferences_motion.py`.
- SwiftUI: `tools/check_input_preferences_ui.py`.
- Guide: `docs/TOUCH_CONTROLS.md`; report: `docs/ios-jit/INPUT_PREFERENCES_BUILD_57.md`.

No Celeste code/assets or FMOD SDK components are included. Host virtual-controller
checks do not establish physical DualSense lighting or device acceptance.
