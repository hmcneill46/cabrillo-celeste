# Cabrillo build55 · saved-game startup repair

Build55 /0.26.1 fixes startup after the temporary import ZIP has been removed.
Native code keeps the expected ContentImport/game-input.zip path configured.
GameCodeStore now tests for an actual file before selecting a new ZIP; otherwise
it verifies the selected retained originals and reuses or rebuilds their cache.

- Fresh public build: `tools/build_release55.py`, developer-owned FMOD SDK.
- Managed builder: `tools/build_saved_game_managed.py`.
- Package compiler: `tools/compile_release55.py`; `release/app55` identity.
- Regression and nine-input checks: `tools/probe_saved_game.py`.
- Full cold/cached/legacy-rebuild gameplay: `tools/check_saved_game_host.py`.
- Report: `docs/ios-jit/SAVED_GAME_BUILD_55.md`.

The optional feather control, all native code, signed49 Shortcuts and game input
adaptations are unchanged from54. The preparation fix does not weaken input or
cache verification: an existing invalid ZIP still fails, and missing/corrupt
saved originals still require import. Earlier sources and artifacts stay frozen.
Original game files, SDKs and private test fixtures are never bundled.
