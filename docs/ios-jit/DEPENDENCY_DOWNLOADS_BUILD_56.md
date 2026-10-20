# Build56 — dependency download repair and runtime agreement

19–20 October2026. Cabrillo0.25.1, `launcher-dependency-downloads-20261019-56`.
The owner asks to repair the Strawberry Jam downloader and verify that the app,
actual Everest payload and dependency resolver agree about supported versions.
The implementation uses the retained stable1.6642.0 source. Final local native,
live installation, actual broken-link recovery and independently verified hosted
IPA checks pass. The owner now authorizes merging PR6 and the0.25.1 Release;
physical runtime acceptance remains separate.

## Confirmed failure and exact archive relocation

The owner's diagnostics identify exact build55 source and all261 hosted input
hashes. Its last installation verifies33 of52 planned archives, including the
StrawberryJam2021 main ZIP, then fails FemtoHelper1.15.22. No commit starts and
application state stays unchanged. This is a download-reference failure before
mod activation, not evidence of an Everest, signing or JIT failure.

The bundled compatibility pin uses GameBanana file1776026,11,103,153 bytes and
SHA256 `5a845805bae30490ed7c9da84410fbe672628b8fe927a830f5f2eb148eb88419`.
Its original URL returns404 or HTML instead of the archive; both old mirrors
return404. The current official [FemtoHelper page](https://gamebanana.com/mods/53722)
API lists the same archived1.15.22 as file1838255. An independent download from
`https://gamebanana.com/mmdl/1838255` matches the full old SHA256 and byte count.
No mod code, version, dependencies or compatibility allowance changes.

`launcher-dependency-downloads/CompatibilityDownloads.json` and its
`BuildContract.json` relocate that transport reference together. All three
compatibility pins remain tested, exact archives. A refreshed community index
still cannot silently replace an app-managed compatibility pin with a newer,
untested helper. Original/cached game files and profile/save paths stay retained.

## Native mirror metadata

Everest6642 reads a `MirrorName` from its community index. The retained native
installer discards it and guesses mirror filenames from the GameBanana URL.
Build56 retains the supplied field in parsed/grouped candidates and Codable
records, then passes it to the actual ZIP transport. Valid explicit names work
with any accepted original HTTPS URL, using only the fixed community mirror
hosts. Missing/null metadata retains the earlier strict canonical numeric
GameBanana fallback. Empty, malformed, path-like or escaped names use the original
URL only. No untrusted value becomes a host or arbitrary path.

The candidate content key excludes `MirrorName`, so changing backup transport
metadata does not invalidate an already verified content cache. File size,
xxHash/SHA256, actual archive module metadata and runtime dependencies still
control acceptance. Same-URL multi-module records must agree about mirror
metadata. Cancellation, incomplete-file cleanup, review invalidation after
inventory changes and transactional mod activation retain their prior behavior.

## General exact-archive recovery

A moved download must not require a new app build for each changed file ID.
After normal and mirror transport fails, the installer can read the authoritative
GameBanana page and its current/archived file metadata. Explicit pinned/root page
anchors are canonical Celeste pages. Other dependencies use bounded catalogue
search, joining the published current file ID to the page before trusting it.
Names alone cannot establish identity. Discovery and retry counts are bounded.

Recovered URLs are transport alternatives for the same reviewed candidate.
Version, size, hash, actual ZIP modules and app compatibility pins stay unchanged.
Every normal, mirror and relocated attempt is verified before entering the cache;
a wrong same-size archive can be rejected and the next candidate tried. Invalid
metadata, unrelated pages, cancellation, missing exact versions and changed
archives must end without a partial mod commit.

## Everest and dependency versions

The source remains official stable1.6642.0 at
`5abd7876821223c20711c1844a5187321d6e904c`. The versioned56 build selects the
retained55 generated Swift/C# runtime identities and rebuilds the same pinned
managed/native dependencies. Celeste1.4.0.0 and CelesteIOS1.0.0 remain unchanged.
EverestCore is Everest's built-in dependency alias; it is included in native
resolution and does not require a separate installed managed module.

The actual compiled payload audit checks the injected VersionString, numeric
modules and adapter/native agreement, rather than accepting only a manifest
label. Additional native controls exercise minimum versions, API/EverestCore
aliases, too-new runtime requirements and actual ZIP metadata that disagrees
with the online graph. A downloaded mod cannot replace any built-in module. Native graph and YAML
parsers now normalize the legacy `API` name only for required dependencies,
matching upstream `EverestModuleMetadata.PostParse`. An absent optional module
named `API` stays optional; `EverestCore` retains its separate built-in alias.

The historical minimum Everest versions in helper manifests are requirements,
not claims about the installed version. GravityHelper1.2.28 and
CollabUtils2 1.13.4 remain exact compatibility pins because their runtime detours
explicitly validate those tested versions/hashes. FemtoHelper remains1.15.22.

## Verification and delivery

Receipts and exact scope are recorded in
[`DEPENDENCY_DOWNLOADS_BUILD_56_EVIDENCE.json`](DEPENDENCY_DOWNLOADS_BUILD_56_EVIDENCE.json).
The final production source passes100 Python build/release controls, actual
arm64/iOS15 compilation,119 native save/profile checks,76 mirror controls,
78 general relocation controls and167 runtime/dependency boundary controls.
The retained132 shortcut and53 cellular-ordering controls,36 generated branches,
15 broken-URL controls and picker policy/production objects also pass with all
their input hashes still exact. All261 frozen55 and253 frozen54 inputs remain
unchanged.

The actual public55 patch DLL's numeric dependency comparator is read as
metadata, audited to permit only integer/boolean operations and System.Version
getters, then isolated into a core-library-only fixture. Its14 comparison cases
agree with the final Swift fixture;156 guard/comparison assertions pass. No
original Everest initializer, adapter or game code runs. Fresh56 managed package
metadata and actual56 version parity also pass as recorded below.

The earlier live transport baseline downloaded and verified all52 Strawberry
Jam archives (1,235,908,245 bytes) and passed128 installation/cache checks. That
baseline compiled before the general-recovery expansion and is explicitly kept
separate from final source acceptance. The final production run revalidates
those public archives from a seeded cache, applies and rescans the installation,
and passes232 checks, including complete installed ZIP/hash/metadata readback,
zero-change final resolution, successful library preflight and a second cache-only
installation with zero download attempts. All52 archives remain identical.

A separate uncached run uses the real removed FemtoHelper file1776026, its exact
old reviewed candidate and normal production HTTPS. Both old mirrors fail; the
official page discovery finds1838255, whose actual bytes, SHA256 and ZIP version
match. All14 assertions pass, including the original candidate/cache identity,
the resolved-URL diagnostic and completed transaction with synthetic original
root/save sentinels preserved. No network provider is overridden in either live
run. The earlier1.24GB fresh transport baseline and final seeded reuse are
distinct evidence; the final old-URL recovery itself downloads the real archive.

The local public checkout audit passes4715 justified/hash-checked file entries,
with private/generated inputs excluded. On20 October the owner explicitly
approves committing/pushing as `hmcneill46`, updating existing draft PR6 and
running the existing restricted SDK workflow for an unsigned56 trial. This
covers the repair and its validation/delivery notes; no new tag/Release is
authorized. Hosted package verification is recorded below.

Host installation and metadata checks do not establish physical gameplay, JIT,
first/cached game preparation, save/resume/normal Quit or native return. The
published54 fallback and earlier iPad/sustained120/save-manager gates remain
separate. Preserve all frozen53/54/55/56 inputs and packages. Use57 for new app
implementation; no original/private game,
credentials, pairing data or SDK build inputs belong in public source or outputs.


## Completed hosted trial and independent kit verification

[Run39371266102](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39371266102) at source
`9e1f6cc4838e7b8aaff1ce86d57e307a5e84abee` completes all five active jobs on20 October.
The publication job is skipped. Both commit author and committer resolve to
`hmcneill46`. The hosted native reports independently confirm119 profile checks,
321 dependency controls and actual arm64/iOS15 compilation. The full build uses
fresh public managed/native sources and the approved official SDK.

The [unsigned five-file kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39371266102/artifacts/12241274430) requires GitHub sign-in;
expiry is3 November2026 at05:04:01 UTC. Independent download verification checks
all274 captured app source hashes, every retained53/54/55 source map, all151
unchanged55 dependency hashes, exact56 download metadata, original bundle ID,
copy imports, signed49 resources and absence of production test fixtures. All
five cryptographic attestations match the exact source, ref, workflow, run and
attempt; the kit stays unchanged throughout verification.

The actual199 packaged DLLs pass434 metadata checks, whose report exactly matches
the hosted fresh-build audit. NLua1.4.1's full RSA strong-name signature validates;
covered-byte and signature-byte tamper controls are rejected. A separate guarded
comparator extracted from this actual56 patch agrees with all14 final Swift
version cases, with156 assertions. Only the isolated pure numeric comparison
runs; the original Everest assembly, initializer, adapter and game never run.

IPA bytes:18,784,686. SHA256:
`b9e0fa34a9163ad0024f4ff2ff02d10290716537deb6629b0e4ead33946d3fe0`.
The preparation recipe preserves original source/input identities. Fresh compiled
tool hashes select recipe generation
`27cbd4baf70cbc5b70173eb6e4e06d34f507dac9f61e8f8e2a0b65c9e9b2765b`;
first/cached phone preparation is still a separate device gate. All274 captured
app inputs and `artifacts/cabrillo-build56-hosted` are frozen; use57 for new app
implementation. Delivery notes remain outside those frozen app inputs.


## Physical phone installer acceptance —20 October2026

On20 October the owner confirms “Yep all works now!” The attached exact56
diagnostics match all274 hosted source hashes on physical iOS27.0.1. Copy-mode
game ZIP import stages875,540,825 bytes; all52 Strawberry Jam archives verify and
install, and a52-change receipt commits successfully. FemtoHelper1.15.22 uses
1838255 with the exact tested SHA256. No storage error is reported. This closes
the phone downloader defect. The export contains no JIT/preparation/gameplay/
save/Quit events, so those separate runtime gates remain. Diagnostics SHA256:
`d8a2d67212a30d4cba221fddf829f28946370eac6836c2bf872bf2b99455eef7`. Raw evidence stays ignored in
`.private/device-evidence/2026-10-20/build56-owner-install`.

The owner confirmation answers the request to install the unsigned56 trial with
the existing Feather setup and retry Strawberry Jam. All189 events and the
completed transaction are reviewed; the original attachment is retained privately.
The bundled runtime identity reports Everest/EverestCore1.6642.0. No original
game or device data is changed by this read-only evidence review. All274 app
inputs and the test kit remain frozen.


## Release publication authorized —20 October2026

After confirming the phone installer, the owner explicitly requests merging PR6
and publishing the latest version as a Release. Preparation commits only scoped
phone acceptance, authorization and release notes. All274 captured app inputs
and151 dependency pins remain exact to the accepted56 trial. The release uses
an annotated `v0.25.1` on reviewed merged `main` and the existing full tagged
build/audit/attestation/verification/publisher workflow. The public five-file kit
will be independently downloaded and checked against that exact tag/run before
publication is recorded as complete. Existing immutable kits and history remain.
