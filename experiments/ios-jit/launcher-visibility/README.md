# Build36: restore Motion Smoothing startup

Version 0.19.1, `launcher-visibility-20260925-36`.

Build35's iOS15 native rebuild omitted the accepted assembly-scoped Mono member
visibility correction. Motion Smoothing failed before its first frame at both
60 and 120Hz. This lane restores the exact correction in `class.c.o`; the other
259 Mono archive members, fifteen other native archives and all 201 managed
assemblies match build35. The iOS15, JIT-route, touch, save and precision changes
are preserved. Sources are frozen after final packaging.

Use `tools/build_visibility_runtime.py`, `tools/build_visibility.py` and
`tools/verify_visibility.py`. `tools/check_visibility.py` exercises fields and
methods with exact, absent and incorrect grants; `tools/check_visibility_motion.py`
reproduces the phone exception with the old metadata source and exercises the
original mod with the restored source. `RuntimeValidation.json` pins those gates.
See [the report](../../../docs/ios-jit/VISIBILITY_BUILD_36.md).
