# Cabrillo build54 · feather touch steering

Build54 /0.26.0 preserves build53's game imports and adds an opt-in built-in
feather control under Settings → Cabrillo extras → Feather follows finger.

- Runtime sources: `managed/FeatherTouch*.cs`, `TouchPort.cs`, `GameEntry.cs`.
- Native preference: `cabrillo.featherTouch`, default off; read at game start.
- Fresh public source build: `tools/build_release54.py`, developer-owned FMOD SDK.
- Managed builder: `tools/build_feather_touch_managed.py`.
- Native compiler/package: `tools/compile_release54.py`; `release/app54` identity.
- Real-game checks: `tools/check_feather_touch_host.py` and
  `tools/check_feather_touch_motion.py`; simulator UI: `tools/check_feather_touch_ui.py`.
- Design and evidence: `docs/ios-jit/FEATHER_TOUCH_BUILD_54.md`.

Only the feather input vector changes. The original game still controls its speed,
turn rate, collisions, timer, animations and audio. A small screen-space deadzone
supplies neutral input; there is no distance-based speed curve. The regular
movement joystick remains in use outside flight. No optional mod ZIP is needed.

Original game inputs, SDKs and private test fixtures are not bundled. Earlier
frozen lanes and the public build52 workflow remain unchanged.
