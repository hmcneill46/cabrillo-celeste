# Celeste native mod browser — build28

0.15.0(28), `launcher-catalogue-20260913-28`. Development source for the native
Browse destination. Read [the implementation record](../../../docs/ios-jit/NATIVE_CATALOGUE_BUILD_28.md)
and [phone instructions](PHONE_README.txt).

Mods contains Installed, Browse and Updates. Browse has native search, five
server-side sorts, categories/subcategories, paged image cards, screenshots,
creator details, inert descriptions and explicit ZIP choices. Search shows the
20 closest name matches across all categories, as provided by the Olympus
catalogue service. Clear search to use category filters and global sorts.

Selected file IDs must resolve to exact indexed releases. The production
installer handles dependencies, runtime constraints, original ZIP verification,
enabled state, journal recovery and persisted results. An identical installed
file is reused. A Tools-category page can contain a valid mod (Memorial Helper);
actual Everest metadata determines eligibility. Unindexed and previous files
remain accessible on GameBanana for manual import. There is no desktop runtime
updater or automatic mod installation.

`CatalogueModels.swift` normalizes the service contracts and validates identifiers.
`CatalogueProvider.swift` owns bounded HTTPS/cache/concurrency/cancellation.
`CatalogueUI.swift` owns browsing state, native presentation and bounded images.
`DependencyPlan.swift` adds explicit selected roots; `DependencyInstaller.swift`
uses the existing verified transaction machinery. `main.m` connects the action
and releases catalogue work before the managed game starts.

Resource policy: four network transfers and two screenshot decodes at most;
4 MiB per response; metadata disk cache 24 MiB/64 records; image disk cache
32 MiB/96 records; strict decoded-image cache 16 MiB/32 images, downsampled to
800 pixels with source dimensions/pixel count checked. Keep 200 visible-page
records before continuing into the next window. Metadata TTL 15 minutes,
categories 24 hours, details 10 minutes, images seven days; failures back off
one minute and may use a dated verified cache. Requests occur while browsing.
The installed launcher works independently of catalogue availability. ZIP
downloads still use the existing separate Wi-Fi/cellular preference.

The complete accepted27 managed payload, Mono, FNA/Metal, CelesteIOS support,
CoreLib correction and StikDebug protocol are read-only inputs. `build_managed.py`,
`build_runtime.py`, `build_reflection.py` and `native-build.py` verify accepted
stages. Native ZIP/YAML dependencies and outputs are isolated under
`.build/ios-jit/launcher-catalogue*`. Never build into the AOT checkout or the
accepted24/26/27 lanes. A delivered identity becomes immutable.

Use Xcode26.6 through `DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer`.
Build commands from the repository root:

```sh
python3 experiments/ios-jit/launcher-catalogue/build_managed.py
python3 experiments/ios-jit/launcher-catalogue/build_native.py --target host
python3 experiments/ios-jit/launcher-catalogue/build.py --simulator
python3 experiments/ios-jit/launcher-catalogue/build.py
```

Meaningful gates: `tests/check_installs.py` (use the local YAML/xxhash Python
environment), `tests/check_catalogue.py`, `tests/simulator_smoke.py`,
`tests/check_launcher_ui.py`, `tests/check_catalogue_ui.py`,
`tests/check_host_graphics.py --normal --without-example --catalogue`,
`tests/check_request_protocol.py` and `tests/check_package.py`. Check each
runner's arguments. Simulator fixtures live in simulator Documents and are
compiled out of the device IPA. Test source changes must be reflected in the
final source receipt; retain exact tested executable/build identities.

The phone uses LiveContainer1 with Launch with JIT OFF, saved script blank,
Fix File Picker ON, and StikDebug in LiveContainer2. Keep one game per process,
existing profile/game paths and Export diagnostics. No game or mod reimports
are needed when upgrading. This remains a private test IPA: prepared game IL,
on-device preparation and FMOD redistribution remain release gates.

No commits, pushes or public publishing without the owner's explicit approval.
