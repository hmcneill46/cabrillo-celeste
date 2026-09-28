# Source publication through build50

## Scope —29 September 2026

The owner requested committing, reviewing and pushing the completed work after
the accepted app50 cellular-start test and independent diagnostic export.
The branch is `codex/owned-game-import`, based on `b7a8d28` (the merged CI PR2).

This source change contains:

- Build38 preparation and caching of game code from the user's original ZIP,
  with pinned public dependency recipes and an explicit FMOD SDK input.
- Home Screen shortcut generation, in-app export/setup and the corrected49
  import field, plus the native launch coordinator through build50.
- Separate reports for historical failures, repairs and observed device gates.
- Public CI coverage of the current shortcut logic; IPA releases stay blocked.

The frozen build38 release recipe remains in `release/current.json`. Publishing
this source does not turn the private50 package into a public release or resolve
FMOD redistribution. No new app identity or signed shortcut is needed.

## Review and correction

Review covered the owned-game cache/activation boundary, source dependency pins,
JIT execution and debugger-detach gates, stage/token checks, network restoration,
typed shortcut URLs, package exclusions and release eligibility. Delivered source
hashes remain unchanged; historical lanes retain their original failure behavior.

The pending CI workflow still invoked the build39 checker, which hardcoded the
local Mac's Xcode path. That missed the accepted50 fixes and could not use the
GitHub runner's configured installation. `tools/ci/check_native_shortcuts.py`
now honors `DEVELOPER_DIR` and compiles50's public tests. It also proves that the
original43 missing-callback and49 cellular-order failures are detected. Signed
shortcut import/UI checks remain separate because they require Apple assets.

## Local verification

- Public source inventory, syntax and private/binary exclusions pass.
- 20 Python build/release controls pass; public IPA readiness remains `BLOCKED`.
- 119 native save/profile controls pass from the owned-game source lane.
- 132 native shortcut launch controls and53 cellular route/order controls pass.
- 36 generated shortcut branches and15 invalid-URL controls pass.
- Original43 and49 negative controls fail for their expected defects.
- Retained build35–50 app source manifests match, including all243 build50 inputs.
- The source scan finds no private keys, access tokens, pairing secret fields,
  signed files, SDK archives, game binaries or raw device log files.

Local receipts are retained under the ignored `.build/publish50-review/`.
GitHub's **Public source checks** run at the pushed commit and retain their own
small JSON reports. These host checks do not establish new physical acceptance.

The existing [build50 report](SHORTCUT_CELLULAR_BUILD_50.md) remains the authority
for the accepted cellular-start/JIT/restoration run. Game/Quit, alternate presets,
other providers and completely out-of-range use retain their separate gates.
