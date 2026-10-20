# Cabrillo build53 · game input compatibility

This development lane preserves the accepted build50 launcher/shortcut49 behavior
and adds four exact managed input sets covering the nine provided original FNA
Celeste1.4.0.0 packages from itch.io, Steam and Epic.

- Native source: this directory; app identity: `release/app53`.
- Managed builder: `tools/build_game_inputs_managed.py`.
- Public source build: `tools/build_release53.py`; explicit developer FMOD SDK.
- App compiler: `tools/compile_release53.py`; explicit public dependency receipts.
- Input/cache and real-game tests: `tools/probe_game_inputs.py`,
  `tools/check_game_inputs_host.py`, `tools/check_game_inputs_motion.py`,
  `tools/check_game_inputs_sj.py`.
- User acquisition guide: `docs/CELESTE_INPUTS.md`; also available from Play.
- Evidence and limits: `docs/ios-jit/GAME_INPUTS_BUILD_53.md`.

Game files are private test inputs and are imported by the user at runtime. They
are never used by the public app builder or bundled into its output. Host checks
are separate from physical iOS acceptance. Earlier lanes remain frozen.
