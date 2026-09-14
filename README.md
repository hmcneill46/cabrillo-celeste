# Cabrillo

**Celeste Mod Loader for Apple Platforms**

Cabrillo is a native launcher for playing Celeste with Everest mods. Import your
game, browse or import mods, review their dependencies, enable JIT, and play.
The launcher uses SwiftUI; the game and its mods run in the same Mono JIT runtime.

The name comes from Cerro Cabrillo in California. The source repository is
[hmcneill46/cabrillo-celeste](https://github.com/hmcneill46/cabrillo-celeste).

**Morro** is the planned name of the separate fully AOT Celeste project,
[currently hosted as celeste-ios](https://github.com/hmcneill46/celeste-ios).
The projects share ideas and selected platform policies, but have independent
builds, runtime strategies and release decisions. This checkout contains no AOT
application, Xcode project, generated game source, or AOT build cache.

## Current state

Build27 is physically accepted on an iPhone 15 Pro Max running iOS26.5.
Build28 adds native mod browsing, categories, five sort orders, details and
reviewed installations. Its phone acceptance is still pending. The repository
separation preserves build28's existing app identity; changing the in-app name
and icon belongs in a separately versioned release.

Start with [the migration report](docs/CABRILLO_MIGRATION.md),
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
| `experiments/ios-jit/launcher-catalogue` | Current native browser, host, tests and build28 source |
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

iPhone is the proven physical target. **iPadOS is the next intended device family**;
the existing package declares iPhone and iPad, but tablet layouts, resizing, input
and JIT must be accepted on actual hardware. macOS is a sensible later target and
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
