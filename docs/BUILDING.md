# Building Cabrillo

The local Cabrillo folder independently rebuilds the current unsigned build28.
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

The migration deliberately freezes build28 source and app identity. The current
root build command is a **locked reproduction recipe**, not a release/version
updater: it rejects changed source and has no partially implemented new-release
mode. Keep it as a regression target.

For the next approved implementation, create a new JIT lane or working copy from
the current launcher, give it a new version/build ID, and derive its independent
builder from this root recipe. Generate fresh BuildInfo, native receipts and
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
