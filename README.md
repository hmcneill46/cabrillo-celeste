# Cabrillo

**Celeste Mod Loader for Apple Platforms**

Cabrillo is a native launcher for playing Celeste with Everest mods. Import your
game, browse or import mods, review their dependencies, enable JIT, and play.
The launcher uses SwiftUI; the game and its mods run in the same Mono JIT runtime.

The name comes from Cerro Cabrillo in California. The source repository is
[hmcneill46/cabrillo-celeste](https://github.com/hmcneill46/cabrillo-celeste).

## CI and releases

[GitHub Actions](https://github.com/hmcneill46/cabrillo-celeste/actions/workflows/ci.yml)
checks the public source on pushes and pull requests, including 119 native save
and backup checks. A separate version-tag workflow is prepared for unsigned IPA
releases with source/dependency hashes and GitHub build attestations.

**IPA publishing is currently blocked**: the private app contains prepared game
code and FMOD libraries, and its dependency build is not yet public. No existing
IPA is uploaded by CI. See [the release guide](docs/RELEASING.md) for the remaining
work, release controls and what provenance can establish.

## Related project

**Morro** is the planned name of the separate fully AOT Celeste project,
[currently hosted as celeste-ios](https://github.com/hmcneill46/celeste-ios).
The projects share ideas and selected platform policies, but have independent
builds, runtime strategies and release decisions. This checkout contains no AOT
application, Xcode project, generated game source, or AOT build cache.

## Strawberry Jam and larger mod packs

We recommend **Increased Memory Limit** on supported devices with enough RAM.
[GetMoreRam](https://github.com/hugeBlack/GetMoreRam/releases/tag/nightly) can enable
the capability for a sideloaded app's App ID; re-sign and reinstall the app
afterward. When running Cabrillo inside **LiveContainer**, apply it to the
LiveContainer instance running the game. For a standalone installation, the
permission belongs to Cabrillo's own signature and provisioning profile.

The extra allowance depends on the device and does not add RAM. See the
[setup guide](docs/INCREASED_MEMORY_LIMIT.md) for the steps and verification.

## Current platform build

[Build35](docs/ios-jit/PLATFORMS_BUILD_35.md) adds iOS15 support, selectable JIT
routes and optional120Hz display callbacks for Motion Smoothing. Real base-game
play, touch, saves and normal Quit pass on an iPad mini4 running15.8.8 with
Dopamine/TrollStore. [Build36](docs/ios-jit/VISIBILITY_BUILD_36.md) repairs an omitted
Mono visibility patch; its phone base-game/Motion Smoothing gameplay/save/Quit
gate passes. Sustained physical120Hz performance remains unaccepted.

[Build37](docs/ios-jit/EVEREST_6580_BUILD_37.md) upgrades Everest to stable1.6580.
Its phone Strawberry Jam exits were confirmed as iOS per-process memory kills.
The installed LiveContainer host lacked its earlier Increased Memory Limit
permission. [The same-release signing repair](docs/ios-jit/BUILD_37_MEMORY_REVIEW.md)
is installed; iOS verifies the process ceiling rose from3376MiB to6144MiB.
The owner confirms Strawberry Jam works after the repair, and new phone logs
verify actual SJ room/touch gameplay at4.05GB with zero recorded runtime errors.
Build32 remains
the broader accepted fallback. Current mod dependencies may require newer Everest.

## Saves and numerical fixes in development

Build32 is the accepted phone fallback and its loading work is published on
`main` (`16ff42c`). Build34 combines build33's whole-profile backup/restore with
individual desktop save transfers, long-press slot actions and retained rollback.
It also repairs hair and related seeker/tutorial/lava arithmetic errors. The
[build34 report](docs/ios-jit/SAVE_TRANSFERS_BUILD_34.md) records local tests and the
uploaded phone kit. The owner deferred33 testing for one combined34 gate.
Phone34 acceptance remains pending; host/simulator checks do not replace it.

## Current state

Build28 adds native mod browsing, categories, five sort orders, details and
reviewed installations. It is [physically accepted](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md)
on an iPhone 15 Pro Max running iOS26.5, including post-browser gameplay, saves
and normal Quit/native return. Accepted27 is also preserved.

[Build29](docs/ios-jit/STARTUP_PREPARATION_BUILD_29.md) is local preparation with
Cabrillo branding, passive startup timings and a fresh independent native recipe.
29 has not been delivered or tested on the phone.
[Build31](docs/ios-jit/BUILD_31_LOADING_REVIEW.md) passes two phone game/backend
runs. Its loading UI pauses and delayed game reveal are addressed in
[build32](docs/ios-jit/FIRST_FRAME_BUILD_32.md): always-visible startup details and
handoff after the first rendered game frame. The verified kit is uploaded to
iCloud; [its phone gate is accepted](docs/ios-jit/BUILD_32_ACCEPTANCE.md).
Build32 is the current fallback. The full touch editor follows the34 phone gate.
Build32 reuses31's exact managed payload. Original28/29/30/31 artifacts remain frozen.

For development, start with [the current handoff](HANDOFF.md),
[the migration report](docs/CABRILLO_MIGRATION.md),
[the roadmap](docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md), and
[the original feasibility audit](docs/ios-jit/FEASIBILITY_AUDIT.md).

## Build locally

The owner's local development folder contains the pinned private inputs needed
for the current build. They are intentionally excluded from Git; a fresh clone
needs these inputs supplied separately. You also need Python3 and **Xcode26.6**,
installed as `/Applications/Xcode-26.6.app`; no old checkout is needed by the
standalone build command once the inputs are present.

```sh
python3 tools/build.py --reproduce-build28
```

The command requires empty output/work folders. To retain earlier build evidence,
choose another `--work .build/<name>` and `--output artifacts/<name>`.
It recompiles the Swift launcher, ZIP/YAML parsers, native bridge and generated
symbol tables, compiles icon assets, links the app and packages an unsigned IPA.
It reuses the accepted managed/runtime libraries, as build28 did.

See [build inputs and reproduction](docs/BUILDING.md) for the precise scope,
historical metadata policy, and source/private dependency distinction. A GitHub
clone alone cannot contain owner-owned game IL or licensed FMOD binaries. The
local `.private` dependency capsule must be backed up separately.

## Repository layout

| Location | Reason it is here |
| --- | --- |
| `experiments/ios-jit/launcher-catalogue` | Accepted build28 native browser and preserved source |
| `experiments/ios-jit/launcher-first-frame` | Build32 passive startup display and first-frame game handoff |
| `experiments/ios-jit/launcher-save-transfers` | Build34 per-slot transfers, profile backups and scoped numerical repair |
| `experiments/ios-jit/launcher-backups` | Preserved build33 whole-profile backup/restore implementation |
| `experiments/ios-jit/launcher-loading-release` | Preserved build31 loading UI and phone-tested managed payload pin |
| Other `experiments/ios-jit` directories | JIT runtime/graphics/compatibility patches and reproducible investigation history |
| `docs/ios-jit` | All JIT research, architecture, implementation and acceptance documentation |
| `modern-ios/CelesteIOSFoundation` | Two shared control/platform policies actually used by JIT |
| `modern-ios/Assets/TouchControls` | The reused touch glyph source artwork and its license |
| `vendor` | Pinned ZIPFoundation/CYaml source and licenses |
| `tools` | Independent Cabrillo build, import, validation and repository checks |
| `.private` | Ignored, pinned managed/native inputs and private migration evidence |
| `.build`, `artifacts` | Ignored fresh build output, symbols, receipts and unsigned IPAs |

Historical experiment builders retain their original paths as documentation.
Use `tools/build.py` for this checkout's independent build. They are not a promise
that every historical failed prototype can be rebuilt from the current capsule.
The [file inventory](docs/MIGRATION_FILE_INVENTORY.json) records a reason and hash
for each imported source/document file.

## Apple platforms

iPhone is the primary physical target. Build35 also passed a scoped base-game
run on an iPad mini4 with iOS15.8.8, including touch, save/Quit and native return.
Other tablets, resizing and input combinations still need device evidence.
macOS is a later target and
already hosts runtime integration tests. tvOS and visionOS need separate JIT,
graphics, input and installation investigations. No support is claimed from an
SDK flag alone. See [platform direction](docs/APPLE_PLATFORMS.md).

## Git and distribution

The public source repository uses `main` as its default branch. The owner
authorized its initial commit and publication on14 September2026. The migration
report and evidence ledger retain their earlier, pre-publication Git snapshot.
Do not commit `.private`, game files, FMOD SDKs, signing material, device logs or
generated IPAs.

The launcher remains a private development build. Public original-game preparation
and FMOD redistribution are still release gates. The inherited source license
and dependency notices are retained; they do not grant rights to game or SDK data.
