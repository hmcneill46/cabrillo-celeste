# Cabrillo 0.29.1 · build59 — local input fixes

Retains the public build58 implementation and corrects edge resizing in the
full-display touch editor and cached controller colour replay after native resume.
Includes live feather/grab/controller
preferences, all supported original game inputs, Everest1.6642, copy imports,
dependency download recovery and isolated built-in StikJIT.

- Fresh public build: `tools/build_release59.py`, with a developer-owned FMOD SDK.
- Managed payload: `tools/build_input_fixes59_managed.py` using `prepare_everest55_public.py`.
- Package: `tools/compile_release59.py`, `release/app59` identity.
- Regressions: `tools/check_touch_resize59.py`, `tools/check_controller_resume59.py`.
- Retained checks: `tools/check_input_fixes59_*.py`.
- Guides: `docs/TOUCH_CONTROLS.md`, `docs/CELESTE_INPUTS.md`.
- Fixes, evidence and limits: `docs/ios-jit/INPUT_FIXES_BUILD_59.md`.

No Celeste code/assets or FMOD SDK components are included. Host and simulator
checks do not establish physical helper/JIT, controller lighting or120Hz acceptance.
Build59 is local and unpublished. The default release pipeline remains on58.
