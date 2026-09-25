# Building Cabrillo

The local Cabrillo folder independently reproduces accepted build28 and builds
the cooperative loading lanes30/31 and native presentation refinement32.
It includes source plus a Git-ignored copy of the pinned dependencies. The
original JIT checkout, the AOT checkout and the owner's original input folder
are not used by the build command.

For checks that run from a fresh **public clone**, use
[the CI and release guide](RELEASING.md). GitHub Actions compiles the current
native save/backup test suite without `.private`. Public IPA publishing remains
gated: the recipes below still require private inputs and do not meet the public
release contract.

## Tools and inputs

- Python3 with its standard library. No third-party Python packages are required
  by the root build, verification or native catalogue check commands.
- Xcode26.6, build17F113, installed at `/Applications/Xcode-26.6.app`, with the
  iPhoneOS26.5 SDK. The build pins and checks this toolchain. It targets arm64,
  minimum iOS26.0 for historical lanes; build35 explicitly rebuilds the required
  archives and targets iOS15.0. Migration was tested on the owner's Intel Mac.
- The local `.private` folder. Its 455 locked build inputs total98,059,597 bytes.
  They include16 native archives, matching Mono/SDL headers, the accepted managed
  payload, and frozen build28 resources. The separate small native-test fixture
  set contains11 files totaling308,734 bytes.

Back up `.private` separately from Git. A source clone alone deliberately cannot
contain prepared Celeste game IL or licensed FMOD binaries. Reproducibility with
the owner's local inputs is different from a public source-only bootstrap or
permission to redistribute the resulting IPA.

## Reproduce the delivered IPA

From the Cabrillo root:

```sh
python3 tools/build.py --reproduce-build28 \
  --work .build/my-reproduction \
  --output artifacts/my-reproduction
python3 tools/verify_reproduction.py artifacts/my-reproduction
```

Both directories must be new. The tool refuses to overwrite earlier builds.
The verified migration output is already in `artifacts/cabrillo-build28/`:

- `CelesteJITEverest-unsigned.ipa` —23,812,187 bytes.
- `CelesteJITEverest.app.dSYM` —symbols kept outside the IPA.
- `build-receipt.json` and `build.log` —actual new compilation provenance.
- `verification.json` —independent package, unsigned and UUID checks.

Expected full IPA SHA256:

```text
87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2
```

The build recompiles58 source inputs:21 ZIPFoundation Swift files, six CYaml C
files,14 launcher Swift files, and17 native bridge/generated-table C/Objective-C
inputs. It generates symbol tables from the actual libraries, rebuilds the icon
catalogue with actool, links, generates symbols, strips debug information from
the app, and packages the unsigned IPA. It does **not** copy a prebuilt launcher
executable or IPA. The copied dependency folder contains neither.

As the original build28 did, it links the accepted Mono/system/renderer/audio/Lua
archives and reuses the201 managed assemblies. Rebuilding Mono, FMOD, Everest,
patched game IL and every historical experiment from upstream is outside this
specific fresh launcher build. Their JIT patches, pins and investigation sources
remain in `experiments/ios-jit`; their upstream SDKs and large historical working
directories are not silently read from another checkout.

## What exact reproduction means here

Build28 embedded a build time, historical commit and dependency receipts, and its
ZIP stored file timestamps/attributes. Reproduction retains those historical
resource bytes and ZIP metadata. The new receipt records the actual build date,
commands and hashes separately. The embedded date is not a claim that the fresh
compilation happened on13 September.

The current Apple linker was observed to choose two orders for Objective-C
message-send GOT entries with identical object files. Repeating the same link
and adding `-reproducible` both demonstrated this. The recipe therefore allows
at most eight relinks and accepts only an executable whose **entire content,
with just its16 UUID bytes zeroed, matches the locked historical hash**. The
successful fresh migration run matched on the second link. No instruction,
pointer or data patch is used to force that match; a differing build fails.

After that exact check, the recipe restores the historical UUID and synchronizes
the freshly generated dSYM. It checks the resulting whole executable hash, then
the whole IPA hash. A negative control changing an executable code byte is
rejected. Apple describes the purpose of hash-derived build UUIDs in
[TN3178](https://developer.apple.com/documentation/technotes/tn3178-checking-for-and-resolving-build-uuid-problems).
This narrow restoration belongs only to historical reproduction; new code must
receive a new build identity and matching symbols.

Debug source paths are normalized to the historical spelling for this comparison.
Those strings do not create a dependency on the old folder. The independent
build was run with macOS sandbox rules denying reads and writes to all three
old/input directories; the denial controls and exact policy are retained in
`.private/migration/isolation-controls.json`.

## Native regression and repository checks

```sh
python3 tools/check_catalogue.py --output .build/my-catalogue-check
python3 tools/audit_repository.py
```

The catalogue command compiles the production catalogue, dependency planner,
installer, reports and ZIP/YAML dependencies fresh for macOS. Its default48
checks use locked, dated service responses and synthetic ZIPs. They cover file
selection, requirements, pins, cache reuse, offline errors, cancellation before
play, reviewed transactions, accurate reports and preservation of unknown saves.
No game assets or third-party mod ZIPs are needed by the default checks.
`--live` additionally contacts the services and installs two small original mods
into the isolated host fixture; it is optional and was not repeated for this
migration. Neither command establishes a physical-device gameplay PASS.

The repository check compares the file inventory, all228 delivered source hashes,
49 native/vendor source hashes, the455 private inputs, Git exclusions and local
symlink boundaries. The migration snapshot records its original pre-commit state;
the live audit reports the current Git state. The owner subsequently authorized
initial public publication to `hmcneill46/cabrillo-celeste` on14 September2026.

## Continue development

The [build29 startup preparation](ios-jit/STARTUP_PREPARATION_BUILD_29.md) now
provides a separate runnable native recipe in `tools/build_development.py`:

```sh
python3 tools/build_development.py --check-inputs
python3 tools/build_development.py \
  --work .build/my-startup-preparation \
  --output artifacts/my-startup-preparation
python3 tools/verify_development_build.py artifacts/my-startup-preparation
python3 -m unittest discover -s tools/tests -v
python3 tools/check_development_package.py artifacts/my-startup-preparation \
  --output .build/my-package-controls
```

The verified local output already exists in `artifacts/cabrillo-build29-preparation`.
It is Cabrillo0.15.1 (29), with passive startup timings and the new name, and
remains local without phone acceptance. [Build28's phone gate is now accepted](ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md).
The new recipe keeps the
existing guest/data identity, recompiles native sources, generates current
resources/receipts and keeps the linker's new UUID with matching external dSYM.
It rejects existing output directories, path aliases and changed pinned inputs.
No historical timestamps, linker retries or UUID restoration are used.

The lane's `BuildIdentity.json` and `Info.plist` are its version authority.
Later implementation changes require a new version/build identity and separate
output; build30 now owns the separate `launcher-loading` lane below.
The recipe reuses all accepted managed/game/runtime/renderer inputs. It cannot
rebuild changed C# or prepared game/FNA IL. Use the build30 managed flow below
for that work; its SDK/upstream/tool inputs are now pinned inside Cabrillo.
See the preparation report's dependency table. Preserve emitted29 artifacts.

The migration deliberately freezes build28 source and app identity. The current
`tools/build.py` command is a **locked reproduction recipe**, not a release/version
updater: it rejects changed source and has no partially implemented new-release
mode. Keep it as a regression target.

For the next implementation, use the separate development recipe above with
a new version/build ID and port the required managed stages. Generate fresh BuildInfo, native receipts and
resources from that lane; do not retain historical metadata or UUID restoration
for changed code. Keep the existing bundle identifier and data paths unless a
separate migration is designed, so the owner's imports and saves survive. Apply
the Cabrillo display name in that new version, then run the appropriate host,
simulator and physical checks.

If changing the managed runtime or renderer, rebuild only the affected pinned
dependencies into new Cabrillo-private stages, preserve accepted dependencies,
and record their new source/toolchain/patch/output hashes. Historical builders
document this work but may need their own external tools/SDK inputs restored;
they are not the standalone current launcher entry point.

`tools/import_legacy.py <old-checkout>` records the one-time extraction procedure.
It was used to populate this folder and refuses an existing migration receipt.
It is not run by builds. Do not reimport over ongoing Cabrillo development.

## Build30 cooperative loading

The new lane is `experiments/ios-jit/launcher-loading`, version0.16.0 (30).
`tools/build_loading_managed.py` builds the changed Everest/game/hook assemblies
and adapter from a private, explicitly pinned capsule. `tools/build_loading.py`
then compiles the native launcher and packages that exact managed receipt.
The16 accepted native runtime/renderer archives remain unchanged. Use new work
and output directories; preserve every existing receipt and artifact.

The additional `.private/loading-inputs` capsule contains19,618 files,
2,413,428,206 bytes: the pinned Everest tree/submodules, SDK8.0.422 and9.0.300,
offline NuGet packages, private original/prepared IL, host Mono libraries and
exact touch resources. `ManagedDependencies.json` locks its manifest. Its one-time
import used `tools/prepare_loading_inputs.py --legacy <explicit-read-only-path>`;
a build never reads or falls back to that legacy path. Preserve the capsule
separately from Git. Host integration fixtures are in separate ignored,
hash-recorded `loading-host-inputs` and `loading-sj-inputs` directories.

```sh
python3 tools/build_loading_managed.py --work .build/my-loading-managed
python3 tools/build_loading.py \
  --managed .build/my-loading-managed/receipt.json \
  --work .build/my-loading-native --output artifacts/my-loading
python3 tools/verify_loading_build.py artifacts/my-loading
python3 tools/check_loading_package.py artifacts/my-loading \
  --output .build/my-loading-package-controls
python3 tools/check_loading_contracts.py --work .build/my-loading-contracts
python3 tools/check_loading_dependencies.py --work .build/my-loading-dependencies
python3 tools/check_loading_assembly.py --managed .build/my-loading-managed/receipt.json \
  --work .build/my-loading-assembly
```

The managed command restores exclusively from its copied offline cache, patches
only a fresh source tree, preserves unrelated resource hashes, and checks FNA
semantics. The native verifier requires precisely four changed managed DLLs,
197 preserved managed DLLs, unchanged protocol/data identity, a fresh UUID and
matching external symbols. No historical metadata or UUID restoration is used.

For real private game integration, run `tools/check_loading_host.py --managed
<receipt> --work .build/<new-host>` and then repeat with `--cached`. Run
`tools/check_loading_host_edges.py --managed <receipt> --host .build/<host>
--work .build/<new-edges>` for multiple-module, failure and full SJ controls.
`tools/check_loading_ui.py --work .build/<new-ui> --device <simulator-UDID>`
compiles a separate presentation fixture; it cannot ship in the device IPA.
Read the [build30 report](ios-jit/RESPONSIVE_LOADING_BUILD_30.md) for exact results,
remaining indivisible work and physical acceptance requirements.

## Build31 delivery refinement

Build31 (0.16.1) corrects the archive/folder counter wording after build30 was
packaged. `launcher-loading-release/ManagedPayload.json` pins the exact validated
build30 managed receipt and every resource. The native lane has a new identity;
all build30 source/artifacts are preserved. Reusing this managed payload is
intentional. Changing it or frozen source requires another build identity.

```sh
python3 tools/build_loading_release.py \
  --managed .build/loading-managed30-d/receipt.json \
  --work .build/my-loading31 --output artifacts/my-loading31
python3 tools/verify_loading_release.py artifacts/my-loading31
python3 tools/check_loading_release_package.py artifacts/my-loading31 \
  --output .build/my-loading31-controls
```

For current results and phone delivery, see the
[build31 report](ios-jit/RESPONSIVE_LOADING_BUILD_31.md). Build30 remains local.

## Build32 first-frame presentation

`launcher-first-frame`, version0.16.2 (32), contains the passive native loading
view and guarded first-rendered-frame window handoff. It pins the exact same
validated managed receipt/resources as phone-tested31. The cooperative managed
source and native runtime/renderer archives remain unchanged. Preserve all earlier
source lanes and outputs; use new directories:

```sh
python3 tools/build_first_frame.py \
  --managed .build/loading-managed30-d/receipt.json \
  --work .build/my-first-frame32 --output artifacts/my-first-frame32
python3 tools/verify_first_frame.py artifacts/my-first-frame32
python3 tools/check_first_frame_package.py artifacts/my-first-frame32 \
  --output .build/my-first-frame32-controls
python3 tools/check_first_frame_ui.py --work .build/my-first-frame-ui --device <simulator-UDID>
```

`tools/check_first_frame_observer.py --work .build/<new> --evidence <private-export>`
compiles the production observer, checks draw/Present ordering and replays the two
collected build31 processes. `tools/check_first_frame_host.py --work .build/<new>
--host .build/loading-host30-c --managed .build/loading-managed30-d/receipt.json`
observes early real game images in an isolated copy of the existing host fixture.
It uses the established macOS Mono BCL and unchanged game/FNA/adapter bytes.
Extra image readbacks exist only in this external host fixture, never the IPA.
See [the build32 report](ios-jit/FIRST_FRAME_BUILD_32.md) and evidence ledger for
current checks and physical acceptance status.

## Build33 profile backups

Build33 uses `experiments/ios-jit/launcher-backups` and reuses every managed
assembly from accepted32. It adds native Swift profile storage/summary/UI and
Objective-C lifecycle/document-picker integration. Use fresh output directories:

```sh
python3 tools/build_backups.py --managed .build/loading-managed30-d/receipt.json \
  --work .build/my-backups-build --output artifacts/my-backups-build
python3 tools/verify_backups.py artifacts/my-backups-build
python3 tools/check_backups_package.py artifacts/my-backups-build \
  --output .build/my-backups-package-controls
python3 tools/check_backups.py --work .build/my-backups-tests
python3 tools/check_backups_ui.py --work .build/my-backups-ui --device <simulator-udid>
python3 tools/check_backups_host.py --work .build/my-backups-game \
  --host .build/loading-host30-c --native .build/my-backups-tests/native \
  --managed .build/loading-managed30-d/receipt.json
```

The source/resource hashes and new executable/dSYM UUID are verified as in32.
The ZIP format limits, recovery contract and actual delivery status are in
[the build33 report](ios-jit/PROFILE_BACKUPS_BUILD_33.md). New implementation after
packaging33 needs a new identity. Builds34–37 now exist; the next unused number is38.

## Build34 individual saves and numerical repair

`experiments/ios-jit/launcher-save-transfers` is a fresh frozen lane. The production
native build pins `.build/precision-managed34-final/receipt.json`, SHA-256
`80bb0a19d7f63944aa6fe23379338c747db776cae51744c73482a390425b13aa`.
It derives from the accepted loading receipt, changing only Celeste.dll and four
method bodies. All other managed resources and16 native archives remain unchanged.
The base/derived receipts, repair report and source/resource hashes are required;
the capsule cannot silently fall back to a legacy checkout.

```sh
python3 tools/build_save_transfers.py --managed .build/precision-managed34-final/receipt.json \
  --work .build/my-save-transfers-build --output artifacts/my-save-transfers-build
python3 tools/verify_save_transfers.py artifacts/my-save-transfers-build
python3 tools/check_save_transfers_package.py artifacts/my-save-transfers-build \
  --output .build/my-save-transfers-controls
python3 tools/check_save_transfers.py --work .build/my-save-transfer-tests
python3 tools/check_save_transfers_ui.py --work .build/my-save-transfer-ui \
  --device <phone-simulator-udid> --device <ipad-simulator-udid>
python3 tools/check_precision_repair.py --managed .build/precision-managed34-final/receipt.json \
  --work .build/my-precision-controls
python3 tools/check_save_transfers_host.py --work .build/my-save-transfer-game \
  --host .build/loading-host30-c --native .build/my-save-transfer-tests/native \
  --managed .build/precision-managed34-final/receipt.json --hair-fixed
python3 tools/check_vanilla_save.py --work .build/my-vanilla-save \
  --game .build/my-save-transfer-game --native .build/my-save-transfer-tests/native
```

The original repair command was `python3 tools/repair_player_precision.py --base
.build/loading-managed30-d/receipt.json --work .build/precision-managed34-final`.
That directory is immutable. Fresh repair experiments require another directory;
their fresh managed MVID/receipt must not replace the shipped pin. A new native
build similarly receives a new UUID and timestamp; no historical UUID restoration
is permitted. Changed implementation or dependencies require identity35 or later.

See [the build34 report](ios-jit/SAVE_TRANSFERS_BUILD_34.md) for119 native checks,
16 simulator UI tests, numerical scope, vanilla compatibility limits and the
combined phone gate. The original serializer test uses the owner's local Mono
installation and private original game files; it ships neither in the IPA.

## Build35 — iOS15 and input timing

[Build35 report](ios-jit/PLATFORMS_BUILD_35.md) records the native source import,
seven rebuilt archives, scoped managed adapter change, real iPad acceptance and
pending phone gate. The standalone pinned capsule remains unchanged.

```sh
python3 tools/build_platform_runtime.py --inputs .private/platform-inputs35 \
  --manifest-sha256 6f57a25d28981cd827f920324737f06ec8ff0a51ef2f3f5efe007aeffa9f027b \
  --work .build/platform-native-new
python3 tools/build_platform_adapter.py --base .build/precision-managed34-final/receipt.json \
  --work .build/platform-managed-new
python3 tools/build_platforms.py --managed .build/platform-managed35-b/receipt.json \
  --work .build/platforms-reproduction --output artifacts/platforms-reproduction
python3 tools/verify_platforms.py artifacts/platforms-reproduction
```

The last two commands use35's exact native/managed receipts from its lane locks.
Fresh runtime rebuild receipts need explicit review and a new identity/pin before
being used in a changed package. Reproduction gets fresh metadata/UUIDs; it does
not claim the delivered IPA's byte identity. All16 selected archive OS floors,
managed resources and executable/dSYM identity are independently checked.
The four Motion Smoothing host cases use a private cloned profile and the original
released ZIP; no game files or mod ZIPs enter Git. Device tooling and USB artifacts
are separate ignored dependencies, not app build inputs.


## Build36 visibility restoration

Build35 is frozen and contains a Motion Smoothing startup regression. Build36
restores only the accepted Mono class.c archive member, with all other35 native
archives and managed resources pinned. Run the runtime restoration builder into
a fresh .build directory, then the field/method and original/corrected Motion
Smoothing checks. The final lane pins their receipts in RuntimeValidation.json.

```sh
python3 tools/build_visibility.py --managed .build/platform-managed35-b/receipt.json --work .build/visibility-build36-reproduction --output artifacts/cabrillo-build36-reproduction
python3 tools/verify_visibility.py artifacts/cabrillo-build36-reproduction
```

See docs/ios-jit/VISIBILITY_BUILD_36.md for the exact patch and acceptance limits.


## Build37 Everest stable1.6580

The source snapshot is separately pinned in launcher-everest6580/ManagedDependencies.json.
The managed builder applies the existing cooperative loading and four-method
precision repairs to the new upstream source. Generated native/managed runtime
identities come from the same JSON. FNA semantic reuse is checked, and every
other managed assembly and all16 corrected36 native archives stay exact.
EverestValidation.json pins native profile tests, real gameplay/source controls,
Motion Smoothing60/120 and the vanilla save roundtrip before packaging.

```sh
python3 tools/build_everest6580_managed.py --work .build/everest-managed37-reproduction
python3 tools/build_everest6580.py --managed .build/everest-managed37-b/receipt.json --work .build/everest-build37-reproduction --output artifacts/cabrillo-build37-reproduction
python3 tools/verify_everest6580.py artifacts/cabrillo-build37-reproduction
```

The packaged lane requires its exact validated managed receipt. A newly rebuilt
managed payload has a new identity and needs a separate reviewed build lane;
never overwrite a historical receipt to make a different payload pass its lock.
