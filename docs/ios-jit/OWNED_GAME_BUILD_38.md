# Build38 — prepare the user's game after import

Cabrillo0.21.0 / build38 moves original and prepared Celeste code out of the app
bundle. This is local development on `codex/owned-game-import`; no new GitHub
write or public IPA publication is authorized by this task. Packaging and
physical-device status are recorded in the evidence section below.

## What the user does

Import the original, unmodified Celeste FNA1.4.0.0 ZIP, enable JIT for this process,
and start the game. Cabrillo verifies the original files, prepares Everest and
the Apple adaptations, generates the mod hooks, and saves a verified generation
in Documents. This heavier preparation happens once per preparation recipe.
Subsequent launches verify and reuse it without needing the ZIP again.

Existing installations need to select their original ZIP once after upgrading:
older Cabrillo imported assets but obtained game code from its bundle. Existing
profiles, mod selections, saves, backup/rollback stores and unknown sidecars retain
their existing paths. The app keeps the selected ZIP after a failed or cancelled
attempt; it deletes only its own staged copy after successful preparation.

The loading screen reports real stages with an indeterminate activity bar. It
retains passive details and the first-draw/readback handoff. After preparation,
native callbacks bind directly to the existing game adapter. There is no extra
preparation layer in each gameplay frame.

## What is in the app

- Publicly built Cabrillo, Everest patch rules and its mod UI resources, FNA, MonoMod, Cecil, Lua and support
  modules; public .NET runtime packs and the rebuilt native JIT/renderer libraries.
- Hash-only identities for the supported original ZIP and its content.
- The existing explicit native FMOD SDK libraries, for private testing only.
- Required licenses, notices, dependency fingerprints and source receipts.

**Absent:** original/prepared Celeste assemblies, Celeste.Content, generated
MMHOOK_Celeste, original game assets, third-party mod ZIPs and the build-only
stripped reference assemblies. A Cecil metadata audit checks actual assembly
identities, including the bundled project-authored canary ZIP; a package scanner
checks filenames, asset types, signing material, all file hashes and symbols.

## Preparation and recovery

`Cabrillo.Bootstrap.dll` has no reference to the game adapter or Celeste. It
accepts exactly the three recorded original file identities from the selected
archive. Existing content-envelope/path checks apply. The game remains unloaded
until all preparation stages and generation receipts complete.

Originals are retained under `Documents/GameCode/v1/original/<source identity>`.
Prepared generations live under the preparation-recipe hash, with an atomically
replaced pointer. Tool hashes are part of that recipe. Changed tool/game recipes
or a damaged prepared generation trigger rebuilding; damaged originals require
the original ZIP. Failed/cancelled work never publishes a partial generation.
Recognized unpublished scratch can be recovered; unknown files and published
older generations are retained. A failure after assembly activation requires a
fresh app process.

The preparation runs the same coreification, Everest patching, HookGen and scoped
platform/physics adaptations as the previous runtime. The tested four-method
hair/seeker/tutorial/lava repair and ten deliberate precision sites remain.

Two Everest lookups now distinguish bundled patch rules from game code in
Documents. The Strawberry Jam regression fixture also exposed Cecil's default
assembly lookup assuming game and runtime were together. A narrow fallback in
`BaseAssemblyResolver.Resolve` consults the verified prepared directory only
after normal resolution fails. The bootstrap sets that directory after commit.
The existing resolver still throws for unrelated missing assemblies. See the
[pinned upstream resolver](https://github.com/jbevain/cecil/blob/0.11.6/Mono.Cecil/BaseAssemblyResolver.cs).

## Source build

Public dependencies are URL/commit/checksum pinned in
`release/owned-game-dependencies.json`; resolved NuGet archives are separately
hash pinned. The public-source preparation step verifies every patch changes its
intended files. This explicit check was added after an intermediate link test
exposed Git-format patches being skipped from an ignored nested working folder.
Those intermediate outputs are not delivery artifacts.

`prepare_owned_public.py`, `build_owned_managed.py` and `build_owned_native.py`
rebuild without the private capsule, old checkouts or a game ZIP. The adapter
compiles against metadata-only references generated from Everest's public
stripped reference and MIT patch source; those references never enter the app.
The local build denial policy blocks those private folders during compilation.
FMOD preparation instead takes an explicit SDK directory, verifies the exact
1.10.09 input archives, extracts arm64 and localizes the six reviewed private
Ogg/Vorbis collisions without changing public FMOD exports.

```sh
python3 tools/build_public_release.py \
  --work .build/my-owned-source \
  --output .build/my-owned-source/output \
  --fmod-sdk '/path/to/FMOD Programmers API'
```

This explicit SDK option produces a **private** local build and truthful private
input provenance. Public mode refuses to run until the release manifest records
FMOD permission and an authorized, checksum-pinned SDK download for CI. Standard
public .NET/NuGet binaries and publicly supplied bindings are disclosed; this is
not a claim that proprietary dependencies are open source or every binary is
compiled from source in one job.

The native app builder is `tools/build_owned_game.py`; it accepts the three
explicit managed/native/FMOD receipts, recompiles the launcher with Xcode26.6,
keeps its fresh UUID and emits a matching dSYM. It preserves the bundle identity
and iOS15 deployment target. Earlier packaged lanes28–37 remain frozen.

## Evidence and delivery

Final managed inputs are `.build/owned-public-managed38-e/receipt.json`, built
from `.build/owned-public-inputs38-e/receipt.json`. The native dependency build is
`.build/owned-public-native38-e/receipt.json`; FMOD is explicitly prepared in
`.build/owned-fmod38-c/receipt.json`. The public stages ran with reads denied to
the private capsule, both historical checkouts, original-input folder and the
owner's ZIP. Five denial controls confirm those boundaries. The native tools
honor `DEVELOPER_DIR` and still require the exact Xcode version; GitHub's Xcode
installation path differs from the local one.

| Check | Final evidence | Result |
| --- | --- | --- |
| Original import, cache, changed recipe, corruption, cancellation and recovery | `.build/owned-game38-store-final` | 19 checks pass |
| Cold and cached game, hair, transfers, save readback, resume and normal Quit | `.build/owned-game38-host-public-c` | Both runs pass |
| Strawberry Jam, full pinned dependency selection, save/resume/Quit | `.build/owned-game38-sj-d` | Cold and warm mod-cache runs pass |
| Original Motion Smoothing1.8.0 | `.build/owned-game38-motion-final` | Fast/Fancy at60/120 pass |
| Native profile, backups and save transfers | `.build/owned-profiles38-a` | 119 checks pass |
| Loading presentation and first-frame guards | `.build/owned-loading-ui38-a` | Seven simulator tests pass |
| Public release/build boundaries | `.build/owned38-python-tests-final.log` | 20 Python tests pass |
| Workflow syntax | Actionlint1.7.12 | Both workflows pass |

The real-game host fixtures use the final game-free managed payload with an
explicit retained macOS native test runtime. They are not tests of the new iOS
native archives on a device. The final cold code preparation took15.65s and warm
verification0.039s on this Intel Mac, excluding asset import and normal game/mod
startup. These are not iPhone/iPad timings or sustained120Hz evidence.

The unsigned IPA and matching dSYM are in `artifacts/cabrillo-build38-final`.
Independent payload and release scanners pass:199 bundled managed assemblies,
zero original/prepared game assemblies, no original content, no signing material.
Its18,659,553 bytes have SHA256
`9968253600c30566a527d97a96780dad353cdf616be8f2af9e0ec9ae8e0f2e03`;
the fresh executable/dSYM UUID is `4b29f84240823c0892780a847167a066`. All230 public
implementation inputs are frozen with a source archive. The34–37 frozen manifests
still match their92/174/183/220 inputs respectively.

All six kit files are **confirmed uploaded** to
`iCloud Drive/Celeste JIT Tests/0.21.0-build-38`, with verified local bytes. The kit
contains a short combined first-import/cached-launch guide and a new Results
folder. Previous Results and fallback installers remain preserved. This is not
confirmation of a phone download or execution.

TrollStore installed38 on the connected iPad, retaining all11 captured save and
profile files byte-for-byte. The original875,540,825-byte ZIP was transferred over
USB, verified remotely and staged for its first import. The prior suspended37
process was retired for a fresh launch. Native launch and first/cached gameplay
checks are awaiting the owner unlocking and opening Cabrillo; no38 device PASS
is claimed. Full native save-manager backup/restore/transfer and earlier37
lifecycle gates remain separate.

The [evidence ledger](OWNED_GAME_BUILD_38_EVIDENCE.json) pins these receipts.
Any further implementation change needs the next identity39; keep this package,
its230 source inputs and all preceding artifacts immutable.

## Public release boundary

The remaining known distribution dependency is **FMOD permission and authorized
SDK delivery to CI**. `release/current.json` stays blocked and the public release
workflow cannot publish this private build. No permissions have been inferred
from another port, and no email has been sent. Device acceptance remains a
separate quality gate before designating a stable public release.
