# Cabrillo 0.29.0 · build58

Combined implementation of local input development and public v0.26.0.
Includes the full-display SwiftUI touch editor, live feather/grab/controller
preferences, all supported original game inputs, Everest1.6642, copy imports,
dependency download recovery and isolated built-in StikJIT.

- Fresh public build: `tools/build_release58.py`, with a developer-owned FMOD SDK.
- Managed payload: `tools/build_unified58_managed.py` using `prepare_everest55_public.py`.
- Package: `tools/compile_release58.py`, `release/app58` identity.
- Tests: `tools/check_unified58_*.py`, `tools/probe_unified58_saved.py`.
- Guides: `docs/TOUCH_CONTROLS.md`, `docs/CELESTE_INPUTS.md`.
- Integration history and evidence: `docs/ios-jit/UNIFIED_BUILD_58.md`.

No Celeste code/assets or FMOD SDK components are included. Host and simulator
checks do not establish physical helper/JIT, controller lighting or120Hz acceptance.
