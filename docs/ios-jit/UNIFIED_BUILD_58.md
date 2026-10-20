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
frozen identity. Source changes belong in the new lane. Original game files,
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

## Validation status

At the start of integration, the local public-source boundary audit passes for
5,620 files. All291 captured local57 inputs and18 referenced evidence receipts
match their retained hashes. This verifies preservation of the local snapshot;
it does not establish correctness of the integrated build.

**Combined build58 validation and IPA delivery are pending.** Record the final
managed/native compilation, source/package audits, regression checks and exact
IPA identity here when complete. Relevant coverage includes cold and saved-game
startup, touch editor save/cancel/input isolation, live preferences/death/maps,
Motion Smoothing, picker/imports, dependency recovery and JIT helper/provider
integration. Host/simulator checks and physical device acceptance remain separate.

The previous physical gates remain scoped to their original evidence. In
particular, local57 has no physical acceptance, DualSense light colours remain
untested on the owner's controller, and published57 package checks do not imply
physical built-in-helper/DDI/JIT/gameplay acceptance. A combined test IPA should
keep the data container and revision49 Shortcut and allow its own cache rebuild.
