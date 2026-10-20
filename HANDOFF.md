# Cabrillo development handoff

## Current work: unified build58 / 0.29.0 — 20 October 2026

The owner explicitly requests preserving this Mac's work and the other computer's
published v0.26.0, merging and pushing the combined source as `hmcneill46`, then
building an unsigned IPA for testing. This authorizes the integration commits,
GitHub push/PR/merge and trial build. **A new version tag or public Release is not
authorized; wait for the owner's test and separate release request.** No iLoader
change or submission is included.

Integration uses `launcher-unified58`, version0.29.0/build58. The local source was
captured at `ee475e3` on `codex/game-input-compatibility`; the other computer's
source is `65e45c2` on `origin/main`, following published v0.26.0. Both histories
must remain reachable. Preserve local input/editor/game-import behavior and the
published Files-picker repairs, Everest1.6642, dependency recovery and integrated
StikJIT. See [the integration report](docs/ios-jit/UNIFIED_BUILD_58.md) for the
lineage mapping and validation state. Integration tests and the new IPA are
pending; earlier passes apply only to their recorded builds.

Build numbers53–57 were allocated independently on both computers. Canonical
`release/app53`–`app57`, `release/public53.json`–`public57.json` and numbered
release builders retain the published versions. Their conflicting local versions
are preserved exactly in `ee475e3`; local feature lanes and evidence remain in the
merged tree. Historical source hashes refer to that original checkout, not to a
substitute recipe with the same number. Use58 for combined implementation.


Historical chronology: written14 September2026; updated20 October for published v0.26.0/build57,
the verified build56 general download repair,
the verified Everest6642/build55 trial,
copy-based Files imports and v0.24.3 publication,
following30 September FMOD clarification after source publication and USB shortcut testing,
iOS15/iPad support, the
build36 Motion Smoothing correction, build37 Everest upgrade and build38 owned-game
preparation, for a fresh development chat opened in
`/Users/harrymcneill/Projects/Cabrillo`. Read this and [AGENTS.md](AGENTS.md) first.
This file is the entry point; linked reports contain deeper source and evidence.
Recheck current files and owner messages before treating this dated state as live.

## Published v0.26.0 / build57 —20 October2026

The owner explicitly requests merging PR7 and publishing the new release.
[PR7](https://github.com/hmcneill46/cabrillo-celeste/pull/7) is merged at
`93415b48ac1c855cd94832f2921ffe7e59fea984`; annotated `v0.26.0` targets that merge.
[Tagged run39414920270](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39414920270)
passes all six jobs: fresh compilation with official SDK acquisition, package
checks, all five attestations, separate Ubuntu verification and publication.
The [public Release](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.26.0)
has all five assets; each independently downloads without authentication and
passes API digests/checksums and exact tag/source/workflow/run attestations.

The immutable `artifacts/cabrillo-v0.26.0-release` kit matches all 299 captured
trial source hashes and all 153 dependency hashes. Actual 199 DLLs pass 434
metadata checks matching the hosted audit, full NLua RSA/tamper checks and 14
native/managed numeric comparisons. The six unsigned helper/framework files,
licences, scripts and host/helper isolation also pass independent inspection.
Release IPA:21,038,042 bytes; SHA256:
`02f60ba0262ea5a76e395f8ce9088169cd9c8388bf2b24a29e4e67fef6a43f08`.
Preserve both this release kit and the original trial kit. All 299 captured app
inputs remain frozen; use58 for new implementation. Publication adds no physical
Feather/helper/DDI/JIT/gameplay acceptance. No iLoader change or submission occurs.

## Retained Built-in StikJIT trial —20 October2026, build57

The owner requests integrated StikJIT as a recommended default, automatic JIT
before Run Celeste with progress, all existing providers preserved, the Run
button icon repaired, automatic pairing-file placement and manual import.
Implementation is in `launcher-integrated-jit`, version0.26.0/build57; source
recipes are `tools/build_release57.py` / `compile_release57.py`.
Read [the57 report](docs/ios-jit/INTEGRATED_STIKJIT_BUILD_57.md).

The iOS17.4 helper owns StikJIT; the iOS15 host keeps the tested mailbox/native
checks and detach gates. Existing explicit provider choices persist; supported
new standalone installs default to built-in. LiveContainer retains its external
methods. Pairing bytes stay protected, are copied atomically and never bundled
or exported in diagnostics. Root Documents tool placement is detected; current
iLoader's hardcoded app list cannot be changed by Cabrillo metadata. The owner
explicitly rules out iLoader changes/submissions, and the proposed patch is
removed. Manual import works independently. The Run label has a centered,
matching foreground for icon and text.

Final local115 Python tests,186 new native launch/pairing controls, actual
43-Swift/6-C/5-Objective-C arm64/iOS15 host compilation, actual arm64/iOS17.4
framework/helper build and14 phone/iPad simulator UI tests pass. Actual simulator
extension IPC also passes process separation,3 progress stages, a validated
prepare reply and temporary credential cleanup using a no-JIT StikJIT stub.
Retained119 profiles/185 native shortcut checks/36 branches/15 bad-URL controls
pass. See the57 report/ledger for exact scopes and receipts. After these local
checks, the owner explicitly approves “Push/build
Cabrillo only”: commit/push as hmcneill46, open a Cabrillo PR and run the unsigned
trial workflow. The later publication request is recorded below; iLoader writes
remain forbidden. Preserve
all274 accepted56 inputs and the immutable public v0.25.1 kit below.

Source `0f08fc64083d539fdba9f1b78fd79bb41e516048` is pushed as hmcneill46 to
`codex/actions-release` in [PR7](https://github.com/hmcneill46/cabrillo-celeste/pull/7).
[Trial39406495715](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39406495715)
passes fresh source/native/managed/FMOD packaging, all five attestations and
separate Ubuntu checksum/attestation verification; publishing is skipped. The
[five-file test kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39406495715/artifacts/12257984521)
requires GitHub sign-in and expires3 November2026 at10:37:38 UTC.
Its independent download in `artifacts/cabrillo-build57-hosted` verifies299 source
hashes, the274 frozen56 inputs,151 unchanged dependency hashes plus two disclosed
StikJIT inputs,199 DLLs/434 metadata checks, full NLua RSA/tamper controls,
14 native/managed numeric comparisons, six exact helper/framework files and all
five exact source/run attestations. IPA21,038,013bytes; SHA256
`c45c0f5067c95ce4422e8def19c6595e078f03f8d52b1061d6d7754428a5a76f`.
All299 captured57 app inputs and this kit are frozen; use58 for new app changes.
No iLoader write or actual Feather/helper/DDI/JIT/gameplay pass is claimed.
Test with the Development profile, preserve the helper, manually import
pairing, connect LocalDevVPN and choose Built-in StikJIT before Run Celeste.

On20 October the owner explicitly requests: “please merge and put the new release
out there”. This authorizes merging PR7, annotated `v0.26.0`, the existing tagged
publication workflow and public IPA/verification/change notes. PR7 is merged at
`93415b48ac1c855cd94832f2921ffe7e59fea984`. Its tree equals the reviewed PR head;
all299 app hashes match the verified trial. Tag object
`d7aadf85461083aec4a4b28f2c51d81d6a03a111` targets the merge; tagged
[run39414920270](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39414920270)
handles publication. Preserve prior trial/release kits and all physical gates.

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

The owner requests latest Everest after the54 release. Official stable1.6642.0
was released17 October2026; exact source is
`5abd7876821223c20711c1844a5187321d6e904c` (7 commits/17 files after6580).
The new55/v0.25.0 lane is `launcher-everest6642`, with separate source recipes,
public dependency lock and synchronized native/managed runtime identities.
Existing platform/loading patches apply, and all253 captured54 inputs remain
exact. Retain the Feather import fix, original bundle ID, JIT/native pins and
Shortcut49. Original game source identity stays unchanged; new patch-tool hashes
select a new prepared-code generation without replacing saves or originals.

Local89 Python controls,119 native save/profile checks and the actual arm64/iOS15
production compile pass. [Hosted trial39320628794](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39320628794)
passes all five active jobs at `e1e78a3511df5642537a75d86ae46e98e0411f34`:
fresh public-source managed/native compilation, official SDK acquisition, full
package audit, all five attestations and independent Ubuntu verification. The
publication job is skipped. The [five-file test kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39320628794/artifacts/12221245338)
requires GitHub sign-in and expires2 November2026 at20:48:01 UTC.

The independent download at `artifacts/cabrillo-build55-hosted` verifies all261
captured app inputs,151 dependencies with only the Everest source hash changed,
original bundle ID/copy-import metadata and signed49 Shortcuts. The actual199
packaged managed DLLs pass434 metadata checks; the local audit report exactly
matches the fresh hosted report. Wrong compiled version and stale tool-hash
controls pass. Actual55 and published54 recipes retain identical original input
pins/source identity, with a new preparation generation. No game, adapter,
native runtime or device JIT was executed by those metadata checks.

IPA bytes:18,765,294; SHA256:
`abd79be029902c301778f8b11044484d00cedc07988f14b3243cf42cde8b04cd`.
Read `docs/ios-jit/EVEREST_6642_BUILD_55.md` and its ledger for exact receipts.
All261 captured55 app inputs and the kit are frozen; next implementation56.
Draft [PR6](https://github.com/hmcneill46/cabrillo-celeste/pull/6) contains the
source upgrade. No55 tag/Release or new physical game/JIT result is claimed.
First/cached preparation, mods, gameplay/save/resume/normal Quit/native return
remain device gates. Keep published54 and all earlier device evidence distinct.

The owner also asks pushes/commits to use `hmcneill46`. The authenticated account
is confirmed and repository-local author/committer use
`57508980+hmcneill46@users.noreply.github.com`. Git's prior automatic name/email
did not grant repository access; do not rewrite published release history.
The source commit's author and committer both resolve to `hmcneill46` in GitHub's
API. Repository-local identity changes leave global Git settings unchanged.

## Copy-based Files imports —19 October, build54 repair

Owner confirmation and a fresh read-only USB collection now close the reported
game-ZIP import defect. Exact54/original bundle ID/source hashes on iOS27.0.1
produce one copy-mode game selection and one875,540,825-byte staged archive.
Journal SHA256 `92ff72a8361d24ea7efd4dcd3b999d08aecc09e6b1a0468bd02ca3654e042985`.
No new physical mod/JIT/gameplay acceptance is inferred. Trial39276928342 and
Ubuntu verification now pass; the trial publication job is skipped.

The owner explicitly authorized the public Release and change notes on19 October.
Annotated `v0.24.3` targets `46dc40678fe839b676a2a9496eb84229d0b4c331`. [Tagged run39285104629](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39285104629) and the
[public Release](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.24.3) complete the build, audit, attestation,
independent verification and five-file publication. All five assets download
without authentication and pass checksums and exact tag/source/workflow/run
attestations. Release IPA bytes:18,764,014; SHA256:
`e3520bced1ff72886d2b1796ee1420f797df71a514ee9b9e0430fd933e18a583`.
All253 tested app inputs and151 dependency hashes remain exact. Preserve the
trial kit and separate tagged kit in `artifacts/cabrillo-v0.24.3-release`; use55 for new app
implementation. The tagged binary has no separate device run claimed, and all
older physical mod/JIT/gameplay/save/lifecycle/iPad/120Hz gates retain their scope.

The owner installs53 and reports the same game-ZIP tap stall. Read-only USB
collection verifies installed53/original bundle ID/iOS27.0.1 and all254 exact
hosted inputs. Its entitlement is valid and hook is installed, but no game
selection callback arrives. The owner tests the same game ZIP in the existing
Saves → Import backup picker: two real callbacks arrive and backup validation
correctly rejects the game ZIP. A further game attempt still fails; no restore
or rollback occurs. Thus53's host hook is insufficient. Keep its build/package
passes separate from this confirmed phone failure.

Build54 /0.24.3 in `launcher-copy-picker` switches just the game/mod selectors
to `asCopy:YES`, matching existing backup/save imports. The53 compatibility
module stays byte-identical. It adds mode diagnostics and keeps all existing
types, multi-selection, staging, scoped reads, validation, JIT and runtime.
The copy/backup phone comparison also differs in purpose/filter;54's actual
game test was still required at that comparison. Local source/UI/compile checks pass;
the complete unsigned54 kit is built and independently verified as recorded
below. The subsequent game-import phone pass is recorded above; physical mod
import remains separate.

Read `docs/ios-jit/COPY_PICKER_BUILD_54.md` and its evidence ledger. All25453
captured inputs/kit remain frozen;54 is the active corrective lane. Original
logs/receipts are ignored in `.private/picker-failure-2026-10-19`. Only relevant
app metadata/journals were read; no extra debugger, installation, phone write or
setting change was dispatched. The owner's prior approval covers this same
tested picker repair/unsigned trial. The later explicit Release request above
extends that scope to v0.24.3 publication, preserving unrelated gates.

Hosted trial39276928342 at `4a094527a96e62fbf63518c088a1dd48d19407e5`
produces the complete five-file54 kit. SDK acquisition, full compilation, package
and attestation creation pass. The independently downloaded kit in
`artifacts/cabrillo-build54-hosted` passes checksums, all253 captured input hashes,
all151 unchanged53 dependency hashes, original bundle ID, copy-import BuildInfo,
production symbols and absence of the test seam. All five local attestations
verify exact source/ref/workflow, hosted runner and run identity. IPA bytes:
18,764,021; SHA256:
`254a126168837708bbb7d136da0c3e426a3522feb375c0d19bb26d5fbcf89762`.
Artifact12199896629 has14-day retention. This manual trial created no tag or
Release; the subsequent tagged publication is recorded above. The separate
Ubuntu verification job now passes; the trial publication job is skipped. Preserve the immutable253
app inputs/kit; use55 for new implementation. Trial delivery used the local IPA
and Actions artifact, with no cloud installer replacement or automatic phone install.

## Signing-aware Files picker —19 October, build53 trial

The owner installed standalone52 through Feather with the supplied Development
profile. Its local ZIP appears normal but tapping never selects/imports; there
is no Open button. They confirm Feather retained Cabrillo's original bundle ID.
The private profile audit finds an explicit different application ID. The owner
then confirms matching Feather's Identifier fixes selection and asks to remove
that workaround for themselves and other users.

Build53 /0.24.2 implements automatic Documents UI host-identifier compatibility
without changing Cabrillo's bundle ID, files, runtime, JIT protocol or scripts.
The new source overlay is `experiments/ios-jit/launcher-signing-picker`; all168
accepted50 base files are locked in `release/app53/Dependencies.json`. Only the
new main and compatibility module replace/add native implementation. Policy,
production arm64 compilation and actual Apple picker/staging checks have
separate receipts; see `docs/ios-jit/SIGNING_PICKER_BUILD_53.md` for final results
and the distinction between synthetic simulator identity tests and phone proof.

`release/public53.json` is the preserved53 manifest. Those builds use
`tools/build_release53.py` with an explicit FMOD SDK. The52 release remains
published and immutable. This Mac has Xcode26.6 but lacks the licensed SDK,
Mono/sn and CMake needed for a local complete fresh dependency/IPA build. The
hosted53 IPA is now built and independently verified as recorded below. No
unchanged-ID phone test has occurred. The next step is an owner phone install
with the original Cabrillo identifier and existing
Development profile. Do not delete either of the owner's existing installations
or infer save migration between their different bundle IDs.

The adapter uses optional Security SPI and private `DOCConfiguration` lookup;
it fails back to original behavior with redacted diagnostics when unavailable.
LiveContainer keeps its existing picker fix. Fixture-only entitlement injection
must never enter production. After reviewing the local checks, the owner
explicitly approves committing/pushing the53 fix and running the existing hosted
workflow for an unsigned test IPA. This is approval for the source/build trial,
not a version tag, public Release or device mutation. Hosted results remain
separate from phone acceptance. Preserve all older runtime/save/lifecycle/iPad/
120Hz acceptance gates.

Source commit `1f2de6d` is now pushed to `codex/actions-release`. Hosted trial
39266218357 passes source/native checks but stops SDK acquisition before sign-in
on a changed public FMOD download-page pin. Independent public-source review
confirms the helper's request contract still matches; only that reviewed asset
hash is refreshed. A credential-free probe and67 Python controls pass. SDK and
library pins/authentication restrictions remain exact; retry the unsigned trial.
See the53 report/ledger for this preparation, separate from phone proof.

Retry39267829175 succeeds at `e63f1e0a8030daa3f0f4228ca6992c428e4f1811`:
official SDK acquisition, full fresh managed/native build, package audit, all
five attestations and separate Ubuntu verification pass; publication is skipped.
The independently downloaded five-file kit in `artifacts/cabrillo-build53-hosted`
passes checksums, all254 captured app-source hashes, all151 unchanged52 dependency
hashes, original bundle ID, production picker symbol and absence of its test seam.
IPA bytes18,763,886; SHA256
`cbf396e7a7b1aec7bbf0a25c19cf3cfe59ef80d26e1f47df1481ed3b7791ad55`.
The Actions artifact is12194283151 with14-day retention; no tag/Release is made.
Keep this immutable kit; use54 for new app implementation. Delivery is through
the local IPA/Actions artifact; no existing iCloud kit, phone or app data is changed.
The unchanged-ID Feather signing/import phone gate subsequently fails as
recorded above. Hosted/package success is not physical acceptance.

## Historical local development records — 30 September–3 October

The following **local**53–57 records describe this Mac's independently numbered
work before integration. They are distinct from the **published**53–57 records
above. Their former no-publication instructions, workflow selection and next-build
numbers are historical; the current authorization and integration state are at
the top. Reproduce colliding local release recipes from commit `ee475e3`.

## Local build57 / 0.28.0 — live input preferences, 3 October

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


## Local build56 /0.27.0 — SwiftUI touch editor, 3 October

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

## Local build55 /0.26.1 — saved-game startup repair, 3 October

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

## Local build54 /0.26.0 — optional feather touch steering, 3 October

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

## Local build53 /0.25.0 — game input compatibility, 30 September

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

The owner tested the verified Actions trial kit, reports that everything looks
good, and explicitly requests the version tag and workflow publication. This
supersedes the previous no-tag/no-Release state for52. This is owner-reported
trial acceptance; no additional device diagnostics or detailed lifecycle/save
coverage is inferred. Keep the earlier granular device gates distinct.

PR4 is merged at `2acf9af18f9dd1f200d8114ba9cbd2f557dfe24c`. All247 captured
app inputs and the tested build/publishing scripts match the trial. Annotated
tag `v0.24.1` points at that commit. The tag-triggered workflow is
[run36696860903](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36696860903).

[Cabrillo v0.24.1](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.24.1) is published with the unsigned IPA, provenance,
package audit, release notes and checksums. Every job in the tag-triggered build,
independent verification and publisher passes. All five public assets download
without authentication and pass their API digests/checksums and tag-specific
GitHub attestations for the exact merged commit.

The release IPA is 18,759,819 bytes, SHA256
`c223f7e31aea15ecc640f8f10388c4628f9ba063f1a52967279c949023123b47`. All 247 captured app source inputs and all 151
dependency inputs match the accepted trial; pre-signed document URLs now identify
the merged commit, with unchanged document hashes. NLua strong-name verification
passes. 189 of 199 managed DLLs are byte-identical to the trial.
The tagged binary has no separate device run claimed.

Exact public files, attestation bundles, release metadata and local verification
are retained in `artifacts/cabrillo-v0.24.1-release`; completed check reports and
raw hosted logs stay ignored in `.build/release-v0.24.1`.

Preserve both the tested trial kit and the separately attested tagged rebuild.
No app source/identity changed for publication;53 remains the next implementation.
FMOD SDK components/credentials and game files remain excluded from Git/releases.
The public IPA is unsigned and requires the user's compatible installation/JIT
setup and their original game ZIP. No phone/iCloud mutation was needed for this release.

## Earlier public Actions trial —30 September

The owner requests a complete hosted IPA build and README/developer guidance,
and explicitly permits the temporary FMOD login as encrypted Actions secrets.
Source/workflow commits, pushes and hosted trials are authorized. PR3 is merged
into main (`51f2ae9`); this work is on `codex/actions-release`. The protected
`cabrillo-release` environment permits `main`, the trial branch and `v*` tags;
credentials are confined to the official SDK fetch step. Never print their values.

[Hosted run 36682093793](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36682093793) passes the complete fresh build and independent
verification at commit `789f20e751901cc4538ff25b8033abeb6f339af7`. The
[trial kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36682093793/artifacts/11083060317) contains five attested files. A separate local download
check verifies all five attestations, checksums, all247 captured app inputs and
NLua's strong-name signature. The IPA is18,759,836 bytes, SHA256
`7392dd6f0199faf0d8501ed690772685e127ee9fd463ed2b3ce59441e719dbe4`.
This manual run did not create a version tag or GitHub Release.

All59 Python controls,119 native profile controls,185 native shortcut checks,
36 generated branches and15 bad-URL controls pass. The complete151-input
dependency provenance explicitly declares14 source archives, one mixed archive,
132 public binaries, two licensed FMOD runtime archives and two signed documents.
The IPA has199 managed assemblies and no bundled original/prepared Celeste code
or game assets. SDK cleanup passes; only the five allowlisted files are uploaded.

The downloaded kit, attestations and verification are retained under
`artifacts/cabrillo-build52-hosted`; raw hosted logs/check reports are ignored in
`.build/hosted-release52`. All247 captured52 app inputs are frozen at the hosted
commit above. New app implementation needs53. No phone or iCloud delivery occurs.

Release52 /0.24.1 uses the unchanged accepted50 launcher sources, freshly built
public runtime dependencies and the exact signed49 Shortcut documents. Its active
manifest is `release/public52.json`; local builders use `tools/build_release52.py`
and their own FMOD SDK. README, BUILDING and RELEASING explain the licensed-input
boundary, workflow modes and what attestations prove. No game ZIP, prepared Celeste
code, private compiled capsule, Apple account or private signing key is used.

The full local51 package passes, but its outer wrapper correctly rejected commit
drift during concurrent workflow edits. Keep that scope separate from hosted52.
Its245 captured inputs and build50's243 inputs remain byte-exact. Hosted51 exposed
a missing Mono6.14.1 `sn` prerequisite and an Intel-only NuGet host pin.52 retains
NLua signing and pins the official Apple Silicon host package separately; all128
package identities and hashes are checked before native compilation. Preserve
the51 manifest/compiler/identity and original38 release manifest as frozen history.

Apple Shortcut signing requires an iCloud session. The public reviewed49 signed
documents instead have their certificate chains, AEA signatures and generated
actions/connections verified on every Mac run. No new sign-in is needed. Their
certificates expire26 October2027; renewal needs a reviewed local signing pass.

Keep app50/shortcut49 on the phone. This is source-build/package evidence, not
physical52 gameplay acceptance. No public version tag or Release has been created.
The manual Actions kit is available for14 days; tags publish only after rebuilding
and verifying. Preserve all earlier save-manager/iPad/sustained120/device gates.

## Earlier local FMOD download verification —30 September

The owner requested local CI preparation before Actions and a stop at credentials,
then supplied a temporary FMOD account for testing. Its credentials were used via
hidden terminal input and were not saved to files, shell arguments or reports.
`tools/check_fmod_access.py probe` verifies the reviewed public website scripts
and HTTP401 boundary; `check-account` passes against the real account and exact
1.10.09 iOS catalogue entry. Sessions are created separately from any browser and
logged out. A changed website flow stops for review. See `docs/RELEASING.md`.

`tools/fetch_fmod_sdk.py` now passes the actual authenticated official download,
checksum, read-only DMG mount, four-file staging and detach. The143,583,015-byte
installer matches the original SHA256 recorded before the download:
`7f1934f248df7202b8efb6951570f60c52566217e230f26ed3682a6447336e5f`.
Both device libraries and licence match their existing pins. The existing FMOD
arm64 preparation/localization step produces byte-identical runtime archives to
`.build/owned-fmod38-c/receipt.json`, using the retained public native receipt
only for its Theorafile symbol check. This is not a full native/IPA rebuild.

The helper restricts the CDN to the exact observed host, forwards no account
headers to it and follows no redirects. Its explicit environment-credential
mode is covered by synthetic tests; the live test used hidden prompts. Safe
receipts: `.build/fmod-download-preparation/{probe,account-check,download,component-check}.json`.
SDK files: `.private/fmod-ci-2026-09-30-a`; prepared runtime libraries:
`.build/fmod-ci-2026-09-30-prepare`. These remain ignored, never public artifacts.
No credentials, account identifiers or signed URLs were written into receipts.
All48 Python controls pass, including28 new FMOD controls and the retained20.

At this earlier stage no GitHub secrets/write, Actions run or app identity
allocation had occurred. The completed hosted52 work above supersedes that
next-step state; delivered app50/shortcut49 remains unchanged.

## FMOD runtime permission received —30 September

The owner supplied Firelight's email reply from Brett Paterson: a built application
may distribute the runtime libraries; source developers must download FMOD from
fmod.com, and SDK components must not be redistributed. The runtime permission
question is answered on those terms. See `docs/RELEASING.md`. The supplied email
text is retained privately at `.private/licensing/fmod/2026-09-30-owner-email.txt`;
no email headers or account access were supplied or needed for this record.

The unchanged50 IPA passes the existing public-package structure/payload audit.
Its FMOD input recipe links the two pinned iOS runtime libraries and includes the
licence notice. The package contains no FMOD SDK headers, separate static archives,
SDK examples or authoring tools. Existing managed-payload evidence still records
no bundled original/prepared Celeste assemblies. This review adds no device pass.

Release implementation remains separate: the frozen38 recipe assumes a configured
SDK ZIP URL and rejects an explicit local SDK as a private input. The local DMG
acquisition check above now resolves the authenticated-download uncertainty. A future51 release
must obtain SDK inputs from FMOD, keep SDK components/credentials out of published
outputs, and truthfully record the licensed binary dependency in provenance.
Do not mirror the SDK for developers or publish old receipts as new release evidence.
The email is recorded locally; no release tag, GitHub write or IPA publication was
performed for this update. Keep app50/shortcut49 and all earlier physical gates.

## Source publication —29 September

The owner explicitly requests committing, reviewing and pushing the completed
work through app50/shortcut49. This supersedes the earlier no-GitHub-write state
for this source publication only. Private packages, game data, FMOD inputs,
signing/pairing data and raw device logs remain excluded. No release tag or
public IPA is authorized; `release/current.json` remains blocked on FMOD.

The publication branch is `codex/owned-game-import`, based on `b7a8d28` (PR2).
It includes build38 user-owned game preparation and the Home Screen launch work
through50, preserving all delivered sources. Review corrected CI's obsolete
build39 shortcut target and Mac-specific Xcode path. The public runner now tests
the accepted50 coordinator and49 generated workflows with the configured Xcode.
Local checks pass:20 release controls,119 native save/profile checks,185 native
shortcut checks,36 workflow branches and15 invalid-URL controls. The original43
missing-callback and49 cellular-order failures reproduce as negative controls.
See [the publication review](docs/ios-jit/SOURCE_PUBLICATION_BUILD_50.md).
Check the branch's remote HEAD and GitHub Actions for publication completion.
This is a source/CI update; keep app50/shortcut49 and use51 for new app code.

## Active development: app50 /0.23.2 with shortcut49 —28 September

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

## Previous development: app49 /0.23.1 with shortcut49 —28 September

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

## Previous development: app48 /0.23.0 with shortcut48 —28 September

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

## Previous phone testing: app47 /0.22.4 with shortcut46 —28 September

USB collection now verifies installed47, recovers the missing journals and records
five successful fresh launches: Automatic on Wi-Fi, two Travel runs with Wi-Fi/VPN
already connected, Travel starting on cellular with VPN disconnected, and Automatic
from that same cellular state. The last three are remotely started after ordinary
process termination of idle Cabrillo/StikDebug. Every run passes26 native checks
while detached. All four Travel runs verify the tunnel in Airplane Mode, receive
their restore receipt, clear recovery and return with the correct ready message.
Automatic correctly chooses Travel without a Wi-Fi address. Times to ready are
25.9/27.7/28.3/53.2/31.8s respectively. A repeated ready launch does not start new
JIT/radio work. Read the updated47 report and ledger for hashes and scope.

The original27 September failure is now located: JIT passes, restoration opens
Shortcuts, then its receipt never arrives. A recovered later journal proves
fresh-process networking recovery succeeds; another late JIT callback is rejected
in an idle process. The missing restore receipt remains unexplained and has not
recurred in the four fresh Travel runs. Do not claim a code fix: app47/shortcut46
remain unchanged. JIT callbacks are absent in both failures and passes, so that
absence alone is not a proven cause. All221 frozen47 inputs still match.

The cellular-start passes occur near a known Wi-Fi network; preparation may rejoin
it before isolation. Entirely out-of-range operation, alternate restore presets,
user cancellation, other current LC guests,47 normal game Quit and independent
diagnostic exports remain separate gates.46/47 Results are still empty. The
recovered47 journals contain game startup/gameplay but no normal Quit. Keep earlier
save-manager/iPad38/sustained120 gates distinct. No repeat of a passed launch solely
for an export. No48 implementation was allocated and no GitHub/public IPA write
is authorized.

The phone is left in Cabrillo with verified JIT ready, Automatic restored, Wi-Fi
and cellular on, Airplane Mode off, and LocalDevVPN connected. All125 save files
(683,136 bytes) and launcher preferences match the pre-test snapshot. Private
evidence is under `.private/device-evidence/2026-09-28/phone47-*`; the last run is
`phone47-automatic-cellular`. USB collector `.build/phone47-snapshot.py` is read-only.
The owner setting requests are answered; no further tap is pending.

Remote UI taps are unavailable on26.5; Apple remote control requires27, and the
signed UI-test runner installation fails the three-app free-signing limit. No
existing app was removed and no second debugger attached. File/log collection,
screenshots and normal process control work. CoreDevice URL launches initially
time out but later recover, allowing the three autonomous fresh tests. A USB
preference-file edit was ineffective because of cached defaults; use the app UI
for setting changes. The owner changed Travel and restored Automatic this way.
Plain LC opening selected the last guest, YouTube, as the owner explained; this is
not an observed shortcut failure.46's generic Home `open-url` route also merits a
separate current-guest selection review before claiming universal one-icon routing.

Build47 in `launcher-shortcut-completion` fixes the false Home Screen launch timeout
observed after the exact46 shortcut successfully enables JIT and returns. The owner
confirms green JIT and Celeste startup. A Wi-Fi screenshot verifies native-pass/
green/Run enabled alongside app43's contradictory timeout. At that original43
review, CoreDevice and native AFC transfers each timed out25s. Do not claim
new level-input or normal-Quit evidence. Raw scoped records/screenshots are under
`.private/device-evidence/2026-09-26/shortcut46`. The latest synced read-only shortcut
check verifies one Cabrillo containing all45 exact46 actions.

App43 waits for an extra JIT-stage Shortcuts receipt even after real native checks
pass and the debugger detaches. A focused regression against original43 fails on
that missing-receipt case;47 passes.47 completes JIT from those actual native gates
in the foreground. It still requires the separate network-stage receipts and keeps
Travel recovery durable until restoration is confirmed. Late JIT callbacks cannot
change a completed launch/newer restore. Diagnostics record callback receipt
separately. Read [the47 report](docs/ios-jit/SHORTCUT_COMPLETION_BUILD_47.md) and ledger.

132 native controls,36 generated branches and12 broken-connection controls pass.
The package is verified:18,697,409 bytes, SHA256
`78e259c6dfe9760cdb3df26a7421f290e59fce9a3acdd878616ed94731c71bd8`,
executable/dSYM UUID`e931080600f83955a66dc1dd3e0b38cd`. All199 managed assemblies,
16 native dependency archives and SwiftUI sources stay43-identical. Only the native
session reducer changes, alongside test/build metadata. All221 inputs are frozen
in `artifacts/cabrillo-build47-final`; all35–46 comparisons pass. Further
implementation needs48. Keep the exact46 shortcut; no new shortcut import is needed.

All six kit files are confirmed uploaded at `Celeste JIT Tests/0.22.4-build-47`;
the initial transient iCloud4355 errors cleared. No direct phone-folder staging
occurred; the owner now reports47 execution after updating through iCloud. To stay below1GB,
only the superseded41 cloud IPA was removed after verifying the exact retained
local copy. All Results and accepted32/working43 installers remain.

Keep app47 and shortcut46; the scoped cellular-start/Travel passes are recorded
above. Preserve an independent export after testing; continue remaining recovery
and game/Quit checks. No new
GitHub/public IPA write. Keep native save-manager, iPad38 and sustained120Hz gates
separate. Finish any current game normally before closing both LiveContainer apps
for a fresh test. All current setting/launch requests are answered.

### Failed45 and retained conversion evidence

All45 actions are verified in the synced shortcut. The owner reports immediate
“Make sure you pass a valid URL to the Open URL action”; the installed Mac runner
returns the same error and exit1. No Cabrillo/JIT handoff occurs. Raw scoped import
and connection evidence is under `.private/device-evidence/2026-09-26/shortcut45`;
the Mac reproduction is `.build/shortcut46-research/original45-home-run.txt`.
All11 revision45 inputs and its six-file uploaded kit remain frozen. Its Apple
content-conversion evidence remains valid; it did not execute the failing pair.
No45 phone-folder transfer occurred after USB disconnected.

### Failed44 and the cause now reproduced

The owner imported44; all48 named actions were verified. Actual app43 session
`aa99d420-4008-41e4-a9dc-81a0acefca4e`, PID21828, passes the VPN hello in19ms. Its
11,083-character JIT link is plain text in Shortcuts. The first helper opening
works; the second Open URL triggers `LCHandleControlAppURL +732` with a nil base64
string. The owner sees Home Screen and the helper error. Mailbox remains1/untraced;
no JIT/game runs. Replace Text, Nothing and the entire workflow finish on the phone,
but no native callback is recorded. See [the44 report](docs/ios-jit/SHORTCUT_FILES_44.md).

The pinned3.8.10 handler/binary matches the exception offset: it tries to decode an
`open-url` query item with no value. Apple's actual WFStringContentItem conversion
reproduces that exact truncation for long links; WFURLContentItem preserves them.
This also explains43's cold guest opening without a request and the successful
native direct route.44's four inputs remain frozen. Its kit is preserved/uploaded;
use46 for new tests. Raw44 evidence is in the private shortcut44 folder.

### Scoped manual43 acceptance

43's installation retained its data container and125 save/profile files, and its
original46 shortcut actions were verified. Its cold Automatic session
`f1769b89-5b7e-4108-a632-1d8fd7864f6a`, PID21378, passes VPN hello in80ms and opens
StikDebug but executes no request; Stop and Output stalls before a later error.
No radio changes occurred. This cold shortcut gate remains failed.

The subsequent native Enable via LiveContainer2 tap with StikDebug running succeeds
for the same PID/request: automatic helper return,26 native checks and debugger
detach. The owner sees green and starts Celeste. The journal verifies cached game
preparation in0.095s, zero active catalogue requests,14 graphics passes and the
first rendered/readback frame. Later collection confirms ten paired menu touches,
profile save readback, normal Quit/stage8 and a delayed native heartbeat. No level
input is observed. This is a manual warm JIT/menu/save/Quit pass, not shortcut
acceptance. See [the43 review](docs/ios-jit/SHORTCUT_GUESTS_BUILD_43.md).

All212 app43 inputs, its exact41 runtime and original shortcut remain frozen.
All43 kit files are uploaded. Preserve every Results folder and accepted32.
Private runtime evidence: `.private/device-evidence/2026-09-26/phone43`, especially
`warm-native-success.jsonl` and `before-shortcut44.jsonl`. Never attach another
debugger alongside Stik; a retained journal is not a live PID check.

## Previous phone test: shortcut revision42 with app41 —26 September

App41 is installed and all six iCloud kit files are uploaded. Direct collection
verifies its data container, LC JIT off/Fix File Picker on and125 unchanged
save/profile files. It passes the actual phone VPN-loopback Remote Pairing hello,
then the39 shortcut fails its first string comparison before StikDebug opens.
Apple's device log reports `ConditionalAction Code=1`, `WFActionIndex=4`; the UI
shows a missing parameter. The native JIT/detach gates correctly remain unpassed.

Shortcut revision42 adds explicit text coercion for the six dictionary-value
comparisons. It uses the exact installed41 app and39 callback protocol; **no42 IPA
is produced**. Read [the report](docs/ios-jit/SHORTCUT_FILES_42.md) and its ledger.
36 isolated Apple conditional-engine checks pass (12 original failure controls),
as do36 generated branches. Six source/dependency inputs are frozen in
`artifacts/cabrillo-shortcut42-final`; next implementation identity43. No GitHub
write/public IPA is authorized. All earlier application inputs remain unchanged.

The five-file42 kit is uploaded to `Celeste JIT Tests/shortcut-42` and staged in
`On My iPhone/LiveContainer/Cabrillo-shortcut42`; full signed-file readback matches.
Initial import kept it as Cabrillo 1 beside old Cabrillo, so the first retry still
executed39 and failed identically. The owner then removed old Cabrillo and renamed
the new copy. Read-only scoped inspection of the synced Mac shortcut records now
confirms **Cabrillo** contains42, including all text coercions. Re-add the Home
Screen icon if its old identifier still targets the removed shortcut.

CoreDevice app-file copies/launches started timing out while LocalDevVPN is on.
Direct paired USB `pymobiledevice3 apps pull` still collects the guest Diagnostics;
native DVT screenshots and USB system-log collection work. Do not restart system
services or attach any debugger. Raw evidence is under
`.private/device-evidence/2026-09-26/shortcut42` (latest collected41 session400b7f83
ends failed, untraced, without StikDebug/game execution). The owner has a pending
request to close Cabrillo/LC1 and run the now-correct shortcut, leaving any prompt
visible for inspection. Then continue Automatic, fresh-process Travel/recovery
and game/Quit. Preserve independent exports and earlier distinct acceptance gates.

## Previous phone test: Remote Pairing probe / build41 —26 September

The owner installed40. Direct collection verifies the exact identity, retained
data container and125 unchanged save/profile files. Automatic passes the LC
availability fix, opens LocalDevVPN and returns, then times out before any JIT
request. The probe incorrectly checked legacy lockdown62078; StikDebug uses
Remote Pairing49152. A hello from the Mac to this phone's verified network address
returns protocol24/minimum8 with tunnel connections allowed, without pairing or
debugger access. This is protocol evidence, not VPN-loopback/JIT acceptance.

Build41 /0.22.2 (`launcher-shortcut-tunnel`) implements that bounded hello and
failure diagnostics, preserving40 routing, actual JIT/detach and recovery gates.
Read [the report](docs/ios-jit/SHORTCUT_TUNNEL_BUILD_41.md) and
[ledger](docs/ios-jit/SHORTCUT_TUNNEL_BUILD_41_EVIDENCE.json).91 native checks and36
generated branches pass; all199 managed assemblies/16 archives, UI and existing
shortcut are unchanged. All210 inputs are frozen in `artifacts/cabrillo-build41-final`.
Further implementation needs42. No GitHub write/public IPA is authorized.

The six-file41 kit is staged on the USB-connected phone at
LiveContainer/Cabrillo-build41 with full IPA readback verified. The unused40
process was closed after collecting its failed state, and LC's installer opened.
An owner request to tap the existing red Cabrillo replacement entry is pending.
Do not retry the ineffective accessibility activation from the40 installer.
After installation, continue Automatic, then fresh-process Travel and game/Quit.
The41 iCloud kit is locally placed; recheck upload status. Only the superseded39
cloud IPA was removed after exact local-copy verification; all Results and local
artifacts remain. Keep independent exports and the earlier distinct gates.

## Previous phone test: shortcut routing correction / build40 —26 September

The owner installed39 and its shortcut and authorized direct Wi-Fi testing, then
connected USB. Phone logs reveal a real39 defect: the LC host denies the
`localdevvpn` availability query, so Cabrillo stops at setup despite the installed
helper. Remote Shortcuts activation reproduces launch into that guard. No39
VPN/JIT or Travel pass is present.

Build40 /0.22.1 fixes this in `launcher-shortcut-routing`; read
[the report](docs/ios-jit/SHORTCUT_ROUTING_BUILD_40.md) and
[ledger](docs/ios-jit/SHORTCUT_ROUTING_BUILD_40_EVIDENCE.json). It uses actual open
results/service replies within LC, retaining host identity, native JIT/detach and
recovery gates. The installed39 shortcut stays compatible.62 native and36
generated-branch controls pass; all199 managed assemblies/16 dependency archives
remain exact39. All210 inputs are frozen in `artifacts/cabrillo-build40-final`.
Next unused identity is41; no GitHub write or public IPA is authorized.

The six-file kit is staged directly on the phone in LiveContainer/Cabrillo-build40;
the IPA readback is exact. The idle39 process was closed and LC's normal installer
opened. A concrete owner request to choose replacement of existing Cabrillo is
pending; do not confuse staging/opening with installation.125 current save/profile
files and preferences are backed up under the private phone evidence. The six-file
iCloud kit at0.22.1-build-40 is confirmed uploaded after a transient account/server
error cleared. Continue with real Automatic, then fresh-process
Travel and gameplay/Quit; preserve independent Results exports and old gates.

The phone screenshot confirms LC's replacement dialog is actually open. Its red
`io.github.hmcneill46.celeste.everest.jit.everest.app` option selects the existing
container. Remote accessibility inspection works, but one activation request had
no effect; the subsequent installed identity remains39. Do not repeatedly retry
remote taps or claim40 installed. The owner has the exact on-screen instruction.

## Previous local delivery: Home Screen shortcut / build39 —26 September

The owner requested one Home Screen icon that prepares JIT and returns to Cabrillo,
including a cellular/Airplane Mode option and recovery. Build39 /0.22.0
(`launcher-shortcuts-20260926-39`) is packaged and its eleven-file kit is confirmed
uploaded. Read [the report](docs/ios-jit/SHORTCUT_BUILD_39.md),
[ledger](docs/ios-jit/SHORTCUT_BUILD_39_EVIDENCE.json) and
[setup guide](docs/HOME_SCREEN_SHORTCUT.md). This remains local/private work; no
new GitHub write or public IPA release is authorized.

- Native coordinator: verifies the local VPN before/after Airplane Mode, sends a
  fresh PID-bound script, supplies the actual LC host bundle for helper return,
  and waits for native memory checks plus detach. Shortcuts stage callbacks cannot
  grant JIT readiness. Its recovery record survives restarts and rejects stale
  callbacks; an unfinished radio shortcut is not followed by concurrent radio writes.
- Automatic leaves Wi-Fi/cellular switches alone with connected Wi-Fi; Travel
  uses an explicit restore preset because their exact previous switches cannot be
  read. First-use permissions, StikDebug's external-request confirmation, pairing
  and online DDI setup remain explicit platform/helper requirements.
-54 native controls,36 generated shortcut branches and4 simulator UI tests pass.
  Two Apple-signed import variants (LC1/default and standalone) exist. All199
  managed assemblies and16 native archives remain exact38; the39 builder locks
  the same three managed/native/FMOD receipts. No game assemblies/assets are bundled.
- Final IPA18,692,002 bytes; SHA256
  `dcf55b9d891f1c98a0885e798e638a49bf54700032f67a83cbdabdfd19a7a2a0`.
  New UUID `750fa3a8d4143f3fb813053143dca898`.210 input files and source archive
  are frozen in `artifacts/cabrillo-build39-final`. New implementation needs40.
- Kit: iCloud → Celeste JIT Tests →0.22.0-build-39, all11 files uploaded. Also
  copied over Wi-Fi into On My iPhone → LiveContainer → Cabrillo-build39; the
  signed shortcut readback is exact. Copying is not installing or executing it.
  The owner has a concrete pending request to update the existing guest, import
  Cabrillo.shortcut with its name unchanged, configure the selected helper's
  confirmation setting and test Automatic on Wi-Fi first. Travel follows in a
  fresh process. Do not claim39 phone acceptance before reviewing this response/logs.
- The iPhone15ProMax is reachable through paired CoreDevice over Wi-Fi, confirmed
  by actual Cabrillo file reads and kit transfer. Airplane Mode deliberately drops
  that connection; collect the durable logs after radios return. Never attach a
  second debugger alongside StikDebug. Raw device evidence is private under
  `.private/device-evidence/2026-09-26/phone39`.
- Newly collected38 phone evidence verifies cold game preparation15.368s, direct
  adapter binding, real first-frame/readback and SJ Grandmaster lobby `GM-main`.
  This scoped38 observation ends backgrounded: cached preparation, normal Quit/
  native return, owner visual review and existing native save-manager gates remain
  open. The iPad38 gate remains separate. Preserve32 as the broader fallback.

Next: inspect the owner's39 response and logs, then test Travel/network recovery
and gameplay/Quit. Preserve independent Results exports. Release configuration
remains the frozen38 gate; no GitHub run has tested39. Next unused identity is40.

## Previous local delivery: owned-game import / build38 —25 September

The owner requested an IPA with no original/prepared Celeste game code or original
game assets, allowing heavier one-time preparation from their original ZIP.
Build38 /0.21.0 (`launcher-owned-game-20260925-38`) is implemented, packaged and
locally tested on `codex/owned-game-import`. Read
[the report](docs/ios-jit/OWNED_GAME_BUILD_38.md) and
[ledger](docs/ios-jit/OWNED_GAME_BUILD_38_EVIDENCE.json). This request authorizes
local work and the established private device/iCloud delivery, not a fresh GitHub
write or public IPA publication.

The game-free bootstrap imports three hash-pinned originals, coreifies and patches
Celeste/Everest and generates hooks in Documents. Original and prepared generations
have verified receipts and atomic publication. Later launches verify/reuse the
cache; native frame callbacks bind directly to the existing adapter afterward.
Two Everest path lookups and Cecil's late assembly-resolution fallback distinguish
bundled public patch rules from the verified game directory. No original/prepared
game, generated game hooks or build-only references enter the app bundle.

- Final public inputs: `.build/owned-public-inputs38-e`; final managed build:
  `.build/owned-public-managed38-e`; native: `.build/owned-public-native38-e`;
  explicit licensed FMOD SDK preparation: `.build/owned-fmod38-c`.
- Public source/native/managed/app stages ran with private capsules, original game
  inputs and historical checkouts inaccessible. No historical folder was modified.
  FMOD1.10.09 is the only private build dependency. The public release recipe and
  locks now exist; publishing stays blocked on permission and an authorized CI SDK
  input. Never describe FMOD as open source or this as bit-for-bit reproducibility.
- Nineteen storage/recovery controls, cold/cached real-game/save/hair/resume/Quit,
  full pinned Strawberry Jam cold/warm mods, Motion Smoothing Fast/Fancy60/120,
  119 profile checks, seven simulator loading tests and20 Python controls pass.
  Final host fixture is `.build/owned-game38-host-public-c`; the ledger pins all
  matching receipts. Host gameplay uses a retained macOS native test runtime and
  does not validate new iOS archives on a device. Mac preparation15.65s and warm
  verification0.039s are not phone/iPad timings or sustained120Hz evidence.
- Package/dSYM, frozen230 input hashes and source archive:
  `artifacts/cabrillo-build38-final`. Unsigned IPA18,659,553 bytes,
  SHA256 `9968253600c30566a527d97a96780dad353cdf616be8f2af9e0ec9ae8e0f2e03`.
  Payload audit finds199 managed DLLs and zero bundled game assemblies.
- All six kit files are confirmed uploaded to
  `iCloud Drive/Celeste JIT Tests/0.21.0-build-38`; Results is preserved for testing.
  No phone download/execution is confirmed. Update the existing LC slot, select
  the original unmodified ZIP once, use fresh JIT, then test first/cached launches.
- Build38 is installed on the connected TrollStore/Dopamine iPad. All11 captured save/
  profile files remain exact. The original ZIP was verified and staged over USB.
  The old suspended37 process was retired; native launch and cold/cached gameplay
  are awaiting the owner opening the app. A concrete async test request is pending.
  Private install/profile/log evidence is under
  `.private/device-evidence/2026-09-25/ipad38`. Do not claim physical38 acceptance.

Next: inspect the owner's38 response/Results and device logs, then fix any actual
failure in a new identity39. Existing full native save-manager and37 lifecycle
acceptance gates remain separate. Keep32 as the broad phone fallback. All38
implementation/package inputs are frozen; next unused identity is39. No new
GitHub write was authorized for this work.

## Latest owner request: public CI and gated IPA releases —25 September

The owner requested GitHub Actions for deliberate stable IPA releases, then chose
"Set up CI now; keep IPA publishing gated until public packaging is ready" after
the current private game/FMOD/compiled dependency constraints were explained.
This authorizes publishing the current public source through build37 and the CI/release
workflows. It supersedes older no-GitHub-write statements for this scoped task;
it does not authorize publishing the current private IPA or unrelated GitHub writes.

The source, workflows and [release guide](docs/RELEASING.md) are published through
[PR2](https://github.com/hmcneill46/cabrillo-celeste/pull/2), prepared on
`codex/github-releases` for `main`. The initial
[push run](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36128707831)
and [PR run](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36128772553)
both pass at source commit `23b323b4961e4343c3628507f24df6a169ddc578`.
Fresh GitHub-hosted Xcode26.6 compilation passes all 119 native profile checks;
the public inventory audit and all 20 Python build/release controls also pass.
Actionlint validates both workflows. Artifact actions were subsequently updated
to pinned upload7.0.1/download8.0.1 to remove the runner's Node20 warning; see the
PR's final check status for that revision.
Public CI needs no private capsule. Normal branch pushes/PRs run checks;
matching version tags or manual tag runs request a separately gated release.
`release/current.json` explicitly blocks37. A reviewed public build recipe is
still required; no tag, public IPA or38 app has been created for this request.
Attestations will identify workflow/source provenance, not make proprietary
dependencies open source or establish byte-for-byte reproducibility.

All frozen37 implementation inputs and physical acceptance boundaries remain
unchanged. The memory repair and remaining save/lifecycle work below still apply.

## Latest evidence: build37 memory repair and SJ gameplay —25 September

The owner uploaded build37 diagnostics and confirms the app closed/restarted by
itself. Read [the37 phone review](docs/ios-jit/EVEREST_6580_BUILD_37.md#phone-evidence--later25-september)
and ledger before further development. Both initial37 attempts pass JIT, Everest1.6580,
MotionSmoothing1.8.0 and the exact54-archive selection, then end during loading.
One reaches the main menu and starts Old Site. Those initial runs have no gameplay/Quit pass.
Wi-Fi iOS unified logs confirm both were killed by jetsam per-process-limit;
the second process was limited to3376MiB and its last sample reaches3.53GB.
The owner installed the full current SJ dependency set, unlike36's two archives.
Do not attribute this solely to Everest or mark37 accepted. The accepted32 run reached4GB on this phone, and the owner reports SJ alone
also fails now. The installed LiveContainer signature and current profiles omit
Increased Memory Limit, while retained profiles for the earlier identity grant it.
The same LiveContainer3.8.10 release has now been re-signed with that permission
and installed in place over Wi-Fi. Its installed permission is verified and all14
Cabrillo save/settings files remain exact. New iOS logs verify the effective
process ceiling rose from3376MiB to6144MiB. Read
[the memory review](docs/ios-jit/BUILD_37_MEMORY_REVIEW.md) before further action.
The owner now confirms SJ works. A new journal collected over Wi-Fi matches37
exactly and verifies SJ Prologue, Beginner Lobby and NotYourBadeline rooms a_01–03,
501 paired touch inputs and4.05GB peak footprint, with zero runtime errors.
The scoped SJ loading/gameplay regression is resolved. The journal ends during
background/pause, so normal Quit/native return and full save readback remain
unrecorded in this37 run. The independent new iCloud export is not yet present;
preserve it when available, without requesting a repeat of successful SJ gameplay.
No debugger was attached. [The memory setup guide](docs/INCREASED_MEMORY_LIMIT.md)
now documents GetMoreRam, host-versus-standalone selection and re-signing.
All54 exact mod archives are in `.build/phone37-repro-inputs`, with a manifest;
`.build/phone37-crash-repro-a` passes isolated host Old Site runs with both
renderers; it does not reproduce iOS memory termination. Matched cold SJ tests of32
and37 also pass;37 has a slightly lower host peak (3.35GB versus3.46GB). Current
phone save/settings files and signing repair receipts remain private. No Cabrillo38
package exists: the repair changes host signing, not frozen37 implementation.
Preserve37 and the scoped gameplay evidence; remaining lifecycle/save gates stay open.

The same export contains a complete36 base-game/Motion Smoothing run: actual
rooms, four resumes, slot1 readback, stage8 normal Quit and delayed native alive,
with zero runtime failures. Standalone StikDebug works in this tested LC setup.
Most gameplay callback windows are about60 despite a120 request; no sustained120
performance claim is accepted. Read the36 report. The native saves/backup/restore
phone gate remains open. Raw logs stay private. No GitHub write is authorized.

## Latest owner request: Everest stable upgrade —25 September

Build37 (`launcher-everest6580`,0.20.0) updates actual Everest source from1.6531
to stable1.6580 (released19 September), commit082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75.
Read [its report](docs/ios-jit/EVEREST_6580_BUILD_37.md) and ledger for delivery
and current physical evidence before acting. Native archives are all exact36;
four managed assemblies change. The input snapshot is
`.private/everest6580-inputs/manifest.json`; the validated managed receipt is
`.build/everest-managed37-b/receipt.json`. Both are pinned by the37 lane.

All119 profile checks, real gameplay/save-transfer/readback/hair/lava/resume/Quit,
new upstream source behavior controls, Fast/Fancy Motion Smoothing60/120 and the
original vanilla save roundtrip pass. An explicit FNA semantic audit allows only
three new patch attributes and two upstream dialogue resources in temporary
preparation output; the actual shipped FNA binary remains exact. Existing loading
continuations, touch polling and four-method precision repair remain. Tests are
host evidence. Later phone evidence above establishes unexpected37 exits and
a complete scoped36 run; it supersedes the earlier empty-Results observation.

The six-file37 kit is confirmed uploaded to
`iCloud Drive/Celeste JIT Tests/0.20.0-build-37`. It is also installed through
TrollStore on the iPad; its native launch confirms37 and Everest1.6580.0 with the
existing profile/content. The iPad still has no37 gameplay evidence. The requested phone export has
arrived and its failure investigation takes priority; see the latest section. Package and all220 captured
implementation inputs are frozen in `artifacts/cabrillo-build37-final`.

Newly reviewed retained34 history in a35 export includes successful gameplay,
save/Quit and zero runtime errors. It does not show native backup/restore or
per-slot transfer actions, so the combined saves gate remains open. Use the latest
kit guide; do not ask for already-passed native/browser/gameplay suites again.
Next unused identity is38. All packaged lanes remain frozen. No new GitHub write
is authorized. The full touch editor follows the outstanding save/recovery gate.

## Earlier failure and correction —25 September

The owner uploaded two build35 phone exports after Motion Smoothing would not
start, at120Hz and60Hz. Both pass JIT then throw MethodAccessException from the
generated Engine.Update before frame1. The owner reports120Hz starts with the
mod disabled. The iOS15 runtime rebuild omitted the previously accepted Mono
class.c visibility patch; the Mac host archive still had it.

Build36 (`launcher-visibility`,0.19.1) restores the exact accepted patch in one
Mono archive member. The other259 objects, fifteen archives and all201 managed
assemblies remain35-identical. The broken-source host control reproduces the
same exception at60/120; restored-source Fast/Fancy60/120 gameplay/save/Quit and
72 field/method grant/denied cases pass. All nine accepted Mono source patches
were audited. Read [the build36 report](docs/ios-jit/VISIBILITY_BUILD_36.md) for
delivery and current physical evidence. Build35 and its Results stay frozen.
The owner reports36 launches and plays normally; its complete retained session
in the37 export now verifies that scoped runtime gate. Build37 is now the requested stable Everest1.6580 upgrade lane. Read
its report before acting; next unused is38. No new GitHub publication is authorized.

## Earlier owner-prioritized work —25 September

**Build35 is delivered; the iPad base-game gate passes.** The owner prioritized
[issue1](https://github.com/hmcneill46/cabrillo-celeste/issues/1), older iOS/JIT
routes and Motion Smoothing over the planned touch editor. Read
[the build35 report](docs/ios-jit/PLATFORMS_BUILD_35.md) and its ledger first.

`launcher-platforms-20260925-35`,0.19.0, targets iOS15. It is installed over USB
through TrollStore on the owner's iPad mini4/iOS15.8.8 with Dopamine active.
The owner played and confirmed correct visuals/audio and normal Quit. Logs pass
26 native checks, catalogue zero-active quiescence, verified original content,
first-frame reveal on callback1, real gameplay/touch, brief resign/foreground, save
readback, shutdown stage8 and a delayed native heartbeat. No JIT/unowned/managed
errors or patch rejections. This is scoped iPad base-game acceptance; retain32
as the accepted **phone** fallback. The game ZIP was transferred over USB and
hash verified; it is already imported on the iPad. Raw device data stays private.

Build35 preserves34's backup/transfer and numerical fixes. It rebuilds seven
native archives for15 from a separate explicit source import; nine stay exact.
Only CelesteJITEverest.dll changes among201 assemblies, moving touch polling to
actual input updates. The 120FPS host test found lost tap edges with the old
adapter; the fix passes Fast/Fancy60/120 gameplay, touch, save/resume/Quit. Native
high refresh is optional and capped to the screen; actual phone120Hz, performance
and new JIT routes are still pending. The original mod remains optional/unbundled.

All six files are confirmed uploaded to `Celeste JIT Tests/0.19.0-build-35`.
Phone download/execution is unconfirmed. Use35's combined guide for the outstanding
34 saves/precision gate plus route and optional Motion Smoothing checks;33/34
Results remain empty. Do not request the already-passed28/32 suites again.

The final package is `artifacts/cabrillo-build35-final`; exact IPA/dSYM/pins and
receipts are in the report. The derived managed receipt is
`.build/platform-managed35-b/receipt.json` (SHA256
`e03d75eb1377a81a71d596c7e47567b431e2c67103eb2af1346f5bc315943fcc`), over the exact
34 repair. Native receipt:`.build/platform-native35-c/receipt.json`, pinned in
NativePayload.json. Preserve the explicit `.private/platform-inputs35` source
capsule and all provenance. An earlier packaging attempt stopped before IPA
creation; only the final35 was delivered. All35 implementation inputs are frozen.
Build36 carries the correction described above;37 is also packaged and the next unused is38. No new commit/push or GitHub comment was authorized.

Next: review35 Results when they arrive, fix evidenced problems first, and then
resume the full touch editor after the outstanding save/recovery gate. Do not
replace the scoped device evidence with host tests or assume every iOS15 or
jailbreak combination works. SSH was used over USB for this owner's installation
and logs; credentials/pairing/host keys stay out of Git and public reports.

## 1. Where to start right now

**Build28 is physically accepted. The browser gate is closed.** The owner
reports all supplied tests visually passed. One complete diagnostics export was
collected from its Results folder at **2026-09-15 07:56:36 UTC**. It contains the
final browser/install/gameplay process and three earlier build28 sessions;
review confirms fresh Cateline installation, reviewed Memorial enabling,
multi-file dismissal, offline behavior, zero-active catalogue quiescence,
26 native/19 graphics checks, exact runtime/modules, saves and complete normal
Quit/native return with a delayed heartbeat. Read
[the acceptance report](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md) and
[ledger](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE_EVIDENCE.json).
No repeat export or successful test is required. The earlier empty-folder check
at14 September23:17:24 UTC is superseded by this evidence.

**Build31 has now been tested on the phone.** One export contains two complete
build31 runs and two older build28 sessions. Both31 runs pass exact runtime/mod
selection, zero-active catalogue quiescence, gameplay/save/Quit and native
heartbeat; one includes12.98s gameplay background/resume. See the
[phone review](docs/ios-jit/BUILD_31_LOADING_REVIEW.md) and its ledger. The owner
reports choppy loading-detail interaction and audible game activity before reveal.
Logs confirm native main-thread steps up to17.29s and a17.7s wait from first game
frame to native window handoff. Preserve31 evidence and sources.

**Build32 is physically accepted.** Read the
[acceptance review](docs/ios-jit/BUILD_32_ACCEPTANCE.md) and its ledger. One export
contains three first-frame handoffs, all on callback1 approximately1.3ms after its
return marker, and a complete SJ room/save/normal Quit/native heartbeat run.
Two older sessions end after background/pause without a Quit record; no new failure
is established. The owner approved the result and requested the next feature.

Build32 is now the accepted fallback,0.16.2 / `launcher-first-frame-20260915-32`.
Preserve28/27/31 and every Results folder. Build29 and30 remain local historical
preparation/intermediate builds. All packaged source lanes remain frozen.
Build34 now combines **individual desktop save transfers, whole-profile backups
and hair/seeker/tutorial/lava numerical repairs**. It is packaged as0.18.0 and
locally validated. The owner explicitly deferred33 testing until these additions
were ready;33 remains preserved and unaccepted. Read the34 report and Results
before requesting tests. Builds35–37 are now delivered; the current next unused identity is38.
The full touch editor follows the combined34 phone gate. All packaged lanes are frozen.

The owner explicitly authorized committing/pushing the completed loading work to
GitHub on15 September2026. That publication is complete: commit
`16ff42ca62438ccfa1c3ea14e76a6606da1bc820` was fast-forward pushed and verified on
`origin/main` on15 September. The next-feature work used `codex/profile-backups`;
the newer CI/source publication is recorded at the top of this handoff. This earlier approval covered completed work through build32 and its acceptance;
future unrelated feature publication still needs owner authorization.

## Build34 combined phone gate —17 September

The fresh `launcher-save-transfers` lane is0.18.0 /
`launcher-save-transfers-20260917-34`. Read
[the report](docs/ios-jit/SAVE_TRANSFERS_BUILD_34.md) and its evidence ledger.
The unsigned IPA is24,056,162 bytes, SHA-256
`02440e406dd9e940465684e9ac32824966303d0067e0dbe650fac73891f786e7`.
Executable/dSYM UUID: `FD136517-5EE7-3169-B275-3CE4BB0011F0`.

Slots1–3 always appear; existing extras are preserved. Long press or ellipsis offers
ZIP/main-file export, replacement review, duplication and details. Import another
save chooses an unused index. Raw vanilla imports can retain mod files; complete
ZIPs replace the target's standard files. All replacements share the durable
whole-profile journal and retained rollback. Do not weaken fresh-process gates.

The hair fault reproduced on actual Mono8 gameplay. An overbroad historical patch
mixed float/double arithmetic in hair, PlayerSeeker and the bird tutorial. Repair
restores ten original float sites while preserving ten deliberate double sites.
The related lava repair restores40 surface bubbles in the fixture, previously4.
Only four Celeste method bodies change;17,300 are unchanged. The bounded expression
audit finds no remaining recognized mismatches, not proof of all game correctness.
Only Celeste.dll changes among201 managed assemblies relative32/33; all16 native
archives match. The exact derived receipt is
`.build/precision-managed34-final/receipt.json`, SHA-256
`80bb0a19d7f63944aa6fe23379338c747db776cae51744c73482a390425b13aa`.
Keep its base receipt and repair provenance; never silently substitute32's payload.

119 native checks,16 simulator UI tests, six precision controls, eight package
negative controls and final package/symbol verification pass. Real game tests use
the exact shipped managed payload. Original Celeste1.4.0.0 serialization also passes
a native→vanilla→native→Everest roundtrip; this is not every-version compatibility.

All six kit files are confirmed uploaded to
`iCloud Drive/Celeste JIT Tests/0.18.0-build-34`, with matching local hashes.
Delivery receipt: `artifacts/cabrillo-build34/delivery.json`. Check its Results
before asking for testing. Follow its combined README-FIRST guide instead of a
separate33 suite. Phone34 download/execution and acceptance remain unconfirmed.
The whole cloud folder is794,488,191 bytes; every prior build/Results is retained.
No33/34 GitHub publication is authorized. New implementation now needs36; see the25 September section.

## Preserved build33 —15 September

The new `launcher-backups` lane is0.17.0 / `launcher-backups-20260915-33`.
Read [the report](docs/ios-jit/PROFILE_BACKUPS_BUILD_33.md) and its evidence ledger.
The unsigned IPA is24,000,196 bytes, SHA-256
`a66a44bd1e477fadb4df8d9127912fca2412babf87b3d3603b9f67461f5de79d`.
Executable/dSYM UUID: `B0843965-0FC8-3020-B7D3-3E5421C8FE13`.

Whole-profile backup, Files review/import/export, staged exact restore and retained
rollback are implemented.59 fresh native checks,10 iPhone/iPad UI checks, six
negative package controls, final arm64 package/symbol checks and a cloned real
profile followed by game load/save/Quit pass. All201 managed assemblies match32.
The user's extra-save-slot request is covered by dynamic slot discovery and
preservation of all files, including mod-only sidecars (350 sparse slots tested).

The six-file kit is confirmed uploaded to `iCloud Drive/Celeste JIT Tests/0.17.0-build-33`.
The delivery receipt is `artifacts/cabrillo-build33/delivery.json`; check
`Results` for newly arrived evidence. All prior builds/Results are retained.
The owner subsequently deferred this test; build34 now supplies the combined gate.
No phone33 acceptance is claimed. Build32 is the fallback. Do not repeat the
closed build28 browser or build32 loading gates without new failure evidence.

Profile recovery must precede mod scans/startup. Keep exact archive identities,
disabled choices, unknown persistent files, retained rollback, fresh-process
requirements and the first-frame handoff. The current portable format requires
the same installed archive set. Build34 adds per-slot formats; missing-mod automation
and the full touch editor remain future work. Public release permission remains separate from local phone delivery.

Start in this order:

1. Read this file and `AGENTS.md`, inspect Git status/HEAD and preserve newer work.
2. Build32's export is reviewed. Do not request a duplicate loading/browser suite.
3. Put newly evidenced backend failures ahead of features. Build36 fixes the
   evidenced35 Motion Smoothing failure;37 adds the requested Everest upgrade.
4. Check the latest36/37 Results and owner replies first, plus earlier Results
   if new evidence arrives. Review the focused37 upgrade and outstanding combined
   saves/backup/restore/hair/gameplay/rollback gate against its exact identity.
   While waiting, independently prepare touch-editor contracts. All packaged
   lanes remain frozen; owner36 visual acceptance does not accept37.
5. Preserve module identities, game-thread ownership, first-frame handoff and
   zero-active catalogue quiescence. The full native touch editor follows backups.
6. The owner authorized the current loading publication and local next-feature
   development. Check the publication record before another GitHub write.


The owner wants development carried forward autonomously, with concrete tests
and inspectable logs when device help is needed. They dislike unnecessary
confirmation questions. Ask only for missing information that actually changes
the work, or for a specific test/approval that is required. Do not stop at a plan
when implementation is authorized and feasible.

## 2. Project, Git and boundaries

| Item | Current value |
| --- | --- |
| Product | **Cabrillo — Celeste Mod Loader for Apple Platforms** |
| Active repository | `/Users/harrymcneill/Projects/Cabrillo` |
| Public GitHub repository | <https://github.com/hmcneill46/cabrillo-celeste> |
| Default branch / remote | `main` / `origin`, tracking `origin/main` |
| Initial published commit | `bbd86a7680c0a3938fa9715ca27d1dd2e61ce96b` |
| Separate AOT sibling | **Morro**, currently <https://github.com/hmcneill46/celeste-ios> |
| Primary physical target | iPhone 15 Pro Max (`iPhone16,2`), iOS 26.5 |
| Additional physical target | iPad mini4/iOS15.8.8: scoped build35 base-game acceptance;37 native launch confirmed |

The owner explicitly authorized the initial commit/push and selected **Public**.
The initial publication is complete. On15 September the owner separately authorized
committing/pushing the completed loading work through build32 and its acceptance.
Continue local next-feature work; future unrelated publication needs authorization. Use `codex/` for
future development branches. Do not rewrite history or force-push.

Keep these directories read-only:

- `/Users/harrymcneill/Projects/Celeste-Everest-JIT-Apple-Platforms` —legacy JIT
  development/archive. Read or copy needed evidence/inputs; never build into,
  switch branches in, clean, reset or edit it.
- `/Users/harrymcneill/Projects/celeste-ios` —actively developed AOT/Morro project.
  Reading its controls/platform work is useful; writes or writable dependencies
  would conflict with ongoing AOT development.
- `/Users/harrymcneill/Projects/Celeste Required Files` —owner's original game and
  SDK inputs. Preserve originals; use new private copies when needed.

`.private`, `.build`, `artifacts`, signing data, device logs and IPAs are ignored.
Never add game binaries/decompiled game source/assets, FMOD SDK contents, pairing
material or private raw logs to the public repository. Keep third-party licenses
and provenance. The public source repository is **not** permission to publish
the current private test IPA: original-IL preparation and FMOD redistribution
remain release gates. No FMOD permission has been established here.

## 3. Current implementation and exact identities

**Build32 is the current physically accepted fallback; preserve28/27/31 too.**
Both use real Everest 1.6531.0; the game and mods run under
Mono 8 JIT. Do not substitute the trimmed AOT game as the dynamic hook target.
The Swift/Objective-C native host remains compiled native code.

| Build 28 item | Expected identity |
| --- | --- |
| Version / build ID | `0.15.0 (28)` / `launcher-catalogue-20260913-28` |
| Immutable source lane | `experiments/ios-jit/launcher-catalogue` |
| Unsigned IPA | `artifacts/cabrillo-build28/CelesteJITEverest-unsigned.ipa` |
| IPA size |23,812,187 bytes |
| IPA SHA256 |`87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2` |
| Executable/dSYM UUID |`98537CA1-09CE-344B-B370-5C27D8F83DC2` |
| Everest source |`d72e94f4b9e62b91cbdea674587ed39d53de9550` |
| Actual version string |`1.6531.0-cjit-d72e94f` |
| RuntimeIdentity SHA256 |`67b284331a08bd3eefb4e3ec5f09ca3b20b9000a4b40f13a0e2e1aa373e63f62` |
| Managed adapter SHA256 |`65b8dca51055627ad8a7da5fb59add7166cf9a39e435b7ac211d9c2df7a4f378` |
| JIT protocol | 1; two 268,435,456-byte arenas; mailbox 96 bytes; response offset 48; error offset 88 |
| Bundled support |`CelesteIOS`1.0.0, ABI 1, required and not user-disableable |
| Content/profile paths |`GameLibrary` and `Profiles/sj-first-play` in the guest's Documents area |

The historical profile name is storage compatibility, not product branding.
Do not rename it or require reimports during UI work. The owner's game, mods,
saves/settings and unknown sidecars should survive app updates.

Build 28 adds native Mods → Browse alongside Installed and Updates: five genuine
server sorts, categories/subcategories, name search, screenshots/details, and
explicit individual file selection. It uses the existing reviewed dependency
installer/reports. The 201 managed assemblies and the native runtime/renderer
are identical to accepted 27. Build 28 does not implement responsive mod-loading
startup, whole-profile backup UI or the full touch layout editor yet.

Key records:

- [Build28 phone acceptance](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md) and
  [physical evidence ledger](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE_EVIDENCE.json).
- [Build 28 browser report](docs/ios-jit/NATIVE_CATALOGUE_BUILD_28.md) and
  [evidence ledger](docs/ios-jit/NATIVE_CATALOGUE_BUILD_28_EVIDENCE.json).
- [Build 27 phone acceptance](docs/ios-jit/BUILD_27_RUNTIME_ACCEPTANCE.md).
- [Migration report](docs/CABRILLO_MIGRATION.md),
  [migration evidence](docs/CABRILLO_MIGRATION_EVIDENCE.json), and
  [build guide](docs/BUILDING.md).

Older reports and source strings can say “build 23 Results”, “SJ lobby”, no remote,
or no GitHub authorization. Those are historical/debug paths, not instructions
for current normal UI testing. Follow this handoff, the current root instructions
and build 28 phone guide. Preserve delivered 28 bytes; correct display text in a
new version instead of editing the accepted/reproduction target in place.

## 4. Build28 evidence location and collection

Phone Files location:

```text
iCloud Drive → Celeste JIT Tests → 0.15.0-build-28 → Results
```

Exact Mac location:

```text
/Users/harrymcneill/Library/Mobile Documents/com~apple~CloudDocs/Celeste JIT Tests/0.15.0-build-28/Results
```

The parent kit already contains seven files: the unsigned IPA, `README-FIRST.txt`,
`INSTALL.md`, `TEST-IDENTITY.json`, `SHA256SUMS.txt`, third-party notices, and
`celeste-jit-probe-TEMPLATE.js`. Their original upload was confirmed 13 September;
build28 phone execution is now verified by the15 September review. The export
does not measure how the owner downloaded the IPA. Source copies of the
instructions are [PHONE_README.txt](experiments/ios-jit/launcher-catalogue/PHONE_README.txt)
and [INSTALL.md](experiments/ios-jit/launcher-catalogue/INSTALL.md).

Before analysis, copy only relevant new Results files into a new ignored folder,
for example `.private/device-evidence/2026-09-15/build28-review/`. Do not overwrite
old evidence. Hash original and copied bytes, record source path, size, collection
time and SHA256. Require a complete local read and successful JSON parse; a
placeholder, zero-byte file or failed iCloud hydration is not missing/failed
phone execution. Do not clean cloud Results or edit exported files.

The reviewed export is5,370,692 bytes, SHA256
`a07d20eff0f1a9236f7cf42ae6a876b5856e2bd2ce02e20c449271f7945931e9`.
Its unchanged private copy, collection receipt and analysis are in
`.private/device-evidence/2026-09-15/build28-review-075636/`.
The original Results file is preserved. New exports must be collected separately.

Expected exports are `CelesteJIT-<launch UUID>.diagnostics.json`, sometimes with
Files-app numeric suffixes. The **contents identify the session**, not the suffix
or the containing build folder. Separate browser/install and post-Quit exports
are useful for future tests, but build28's single export retained both and is
sufficient. Multiple exports may overlap or represent two snapshots of the same
process. A recovery launch may export an earlier played/crashed process inside
`previous_sessions`; examine that history before asking for another test.

If Results is empty, do not request a reinstall or create another identical IPA.
The existing kit is ready. If the owner needs the steps again, use section 5 and
the supplied phone guide. No new standalone JIT script is required for28.

## 5. Physical test contract

**Installation/run arrangement is fixed:** game in LiveContainer slot1, StikDebug
in LiveContainer slot2. Update the existing game entry while preserving data.
Keep **Launch with JIT OFF**, its saved JIT script blank, and **Fix File Picker ON**.
The latter fixed a real case where a locally downloaded ZIP could not be selected.
Close the previous game process and open28; do not delete/recreate the data container.
Capture actual LiveContainer/StikDebug versions when supplied; do not infer them.

| Area | Requested phone observation and corresponding evidence |
| --- | --- |
| Native browse, without JIT | Scroll/load another page, try Newest/Most downloaded/Most liked, Maps → Standalone, and portrait/landscape. Cards, menus, images and text should fit and respond. Use owner feedback/screenshots for visual facts; diagnostics cannot prove every alignment. |
| Exact reuse | Search Memorial Helper, including its valid Tools-category page. Review an existing exact file without downloading a duplicate. A disabled exact match should present enabling for review. Do not enable/replace unreviewed files. |
| Small install/report | Search Cateline; original 0.1.0 is about 17 KB. If absent, review/download/install and verify the actual installed/enabled report. If already installed, the supplied guide explicitly expects reuse. Record which path really occurred; reuse is not fresh-download evidence. |
| Multiple files | Open a multi-file page such as SpringCollab2020, inspect separate map/audio/extra choices and their sizes, select explicitly and review. Dismissing review must not install anything. No large download is required for this check. |
| Offline, optional | Previously visited data remains with an honest offline state; unvisited search offers Retry. Installed-profile play is independent of catalogue availability. This was optional in the delivered guide; do not invent a compulsory replay if omitted. |
| Fresh JIT | Enable via LiveContainer2 with this running process's inline PID-specific request. StikDebug completes and detaches; return to the same process and pass native memory/execution checks. |
| Play after browsing | Run the existing profile, enter an ordinary map, check controls/audio/progression/saves. Verify Cateline's appearance if enabled. The new browser must be quiescent before managed preparation. |
| Quit/export | In-map Save and Quit returns to the game menu; normal main-menu Quit returns to SwiftUI. Export after native return, ideally after five seconds so the delayed heartbeat is present. A separate browser/install snapshot is useful; the reviewed single28 export already retains both. |

Check actual mod registration and committed transactions, not just a UI “PASS”.
Do not require a specific collaboration or exactly56 module identities: the
owner can change the mod set, and module callbacks can be duplicated. A genuine
new small install is useful if both documented examples were already installed,
but do not delete working mods to force it. Mark that route NOT OBSERVED and ask
for a targeted additional install only if necessary to close the intended gate.

Build 28's guide does not require a fresh second gameplay run or a new 30-second
background test. Report either if present; carry accepted 27's separate coverage
if not. Do not silently enlarge the requested test. A new launch can itself
prove preservation of an earlier save when slot/profile evidence matches.
The current28 session saves slot0 with sidecar194→209→209; its later fresh-process
209 reload is unobserved. An earlier28 session saves slot3 with0→178→178. The old27
latest980 reload is also unobserved and must not be imposed on different slots or
mod selections. Compare actual exports and owner changes before expecting a counter.

**One game per process remains intentional.** After Quit, relaunch before another
game or mod configuration session and obtain fresh JIT. Do not reuse an old
PID/address script. The normal product has no permanent Finish button; old debug
controls and the game main-menu Quit are different paths.

## 6. How to analyze the diagnostics correctly

The authoritative format is implemented in
`experiments/ios-jit/launcher-catalogue/src/main.m` (`CJLog.exportDiagnostics`)
and `src/CJEventStore.m`. Export schema2 has:

- `kind: celeste-jit-launcher-diagnostics`, top-level `session`, `build`, `device`;
- `current_events`, `retention`, `native_console_tail`, `mod_installations`;
- up to three `previous_sessions`, each with `events`, journal metadata, its
  console tail, and sometimes `previous_journal_part.events`;
- owner-entered debugger/container versions, which can legitimately be absent.

Each ordinary event has `event`, `session`, `sequence`, `time_unix`,
`uptime_seconds` and `fields`. For each process, obtain identity from its own
`native_launch.fields.build/device/process`; the top-level export identifies
only the current exporting process. Never label older failures as build 28 merely
because they appear in a build 28 export.

A browser-only process legitimately has no JIT/game checks. Apply the game gates
to a process that actually attempted gameplay, and retain the native-only result
as its own valid part of the review.

Review procedure:

1. Enumerate every process across every export and previous journal part. Group
   by session UUID, associate launch build/device/PID, and deduplicate repeated
   snapshots by sequence plus matching event content. Synthetic counter records
   may have no sequence; preserve their timestamp/fields and provenance. If two
   records conflict, retain both and investigate instead of dropping one.
2. Match build 28's identity to section 3 and `TEST-IDENTITY.json`. Read actual
   `runtime_identity_pass`, `everest_selection_pass`,
   `everest_selection_module_verified` and `everest_module_registered` messages.
   `BuildInfo` alone does not prove that the expected managed runtime executed.
   Frozen28 maps `runtime_identity_pass` through `CJGraphicsMark` to
   `graphics_fixture_message`; the full version/source/manifest message is still
   retained. Account for that mapping rather than requiring the original name.
   `mono_reflection_flags_registered` must report ABI 1. Map identities by exact
   module name/version; distinguish archive count from callback count.
3. Review `mod_installations` and persisted reports/journals against the before/
   after enabled library and actual next-game registration. Successful commits,
   verified cached ZIPs, failures, cancellation, unattempted and enable-only work
   are different results. `applicationState: applied` and actual `changes` prove
   applied changes; downloaded bytes alone do not. `inProgress` read back after
   interruption must not become success. Sources: `native/InstallReport.swift`,
   `InstallJournal.swift`, `DependencyInstaller.swift` and `ModLibrary.swift`.
4. Require `catalogue_quiesced` **before** `graphics_test_start`/managed preparation,
   with zero active catalogue requests. The provider must be suspended, with
   rows/images cleared and no new request launched during the game. Its payload
   is the provider diagnostics dictionary from `prepareForGameWithCompletion`.
   In delivered28 it has top-level `activeRequests`/`suspendedForGame` and nested
   `counts`/`lastFailure`. Inspect the actual schema for later versions.
5. Check native `check_pass`/`check_fail`, JIT protocol/arena mapping and debugger
   detachment. Accepted 27 recorded 26 native checks, two 256 MiB regions with 16,384
   RX pages each and no debugger attached during generated code execution.
   Check individual names/results; absence in a clipped excerpt is not a PASS.
6. Require successful `graphics_start_result`, `graphics_first_frame_returned`,
   actual game/map activity, correct expected registrations and successful
   graphics/readback checks. The prior accepted game suite had 19 graphics checks;
   interpret the names and active profile rather than hard-coding all mod counts.
   Read the logged map SID/room, not an assumption from the test's title.
7. Inspect sampled and final runtime counters: `jit_failed`, `jit_unowned`,
   `managed_errors`, `patch_rejections` should remain zero. Examine explicit
   `mono_jit_failed`, managed exception/details, game error and loader events
   even if later UI looks successful. A caught Everest exception can still expose
   a real runtime failure. Record code reservation/budget and process footprint.
8. Verify saves/sidecars using `game_save_pass`, `everest_mod_save_pass`, shutdown
   records and later-load evidence where present. Same-process readback is not
   fresh-process persistence. The prior 27 route was SJ
   `StrawberryJam2021/1-Beginner/Ceph` (Cassette Cliffs), room4→room5, then a
   fresh room5 reload; counters928→969→980. It was not a Spring/Paint phone run.
9. Verify **all eight shutdown stages** and native return:
   `graphics_bridge_pass` with `shutdown_stage: 8`, successful main-thread detach,
   `graphics_result_presented.passed: true`, and ideally `graphics_post_run_alive`
   emitted five seconds later. Check quit reason/origin. `game_checks_pass` alone
   does not establish a completed native return. A snapshot exported before the
   delayed event is missing that observation, not proof of a hang.
10. Review retention/error fields. The console export is a bounded tail; journal
    excerpts may be clipped; routine events are sampled with counters. Do not
    interpret sequence gaps as dropped execution or count just retained samples
    as the total JIT work. `storage_error`, clipping, partial JSONL tails and
    overflow limit what can be concluded.

Current allocation evidence is `retention.allocation_trace`: base64 of 24-byte
little-endian `<QQQ>` rows `(address, requested_bytes, total_reserved_bytes)`.
Verify decoded length, SHA256, record count and `overflow_records`; use the exact
session's prepared arena/allocation data for coverage claims. Earlier-session
exports do not automatically contain that complete trace. On disk it is
`session-<UUID>.jsonl.allocations.bin`; raw rotated journals may also have
`.previouspart`. Do not claim complete allocation proof from a bounded excerpt.

Shutdown stage names, in order: Finishing pending saves; Verifying saved data;
Ending the game loop; Releasing textures; Closing game and mod hooks; Closing
platform services; Removing host hooks; Complete. `Stop` 3 keeps draining pending
saves, 4 yields, 1/2 represent complete/incomplete. The independent shutdown
heartbeat observes state; it never kills the process. There is no intentional
gameplay timeout. Do not add one to mask a hang.

Record each gate as PASS, FAIL or NOT OBSERVED, with session IDs, event evidence
and limitations. Keep raw data private. Publishable summaries may reference
hashes and sanitized observations, not raw personal/device logs. Write a new
`docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md` plus an evidence ledger **only when
the evidence warrants it**, then update current `AGENTS.md`, this handoff and
the roadmap. Keep original delivery/migration receipts as dated history. If a
gate is incomplete, ask only for the specific missing observation/log.

### Crashes, hangs and direct collection

On a crash, have the owner reopen and export before another game so the failed
process is retained in history. A native crash/Jetsam report or fuller console
may be needed to distinguish a native fault, memory termination, loader failure
or incomplete shutdown; do not diagnose a leak from a high footprint alone.
Use exact matching UUID symbols in `artifacts/cabrillo-build28/`.

The owner authorizes relevant USB collection and useful debugger attachment.
**Never attach concurrently with StikDebug.** Default handoff/return is iCloud;
do not assume the phone is currently connected. If USB is available, identify
the owner's `iPhone16,2`, the actual signed LiveContainer1 bundle and current
guest data UUID; another connected phone or stale UUID is not the target.

[The scoped collector](experiments/ios-jit/device-tools/pull_diagnostics.py) and
[its guide](experiments/ios-jit/device-tools/README.md) describe House Arrest
`VendDocuments`/AFC using `pymobiledevice3==11.12.4`. Set up its environment and
private pairing/inventory inside Cabrillo; the guide's old environment paths
were not imported as runnable dependencies. It reads only the selected guest's
Diagnostics folder, performs stable repeated reads, preserves a partial final
line and does not write to/launch the phone. Its default chooses the latest
process, which can be merely the recovery/export process: choose `--session`
explicitly when appropriate. It collects JSONL and console, not every rotated
part/allocation file; retrieve any additional needed artifact explicitly within
the same authorized scope. Preserve **Export diagnostics** permanently.

## 7. Building in Cabrillo

Use **Xcode 26.6 / build 17F113** at
`/Applications/Xcode-26.6.app/Contents/Developer`, with iPhoneOS SDK 26.5.
Migration was compiled on an Intel Mac. The current app targets arm64/iOS 26.0
minimum and declares iPhone+iPad; SDK declarations are not device acceptance.
Use the developer path per command rather than changing the owner's global
Xcode selection. Root tools use Python3's standard library.

The local folder contains everything needed for the **current launcher rebuild**:

- Public source/docs/vendor files, including the current lane, previous JIT
  patches/tests and the small shared control/artwork subset. No AOT app/project.
- `.private/migration/build28-replay.json` and `inputs.json`: exact dependency,
  package, source and provenance locks; 455 build inputs, 98,059,597 bytes.
- `.private/inputs`: 16 accepted native archives and matching Mono/SDL headers.
- `.private/resources/build28`: 201 managed assemblies plus frozen resources.
- `.private/test-inputs`: 11 dated-service/synthetic-ZIP fixtures, 308,734 bytes.

A GitHub clone does **not** have these private inputs. Do not pretend missing game
IL/FMOD can be downloaded from the public repository. Back up `.private` separately.
The one-time `tools/import_legacy.py` is not a normal build step and must not
overwrite this working project.

From the Cabrillo root, using new work/output names:

```sh
python3 tools/audit_repository.py
python3 tools/build.py --reproduce-build28 \
  --work .build/another-reproduction \
  --output artifacts/another-reproduction
python3 tools/verify_reproduction.py artifacts/another-reproduction
python3 tools/check_catalogue.py --output .build/another-catalogue-check
```

Do not rerun expensive passing checks merely to reread this handoff. The verified
reproduction already exists in `artifacts/cabrillo-build28/`, with receipts/logs
and matching dSYM. It compiled 58 source inputs, generated tables/icons, and
produced the **exact full build 28 IPA hash**, while macOS denied access to all
three legacy/AOT/original-input directories. All 48 default native catalogue/
transaction tests passed from fresh local source and vendor compilation.
`--live` adds ten service/real-install checks but was not repeated during migration;
the original build 28 suite had 58 checks and separate host/simulator gates.

**Important: `tools/build.py` is a locked build 28 reproduction recipe, not a
generic new-release builder.** It requires the exact historical source and
reuses accepted runtime/managed libraries. It retains original ZIP/resource
metadata and permits bounded relinking for the observed Apple linker GOT-order
variation. Only after every non-UUID executable byte matches the locked hash
does it restore 16 historical UUID bytes and synchronize the fresh dSYM. The
full executable and IPA must then match. A changed code byte is rejected.
Actual new compilation provenance is stored outside the historical BuildInfo.
See [BUILDING.md](docs/BUILDING.md); do not use that UUID/metadata restoration for
changed code or claim all Mono/SDK/managed dependencies were rebuilt from upstream.

### Current independent build lanes

- **29:** `launcher-startup`,0.15.1; local preparation only. Its builder/verifier
  and all recorded artifacts remain frozen. It reuses all201 managed DLLs.
- **30:** `launcher-loading`,0.16.0; frozen local loading intermediate. Managed
  source, SDK/upstream pins and `tools/build_loading_managed.py` live here. The
  validated managed receipt is `.build/loading-managed30-d/receipt.json`.
- **31:** `launcher-loading-release`,0.16.1; corrected native delivery lane.
  `ManagedPayload.json` pins that exact managed receipt/resources. Build with
  `tools/build_loading_release.py`; verify with `tools/verify_loading_release.py`.
  See the report/ledger at the top for final package, delivery and phone state.

The managed capsule is `.private/loading-inputs`:19,618 files/2,413,428,206 bytes,
including the source/submodule pins, offline packages, SDK8.0.422/9.0.300,
private original/prepared IL and host inputs. The build runs only in new Cabrillo
stages, with the old checkouts inaccessible. Extra real-game test fixtures are
separately pinned in `.private/loading-host-inputs` and `.private/loading-sj-inputs`.
They are not public source files or dependencies writable by a build.

The next unused number is **32**; recheck owner messages/current files before
allocating it. New implementation requires a new identity and work/output stages.
Use the current independent root tools, preserve all frozen31/30/29/28 inputs,
and keep the existing guest bundle/data paths. Historical experiment builders
can be read for context; they are not guaranteed runnable current entry points.
Never make either old checkout a writable dependency.

## 8. Architecture and regression boundaries

Current native source is `launcher-loading-release`; managed/loading source is
`launcher-loading`. The accepted28 source below is the preserved reference, not
the place for implementation edits.

| Responsibility | Source to inspect |
| --- | --- |
| Native app/lifecycle/JIT/session handoff | `launcher-catalogue/src/main.m`, `CJGraphicsManaged.m`, `CJGraphicsPlatform.m`, `CJSession.*` |
| SwiftUI launcher/browser | `native/LauncherUI.swift`, `CatalogueUI.swift` |
| Catalogue contracts/network/cache | `CatalogueModels.swift`, `CatalogueProvider.swift` |
| ZIP library and dependency transactions | `ModLibrary.swift`, `DependencyPlan.swift`, `DependencyInstaller.swift`, `InstallJournal.swift`, `InstallReport.swift`, `ModUpdates.swift` |
| Managed game/boot/frame/storage | `managed/GameEntry.cs`, `Platform.cs`, `ContentLibrary.cs`, `ContentStore.cs`, `ModSelection.cs` |
| Game-side iOS integration | `support-module/IOSPlatformModule.cs`, `InputSourcePolicy.cs` |
| Native code mappings/protocol | `CJHookCodeArena.c`, `CJHookProtocol.h`, `VMRange*`, `scripts/celeste-jit-probe.js` |
| Runtime identity/pins | `RuntimeIdentity.json`, generated native/managed identity files, `CompatibilityDownloads.json`, `RuntimeCompatibleReleases.json` |

Paths in this table are under `experiments/ios-jit/launcher-catalogue/`.
These are reference inputs for a new lane, not permission to mutate frozen 28.

Preserve these established contracts:

- Native host owns JIT, files, network, lifecycle and presentation. The required
  support module owns game-side Quit and input prompts; bootstrap must work
  before user mods/support registration. Do not import .NET10 Apple bindings
  or trimmed AOT game assemblies into this Mono 8 host.
- Keep accepted Mono allocation/memory fixes, MonoMod literal-field handling,
  build 24 FNA/Metal retained-backbuffer/MSAA/bounds fixes, and build 26 CoreLib
  reflection ABI 1 correction. Their changes solved actual phone/host failures;
  reverting them can revive seemingly unrelated mod errors.
- Build 27 rebuilt actual Everest 1.6531.0 and patched game/hooks. Do not implement
  another runtime upgrade by editing version strings. Verify actual registration.
- Exact YAML module names, file IDs and verified archive metadata govern installs.
  A GameBanana title/category is not a module identity. Memorial Helper is a
  valid indexed mod on a Tools page. Multi-file pages require an explicit choice.
- Three compatibility-pinned releases are GravityHelper 1.2.28, CollabUtils2
  1.13.4 and FemtoHelper 1.15.22. They differ from optional older runtime-compatible
  alternatives in `RuntimeCompatibleReleases.json`. Preserve compatible locals;
  never relax a minimum version. ExtendedVariantMode 0.51.0/MaxHelpingHand 1.40.10
  are supported by runtime 27/28; blocking in older 26 was correct then.
- Updates retain the prior ZIP disabled and preserve an updated mod's disabled
  choice. Dependency resolution can enable a reviewed existing match. Recover
  journals before scans/play; never overwrite unknown changed files/state.
  Reports must describe committed old/new versions and actual enabled changes.
- Update checks are explicit plus optional idle Updates-page checks after 24 h,
  with 1 h automatic failure backoff. Cache eligibility binds actual runtime/pins
  and is re-evaluated offline after policy changes. No automatic mod installs.
- Catalogue work is bounded: four transfers, 4 MiB responses, 200 rows, 24 MiB metadata
  cache, 32 MiB image disk cache, 16 MiB/32 decoded images, two 800 px decodes, 350 ms search
  debounce. Visible images add memory beyond the LRU. Suspend/clear before play.
- Olympus-style name search returns up to 20 relevance matches across categories;
  the paged list supports real sorts/filtering. Do not fake global sorting of
  search matches. Services may use `GameBananaType=Obsolete`; trust verified
  PageURL/file identity. Recheck live contracts when changing provider behavior.
- Retain full arbitrary-mod save/settings/sidecar data. The vanilla strict save
  serializer/allowlist is not a valid general backup policy. Current gameplay
  diagnostics checking standard saves do not define all mod storage semantics.

## 9. Roadmap after the accepted browser gate

### Completed through32: responsive real loading, including backend work

The following design rationale is historical. Build32's accepted presentation
and build31's managed loading work implement this increment; keep their limitations.

Read [the current roadmap](docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md),
especially “Real SwiftUI startup progress”. Desktop Everest uses a separate
splash process and named pipe. Its real mod counts/stages can inform the native
bridge; leave the desktop subprocess disabled on iOS. Revalidate the call sites
against the **current d72e94f runtime**, not only the older research snapshot.

The known blockage is concrete: `main.m` does runtime/content preparation on an
attached worker, then calls `startGraphics` on UIKit's main thread.
`CJGraphicsCall("Start")` requires that main thread; `GameEntry.Start` constructs
`new JitGame()` and calls `CJITBeginExternalLoop`, which synchronously performs
substantial Everest/game startup. Merely queuing SwiftUI progress on the same
blocked thread will not produce a responsive loading screen.

Profile/instrument real phases first. Design resumable/cooperative stages or
move only proven thread-independent work to a correctly attached worker. Preserve
UIKit/window/Metal and thread-affine game/mod calls. Do not move all startup to
an arbitrary background thread, pump a nested UIKit run loop, or fake progress.
Count scanned/loaded/skipped/failed archives/modules where measurable; use an
indeterminate state elsewhere. Mod count is not a percentage of elapsed work.
Keep smooth native presentation, current-stage text, elapsed time and bounded
diagnostics, with a reliable first-frame/window handoff. Respect backgrounding
before presentation and honest cancellation once initialization has begun.

Acceptance should cover real cold/warm loads, multiple-module archives and failed
loads, UI responsiveness, thread affinity, gameplay/save/Quit and preserved
catalogue quiescence. Build 27's observed Run→first-frame 74.71/26.52s and sampled
4.05/3.72 GB footprints justify this work; they are not controlled cold/warm
benchmarks, a leak diagnosis or older-device performance evidence.

### Implemented in33/34; combined phone gate pending: saves and backups

Build34 adds per-slot transfers to33's whole-profile implementation. Follow the
current combined phone guide and report above before moving the acceptance gate.

SwiftUI/Files owns the manager. Default small backups preserve saves, settings
and unknown persistent sidecars plus mod identity/schema manifests, usually
excluding game content and mod ZIPs. Optional full archives can include mods.
Back up while inactive; restore through staging/new profile and rollback,
validate containment and require a fresh process. Never execute a mod to preview
a backup or discard unknown data because vanilla XML validation rejects it.
Automatic cloud save merging is later work.

### Next after34 acceptance: complete native touch editor and presentation polish

Port the full D3 interaction feature set from the read-only AOT reference:
fixed/floating movement, four split orientations, duplicate/swap, sliding,
circle/rectangle/shoulder grab, Hold/Invert/Toggle and source-aware behavior,
opacity/visibility, haptics, move/resize, mirror, undo/reset/delete, import/export,
and up to four extras including Crouch Dash/Quick Restart. Use a SwiftUI draft
canvas/inspector with Save/Cancel and normalized geometry shared with hit tests.
Preserve stable simultaneous touch transport; individual SwiftUI taps cannot
replace held/sliding/multitouch controls. Match glyph centering and hit areas.
Existing optional performance metrics are useful, but callback timings are not
GPU timings or an automatically valid 1%-low metric.

### Platforms and distribution

The owner wants iPad support: make new native UI adapt to tablet sizes, safe areas,
resizing and pointer/keyboard/controller input now; verify JIT and gameplay on
real iPad hardware later. macOS is a plausible product after the existing x64
host tests; Apple-silicon packaging/runtime still needs work. tvOS/visionOS need
separate JIT/install, graphics and input investigation. See
[Apple platform direction](docs/APPLE_PLATFORMS.md). No watchOS target is planned.

Public direction is a small reusable launcher, owner-imported original Celeste
files and arbitrary compatible mods, with no end-user Xcode. Current private
prepared game IL and FMOD still prevent treating the test IPA as a public release.
Do not tell users desktop FMOD binaries can serve as the iOS library or infer
permission from another project's reported agreement.

## 10. New test kits and maintaining this handoff

Default to iCloud:

```text
iCloud Drive/Celeste JIT Tests/<version>-build-<number>/
```

The owner allows up to 1 GB total. Include a clearly named unsigned IPA, short
phone README, exact build/runtime/hash identity, checksums and any genuinely
needed fixtures/script instructions. Preserve all existing user data and every
Results folder. Verify bytes locally and on the iCloud copy; distinguish local
placement, confirmed upload, actual phone download and accepted phone execution.
Past iCloud account errors were sometimes misleading: owner download success is
valid evidence of download; local placement alone is not upload proof.

Superseded large cloud installers may be removed only after their exact local
copies are verified. Keep the physically accepted fallback. Direct USB copying
to the owner's LocalSend Documents under the same versioned folder is a fallback,
not the default, and needs verified target/container access. Do not copy to an
unrelated connected device. Keep symbols outside the IPA: an early in-app dSYM
caused LiveContainer “Failed to Sign .../DWARF/...” errors.

Before a new handoff, run the checks appropriate to the actual change. Preserve
exact source/runtime/package/symbol identities and mark host/simulator/phone
results separately. Simulator orientation screenshots must settle after rotation;
`XCUIScreen.main.screenshot()` avoids the previously cropped app-frame capture.
Keep simulator fixture transport out of the device binary. Do not rebuild old
accepted runtime or renderer stages in place just to satisfy copied scripts.

Update this handoff, root `AGENTS.md` and roadmap when actual evidence changes
the next step. Keep the public file inventory current, with a reason and SHA256
for new/changed files; preserve `import_sha256` as historical extraction identity.
The inventory describes itself without a recursive self-hash. The repository
audit still verifies frozen 28's 228 source inputs and 49 native/vendor inputs;
new code should live outside those frozen inputs, with its own checks.

Do not commit/push these handoff edits unless the owner authorizes it. They are
available immediately to a new chat opened in this **local Cabrillo folder**.
