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

## Published v0.25.1 / build56 —20 October2026

The owner explicitly requests merging PR6 and publishing the latest release after
confirming the phone installer. [PR6](https://github.com/hmcneill46/cabrillo-celeste/pull/6)
is merged; annotated `v0.25.1` targets `dd4294254f3ecf7b20fa41e2c133fff5fc9b19b9`.
[Tagged run39375179251](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39375179251)
passes all six jobs, including fresh source/package audits, all five attestations,
separate Ubuntu verification and publication. The
[latest public Release](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.25.1)
has all five approved assets. They independently download without authentication
and pass API digests/checksums and exact tag/source/workflow/run attestations.

Release IPA bytes:18,784,694. SHA256:
`d96522f1ef12f0cbe12beee00ed23d92218e732cf498e464850458ef57575c9c`.
All274 app hashes and151 dependency hashes match the accepted56 trial. Actual199
DLLs pass434 metadata checks matching the hosted audit, full NLua RSA signature
verification/tamper controls and14 tagged/native version comparisons. Retain the
immutable `artifacts/cabrillo-v0.25.1-release` and earlier kits; use57 for new app
implementation. The accepted phone trial establishes ZIP copy/staging and52-mod
installation; no separate tagged-binary gameplay/JIT/save/lifecycle pass is inferred.

## General dependency download repair —19–20 October, build56

The owner requests the FemtoHelper download repair and explicitly requires a
general solution for moved downloads, plus agreement between actual Everest and
native dependency/version checks. The completed source is in
`launcher-dependency-downloads`, Cabrillo0.25.1/build56, retaining stable1.6642.0.
All261 captured55 inputs stay frozen. Read
`docs/ios-jit/DEPENDENCY_DOWNLOADS_BUILD_56.md` and its evidence ledger for current
checks. Final100 Python,119 save/profile,321 dependency controls and actual iOS
compilation pass. The final host installation verifies all52 Strawberry Jam
archives and232 checks with seeded public cache, then a separate uncached real
1776026→1838255 recovery passes14 assertions. Original fresh52-download baseline
is retained separately. [Hosted run39371266102](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39371266102)
passes fresh managed/native compilation, official SDK acquisition, package audits,
all five attestations and independent Ubuntu verification. The downloaded kit
verifies all274 captured sources,151 exact55 dependency hashes,199 DLLs/434 metadata
checks, full NLua strong-name signature and14 actual56/native version comparisons.
IPA SHA256 `b9e0fa34a9163ad0024f4ff2ff02d10290716537deb6629b0e4ead33946d3fe0`.
All274 captured56 app inputs and `artifacts/cabrillo-build56-hosted` are frozen;
use57 for new app implementation. Physical gameplay/JIT remains untested for56.

On20 October the owner confirms “Yep all works now!” The attached exact56
diagnostics match all274 hosted source hashes on physical iOS27.0.1. Copy-mode
game ZIP import stages875,540,825 bytes; all52 Strawberry Jam archives verify and
install, and a52-change receipt commits successfully. FemtoHelper1.15.22 uses
1838255 with the exact tested SHA256. No storage error is reported. This closes
the phone downloader defect. The export contains no JIT/preparation/gameplay/
save/Quit events, so those separate runtime gates remain. Diagnostics SHA256:
`d8a2d67212a30d4cba221fddf829f28946370eac6836c2bf872bf2b99455eef7`. Raw evidence stays ignored in
`.private/device-evidence/2026-10-20/build56-owner-install`.

The supplied exact55 diagnostics show33/52 archives verified, then
FemtoHelper1.15.22 oldfile1776026 fails; no mod transaction commits. The official
archived file1838255 has identical11,103,153 bytes/SHA256
`5a845805bae30490ed7c9da84410fbe672628b8fe927a830f5f2eb148eb88419`.
The56 metadata relocates that link without changing tested helper contents.
General recovery must use bounded authoritative listings and preserve the exact
reviewed archive identity. The native overlay also carries current MirrorName
metadata and aligns required/optional API alias handling with upstream Everest.
Keep the original bundle ID, copy imports, save/profile paths, JIT and Shortcut49.

On20 October, after the local fix/checks completed, the owner explicitly answers
“Go for it” to committing/pushing tested56 as `hmcneill46`, updating existing
draft PR6 and running the existing workflow for an unsigned test IPA. This
includes the repair's source, validation/delivery notes and scoped build fixes.
The owner then confirms the phone installer and explicitly requests on20 October:
“merge the pr and get the latest as a release”. This authorizes merging PR6,
annotated `v0.25.1` at the reviewed merged source, the existing tagged release
workflow, public IPA/verification assets and release/change/delivery notes.
Preserve published history and all274 frozen app inputs. Physical gameplay/JIT/
save/lifecycle gates stay distinct from the accepted phone installer.

## Everest stable1.6642 update —19 October, build55

The owner requests the latest Everest after54 publication and asks future pushes
to use GitHub account `hmcneill46`. Repository-local Git author/committer are now
`hmcneill46 <57508980+hmcneill46@users.noreply.github.com>`. The authenticated
GitHub API account and sole listed repository collaborator are `hmcneill46`;
commit display names are separate from push authentication. Preserve published
history and use this identity for the current source/build trial.

Build55 /0.25.0 uses official stable1.6642.0, released17 October, commit
`5abd7876821223c20711c1844a5187321d6e904c`. Its new overlay is
`launcher-everest6642`; source recipes/manifests have55 identities. Only the
Everest dependency pin changes. Existing platform patches and loading, all253
captured54 inputs, Feather copy imports, native/runtime pins and signed49
Shortcuts remain preserved. Native and managed runtime expectations change
together. The preparation recipe automatically creates a new cache generation
while retaining the original game identity/files, previous generations and saves.

Read `docs/ios-jit/EVEREST_6642_BUILD_55.md` and its ledger for current checks.
Local89 Python controls,119 save/profile checks and actual iOS compilation pass.
[Hosted trial39320628794](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39320628794)
at `e1e78a3511df5642537a75d86ae46e98e0411f34` now passes fresh public managed/native
compilation, official SDK acquisition, package audits, all five attestations and
separate Ubuntu verification. Release publication is skipped. The independently
downloaded kit in `artifacts/cabrillo-build55-hosted` verifies all261 captured
source hashes,151 dependencies (only Everest changes), original bundle ID/copy-import metadata
and signed49 Shortcuts. Its actual199-DLL metadata passes434 checks, with the
independent report exactly matching the hosted audit. IPA bytes:18,765,294;
SHA256 `abd79be029902c301778f8b11044484d00cedc07988f14b3243cf42cde8b04cd`.
All261 captured55 inputs/kit are frozen; use56 for new app implementation.
Draft [PR6](https://github.com/hmcneill46/cabrillo-celeste/pull/6) retains the
source trial; no55 tag/Release or physical JIT/gameplay is claimed. Preserve
published54 and every earlier scoped device result.

## Copy-based Files imports —19 October, build54 correction

The owner now confirms54 imports the game ZIP successfully. Read-only USB
verifies exact0.24.3/build54, original ID, all253 source hashes, copy-mode game
selection and875,540,825bytes staged on iOS27.0.1. Journal SHA256:
`92ff72a8361d24ea7efd4dcd3b999d08aecc09e6b1a0468bd02ca3654e042985`.
The full trial workflow and Ubuntu verification pass. This closes the reported
game-ZIP selection/staging defect; physical mods/gameplay/JIT remain separate.

On19 October the owner explicitly authorized GitHub Release publication and
change notes. Annotated `v0.24.3` targets `46dc40678fe839b676a2a9496eb84229d0b4c331`; [tagged run39285104629](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39285104629)
and the [public Release](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.24.3) now complete the existing audited
build/verify/publication workflow. All five assets independently download without
authentication and pass checksums and exact tag/source/workflow/run attestations.
Release IPA SHA256: `e3520bced1ff72886d2b1796ee1420f797df71a514ee9b9e0430fd933e18a583`.
All253 app inputs and151 dependency hashes match the tested trial. Preserve both
immutable kits; the tagged kit is `artifacts/cabrillo-v0.24.3-release`. Earlier trial-only/no-Release
statements below describe historical stages. No separate tagged-binary device
run or new mod/JIT/gameplay/save/lifecycle/iPad/120Hz acceptance is inferred.
Use55 for new implementation; unrelated future GitHub writes remain outside scope.

The owner reports53 still fails game selection. USB verifies exact53 source
metadata/original ID on iOS27.0.1; entitlement lookup and hook installation pass,
but game selection never calls the delegate. Two owner-driven backup-picker
tests select the same game ZIP and correctly reject its backup manifest; no
restore/rollback runs. Save/backup already request copies; game/mod request
open-in-place. Build54 /0.24.3 changes those two selectors to copies and adds
redacted mode diagnostics. The compatibility module remains exact53.

Read `docs/ios-jit/COPY_PICKER_BUILD_54.md` and its ledger before acting. Keep
all254 captured53 inputs/kit frozen.54 is the active corrective source recipe;
the complete54 kit is built/independently verified; original-ID game selection
and staging now pass as recorded above. All253 captured54 app inputs are frozen;
use55 for new implementation. Release authorization is recorded above; unrelated
publication remains outside scope. Do not infer additional device gates from the
backup picker or iOS26.5 simulator. Original
private phone evidence stays ignored; read-only USB collection changes no phone
settings, installation, debugger or user files.

## Signing-aware Files picker —19 October, build53 trial

The owner confirms that matching Feather's Identifier to the supplied explicit
Development profile repairs ZIP selection, then explicitly requests an in-app
fix preserving Cabrillo's bundle ID and existing signing setup. Build53 /0.24.2
adds `launcher-signing-picker` as an overlay: a new `main.m` and a narrow Documents
UI host-identifier adapter, with the accepted50/52 base frozen and hash-pinned.
Read `docs/ios-jit/SIGNING_PICKER_BUILD_53.md` for behavior and validation limits.

The preserved53 source manifest is `release/public53.json`; its recipe is
`tools/build_release53.py` / `compile_release53.py`. Published52 and its builders
remain immutable. Source commit `1f2de6d` is pushed to `codex/actions-release`;
the completed53 IPA is now independently verified. No phone acceptance, tag or
Release is claimed. The first hosted trial
passes source/native checks and stops SDK acquisition before sign-in on FMOD's
changed download-page pin. The independently reviewed pin is refreshed without
changing SDK or authentication boundaries; see the53 report. This Mac lacks the licensed FMOD SDK and
full runtime build tools; native device compilation and simulator controls are
separate from a complete package build. After reviewing the completed local
checks, the owner explicitly approves committing/pushing this53 fix and running
the existing GitHub workflow for an unsigned test IPA. This authorizes the trial
source/build writes; it does not authorize a version tag or public Release.

Retry39267829175 passes SDK acquisition, fresh build/package audit, all five
attestations and independent Ubuntu verification at `e63f1e0`. The separately
downloaded kit in `artifacts/cabrillo-build53-hosted` passes checksums, all254
captured source hashes, all151 unchanged52 dependency hashes and production
picker/bundle-ID checks. IPA SHA256:
`cbf396e7a7b1aec7bbf0a25c19cf3cfe59ef80d26e1f47df1481ed3b7791ad55`.
Keep53 frozen;54 continues the repair. Original-ID Feather phone testing
subsequently fails as recorded above. No existing cloud kit, device or app data
is changed by its delivery.

The adapter reads only the running process's own `application-identifier` and
adjusts Documents UI requests for that app's original host. It never changes the
public bundle identifier, JIT state, entitlements, permissions or data paths.
LiveContainer retains its own picker handling. Missing private APIs retain the
original path and report a redacted status. Test identity injection is compiled
only into fixtures; production objects must exclude its symbol. Preserve all
older source lanes and scoped device gates; no new physical pass is inferred.

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
