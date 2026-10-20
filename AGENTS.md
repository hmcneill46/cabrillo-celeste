# Cabrillo development

Start a fresh development chat with [HANDOFF.md](HANDOFF.md). It records the
accepted build32 phone fallback, accepted build35 iPad base-game run, accepted build36 phone base-game/Motion Smoothing runtime gate, delivered
build37 Everest upgrade with unexpected phone exits and a pending combined saves gate, evidence review and independent build constraints. Recheck its dated state before acting.

## Scope and ownership

- Cabrillo is the independent Celeste/Everest JIT launcher for Apple platforms.
  Read `docs/CABRILLO_MIGRATION.md`, `docs/BUILDING.md`, the JIT feasibility audit
  and roadmap before changing the build.
- The owner chose Cabrillo for JIT and Morro for the separate fully AOT project.
  The searchable product description is "Celeste Mod Loader for Apple Platforms";
  repository: `https://github.com/hmcneill46/cabrillo-celeste`, with remote
  `origin` and default branch `main`.
- Do not commit, push, create/publish a remote, or write to GitHub without explicit
  owner approval. Local reversible edits, tests and experiments are authorized.
- The owner explicitly authorized the initial commit/push and chose a public
  repository on14 September2026. That first-publication authorization is recorded;
  it does not grant blanket approval for unrelated future GitHub writes.
- On15 September the owner separately authorized committing/pushing the completed
  loading work through build32 and its phone acceptance, then continuing local
  development on the next feature. Verify publication state in HANDOFF.md.
- On25 September the owner requested GitHub Actions for the current source and
  explicitly chose: "Set up CI now; keep IPA publishing gated until public
  packaging is ready". This authorizes publishing the current public source and
  these workflows. It does not authorize publishing private IPAs or clearing
  unresolved distribution gates. See `docs/RELEASING.md` and the latest handoff;
  earlier no-publication statements are historical for this scoped request.
- On29 September the owner explicitly requested: "commit it, review it then push
  it to GitHub". This authorizes publication of the completed source through
  app50/shortcut49, its evidence summaries and CI corrections. Earlier statements
  that these changes lack GitHub authorization are historical. It does not
  authorize public IPA releases, clearing FMOD gates or unrelated future writes.
  See `docs/ios-jit/SOURCE_PUBLICATION_BUILD_50.md` for scope and review.
- Both `/Users/harrymcneill/Projects/celeste-ios` and the legacy
  `/Users/harrymcneill/Projects/Celeste-Everest-JIT-Apple-Platforms` are read-only.
  Never build into, clean, reset or otherwise change those checkouts/caches.
- Preserve originals in `/Users/harrymcneill/Projects/Celeste Required Files`.
  No game code/assets, FMOD SDKs, signing identities, pairing data or private
  logs may enter Git. `.private`, `.build` and `artifacts` remain ignored.
- Use Xcode26.6. Historical lanes use the local `.private` capsule as an explicit pinned
  dependency, not a Git source directory. Build38 uses public source receipts and
  an explicit FMOD SDK instead. Never silently fall back to a legacy checkout.

## Build57 / 0.28.0 — live input preferences, 3 October

The owner requests live feather controls in the touch editor, original Celeste
grab semantics with separate input-method preferences, optional persistent toggling,
controller symbol selection and investigation of DualSense recognition/colours.
Work is local in `launcher-input-preferences`; no new GitHub write is authorised.
Public workflows still select52. Read `docs/TOUCH_CONTROLS.md` and
`docs/ios-jit/INPUT_PREFERENCES_BUILD_57.md` with its evidence ledger.

Pause → Touch controls… → Details → Behavior exposes the live options. Save applies
changes without restarting; Cancel retains saved preferences. Feather uses the
existing preference and original physics. Grab feeds original virtual input and
uses Celeste's own GrabMode/UpdateGrab/GrabCheck. Changing its ordinary Options
setting remembers the mode for the active touch/controller/keyboard source.
Default resets normally. Until untoggled preserves the original latch across
actual death and map changes, separately for each source; changing mode/behaviour
or ending the game clears it. No held state is stored across app launches.

Automatic symbols use the selected FNA/SDL controller type, recognising DualSense
where Everest's older GUID list does not. Manual Xbox/PlayStation/Switch/Stadia
symbols retain bindings and explicit mod overrides. Original light colours pass
through FNA/SDL and replay after late connection, reconnect, player change and
foreground return. Physical DualSense colours remain a device gate. Native editor
dismissal now also clears isolation after discarding an iPad confirmation dialog.
The full-display placement and actual-size landscape editor remain unchanged.

Final managed payload: `.build/input57-managed-c/receipt.json`. 191 of199 DLLs
match56; the adapter changes and seven pinned public MonoMod/NLua dependencies
rebuild. Bootstrap/preparation/FNA/support module and16 native dependency archives
remain exact56. Native/FMOD receipts: `.build/release51-local/{native,fmod}`.
Both signed49 Shortcuts are unchanged. `tools/build_release57.py` provides the
separate fresh public-source build with a developer-owned FMOD SDK. No original
or prepared game code/assets, SDK components or signing material are bundled.

59 Swift and2,743 managed policy/geometry controls, six actual Apple UI tests,
three complete real-game runs with56 new input checks each, and a separate10-check
actual death/respawn/cross-map run pass. Original Motion Smoothing1.8.0 is checked
at60/120 Fast/Fancy. Receipts are `.build/input57-{policy-b,ui-c,host-e,lifecycle-a,motion-d,motion-e}/receipt.json`.
The pinned Mac SDL virtual backend tests real input/LED callbacks; PS5 type is
supplied at the native query boundary because its virtual bus hides VID/PID.
These are host/simulator checks, not physical57 acceptance or sustained120Hz.
55/56 Results remain empty at review; prior device gates remain distinct.

The independently checked57 IPA and matching dSYM are in
`artifacts/cabrillo-build57-final`. IPA SHA256
`7b8abb06247baa0ac1e1fa49535a50c34c5e8534dbd50ab3e5ad1368503fdf4b`;
19,039,518 bytes. All291 captured inputs are frozen after final verification;
use58 for new implementation. Keep the data container and shortcut49; allow a
cache rebuild, test another fresh-process return, normal Quit and diagnostics.
No phone has been modified. All18 earlier checked source manifests still match.

All nine57 kit files have exact local readback and confirmed upload in iCloud →
Celeste JIT Tests → 0.28.0-build-57. Initial transient iCloud errors cleared.
Only the superseded37 cloud IPA was removed after exact local-copy and receipt
verification. Every Results folder, local37 artifact and accepted fallback remains.
Cloud total993,871,336 bytes. Delivery receipt:
`artifacts/cabrillo-build57-final/icloud-delivery.json`.


## Build56 /0.27.0 — SwiftUI touch editor, 3 October

The owner requests Morro control parity, an optional tap/hold-to-jump and swipe-to-
dash mode, then explicitly requires edge-to-edge placement and an actual-size
landscape editor with a16:9 game guide. Work is local in `launcher-touch-editor`
on `codex/game-input-compatibility`; no new GitHub write is authorized. Public
workflows still select52. Read `docs/TOUCH_CONTROLS.md` and
`docs/ios-jit/TOUCH_EDITOR_BUILD_56.md` with its evidence ledger.

Settings → Controls → Customize touch controls and Pause → Touch controls… open
the same SwiftUI editor. It supports fixed/floating movement, circle/rectangle
buttons, all four split Jump/Dash orientations and swapping/sliding, duplicates,
24 total controls, Crouch Dash/Quick Restart, per-source Hold/Toggle/Inverse Grab,
opacity/haptics/visibility, Undo/Mirror/Reset, Files export/import preview and Morro
D3 v2 conversion. Portrait retains detailed choices; landscape fills the display
at actual size, with a16:9 guide and movable/hideable toolbar. Coordinates cover
the full display, including outside the game image and safe insets. Defaults
avoid the hardware edges. Keep this full-display contract in future changes.

The optional experimental gesture region holds Jump on contact and triggers one
eight-way Dash after its threshold, independently of joystick movement. Lift for
the next swipe. A swipe begins with Jump; use buttons/split for a dash without it.
Menus confirm on tap release and cancel on swipe; feather steering takes priority
in flight. All game physics stay original. Native editing isolates gameplay input.

Final `.build/touch56-managed-d/receipt.json` passes45 Swift and2,740 managed
policy/geometry controls, four actual Apple UI tests across iPhone/iPad simulators,
three full real-game host runs and original Motion Smoothing1.8.0 at60/120 Fast/
Fancy. Each full run includes17 new input checks,37 gesture/37 feather checks,
hair, desktop saves, save/resume and normal Quit.59 Python controls pass. Final
receipts: `.build/touch56-{policy-e,ui-h,host-i,motion-c}/receipt.json`.
These are host/simulator checks, not physical56 acceptance or sustained120Hz.
55 Results remain empty; its physical gate and earlier granular gates stay pending.

191 of199 managed DLLs match55; the adapter changes and seven pinned public
MonoMod/NLua dependencies rebuild. Bootstrap/preparation and feather sources stay
exact55. All16 native dependency archives and both signed49 Shortcuts are unchanged.
Local native/FMOD receipts remain `.build/release51-local/{native,fmod}/receipt.json`.
`tools/build_release56.py` provides the separate fresh public-source builder with
a developer-owned FMOD SDK. No original/prepared game code, original assets,
SDK components or signing material is bundled. No phone was modified.

The independently verified unsigned56 IPA and matching dSYM are retained in
`artifacts/cabrillo-build56-final`. IPA SHA256
`b20ed0a6aafc40bf957f2be64411db80a71591dfd88f6206214037e6fffd9b96`;
19,020,874 bytes. All285 captured inputs are frozen; use57 for new implementation.
All17 earlier checked source manifests still match. Keep the existing data
container and shortcut49; allow a cache rebuild and also test a fresh-process
return, editor comfort/input, normal Quit and Export diagnostics.

All nine56 kit files have exact local readback and confirmed upload in iCloud →
Celeste JIT Tests → 0.27.0-build-56. Initial transient upload errors cleared.
Only the superseded53 cloud IPA was removed after exact retained-copy and package
receipt verification. Every Results folder, local53 artifact and accepted fallback
remains. Cloud total998,928,055 bytes.

## Build55 /0.26.1 — saved-game startup repair, 3 October

The owner reports54 cannot start Celeste. The2,417,490-byte54 Results export
matches the final54 BuildInfo exactly, SHA256:
`e18e57478734e79fdb40d3cd18d047a4d31fbd148ca1999ec55dc3fd379e6331`.
Its session passes26 native JIT checks and Shortcut readiness. Both game attempts
verify all1,216 saved assets, then reject game-code preparation. No game or
feather execution occurs. Earlier52 history records prepared-code reuse/startup.
Keep this failed54 evidence separate from the prior host/simulator passes.

The53/54 store mistook native's nonempty staging pathname for an existing ZIP,
even after a previous successful import removed the temporary file.55 in
`launcher-saved-game` requires an actual file before selecting a new import;
otherwise it verifies retained originals and reuses/rebuilds their cache. This
restores the native caller's existing contract. A present invalid ZIP still fails,
and corrupt/missing originals still require import. Read
`docs/ios-jit/SAVED_GAME_BUILD_55.md` and its ledger. No new GitHub write is authorized.

The original54 source reproduces the exact rejection. The repair passes22 store
controls and97 checks across all nine input ZIPs. Three full host runs pass:
first import, cached launch with the missing native ZIP path, and a pre-53 storage
contract with retained originals but no selection pointer/current generation.
They pass gameplay,37 gesture/37 feather controls, hair, desktop saves, resume and
normal Quit. Original bytes survive the rebuild.59 Python controls pass.
These are host checks; physical55 acceptance and earlier granular gates are pending.

`.build/saved55-managed-a/receipt.json` is the final managed payload.191 of199 DLLs
match54; Bootstrap and seven pinned public dependencies rebuild. Only
GameCodeStore.Prepare changes among372 Bootstrap method bodies. The feather game
adapter, native/SwiftUI sources,16 native dependency archives and both signed49
Shortcuts remain exact54. Local native/FMOD receipts are
`.build/release51-local/{native,fmod}/receipt.json`. `tools/build_release55.py`
provides the separate fresh public-source build using a developer-owned FMOD SDK.
Public workflows still select52; no original game code/assets or SDK components
are bundled. Preserve all earlier frozen inputs and test kits.

The verified55 IPA and matching dSYM are in `artifacts/cabrillo-build55-final`.
IPA SHA256 `e257b92175657c1d1374700c58bd93036795d499407c3a2c5bb43f42d42b3645`;
18,787,140 bytes. All273 captured app inputs are frozen; use56 for new implementation.
All16 checked earlier source manifests still match. No phone was modified.
Keep the existing data container and shortcut49, allow one cache rebuild and test
another fresh-process start, then normal Quit and Export diagnostics.

All eight55 kit files have exact local readback and confirmed upload in iCloud →
Celeste JIT Tests → 0.26.1-build-55. Only the superseded54 cloud IPA was removed after exact
local-copy and receipt verification. Its Results export, every other Results
folder, local54 artifacts and accepted fallbacks remain. Cloud total998,666,002 bytes.

## Build54 /0.26.0 — optional feather touch steering, 3 October

The owner requests feather flight that follows a finger, without new speed or
acceleration rules, and an in-app toggle. Local work is in
`launcher-feather-touch` on `codex/game-input-compatibility`; no new commit, push
or public release is authorized. Read `docs/ios-jit/FEATHER_TOUCH_BUILD_54.md` and
its evidence ledger. Public release workflows continue to select52.

Settings → Cabrillo extras → Feather follows finger defaults off. It is built
into the game adapter; no optional mod import is needed. A fresh eligible touch
in feather flight supplies a normalized direction toward the finger. Release,
or the small circle around Madeline, supplies original neutral input. The16/22
point hysteresis avoids rapid heading reversal near the target. Original Celeste
still controls all speeds, acceleration and turning. Action buttons and ordinary
movement retain their controls. Pause/death/transition/source changes require a
fresh touch. The preference is sampled for each start attempt, including a retry
after cancelled preparation, and is locked during gameplay.

The final `.build/feather54-managed-e/receipt.json` passes cold/off and cached/on
real-game host runs:37 gesture controls,37 integration checks, original feather
speed controls, hair, desktop saves, save/resume and normal Quit. Original Motion
Smoothing1.8.0 passes60/120 Fast/Fancy with the same final managed payload. Forward
and inverse input conversion share the rendered camera, including its smoothing
offset. iPhone/iPad simulator tests pass default/persistence/session locking.
All59 Python controls pass. These are host/simulator checks, not phone acceptance
or sustained120Hz display measurements.

191 of199 managed DLLs match53; the adapter changes and seven pinned public
MonoMod/NLua dependencies are rebuilt. Bootstrap, content manifest and game input
compatibility sources remain exact53. Rebuilt tool hashes change the preparation
recipe, requiring a fresh cache from retained originals on the first run. All16
native dependency archives and signed49 Shortcuts remain unchanged. Explicit
native/FMOD receipts are `.build/release51-local/{native,fmod}/receipt.json`.
`tools/build_release54.py` provides a separate fresh-source build with an explicit
developer-owned FMOD SDK. No original/prepared game code, original assets, SDK
archives or signing material is bundled.

The verified unsigned54 IPA and matching dSYM are retained in
`artifacts/cabrillo-build54-final`. SHA256:
`b298b217e20a4e6585c19fe365c077c6215434fe462ef69cf64cc2efa88dc437`;
18,787,093 bytes. All272 captured inputs are frozen; use55 for new implementation.
All15 retained earlier source manifests still match. Keep shortcut49 and the
existing data container. No phone was modified; feather feel, physical gameplay/
Quit and all older granular gates remain pending. Earlier nine-input and full
Strawberry Jam evidence remains scoped to53.

All eight kit files have exact local readback and confirmed upload in iCloud →
Celeste JIT Tests → 0.26.0-build-54. Initial transient iCloud errors cleared.
Only the superseded38 cloud IPA was removed after exact
retained-local-copy and receipt verification. Every Results folder, local38
artifact and accepted fallback remains. Local cloud total996,231,844 bytes.

## Build53 /0.25.0 — game input compatibility, 30 September

The owner requests support for all nine supplied original itch.io, Steam and Epic
FNA1.4.0.0 ZIPs and store acquisition instructions, using Morro as a reference.
Work is local on `codex/game-input-compatibility`; no new GitHub publication was
requested. Read `docs/CELESTE_INPUTS.md` and
`docs/ios-jit/GAME_INPUTS_BUILD_53.md` before continuing this feature.

`launcher-game-inputs` adds four exact input combinations, local creation of the
empty companion missing from Epic Windows, and a bounded pre-Everest Steam IL
adaptation. It changes exactly11 desktop-service method bodies, preserves the
other game methods and original IL, and removes desktop Steam client dependencies.
Schema2 caches key by recipe and source; a selected-source pointer commits only
after preparation. Existing standard originals migrate without a new ZIP. The
native availability hint recognizes the selected source. Play includes a game
files guide; the docs give Steam depot and optional Epic/Legendary instructions.
Morro's MIT attribution is retained. Its AOT/device results are separate evidence.

All nine full ZIP imports and97 compatibility/recovery controls pass, plus the19
retained code-store checks and14 native availability controls. All four distinct
input combinations pass cold/cached real-game host gameplay, hair, desktop save
transfers, save/resume and normal Quit. Original Motion Smoothing passes Fast/Fancy
at60/120 host callbacks. Full Strawberry Jam cold/cached mod runs on the Steam
game also pass maps, hooks, saves/resume and normal Quit.59 Python release controls
and Actionlint pass. These are
host checks, not physical53 acceptance or sustained120Hz display evidence.

The final managed receipt is `.build/game-input53-managed-b/receipt.json`;
explicit unchanged native/FMOD dependency receipts are in
`.build/release51-local/{native,fmod}`. `tools/build_release53.py` is the separate
fresh public-source build recipe with a developer-owned FMOD SDK. Existing public
release workflows still select52. All earlier frozen35–50 and hosted/tagged52 app
inputs remain exact.

The verified unsigned53 IPA and matching dSYM are in
`artifacts/cabrillo-build53-final`. IPA SHA256:
`3a0e4ec5b72e1e13d6a6f00db7bac0f7a7aa7bf8450ed28d9c3aaaecaec16f31`;
18,782,511 bytes;259 captured app inputs are frozen. Use54 for new implementation.
The independent audits confirm199 managed assemblies and no original/prepared
game code, original assets, SDK archives or signing material. Keep shortcut49.
Phone installation/import/gameplay/Quit and the older granular device gates remain
pending; no phone was modified during this work.

All eight kit files have exact local readback and confirmed upload in iCloud →
Celeste JIT Tests → 0.25.0-build-53. Initial transient iCloud errors cleared. Only the superseded49 cloud IPA
was removed after exact retained-local-copy and receipt checks. Every Results
folder and fallback remains. Local cloud total996,088,256 bytes.

## Published v0.24.1 / build52 —30 September

The owner reports successful testing of the trial kit and explicitly authorizes
the version tag and public Release. PR4 is merged at `2acf9af`; annotated
`v0.24.1` targets that commit. [The tagged run](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36696860903) passes every build,
verification and publishing job. [The Release](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.24.1) has all five approved assets.
They independently download without authentication and pass checksums and exact
source/tag/workflow attestation verification. Release IPA SHA256:
`c223f7e31aea15ecc640f8f10388c4628f9ba063f1a52967279c949023123b47`. See HANDOFF and docs/RELEASING.md.

The 247 captured app inputs and 151 dependency inputs match the tested trial.
Retain both immutable kits; the new release files/evidence are in
`artifacts/cabrillo-v0.24.1-release`. No app implementation changed for publication;
use53 for new app changes. Owner-reported trial acceptance adds no detailed
save/lifecycle/iPad/sustained120 gate or new device log. No phone mutation is needed.
SDK components, credentials and game files remain excluded from public outputs.
The earlier no-tag/no-Release statements below describe the superseded trial stage.

## Earlier public Actions trial —30 September

The owner requests a complete working GitHub Actions IPA build and README/developer
instructions. This authorizes source/workflow commits, pushes and hosted trials.
The owner explicitly permits storing the temporary FMOD login as encrypted GitHub
Actions secrets. They are confined to the restricted `cabrillo-release` environment
and the official SDK fetch step. Never print credentials or include them in source,
shell arguments, reports or public outputs.

The owner supplied Brett Paterson / Firelight's email permitting the FMOD runtime
inside a built application. Developers must obtain their own SDK from fmod.com;
SDK components must not be redistributed. This resolves the runtime permission
gate. Preserve that distinction and the applicable licence/notices. No SDK mirror,
SDK artifact/cache or embedded game code/assets is permitted.

The complete52 /0.24.1 hosted run36682093793 passes at `789f20e`: official SDK
acquisition, fresh public managed/native compilation, app/package audit, five
attestations and separate Ubuntu verification. Independent downloaded-kit checks
pass all five attestations/checksums,247 captured app source hashes and NLua's
strong-name signature. The18,759,836-byte IPA SHA256 is
`7392dd6f0199faf0d8501ed690772685e127ee9fd463ed2b3ce59441e719dbe4`.
All59 Python,119 profile,185 shortcut,36 branch and15 bad-URL controls pass.
See HANDOFF and `docs/RELEASING.md` for run/download links and the exact scope.

The active manifest is `release/public52.json`; use `tools/build_release52.py` with
an explicit developer-owned FMOD SDK for local builds. Preserve frozen38–51,
including51's first local package/compiler/manifest.52 adds only the separately
pinned Apple Silicon NuGet host package to the original128-package lock; all common
hashes remain exact. Mono6.14.1 supplies NLua's `sn` build tool; the iOS Mono runtime
still builds separately from pinned8.0.28 source. Public signed49 Shortcut resources
are verified against Apple signatures and generated actions, without an iCloud
login. Their signing certificates expire26 October2027.

All247 captured52 app inputs are frozen in the hosted kit's BUILD_PROVENANCE.json,
retained in `artifacts/cabrillo-build52-hosted`; use53 for new app implementation.
No public version tag or Release has been created; manual artifacts last14 days.
Keep app50/shortcut49 on the phone. Hosted compilation is not new physical-device
acceptance. Earlier device, save-manager, iPad and sustained120 gates stay distinct.

## Active owner-prioritized work —28 September, app50 / shortcut49

The owner installed50, kept shortcut49 and confirms the fresh cellular test passes.
USB verifies exact installed BuildInfo and both signed49 assets. The journal starts
without a Wi-Fi address, Automatic selects Travel, the route becomes ready after
LocalDevVPN returns, isolation is acknowledged, the offline service hello passes,
and all26 native JIT checks pass with known debugger detach. Cabrillo returns,
restores the both-on preset and clears recovery, ready after31.262s.125 saved files/
683,136bytes and preferences remain unchanged. Journal hash:
`6b5b49d5792519fb88352c06a6369a6367c2c95f8132571253834dac753cd31a`.
This is a scoped physical cellular-start pass; no repeat solely for an export.
The installation/test and independent-export requests are answered. The owner’s
960,314-byte50 export is reviewed and confirmed uploaded in50/Results; SHA256
`9fdaaac4ca669c11ccad121acd6f26cf33015dbaa38eca9e1db2b4af9933efa4`.
Its98 current events contain the exact95 accepted USB events,26 native passes,
ready/restored status and no storage error. Both prior49 failures are separately
retained in its history. No game starts in this export. Keep app50/shortcut49;
no repeat test or export is needed for this gate. Entirely out-of-range operation,
alternate presets, cancellation, other guests/providers and game/Quit remain
separate, along with earlier native saves/iPad38/sustained120 gates.

The owner confirms49's text field/import works, then reports cellular
Home launch failure with Wi-Fi disabled in both Control Centre and Settings. USB
retrieves both app49 runs: Automatic selects Travel, prepare/LocalDevVPN return, the
pre-isolation developer endpoint stays unreachable,25s times out, restore succeeds.
Neither run requests JIT. The second journal hash is
`26b69108725a847de3d541f8bc5b7a7118a8e8b3bcc3a4951ae19ac8f2ed7fc6`.
The prior47 cellular tests could rejoin nearby Wi-Fi; keep that scope distinct.

Build50 /0.23.2 in `launcher-shortcut-cellular` checks the selected tunnel route
before isolation, then the full Remote Pairing hello after the isolate receipt.
It retains actual native JIT/detach and restoration gates, rejects stale probe
results and distinguishes route/service timeouts.132 native,50 setup,53 cellular
controls and36 shortcut branches pass; exact49 reproduces the ordering failure.
All199 DLLs,16 archives and SwiftUI remain exact49. Both signed49 templates stay
byte-identical; KEEP the imported49 shortcut. No new shortcut import is needed.
All243 captured inputs are frozen in `artifacts/cabrillo-build50-final`; next51.
Read `docs/ios-jit/SHORTCUT_CELLULAR_BUILD_50.md` and its ledger.

All six kit files are confirmed uploaded in `0.23.2-build-50`.
All six also have exact USB readback at On My iPhone → LiveContainer → Cabrillo-build50.
App50 installation and the scoped cellular Home/JIT/restoration gate are now
verified as above. Remote start of the old-order intervention timed out; no test
or radio mutation was dispatched by that earlier attempt.
Only the superseded48 cloud IPA was removed after exact local/package verification;
all Results and accepted32/working43/47 remain. Cloud total996,049,219bytes after the export.
Finish active games normally. Source publication is authorized on29 September;
public IPA publishing remains gated. Preserve
independent exports and the distinct recovery/game/Quit/save-manager/iPad/120 gates.

## Previous owner-prioritized work —28 September, app49 / shortcut49

The owner reports48's Configure This Shortcut field immediately erases typing.
USB verifies installed48, native file export and the URL-list setup screen. The
actual Apple iOS26.5 simulator reproduces the lost edit in the exact48 signed file.
Build49 /0.23.1 in `launcher-shortcut-import` binds the question to blank Text,
then uses an explicitly connected typed URL. Empty answers open Cabrillo setup.
The49 shortcut works with installed48; app49 bundles it for future exports.

Two actual Apple import UI tests pass: original48 failure,49 typing/paste/blur,
import/replace and exact configured URL delivery to an isolated simulator fixture.
132 native,50 setup,36 branch and15 bad-connection controls pass; Apple host checks
also pass. All199 DLLs,16 archives, SwiftUI and the47 reducer remain exact48.
All238 inputs are frozen in `artifacts/cabrillo-build49-final`; next implementation50.
Read `docs/ios-jit/SHORTCUT_IMPORT_BUILD_49.md`, its ledger and the setup guide.

All seven kit files are confirmed uploaded at `0.23.1-build-49`. All seven are staged
with exact USB readback in On My iPhone → LiveContainer → Cabrillo-build49.
At initial delivery the installed app was48; later failed runs verify app49.
The owner confirms49's text stays and import succeeds;
that setup request is answered and the disappearing-field defect is closed.
The import pass stays separate from the later app49 cellular Home/JIT failure.
Its installation is now verified; see the accepted50 repair above. Preserve47/46 and all Results. No cloud
installer was removed; total995,079,880bytes. Keep physical gates distinct and
finish any active game normally. No GitHub/public IPA write is authorized.

## Previous owner-prioritized work —28 September, app48 / shortcut48

The owner requested in-app shortcut creation for standalone/LiveContainer and
current StikDebug provider choices. Build48 is packaged/verified in
`launcher-shortcut-setup`. Settings → Add Home Screen shortcut exports bundled
Apple-signed files; LC installs paste an app-generated exact host/guest/data link
into the import question. Import and Home Screen creation still require owner taps.
Standalone Cabrillo can configure an LC2 StikDebug guest through its copied launch
link; same-host LC2 Cabrillo/StikDebug is rejected. Provider changes remain native.

132 retained native controls,50 setup controls,36 branches,12 broken URL controls
and7 UI tests each on iPhone/iPad simulators pass. All199 managed assemblies,
16 archives and the47 reducer remain exact47. All233 inputs are frozen in
`artifacts/cabrillo-build48-final`; next implementation49. Read
`docs/ios-jit/SHORTCUT_SETUP_BUILD_48.md`, its ledger and the setup guide.

All six48 kit files are confirmed uploaded in `0.23.0-build-48`; initial transient
errors cleared. The kit is also staged at On My iPhone → LiveContainer →
Cabrillo-build48 with exact USB readback. Subsequent USB evidence verifies installed48
and native export. The owner’s setup request is answered: Apple’s URL-list import
field discards input. See active49 repair above; no48 Home/JIT pass is claimed.
New physical import/Home routing,
standalone/LC2 handoff and48 game/Quit are pending. Keep47/46 as the verified phone
fallback. Only33’s superseded cloud IPA was removed after exact retained-copy and
receipt checks; every Results folder, local original and32/43/47 installers remain.
No GitHub/public IPA write is authorized. Finish an active game normally before
updating; preserve independent48 diagnostics and all older distinct physical gates.

## Previous owner-prioritized work —28 September, app47 / shortcut46

USB evidence verifies installed47 and five fresh phone passes: Automatic on Wi-Fi,
two Travel launches with VPN preconnected, Travel from cellular/VPN-disconnected,
and Automatic from the same cellular state. The final three are remotely driven.
All pass26 native checks while detached; four Travel runs verify the offline
tunnel, receive the restoration receipt, clear recovery and return ready. A repeat
Home launch while ready starts no new JIT or radio work. The recovered original
failure passes JIT but receives no restore receipt; a later fresh-process recovery
passes. Its cause remains unexplained, not fixed by these successful repetitions.
Keep that failed journal and the passes distinct. No48 was allocated.

The phone is left ready in Cabrillo, Automatic restored, Wi-Fi/cellular on and VPN
connected. All125 saved files and launcher preferences match their before-test
values. The owner setting/launch requests are answered. No further tap is pending.
The cellular tests occur near known Wi-Fi, which preparation may rejoin; wholly
out-of-range operation, other restore presets, cancellation, other current LC
guests and47 game/normal Quit remain separate gates.46/47 Results remain empty;
keep independent exports without repeating a passed run solely for one.

Relevant file/log collection, screenshots and ordinary URL/process control work;
the latter initially times out and later recovers. Remote taps require iOS27; the
UI-test runner cannot install because of the free-profile three-app limit. No app
was removed or extra debugger attached. A USB preference edit did not defeat cached
defaults; use Cabrillo's Settings for changes. Read the updated47 report/ledger
and HANDOFF, with private evidence under `.private/device-evidence/2026-09-28`.
Plain LiveContainer opening selected YouTube as its last guest; that observation
is not a reproduced shortcut failure.46's generic Home URL also warrants a
separate explicit guest-selection review.47 and46 remain frozen.

Build47 /0.22.4 in `launcher-shortcut-completion` is packaged and verified. It fixes
app43's false Home Screen timeout after native JIT succeeds. The owner confirms
exact46 automatic return, green JIT and Celeste start; the network screenshot
shows the contradictory timeout. Native journals were unavailable at that review;
the28 September47 collection and scoped passes above supersede that limitation.
Keep that scoped result separate from level-input/Quit and physical47 acceptance.

47 completes JIT after actual native execution and known debugger detach in the
foreground, without requiring the extra JIT callback. Network stages still require
their correct receipts; Travel recovery, cancellation and detach gates remain.
132 native controls, original43 missing-callback failure reproduction,36 branches
and12 bad-connection controls pass. All199 managed assemblies/16 archives and
SwiftUI sources stay exact43. Read `docs/ios-jit/SHORTCUT_COMPLETION_BUILD_47.md`,
its ledger and HANDOFF. All221 inputs are frozen in `artifacts/cabrillo-build47-final`;
next implementation48. Keep shortcut46; no new import is needed.

All six47 iCloud kit files are confirmed uploaded; initial transient4355 errors
cleared. No direct phone staging occurred; installation/execution is now verified
through USB metadata/journals. The replacement/Wi-Fi requests are answered. Let any
current game finish normally before closing the apps for a fresh test.
Only the superseded41 cloud IPA was removed after exact retained-local-copy checks;
all Results and accepted32/working43 remain. After normal Quit, preserve independent
46/47-run diagnostics, keep app47/shortcut46 and retain the remaining distinct gates.
No GitHub/public IPA
write authorized. Earlier save-manager/iPad38/sustained120 gates remain distinct.

44's verified phone run opens the helper, then crashes its LC URL decoder with
`open-url` present but no value. Apple WFStringContentItem reproduces this exact
long-link truncation; typed URL items preserve every byte. The natural44 workflow
finishes, but no native callback/JIT is collected. Keep44 frozen and use46.

App43's direct warm native-button retry passes26 native checks while detached,
returns automatically and starts Celeste using cached preparation in0.095s.
The later journal confirms ten paired menu touches, profile save readback, normal
Quit/stage8 and native heartbeat. This scoped manual pass is separate from Home
Screen and level-input acceptance. Preserve all Results and accepted32. Never
attach another debugger with StikDebug.

## Previous owner-prioritized work —26 September, shortcut42 / app41

App41 is installed, uploaded and passes the real phone VPN-loopback hello;125
save/profile files are unchanged. The39 shortcut then fails its generic-value
comparison before StikDebug opens. Shortcut revision42 adds explicit text coercion
and passes36 isolated Apple condition checks (12 original failure controls) plus36
generated branches. It retains app41 and the39 protocol; no42 IPA is produced.
Read `docs/ios-jit/SHORTCUT_FILES_42.md`, its ledger and HANDOFF. Six42 inputs are
frozen in `artifacts/cabrillo-shortcut42-final`; next implementation is43.
The five-file kit is uploaded and staged with exact readback. Initial import made
Cabrillo 1; the owner has now removed old Cabrillo and renamed42 correctly, which
is verified from synced contents. CoreDevice calls time out, but paired USB AFC
log collection still works. An owner request to close LC1 and run the new shortcut
is pending. Keep native JIT/detach/recovery gates; never attach another debugger.
Continue Automatic, Travel/recovery, then game/Quit. No GitHub/public IPA write.

## Previous owner-prioritized work —26 September, build41

The owner installed40;125 save/profile files are unchanged. Automatic opens the
VPN and returns, then times out at the legacy lockdown probe before any JIT
request. Build41 /0.22.2 (`launcher-shortcut-tunnel`) checks the actual StikDebug
Remote Pairing endpoint49152 with a bounded, unauthenticated hello. A direct Mac
hello to the positively identified phone confirms its protocol; that is separate
from the phone VPN/JIT gate.91 native controls and36 shortcut branches pass.
All199 managed assemblies/16 archives, UI and existing39 shortcut stay unchanged.
Read `docs/ios-jit/SHORTCUT_TUNNEL_BUILD_41.md`, its ledger and HANDOFF. All210
inputs are frozen in `artifacts/cabrillo-build41-final`; new implementation needs42.
The kit is staged directly with exact IPA readback and the installer opened; owner
replacement selection is pending. Recheck iCloud upload. Only the superseded39
cloud IPA was removed after exact local verification; preserve all Results and
local artifacts. Continue Automatic, then Travel/recovery and game/Quit. No
GitHub write/public IPA authorized. Do not claim unobserved physical passes.

## Previous owner-prioritized work —26 September, build40

Direct phone testing found build39's setup defect: LiveContainer denies its
`localdevvpn` canOpenURL query despite the installed helper. Build40 /0.22.1
(`launcher-shortcut-routing`) uses actual handoff/service results in LC while
retaining host identity, native JIT/detach and recovery gates.62 native checks and
36 generated branches pass; all199 managed assemblies/16 archives and the existing
39 shortcut remain unchanged. Read `docs/ios-jit/SHORTCUT_ROUTING_BUILD_40.md`,
its ledger and HANDOFF. All210 inputs are frozen in `artifacts/cabrillo-build40-final`;
new implementation needs41. The kit is staged directly on the USB-connected phone
with exact IPA readback; owner replacement selection is pending. All six iCloud
kit files are confirmed uploaded after a transient error cleared. Do not claim
installation or a physical handoff pass without new evidence. Continue
Automatic, then Travel/recovery and game/Quit. No GitHub write/public IPA authorized.

## Previous owner-prioritized work —26 September, build39

Build39 /0.22.0 (`launcher-shortcuts`) adds the requested Home Screen shortcut,
verified local VPN/JIT handoff, actual LC host return identity and recoverable
Travel networking. All199 managed assemblies and16 runtime archives remain
exact38.54 native controls,36 generated shortcut branches and4 UI tests pass;
the Apple-signed import files and IPA are uploaded in the eleven-file iCloud kit
and staged directly over Wi-Fi in LiveContainer/Cabrillo-build39 on the phone.
Staging is not installation. A concrete owner test request is pending for
Automatic, then Travel and gameplay/Quit. Read `docs/HOME_SCREEN_SHORTCUT.md`,
`docs/ios-jit/SHORTCUT_BUILD_39.md`, its ledger and the latest HANDOFF.
All210 captured39 inputs are frozen in `artifacts/cabrillo-build39-final`; new
implementation needs40. Exact former radio states are unavailable to Shortcuts;
Travel restores a user-chosen preset, while the Wi-Fi path leaves switches alone.
Do not claim universal unattended behavior through locked devices, unaccepted
permissions, helper confirmation, missing DDI or stale pairing. Preserve recovery
and actual native JIT/detach checks. No new GitHub write or public IPA is authorized.

The newly collected38 phone journal confirms cold game preparation15.368s and
SJ Grandmaster lobby gameplay, ending backgrounded. Keep this scoped runtime
observation separate from cached preparation, normal Quit, visual acceptance,
native saves and the iPad38 gates. The rest of38 delivery below is retained.

## Previous owner-prioritized work —25 September

Build38 /0.21.0 in `launcher-owned-game` is packaged and its six-file iCloud kit
is confirmed uploaded. It prepares original Celeste code from the user's ZIP in
Documents and caches it; no original/prepared game code or original assets are
bundled. Public dependencies build without the private capsule or old checkouts.
The remaining known distribution gate is FMOD permission and authorized SDK
access for CI. Read `docs/ios-jit/OWNED_GAME_BUILD_38.md`, its ledger and HANDOFF.

Cold/cached host gameplay, saves, hair, resume/Quit, full pinned Strawberry Jam,
Motion Smoothing60/120, recovery and native UI/profile controls pass. The host
runtime is a separate retained test fixture; these are not iOS device acceptance.
Build38 is installed on the iPad with11 save/profile files preserved and the
original ZIP already staged. First/cached device runs remain pending. Source and
artifacts are frozen in `artifacts/cabrillo-build38-final` (230 inputs); new
implementation needs39. Keep every earlier lane and its distinct acceptance gates.
No new GitHub write or public IPA publishing is authorized by this request.

## Current state

- Public CI and a gated version-tag release workflow are configured through
  [PR2](https://github.com/hmcneill46/cabrillo-celeste/pull/2). Fresh GitHub-hosted
  runs pass the public inventory audit, 20 Python build/release controls and119 native profile
  checks without private dependencies. The29 September source publication adds
  the38 public dependency recipe/owned-game import and shortcut work through50,
  including current native shortcut CI. Check the publication branch's GitHub
  Actions for its hosted results. `release/current.json` still blocks38 until
  FMOD distribution inputs are approved; no private IPA is published.
- The latest37 export contains two owner-confirmed unexpected app exits. Both
  pass26 JIT checks, Everest1.6580 and MotionSmoothing1.8.0 registration with54
  selected archives; one reaches the menu then starts Old Site. No37 gameplay/
  Quit pass is present. Wi-Fi iOS logs confirm jetsam per-process-limit with
  a3376MiB limit; the last sample reaches3.53GB. Earlier32 ran at4GB, and the
  owner confirms SJ alone now fails. Current LiveContainer signing omitted
  Increased Memory Limit; retained earlier profiles grant it. The exact same
  LiveContainer3.8.10 release is now re-signed with the permission and installed
  over Wi-Fi. Installed entitlements and14 unchanged save/settings files are
  verified; native launch passes and iOS confirms the new6144MiB process limit.
  The owner confirms SJ now works. A new exact37 phone journal verifies SJ
  Prologue, Beginner Lobby and NotYourBadeline a_01–03,501 paired touch inputs
  and4.05GB peak footprint with zero runtime errors. The SJ regression is closed.
  This run ends backgrounded without normal Quit/native-return evidence. The
  independent new iCloud export and full lifecycle/save gates remain outstanding;
  do not request a repeat of already-passed SJ gameplay solely for the export.
  Read `docs/ios-jit/BUILD_37_MEMORY_REVIEW.md` and the37 ledger. The matched32/37
  host comparison passes with a slightly lower37 peak. This is a host signing
  repair, not a new Cabrillo implementation. Physical acceptance is scoped to the
  recorded SJ gameplay. `docs/INCREASED_MEMORY_LIMIT.md` documents the owner-requested
  GetMoreRam alternative and the correct LiveContainer/standalone signing target.
  Full SJ mods were added
  between36 and37, so the runs do not isolate Everest alone. Follow the37 report;
  preserve these distinct physical gates. All37 inputs remain frozen; any new
  Cabrillo implementation needs38. No38 package has been allocated for this repair.
- The same export verifies36's base-game/Motion Smoothing gameplay, four resumes,
  save readback, stage8 normal Quit and delayed native heartbeat with zero runtime
  errors. It also confirms standalone StikDebug in the tested LC setup. Most
  gameplay callback windows are around60 despite a120 request; sustained120Hz
  and the native save-manager gate remain pending. Keep32 as the broader fallback.

- Build37 (`launcher-everest6580`,0.20.0) upgrades actual Everest source and both
  runtime identities to stable1.6580.0, commit082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75.
  All16 native archives are exact36; four managed assemblies change,197 remain
  exact. Build34 precision repairs and35 touch polling are preserved. Follow
  `docs/ios-jit/EVEREST_6580_BUILD_37.md`; build/package checks and frozen inputs
  must not be mistaken for physical acceptance. Preserve all earlier artifacts.
  `EverestValidation.json` pins profile, real-game/source, Motion Smoothing60/120
  and original-vanilla save roundtrip receipts. The iPad35 base-game gate and
  scoped36 phone acceptance remains distinct from37 acceptance. All six37 kit files
  are uploaded;37 is installed on the iPad with native-launch identity confirmed.
  Phone37 evidence has arrived and records unexpected exits; iPad37 gameplay
  remains pending. All220 captured37 inputs are frozen; next unused is40.

- Later25 September: phone35 fails before its first frame with Motion Smoothing
  at both60/120Hz, despite passing JIT. An accepted Mono class.c visibility patch
  was omitted in the iOS15 rebuild. Build36 (`launcher-visibility`,0.19.1) restores
  that exact archive member. All201 managed assemblies and fifteen other native
  archives remain35-identical. Follow `docs/ios-jit/VISIBILITY_BUILD_36.md` for
  current delivery/evidence. New implementation work must use the next identity40.
  The older host runtime retained the patch; require the new original-source
  failure control and restored-source test gates before treating host checks as
  evidence for this change. The37 export now verifies the scoped36 runtime gate;
  the native saves gate is still pending. Build37 is the requested stable Everest1.6580
  upgrade lane; do not mix its managed payload with36 metadata.

- 25 September: build35 (`launcher-platforms`,0.19.0) is installed on the owner's
  iPad mini4/iOS15.8.8 via TrollStore with Dopamine active. Native JIT, real base-game
  gameplay/touch, brief resign/foreground, save readback, normal Quit/stage8/native heartbeat
  and owner visual/audio review pass. This is a scoped iPad acceptance; build32
  remains the accepted phone fallback. Read `docs/ios-jit/PLATFORMS_BUILD_35.md`.
- Build35 adds iOS15 UI/native compatibility, explicit JIT routes and optional
  up-to120Hz display callbacks. Seven archives are rebuilt from an explicit pinned
  source capsule; nine remain exact. Only the managed adapter changes relative34:
  touch polling now happens at MInput.Update so render-only ticks cannot consume
  presses. Original Motion Smoothing1.8.0 passes Fast/Fancy at60/120 on the host;
  phone refresh rate, performance and new JIT routes still need physical checks.
- Build35 is frozen and all six iCloud kit files are confirmed uploaded. Use its
  combined guide;33/34 Results were still empty on25 September. Preserve34's
  numerical repairs and backup/transfer gate, now also carried by35. Managed pin:
  `.build/platform-managed35-b/receipt.json` (derived from exact34); native pin:
  `.build/platform-native35-c/receipt.json`. Both hashes are in the lane JSON locks.
  Final package/artifacts: `artifacts/cabrillo-build35-final`. Public source is
  included in the later scoped CI publication above. Next unused identity is39;
  recheck before allocation.

- Accepted physical fallback: build32, Everest1.6531.0; preserve28/27/31 too.
  The15 September review of one export plus retained history closes the native
  browser/install/gameplay/Quit gate. See `docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md`.
  Do not convert a host build or migration hash comparison into a device PASS.
- Build31 phone review passes two complete backend/gameplay/save/Quit runs and
  confirms the owner's loading UI concerns: long main-thread pauses and17.7s of
  hidden game frames before the title menu. See `docs/ios-jit/BUILD_31_LOADING_REVIEW.md`.
- Build32 (`launcher-first-frame`,0.16.2) refines the native display and reveals
  after first draw/post-Present readback in a successful foreground Frame callback.
  It reuses build31's exact phone-tested managed payload. The verified kit is
  uploaded to iCloud. Check its report/ledger
  and Results before requesting testing: `docs/ios-jit/FIRST_FRAME_BUILD_32.md`.
  Build32 is now physically accepted; see `docs/ios-jit/BUILD_32_ACCEPTANCE.md`.
  Retain all original artifacts and Results folders.
- Build33 (`launcher-backups`,0.17.0) adds Saves, portable whole-profile backups,
  staged exact restore and retained rollback. It reuses every32 managed assembly.
  New sources/package are frozen after packaging; phone33 is still unaccepted.
  Preserve its recovery boundaries, all unknown files, exact archive identities,
  disabled choices and fresh-process requirement. Read its report and ledger.
- Build34 (`launcher-save-transfers`,0.18.0) adds individual ZIP/main-file transfers,
  long-press menus, replacement/duplication review and empty slots1–3. The owner
  deferred33 testing; use34's combined backup/transfer/hair phone guide. All six
  files are confirmed uploaded. Check its Results and `docs/ios-jit/SAVE_TRANSFERS_BUILD_34.md`.
  Phone34 is unaccepted; sources/package and repair provenance are now frozen.
  A scoped repair changes four Celeste method bodies for hair, PlayerSeeker, bird
  tutorial and lava arithmetic. Only Celeste.dll changes among201 assemblies;
  all16 native archives match32. Pin `.build/precision-managed34-final/receipt.json`
  as recorded in ManagedPayload.json; do not substitute the older managed payload.
- Build29 is local preparation;30/31 sources and artifacts are frozen. Build32 has
  its own native identity and pins the same managed dependency in `ManagedPayload.json`.
  New implementation changes after packaging require another identity (next unused40;
  recheck before allocating). No historical UUID restoration for changed builds.
- Individual mod/game callbacks can still pause updates; the final pass yields
  between modules without holding its list monitor. Preserve its reentrancy guard,
  optional-cycle decisions, exact load order, game-thread ownership and window
  focus. Do not claim full phone responsiveness from host/simulator checks.
- Original delivered sources/artifacts remain immutable. Reproduction uses exact
  source/resource hashes and historical packaging metadata. New implementation
  changes require a new version/build identity and fresh evidence.
- The standalone build entry point is `tools/build.py`. Historical experiment
  builders are retained for their runtime patches and investigation context.
- `tools/build_development.py` builds the separate native preparation lane with
  fresh metadata/UUIDs against the pinned capsule. Build33 uses
  `tools/build_backups.py` with `tools/verify_backups.py`; the builder
  requires the exact validated managed receipt, with a separate new native UUID.
  Build34 uses `tools/build_save_transfers.py` / `verify_save_transfers.py` and
  the explicit derived managed receipt. Its repair tool and all hashed inputs
  are also frozen. Preserve ten intentional movement precision sites and the
  bounded audit's limits; host repair checks are not physical gameplay acceptance.
- UUID restoration is allowed only for build28 reproduction after matching every
  other byte against the locked executable hash. Never use it to conceal changed
  instructions, data, load commands or resources. Record the actual build time
  outside the historical app metadata and keep dSYM UUIDs consistent.
- `docs/MIGRATION_FILE_INVENTORY.json` records why imported files exist. Keep
  JIT-specific source, tests, documentation, licenses and required shared policy;
  do not pull in the AOT app or unrelated build outputs.
- Preserve exact module identities, compatibility pins, minimum runtime versions,
  reviewed installs, disabled choices, whole transaction recovery and accurate
  reports. GameBanana titles are not dependency identities.
- One game per process; fresh JIT request each time. Preserve normal main-menu
  Quit/native return, saves/settings/unknown sidecars and Export diagnostics.
- Keep catalogue work bounded and cancel it before managed startup; require
  `catalogue_quiesced` with zero active requests in phone evidence.

## Physical testing and delivery

- Target: iPhone15ProMax/iOS26.5. Celeste runs in LiveContainer slot1; StikDebug
  stays in slot2. Launch with JIT OFF, saved script blank, Fix File Picker ON.
  Use the app's fresh PID-specific inline request. Never attach another debugger
  concurrently with StikDebug.
- Owner authorizes relevant log collection and concrete physical tests. Provide
  exact steps and inspectable logs. Use exported map/room evidence directly.
- Default handoff: `iCloud Drive/Celeste JIT Tests/<version>-build-<number>`, up to
  1GB total. Include the unsigned IPA and short guide. Verify bytes and distinguish
  local placement, confirmed upload and actual phone download/execution.
- Preserve every Results folder. Superseded large installers may be removed from
  iCloud only after their exact local copies are verified. Keep the accepted
  fallback. Direct USB transfer to this owner's phone/LocalSend is a fallback.
- Preserve independent Export diagnostics even when automatic USB collection works.

## Roadmap and release boundary

- Build34 combines whole-profile backup, per-slot desktop transfers and numerical
  repairs. Phone34 acceptance is pending; review its Results and
  `docs/ios-jit/SAVE_TRANSFERS_BUILD_34.md` before requesting testing. Build33 stays
  preserved and unaccepted; the owner requested one combined34 test.
  The full-parity SwiftUI touch editor follows that gate; the owner prioritized35 platform/JIT work in the meantime.
  Do not queue fake progress behind blocking main-thread startup or move graphics
  initialization to an arbitrary worker.
- iPadOS is an intended next device target. Resizing, safe areas, pointer/keyboard/
  controller input, touch layout and JIT need tablet-specific evidence. macOS is
  a later product target; tvOS/visionOS remain investigations, not promised support.
- A public Git repository is separate from a publicly distributable IPA. Original
  IL preparation and FMOD permission remain unresolved release gates.
- Detailed historical decisions are in `docs/history/LEGACY_AGENTS_BUILD28.md`
  and `docs/ios-jit`; current instructions above supersede old active-work labels.
