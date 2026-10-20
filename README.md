# Cabrillo

**Celeste Mod Loader for Apple Platforms**

Cabrillo is a native launcher for playing Celeste with Everest mods. Import your
game, browse or import mods, review their dependencies, enable JIT, and play.
The launcher uses SwiftUI; the game and its mods run in the same Mono JIT runtime.

The name comes from Cerro Cabrillo in California. The source repository is
[hmcneill46/cabrillo-celeste](https://github.com/hmcneill46/cabrillo-celeste).

## Downloads and verified builds

[GitHub Actions](https://github.com/hmcneill46/cabrillo-celeste/actions/workflows/release.yml)
builds unsigned iPhone/iPad IPAs from the public source. Published versions appear
under [Releases](https://github.com/hmcneill46/cabrillo-celeste/releases).
Normal pushes run source checks; a maintainer chooses when to publish a version
tag. Manual trial builds produce downloadable Actions artifacts without a Release.

**[Download Cabrillo 0.26.0 / build 57](https://github.com/hmcneill46/cabrillo-celeste/releases/download/v0.26.0/Cabrillo-0.26.0-unsigned.ipa)** ·
[Release page and verification files](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.26.0).
The [tagged GitHub Actions run](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39414920270) passes
fresh compilation, package audits, all five attestations, separate verification
and publication. All five Release assets independently download without sign-in
and pass checksums/API digests and exact tag/source/workflow/run verification.
Release assets persist beyond temporary Actions artifacts.

Version 0.26.0 / build 57 adds recommended Built-in StikJIT for new standalone
iOS 17.4+ installations. Run Celeste prepares and enables JIT with visible progress,
then launches after native checks and known debugger detach. Manual pairing-file
import, actual local-tunnel readiness and a visible, centered Run icon are included.
Existing saved JIT choices, external methods and LiveContainer support remain.

Stable Everest 1.6642.0, the dependency-download and Feather import repairs,
save/profile paths and Shortcut49 are retained. All 299 captured trial sources
and 153 dependency hashes match the release; StikJIT's upstream prebuilt idevice
library is explicitly disclosed. See [change notes](CHANGELOG.md) and
[the verification report](docs/ios-jit/INTEGRATED_STIKJIT_BUILD_57.md).

You need **iOS15 or later, a compatible installation/JIT setup, and your own
Celeste FNA1.4.0.0 game ZIP**. The IPA contains no original/prepared Celeste game
code or original game assets. Cabrillo prepares your imported copy on its first
game launch and reuses that cache afterward.

**FMOD runtime code is included with Firelight's permission. Players do not need
an FMOD account.** Source developers must download their own SDK from FMOD;
Cabrillo does not redistribute SDK components.

Each build includes checksums, a package audit and source/dependency provenance.
GitHub attestations tie the downloaded files to the public workflow and commit.
FMOD, .NET/NuGet binaries and signed Shortcut resources are declared inputs;
this is not a claim that every dependency is compiled from source or that separate
builds are byte-identical. See [how releases work and how to verify a download](docs/RELEASING.md).

## Combined development build

The next test build, **0.29.0 / build58**, brings together the published v0.26.0
work and this Mac's previously unpushed game-input and touch-control development.
It is being validated before a new public release. The download above remains
the published v0.26.0; the features below describe the combined development lane.
See [integration status and source preservation](docs/ios-jit/UNIFIED_BUILD_58.md).

### Game files from itch.io, Steam and Epic

The importer supports the nine original FNA1.4.0.0 distributions used for local
compatibility testing, including Steam and Epic Windows. Read
[how to obtain the correct game ZIP](docs/CELESTE_INPUTS.md) for Steam depot and
Epic download instructions. Existing retained game files can rebuild their
prepared cache without requiring the original temporary import ZIP again.

### Custom touch controls

**Settings → Controls → Customize touch controls** and **Pause → Touch controls**
open a SwiftUI editor. Arrange and resize circles or rectangles, duplicate
buttons, split Jump/Dash regions, and add Crouch Dash or Quick Restart. Controls
can use the entire display, edge to edge. Portrait provides detailed choices;
landscape shows an actual-size layout with a16:9 game-image guide. Layouts can be
saved to Files and shared, including conversion of Morro D3 v2 layouts.

An optional experimental preset uses touch/hold for Jump and an eight-direction
swipe for Dash, independently of the movement joystick. **Feather follows finger**
is also optional and can be changed during play. Both retain Celeste's physics.

The Behavior page uses Celeste's own Hold/Toggle/Inverse Grab logic, remembers
each input method's choice and offers optional toggling that persists across
death and map changes. Controller symbols can be selected manually; Automatic
recognizes DualSense through SDL. Original controller light colours replay after
reconnection. Physical DualSense light behavior still needs device verification.
See the [touch controls guide](docs/TOUCH_CONTROLS.md) and
[local input-preference evidence](docs/ios-jit/INPUT_PREFERENCES_BUILD_57.md).

## Built-in JIT setup

[Build57 /0.26.0](docs/ios-jit/INTEGRATED_STIKJIT_BUILD_57.md) adds integrated
StikJIT for supported standalone installations: connect the local VPN, import
your pairing file and press Run Celeste. Cabrillo shows preparation progress and
verifies JIT before launching. Existing saved JIT choices and LiveContainer
methods remain available. Manual pairing import also works when a tool does not
yet recognize Cabrillo. Sign with debugging permission, preserve the embedded
helper extension, enable Developer Mode and use a valid pairing file. Built-in
JIT requires standalone iOS 17.4+; LiveContainer keeps its existing methods.
The public release passes build/package checks; physical helper/JIT acceptance
remains separate. See [building instructions](docs/BUILDING.md) and the report's
signing and setup details. No iLoader changes are required.

## Home Screen launch in development

[Build50](docs/ios-jit/SHORTCUT_CELLULAR_BUILD_50.md) corrects the cellular launch
sequence: connect the local VPN route, enable Airplane Mode, then check the developer
service before JIT. Native execution, debugger detach and network restoration
remain required. The owner's fresh cellular-start run now passes all26 native JIT
checks, automatic return and restoration; USB logs verify the31.3-second launch.

**Settings → Add Home Screen shortcut** exports bundled Apple-signed templates for
standalone or LiveContainer use. The user imports the file and adds its Home icon.
The release retains the accepted revision49 shortcut; existing users need no reimport.
49 fixes the disappearing setup text and has owner-confirmed phone import plus
actual Apple simulator import/URL execution evidence. App47/shortcut46 retains its
scoped phone Wi-Fi/Travel passes. [Setup and test steps](docs/HOME_SCREEN_SHORTCUT.md)
explain helper requirements, recovery and remaining prompts. New source builds
retain this functionality; their device acceptance is recorded separately.

## Related project

**[Morro](https://github.com/hmcneill46/morro-celeste)** is the separate fully AOT Celeste project.
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

## Platform support and device evidence

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

Build32 is the accepted phone fallback and its loading work was published on
`main` (`16ff42c`). Build34 combines build33's whole-profile backup/restore with
individual desktop save transfers, long-press slot actions and retained rollback.
It also repairs hair and related seeker/tutorial/lava arithmetic errors. The
[build34 report](docs/ios-jit/SAVE_TRANSFERS_BUILD_34.md) records local tests and the
uploaded phone kit. The owner deferred33 testing for one combined34 gate.
Phone34 acceptance remains pending; host/simulator checks do not replace it.

## Earlier device acceptance

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
Build32 remains an accepted fallback. The local touch editor was developed at
the owner's request; its device acceptance remains separate from the earlier
save-manager gate.
Build32 reuses31's exact managed payload. Original28/29/30/31 artifacts remain frozen.

For development, start with [the current handoff](HANDOFF.md),
[the migration report](docs/CABRILLO_MIGRATION.md),
[the roadmap](docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md), and
[the original feasibility audit](docs/ios-jit/FEASIBILITY_AUDIT.md).

## Developers: build locally

The combined development recipe is `tools/build_release58.py`; it targets
0.29.0/build58 with stable Everest1.6642.0, dependency download recovery, copy-based
Files imports, Built-in StikJIT and the touch/input features above. Use
`tools/build_release57.py` to reproduce the published v0.26.0 source lane.
Build58 validation and delivery are tracked in
[the integration report](docs/ios-jit/UNIFIED_BUILD_58.md).

Use macOS, Python3.12 or later, CMake, Mono6.14.1 (including `sn`) and **Xcode26.6 /17F113**. Download your own
**FMOD Engine1.10.09 iOS SDK** from [fmod.com](https://www.fmod.com/download), then:

```sh
python3 tools/build_release58.py --work .build/my-source-build \
  --output .build/my-source-build/output --fmod-sdk '/path/to/FMOD Programmers API'
```

This fetches pinned public dependencies and compiles the current app with your
licensed FMOD input. It needs no game ZIP, private compiled capsule or Apple
signing account. Keep SDK files and credentials out of Git and shared build outputs.
Set `DEVELOPER_DIR` if your Xcode path differs from
`/Applications/Xcode-26.6.app/Contents/Developer`.

[The build guide](docs/BUILDING.md) covers requirements and outputs.
[The release guide](docs/RELEASING.md) explains the protected Actions environment,
why FMOD is fetched separately, and which files may be published. Historical
reproduction commands remain documented separately.

## Repository layout

| Location | Reason it is here |
| --- | --- |
| `experiments/ios-jit/launcher-unified58` | Combined build58 source, preserving both development histories |
| `experiments/ios-jit/launcher-input-preferences` | Preserved local57 input/editor implementation and regression fixtures |
| `experiments/ios-jit/launcher-integrated-jit` | Published57 standalone StikJIT host/helper integration |
| `experiments/ios-jit/launcher-dependency-downloads` | Build56 general archive relocation, current mirror metadata and runtime/dependency parity |
| `experiments/ios-jit/launcher-everest6642` | Build55 stable1.6642 source patch, synchronized runtime identities and compiled metadata audit |
| `experiments/ios-jit/launcher-copy-picker` | Build54 copy-based game/mod imports with retained build53 signing adaptation |
| `experiments/ios-jit/launcher-owned-game` | Build38 source-built bootstrap and preparation of the user's original game |
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
| `release` | Current release identity, pinned dependency inputs and verified Shortcut resources |
| `.private` | Ignored, pinned managed/native inputs and private migration evidence |
| `.build`, `artifacts` | Ignored fresh build output, symbols, receipts and unsigned IPAs |

Historical experiment builders retain their original paths as documentation.
Use `tools/build_release58.py` for the combined development recipe and `tools/build.py` for
accepted28 reproduction. Historical tools are not a promise
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

FMOD runtime permission is recorded; its SDK remains a separately licensed build
input. Users supply their original game files. Source licences and dependency
notices do not grant rights to redistribute game or SDK data.
