# Build53 — original Celeste files from itch.io, Steam and Epic

**Later finding:** the phone54 export exposes a53/54 cached-startup regression
when native supplies an absent staging ZIP path. Use the separate
[build55 repair](SAVED_GAME_BUILD_55.md). The original53 evidence below did not
exercise that native path; its warm tests used null/empty archive arguments.

Cabrillo0.25.0 / build53 adds the nine original FNA1.4.0.0 distributions supplied
by the owner. Development is local on `codex/game-input-compatibility`. The
published0.24.1/build52 and its tag workflow remain unchanged. No new GitHub
commit, push, tag or Release is authorized by this compatibility request.

## User behavior

Choose one original game ZIP. Cabrillo discovers its game/content root, verifies
the actual file hashes, and prepares that copy with Everest. Whole-folder ZIPs,
flat downloads and wrapped macOS `Celeste.app/Contents/Resources/` layouts work.
Store names and archive filenames are not used as proof of compatibility.

Play now has **How to get your game files**. The repository's
[game files guide](../CELESTE_INPUTS.md) includes itch.io downloads, Steam console
depot commands, optional Epic/Legendary acquisition and ZIP/import instructions.
It adapts Morro's MIT guide, credits its pinned revision and preserves its licence.

No game code or assets are bundled. The user's original download is read-only.
Their saves, profiles and mod selections retain their locations. Existing standard
originals from38–52 can be prepared again without a ZIP. Later launches reuse the
verified cache. JIT, shortcut49, loading/first-frame behavior and the runtime pins
are retained.

## Exact coverage

| Source package | Input combination | Full content/code import |
| --- | --- | --- |
| itch.io Windows OpenGL/FNA | Standard | Pass |
| itch.io Linux FNA | Standard | Pass |
| itch.io macOS FNA | Standard | Pass |
| Epic macOS FNA | Standard | Pass |
| Epic Windows FNA | Empty companion | Pass |
| Steam Linux 2021 | Steam Linux/macOS | Pass |
| Steam Linux public2025 | Steam Linux/macOS | Pass |
| Steam macOS FNA | Steam Linux/macOS | Pass |
| Steam Windows OpenGL/FNA | Steam Windows | Pass |

Every row is Celeste1.4.0.0 / FNA21.3.5 and verifies all1,216 assets
(1,158,665,183 bytes; aggregate
`30a1c147d1a3ab0aa45762094e393ed7fd69951dd66e5af063447641e0699c46`).
Four exact combinations of executable/FNA/companion/Steamworks hashes cover these
nine packages. They are recorded in the lane's `OriginalGameIdentity.json`.
Desktop native-library markers are not required: those files are never imported
or executed. Identical supported code/content can therefore work under another
folder/store label without pretending that storefront was independently tested.

Other game versions, XNA, modified/Everest game folders and unverified console or
Microsoft Store packages remain unsupported. This is not a claim about every
Celeste release ever sold. Morro's AOT/device acceptance is not Cabrillo evidence.

## Preparation changes

- **Epic Windows:** the supported original omits `Celeste.Content.dll`. The
  companion in the other packages contains only the module record and no game
  types/resources. For this exact missing-companion input, Cabrillo creates empty
  assembly metadata locally. It does not borrow game bytes from another edition.
- **Steam:** a bounded Cecil IL adaptation runs after coreification and before
  Everest. It removes desktop client startup/callbacks, Steam identity, and online
  achievement/statistic behavior, then verifies no Steamworks reference survives.
  Everest deliberately selects its non-Steam patch rules. The original executable
  remains byte-exact under `orig/` for mod metadata. All method signatures are
  retained; comparison against coreified original code finds exactly11 changed
  desktop-service method bodies and no other method-body changes.
- **Cache:** schema2 records the approved input sets. Originals remain in
  `GameCode/v1/original/<source>`; prepared generations use
  `GameCode/v1/<recipe>/<source>/<generation>`. A bounded `selected-source.json`
  records the last successfully prepared source. Failed/cancelled switches retain
  the previous selection. Corrupt prepared generations rebuild from retained
  originals; damaged originals need reimport. Unknown/recovery files are retained.
- **Native availability:** Play recognizes the selected source and the legacy
  standard original. This remains only an availability hint; managed preparation
  verifies code/content on each launch. Invalid pointers cannot choose arbitrary
  directories or silently fall back to a different selected edition.

Steam achievements and Steam Cloud do not operate in Cabrillo. Local game saves,
manual desktop transfers, Everest hooks and the existing physics repairs remain.
The adaptation adds no work to gameplay frames.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Existing original/cache/corruption/cancellation controls | `.build/game-input53-store-d/receipt.json` | 19 pass |
| Nine full ZIPs, source switches, migration, mixed/modified/unsafe inputs, scoped IL comparison | `.build/game-input53-store-d/matrix.json` | 97 pass |
| Standard cold/cached real game | `.build/game-input53-host-standard-a` | Both pass |
| Epic Windows cold/cached real game | `.build/game-input53-host-epic-a` | Both pass |
| Steam Linux/macOS cold/cached real game | `.build/game-input53-host-steam-b` | Both pass |
| Steam Windows cold/cached real game | `.build/game-input53-host-steam-windows-a` | Both pass |
| Original Motion Smoothing1.8.0 with Steam game | `.build/game-input53-motion-steam-a` | Fast/Fancy at60/120 pass |
| Full retained Strawberry Jam selection with Steam game | `.build/game-input53-sj-steam-a` | Cold/cached mods, maps, hooks, saves, resume and Quit pass |
| Native selected/legacy input availability | `.build/game-input53-native-state-a` | 14 pass; public CI step added |
| Existing public build/release rejection controls | `.build/game-input53-python-tests.log` | 59 pass |
| Workflow syntax | Actionlint1.7.12 | Both workflows pass |
| IPA and game-free payload checks | `artifacts/cabrillo-build53-final/verification.json` | Pass |

Each of the eight real-game runs verifies cooperative boot, hair behavior,
desktop save transfer, save readback, suspend/resume and normal Quit. These run
the package's final game-free managed payload with the retained, explicitly pinned
Mac native test runtime. They are not tests of the iOS native archives on a device.
Motion Smoothing checks callback behavior, not physical120Hz display performance.

The final managed payload is `.build/game-input53-managed-b/receipt.json`, built
from the pinned public inputs in `.build/release51-local/inputs/receipt.json`.
The app recompiles all native launcher/UI source with Xcode26.6 and explicitly
uses the unchanged public native/FMOD dependency receipts from
`.build/release51-local/{native,fmod}`. (FMOD is the1.10.09 licensed runtime.)
The independent full source entry point is `tools/build_release53.py`; it rebuilds
those dependencies afresh and requires the developer's own FMOD SDK. No game files
are needed by either app build recipe.

All captured35–50 source manifests and both hosted/tagged52 source manifests
remain exact. Build53 has259 captured app inputs; these are frozen with an archive
in `artifacts/cabrillo-build53-final`. Further app implementation needs54.

## Package and delivery

The unsigned IPA is18,782,511 bytes, SHA256
`3a0e4ec5b72e1e13d6a6f00db7bac0f7a7aa7bf8450ed28d9c3aaaecaec16f31`.
Its fresh executable and matching dSYM UUID is
`e5b972cc5ac736e2a391d9e8da7cf61a`. Metadata and independent package scans confirm
199 bundled managed assemblies, zero original/prepared Celeste game assemblies,
no original game assets, SDK archives or signing material. The game adapter and
FNA DLLs match the release; other rebuilt dependency hashes are recorded rather
than assumed byte-identical.

Physical53 import, gameplay and normal Quit are pending. Keep the existing
shortcut49 and installation data container. The test guide asks for ordinary
play/save/resume/Quit and an independent diagnostic export; it does not ask to
repeat all nine equivalent packages on the phone. Earlier save-manager, iPad and
sustained120Hz gates remain separate.

All eight test-kit files have exact local readback and **confirmed upload** in
`iCloud Drive/Celeste JIT Tests/0.25.0-build-53`. Initial transient iCloud account
errors cleared; all files report uploaded with no error.
The superseded49 cloud IPA alone was retired after its exact local original and
receipt matched. All Results folders and fallback installers remain. Local cloud
folder usage is996,088,256 bytes. This is not phone installation/execution.

The [evidence ledger](GAME_INPUTS_BUILD_53_EVIDENCE.json) pins the final receipts.
Earlier failed development controls are retained privately: the first Steam
adapter used an incorrect method name, a strengthened comparison test needed to
distinguish generic arities, and one native compilation correctly refused to
package after that test source changed. None is the delivered kit.
