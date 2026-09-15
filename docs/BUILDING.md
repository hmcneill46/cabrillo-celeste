# Building Cabrillo

The local Cabrillo folder independently reproduces accepted build28 and builds
the cooperative loading lanes30/31 and native presentation refinement32.
It includes source plus a Git-ignored copy of the pinned dependencies. The
original JIT checkout, the AOT checkout and the owner's original input folder
are not used by the build command.

## Tools and inputs

- Python3 with its standard library. No third-party Python packages are required
  by the root build, verification or native catalogue check commands.
- Xcode26.6, build17F113, installed at `/Applications/Xcode-26.6.app`, with the
  iPhoneOS26.5 SDK. The build pins and checks this toolchain. It targets arm64,
  minimum iOS26.0. Migration was tested on the owner's Intel Mac.
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
