# Build58: integration of both Cabrillo development histories

Date:20 October2026. Target: **0.29.0 / build58**. Implementation lane:
`experiments/ios-jit/launcher-unified58`.

## Scope and authorization

The owner requests preserving all work from this Mac and the other computer,
merging and pushing it as `hmcneill46`, then building an unsigned test IPA. Source
commits, push/PR/merge and a trial build are authorized. A new version tag or
public Release requires the owner's later request after testing. The existing
[public v0.26.0](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.26.0)
remains available. No iLoader change or submission is included.

## Source lineages

The common starting point is `614154c`. Local work was captured before integration
in `ee475e3` on `codex/game-input-compatibility`. The other computer's source is
`65e45c2`, after the published v0.26.0 merge/tag at `93415b4`. Both computers used
build numbers53–57 independently:

| Build | This Mac's local series | Other computer's published series |
| --- | --- | --- |
| 53 | 0.25.0: itch.io/Steam/Epic game inputs | 0.24.2: signing-aware Files picker |
| 54 | 0.26.0: optional feather touch steering | 0.24.3: copy-based Files imports |
| 55 | 0.26.1: retained-game startup repair | 0.25.0: Everest stable1.6642 |
| 56 | 0.27.0: full-display SwiftUI touch editor | 0.25.1: dependency download recovery |
| 57 | 0.28.0: live input preferences/controller integration | 0.26.0: integrated StikJIT |

Canonical `release/app53`–`app57`, public manifests and numbered release builders
retain the published series byte-for-byte. Their conflicting local versions remain
in the local snapshot commit, recoverable in a separate checkout. Feature lanes,
test sources and dated evidence from both series remain in the combined tree.
Existing captured-source hashes refer to their original commit and retain their
meaning; one build's recipe must never be substituted for the other.

The new identity0.29.0/build58 is higher than both series and avoids reusing a
frozen identity. Integration changes were isolated in the new lane. Original game files,
FMOD SDKs, credentials, private logs and compiled test artifacts remain excluded
from Git. The protected FMOD download/runtime packaging boundary is retained.

## Combined behavior to preserve

- Import all nine tested original itch.io, Steam and Epic FNA1.4.0.0 packages;
  retain source-keyed caches and rebuild from retained originals when the temporary
  staging ZIP is absent. Keep the game-files acquisition guide and Morro notice.
- Keep the full-display SwiftUI touch editor, actual-size landscape view,16:9
  guide, split/duplicate controls and optional jump/swipe-dash region.
- Keep live feather steering, original Celeste grab semantics, per-input-method
  modes, optional grab persistence, controller symbols and light-colour replay.
- Keep copy-based Files import and signing compatibility from the published lane.
- Keep stable Everest1.6642, synchronized native/managed identities, authoritative
  bounded dependency relocation and required/optional dependency alias behavior.
- Keep built-in StikJIT in its separate iOS17.4 helper, with the iOS15 host's native
  execution and detach gates. Preserve external/LiveContainer providers, protected
  pairing-file handling and signed revision49 Home Screen Shortcuts.
- Keep existing bundle identity, profiles, saves and rollback behavior.

## Integration and preservation

The merge at `eaa57b0` has both preserved parents, `ee475e3` and `65e45c2`.
[PR8](https://github.com/hmcneill46/cabrillo-celeste/pull/8) contains the combined
source and records its final GitHub check and merge status. Both histories must
be retained with a merge commit. The local test package and iCloud delivery
are verified below. No new version tag or public Release has been made.

All299 captured published57 sources remain exact. All291 captured local57
sources remain exact in its snapshot parent; the six colliding canonical paths
remain recoverable there. All30 published53–57 identity, manifest and numbered
builder/compiler files retain their published bytes. The initial local audit also
verified all18 earlier evidence-receipt hashes. Both original histories and the
dated feature reports are retained.

## Completed validation

The combined source passes the following local checks. The
[evidence ledger](UNIFIED_BUILD_58_EVIDENCE.json) records receipt hashes and
counts without copying private logs, game files, credentials or device data.

| Check | Result and scope |
| --- | --- |
| Python release/integration controls | 133 pass, including source-catalogue, metadata and preserved-feature controls. |
| Native policies | 186 JIT/pairing,12 picker scenarios,321 dependency controls and14 game-input controls pass against selected58 sources. Fixtures do not enable device JIT. |
| Touch/input policies | 59 Swift and2,743 managed geometry/input controls pass. |
| Apple UI tests | 12 tests pass across iPhone and iPad simulators, covering touch editing/live preferences and the combined launcher. |
| Managed payload | All199 assemblies pass434 metadata/identity checks, with wrong-version and stale-tool negative controls. The actual schema2 recipe preserves all four game-source identities. |
| Original game inputs | All nine original ZIPs pass, with22 retained-store and97 input/recovery controls. |
| Full real-game host runs | Three pass: cold import, cached startup with the missing temporary ZIP, and rebuild from older retained originals. Each covers input preferences, touch/feather, numerical fixes, desktop saves, resume and normal Quit. |
| Grab lifecycle | Ten real death/respawn/map-change checks pass. |
| Motion Smoothing1.8.0 | Fast/Fancy at60/120 host draw callbacks pass with original60Hz physics. These are not sustained physical120Hz measurements. |
| Full Strawberry Jam | Both cold and cached runs pass with52 original mod archives plus one test canary. Tests enter the real Beginner lobby and Bing map, exercise hooks, save/resume and Quit normally. |
| Production iOS host compilation | All25 selected launcher Swift files,21 ZIPFoundation files,6 CYaml files and15 Objective-C host files compile for arm64/iOS15 with the actual generated Swift bridge. All130 captured inputs remain stable; the picker test seam is absent. |
| Fresh dependency/helper builds | Managed/native dependencies build from the pinned public inputs with an explicit developer-owned FMOD SDK. The separate unsigned StikJIT helper/framework builds for iOS17.4; its58 identity is verified before packaging. |

The final production compile receipt is
`.build/unified58-compile-d/receipt.json`. The source-only check excludes
SDL/Mono graphics implementation and linking; the full IPA build covers those.
Its earlier run completed compilation but rejected its receipt because the
compiler's metadata code changed during that run. The fresh run passes.

## Defects caught before delivery

The first integration IPA omitted `game_code_legacy_source_id` and
`game_code_sources` from native `BuildInfo.json`. Its managed recipe was correct,
but native saved-game availability could reject retained originals after the
temporary import ZIP had been removed. A control using the actual
`CJGameInputsAvailable` function and metadata extracted from that IPA reproduces
the rejection. The compiler now copies the catalogue from the actual recipe;
the package verifier compares it, and the fresh-build workflow runs the
packaged-metadata control. The corrected package passes15 native behavior checks plus36 fixture setup
assertions without using proprietary game files. The first IPA stays
retained as a failing negative control and is not a test-kit candidate.

Independent review of the second package then found an outdated bundled
third-party notice inherited from build38: it omitted Morro and still described
Everest1.6580 and an unresolved FMOD permission gate. A new58 notice corrects
the current dependencies and runtime permission while retaining the developer
SDK restriction and required licences. The compiler now selects it and package validation requires its current notices
before a fresh final package. The second IPA
(`2a71fd90c39008e4d2c6214d5ec52bd38f20cf74a41eb746a44b86385e0a0630`,
21,325,971 bytes, source `6dd9991`) is intermediate evidence, not the final kit.
Its346 captured sources,199 DLLs,16 native archives, six helper files and dSYM
passed independent checks; the notice defect blocked acceptance.

## Test package and remaining gates

The final unsigned **0.29.0/build58** IPA passes independent verification:

- Clean source commit: `5d535d85ffc2f43d60c58a7fe9bc2064dffa2522`.
- SHA256: `73b5c6f2f41089abc2973e922d5a1664472b127b309713324a13078a7fdd28d5`.
- Size: **21,326,350 bytes**; all345 captured inputs match the source commit.
- Matching executable/dSYM UUID: `a9d1992eceef3756bac0a2a38a836bc8`.
- All199 managed assemblies,16 native archives and six helper/framework files
  match their receipts. The schema2 retained-input catalogue and combined
  FMOD/Morro/StikJIT notices pass. No game code/assets, SDK components, pairing
  data or signing identities are bundled.

The retained local kit is `artifacts/cabrillo-build58-final`. All nine test-kit
files have exact readback and confirmed upload at **iCloud Drive → Celeste JIT
Tests → 0.29.0-build-58**. Initial transient iCloud errors cleared. Only the
superseded local55 cloud IPA was removed after its exact local copy and package
receipts were checked; all Results folders, local artifacts and accepted
fallbacks remain. Total cloud size is996,437,125 bytes.

The package was compiled locally from fresh pinned public managed/native inputs
and a developer-owned FMOD SDK. It is not a new hosted release/attestation claim.
GitHub's retained `6dd9991` push and PR runs
[39424156697](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39424156697)
and [39424166753](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39424166753)
pass source and combined native/Swift/helper/policy jobs. PR8 records the final
head's checks before merge. The public workflow selects58 for a future manual
`publish=false` trial; no new Release or version tag is created by this work.

All345 captured app inputs are frozen after this review; use59 for new app changes.

Keep the existing data container, saves and revision49 Shortcut. Allow one
prepared-code cache rebuild, then check a second fresh-process start, normal
Quit and Export diagnostics. Review the full-display editor in portrait and
landscape, live feather/grab choices and the controller's preferred symbols.
For standalone Built-in StikJIT, preserve the helper during signing and use the
documented pairing/VPN setup; LiveContainer retains its existing provider.

No new physical device acceptance is inferred. Actual installed helper
registration/DDI/JIT, physical touch comfort, DualSense light colours and
sustained120Hz remain device gates. Earlier save-manager, lifecycle and iPad
gates keep their original scope. No phone has been modified for this integration.
