# CI and public IPA releases

## What the workflow builds

[Build and publish IPA](../.github/workflows/release.yml) builds an unsigned iPhone/
iPad app from the selected Git commit on a fresh GitHub-hosted macOS runner.
The current development recipe is [release/public58.json](../release/public58.json),
version 0.29.0 / build58. It combines both computers' development: game-file
compatibility, full-display touch editing and live input preferences, alongside
stable Everest1.6642, copy-based imports, dependency recovery and Built-in StikJIT.
The host retains iOS15 and the isolated helper requires iOS17.4. The FMOD SDK
stays private; its permitted runtime and applicable licence are included.
StikJIT's upstream prebuilt idevice dependency remains explicitly disclosed.

[Build58's report](ios-jit/UNIFIED_BUILD_58.md) records the combined source and
test-kit checks. The owner authorizes source integration and an unsigned test
IPA, **not a new version tag or public Release**. A manual workflow trial must
use `publish=false`; publication awaits a separate request after device testing.
The current public download remains v0.26.0/build57, whose unchanged recipe and
[report](ios-jit/INTEGRATED_STIKJIT_BUILD_57.md) remain available. Source and
delivery commits use the GitHub account `hmcneill46`; GitHub's web merge is
associated with that account.

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

## Unsigned0.25.1/build56 trial —20 October2026

[Run39371266102](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39371266102) passes all five active jobs at
`9e1f6cc4838e7b8aaff1ce86d57e307a5e84abee`, ref
`refs/heads/codex/actions-release`, attempt1. Official SDK acquisition, fresh
managed/native compilation, package audits, all five attestations and separate
Ubuntu verification pass. Release publication is skipped.

The [five-file unsigned kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39371266102/artifacts/12241274430)
requires GitHub sign-in and expires3 November2026 at05:04:01 UTC. Its independent
download at `artifacts/cabrillo-build56-hosted` verifies all274 captured source
hashes, all151 unchanged55 dependency hashes, original bundle ID/copy imports,
exact compatibility archives and signed49 Shortcuts. The actual199 DLLs pass434
metadata checks matching the hosted audit exactly, full NLua RSA strong-name
verification with tamper controls, and14 numeric dependency comparisons against
the production Swift rules. No game, adapter or original Everest initializer runs.

IPA bytes:18,784,686. SHA256:
`b9e0fa34a9163ad0024f4ff2ff02d10290716537deb6629b0e4ead33946d3fe0`.
Freeze all274 captured56 app inputs and the kit; use57 for new app implementation.
Physical gameplay/JIT, first/cached preparation, saves/lifecycle and earlier
separate iPad/120Hz gates remain distinct. See
[the56 report](ios-jit/DEPENDENCY_DOWNLOADS_BUILD_56.md) and its evidence ledger.

## Unsigned0.25.0/build55 trial —19 October2026

[Run39320628794](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39320628794)
passes all five active jobs at source `e1e78a3511df5642537a75d86ae46e98e0411f34`,
ref `refs/heads/codex/actions-release`, attempt1. Official SDK acquisition, fresh
managed/native compilation, package audit, all five attestations and separate
Ubuntu verification pass. The publication job is skipped; no55 version tag or
Release is created. Source attribution resolves to `hmcneill46` for both author
and committer.

The [five-file test artifact](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39320628794/artifacts/12221245338)
requires GitHub sign-in and expires2 November2026 at20:48:01 UTC. The independently
downloaded kit in `artifacts/cabrillo-build55-hosted` verifies checksums,261
captured app source hashes,151 dependency hashes with only Everest changed,
original bundle ID, copy imports and signed49 Shortcuts. All five attestations
verify the exact source/ref/workflow and hosted run identity. Its199 compiled
managed DLLs pass434 metadata checks, with a byte-identical independent/hosted
audit report. Hosted wrong-version and stale-recipe controls pass. Original game
input pins/source ID are identical to published54, while preparation tool hashes
select a new cache generation.

IPA bytes:18,765,294. SHA256:
`abd79be029902c301778f8b11044484d00cedc07988f14b3243cf42cde8b04cd`.
Freeze all261 captured app inputs and this kit; use56 for new implementation.
These checks execute the metadata auditor, not the game or iOS JIT. First/cached
preparation, mods and physical gameplay/save/lifecycle acceptance remain pending.
See [the build55 report](ios-jit/EVEREST_6642_BUILD_55.md) and
[draft PR6](https://github.com/hmcneill46/cabrillo-celeste/pull/6).

## Published release: v0.24.3 —19 October2026

[Download the public IPA](https://github.com/hmcneill46/cabrillo-celeste/releases/download/v0.24.3/Cabrillo-0.24.3-unsigned.ipa) from the [Release page](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.24.3).
Annotated `v0.24.3` targets `46dc40678fe839b676a2a9496eb84229d0b4c331`. [Tagged run39285104629](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39285104629) rebuilt,
audited, attested, independently verified and published the five-file kit.
A separate download without authentication verifies every public file's size,
checksum/API digest and exact tag/source/workflow/run attestation.

Release IPA bytes:18,764,014. SHA256:
`e3520bced1ff72886d2b1796ee1420f797df71a514ee9b9e0430fd933e18a583`.
All253 captured app inputs and151 dependency hashes match the accepted trial.
Only generated release-note prose and documentation changed for publication;
the builder wrapper is outside those253 inputs and its hash is recorded in
provenance. The trial kit remains immutable at
`artifacts/cabrillo-build54-trial-frozen`; retain the separately verified tagged
kit in `artifacts/cabrillo-v0.24.3-release` and the byte-identical locally renamed trial ZIP.

The owner-confirmed trial game-ZIP selection/staging pass uses the original ID
and existing Development profile on iOS27.0.1. The freshly tagged binary has no
separate physical-device run claimed; mod import, gameplay and JIT acceptance
remain distinct. See [CHANGELOG](../CHANGELOG.md).

## Unsigned0.24.3/build54 trial —19 October2026

[Run39276928342](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39276928342)
produces the unsigned54 kit from `4a094527a96e62fbf63518c088a1dd48d19407e5`.
Official SDK acquisition, fresh compilation, package audit and attestation
creation and separate Ubuntu verification pass; trial publication is skipped.
The [five-file artifact](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39276928342/artifacts/12199896629)
requires GitHub sign-in and has14-day retention. A separately downloaded copy
passes checksums, all253 captured source hashes, all151 unchanged53 dependency
hashes, original bundle ID and copy-import BuildInfo. All five local attestations
verify the exact source/ref/workflow, GitHub-hosted runner and run invocation.
IPA bytes18,764,021; SHA256:
`254a126168837708bbb7d136da0c3e426a3522feb375c0d19bb26d5fbcf89762`.
Keep the253 app inputs/kit frozen; use55 for new implementation. Original-ID
Feather game ZIP selection/staging passes; physical mod import remains separate.
The subsequently published tagged Release is recorded above.

## Unsigned0.24.2/build53 trial —19 October2026

[Run39267829175](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39267829175)
passes all build/audit and independent attestation jobs at
`e63f1e0a8030daa3f0f4228ca6992c428e4f1811`. Release publication is skipped.
The [five-file test kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39267829175/artifacts/12194283151)
has14-day retention and requires GitHub sign-in. A separately downloaded copy
passes checksums, exact source/dependency checks and all five attestations.
The18,763,886-byte IPA SHA256 is
`cbf396e7a7b1aec7bbf0a25c19cf3cfe59ef80d26e1f47df1481ed3b7791ad55`.
All254 captured app inputs are frozen; new app changes need54. Phone acceptance
with the original identifier/current Feather profile subsequently fails. See the53
report for the reviewed public FMOD website pin repair needed before this trial.

The build takes no Celeste game ZIP and no private compiled Cabrillo capsule.
Players import their own original Celeste FNA1.4.0.0 files. The first game launch
prepares that copy; subsequent launches reuse the verified cache. FMOD runtime
code is linked into the app under the permission below. No FMOD SDK is published.

## Published release: v0.24.1

[Download the public IPA](https://github.com/hmcneill46/cabrillo-celeste/releases/download/v0.24.1/Cabrillo-0.24.1-unsigned.ipa) from the [Release page](https://github.com/hmcneill46/cabrillo-celeste/releases/tag/v0.24.1).
[Tagged run36696860903](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36696860903) successfully rebuilt, audited, attested, independently
verified and published all five files at commit
`2acf9af18f9dd1f200d8114ba9cbd2f557dfe24c`. A separate unauthenticated download
verified every published file and its tag-specific attestation. IPA SHA256:
`c223f7e31aea15ecc640f8f10388c4628f9ba063f1a52967279c949023123b47`.

The owner tested the trial kit and reports everything looks good before authorizing
publication. The tagged rebuild uses the same 247 captured app source inputs and
the same 151 dependency inputs. This preserves the scoped trial acceptance; it
does not claim additional detailed device tests for the freshly compiled binary.

### Earlier trial build

[Hosted run 36682093793](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36682093793) passes the complete fresh build and independent
verification at commit `789f20e751901cc4538ff25b8033abeb6f339af7`. The
[trial kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/36682093793/artifacts/11083060317) contains five attested files. A separate local download
check verifies all five attestations, checksums, all247 captured app inputs and
NLua's strong-name signature. The IPA is18,759,836 bytes, SHA256
`7392dd6f0199faf0d8501ed690772685e127ee9fd463ed2b3ce59441e719dbe4`.
This manual run did not create a version tag or GitHub Release.

A successful build/package check is separate from physical gameplay acceptance.
The existing build50 phone evidence and earlier game/iPad checks remain scoped to
those builds. The owner subsequently reports a successful trial test as described above; no
additional diagnostic export or detailed device coverage is inferred.

## Why there are separate workflows

| Run | Inputs and purpose | Published output |
| --- | --- | --- |
| Branch pushes and pull requests | Public checkout; inventory, Python controls, native saves/shortcut tests and signed-document verification; no FMOD credentials | Small test reports |
| Manual **Build and publish IPA**, with **publish** unchecked | Trusted branch or matching version tag; freshly fetched dependencies and FMOD SDK | Audited, attested IPA kit as a run artifact; no GitHub Release |
| Push a matching `v*` tag, or manually select that tag with **publish** checked | Same full source build and checks, followed by independent attestation verification | GitHub Release; `-rc.N` tags become prereleases |

Ordinary pushes do not create Releases or use the FMOD account. The full build is
slower and needs licensed SDK access, so it runs only when explicitly requested
or when the maintainer chooses a version tag. The manual branch trial is useful
before deciding to release. The workflow refuses to publish from a branch, use
the wrong version tag, build a dirty checkout or overwrite an existing Release.

## FMOD runtime permission

On30 September2026 the owner supplied Firelight Technologies' reply from Brett
Paterson permitting distribution of a built application with FMOD runtime
libraries. Developers accessing the source must download FMOD from **fmod.com**;
SDK components must not be redistributed. The original supplied email is retained
privately. This is permission for the runtime in the app, not an SDK redistribution
exception or an open-source licence for FMOD. Retain its applicable licence and
notices; see [FMOD legal information](https://www.fmod.com/legal).

Players downloading the IPA need no FMOD account. Developers must obtain their
own **FMOD Engine1.10.09 iOS SDK, build97915** from
[FMOD downloads](https://www.fmod.com/download). Do not extract development inputs
from Cabrillo, commit the SDK or offer a mirror. See [Building Cabrillo](BUILDING.md)
for the local command using an explicitly supplied SDK.

The release job receives `CABRILLO_FMOD_USERNAME` and `CABRILLO_FMOD_PASSWORD` from
the encrypted **cabrillo-release** GitHub environment. Its deployment policies
allow `main`, version tags and the temporary `codex/actions-release` trial branch.
Fork and pull-request checks do not receive these secrets. Only the SDK download
step exposes them to its process; compiler and artifact steps do not receive them.
A fork's maintainer must configure their own licensed account and environment.

The downloader uses a new FMOD session, obtains the exact catalogue entry, follows
its temporary vendor CDN URL without forwarding account headers, verifies the
installer, logs out, mounts the DMG read-only, stages the required inputs and
unmounts it. It never records passwords, tokens, account IDs or signed URLs.
The installer and SDK stay in ignored temporary directories, are excluded from
all uploads/caches, and are removed by an always-run cleanup step.

The143,583,015-byte official installer is pinned to SHA256:
`7f1934f248df7202b8efb6951570f60c52566217e230f26ed3682a6447336e5f`.
The two original iOS archives and licence have independent pins. Only the linked
runtime code and required licence notice enter the IPA; SDK headers, separate
static archives, examples and authoring tools do not.

The authenticated download follows the inspected FMOD website, **not a documented
stable API**. The helper pins the reviewed website scripts and observed CDN host;
a changed website, destination or checksum stops the job for review. Do not fix
such a failure by publishing a private SDK mirror or disabling its checks.

## Signed Home Screen shortcut resources

Apple's `shortcuts sign` command requires an iCloud login. Fresh hosted runners
have none. The repository therefore includes the tested, pre-signed revision49
documents beside their generated plist/action source in
[release/shortcuts49](../release/shortcuts49). These are declared document resources,
not a prebuilt Cabrillo app. No Apple account credentials or private signing key
are committed or supplied to Actions.

Every Mac CI/release run validates the file hashes, certificate chain to the
pinned Apple Root CA G3, archive signature and contained workflow. It regenerates
the actions using `build_shortcut_files49.py` and compares every action and
connection; only Apple's observed client-version/name metadata changes are
normalized. The current signing certificates expire26 October2027. Renewing the
documents needs a reviewed local signing/import check and updated pins. Ordinary
builders need no iCloud account to use and verify these resources.

## What download verification proves

The full build also checks Mono6.14.1 and its `sn` tool, required by NLua's
upstream assembly signing target. This is a host build prerequisite; the iOS Mono
runtime is independently compiled from pinned8.0.28 source. The toolchain report
records the signer, CMake and Python versions. Intel and Apple Silicon build hosts
use separately pinned NuGet host packages; all common package checksums remain
identical. A package missing from or added to the lock fails the build.

The run uploads only these five files:

- `Cabrillo-0.24.3-unsigned.ipa`
- `BUILD_PROVENANCE.json`
- `PACKAGE_AUDIT.json`
- `RELEASE_NOTES.md`
- `SHA256SUMS`

The package audit checks the unsigned arm64 iOS identity, fresh executable/dSYM
UUIDs, archive safety and payload identities, including the absence of original/
prepared Celeste assemblies and original game assets. The release kit has an
explicit allowlist. SDKs, source caches and raw build logs are never artifacts.

GitHub attests every file. A separate Ubuntu job downloads the kit, checks its
checksums and verifies every attestation against this repository, the exact
workflow, source ref and commit, while rejecting self-hosted runners. A publishing
job repeats verification and confirms the tag still points at that commit before
creating the Release. Only that job has permission to write Releases.

This provides evidence that the downloaded bytes were produced by the displayed
GitHub workflow from the recorded source revision. Review that workflow and its
inputs alongside the attestation. It is not a claim that every dependency was
compiled from source, that FMOD is open source, that independent builds are
byte-for-byte identical, or that the game passed physical-device testing.

`BUILD_PROVENANCE.json` distinguishes source archives, mixed upstream bundles,
public binaries such as .NET packs/NuGet packages, licensed FMOD binaries and
pre-signed Shortcut documents. It records their origins and hashes, the compiler
versions, source hashes, source commit, workflow run and IPA checksum.

To check downloaded files from the **same** release on a Mac with GitHub CLI:

```sh
shasum -a 256 -c SHA256SUMS
gh attestation verify Cabrillo-0.24.3-unsigned.ipa \
  --repo hmcneill46/cabrillo-celeste \
  --signer-workflow hmcneill46/cabrillo-celeste/.github/workflows/release.yml \
  --source-ref refs/tags/v0.24.3 \
  --source-digest FULL_COMMIT_FROM_BUILD_PROVENANCE \
  --deny-self-hosted-runners
```

Replace the example tag/commit with the actual values in `BUILD_PROVENANCE.json`;
for a manual build use its recorded branch ref. The same command can verify each
other kit file. See GitHub's [artifact attestation documentation](https://docs.github.com/en/actions/concepts/security/artifact-attestations).

## Maintainer release steps

1. Review the source and relevant device evidence. New implementation changes
   require a new app version/build identity; preserve delivered/frozen builds.
   Keep the release manifest, native app identity and source recipe consistent.
2. Use **Actions → Build and publish IPA → Run workflow** on `main` with
   **publish** unchecked for a full trial. The source/environment policy must allow
   the chosen ref. Inspect the build, payload audit and independent verification.
3. When choosing to publish, push an existing reviewed commit as `v<version>` or
   `v<version>-rc.N`, matching the manifest version. Tags trigger the full build
   automatically. A release candidate is marked as a prerelease, not latest stable.
4. A failed tagged run can be rerun. A manual tagged run needs **publish** checked
   to create a Release. The workflow never overwrites an existing Release; changes
   need a new identity/tag. Re-run with a new ref after correcting source failures.

Actions are pinned by commit. Release jobs check out the initiating commit with
Git credentials persistence disabled. The build reads source and writes
attestations; the separate publisher receives only the verified output kit.
GitHub retains manual run artifacts for14 days. Release assets persist independently.

## Local checks and SDK diagnostics

```sh
python3 tools/ci/check_public_repository.py
python3 -m unittest discover -s tools/tests -v
python3 tools/release_pipeline.py readiness
python3 tools/verify_release_shortcuts.py
python3 tools/ci/check_native_profiles.py --lane launcher-owned-game
python3 tools/ci/check_native_shortcuts.py
```

Use fresh work directories for repeated native checks. Full builds need macOS,
Python3.12 or newer, CMake, Mono6.14.1 (including `sn`) and **Xcode26.6 /17F113** with iPhoneOS SDK26.5.
Set `DEVELOPER_DIR` if needed; the hosted path is
`/Applications/Xcode_26.6.app/Contents/Developer`.

For your own FMOD account, the optional downloader uses hidden terminal prompts:

```sh
python3 tools/check_fmod_access.py probe --report .build/fmod-probe.json
python3 tools/fetch_fmod_sdk.py \
  --work .private/my-fmod-sdk --report .build/my-fmod-sdk.json
```

Choose a fresh `.private` work directory. Never pass credentials in shell
arguments or commit them. `--credentials-from-env` is an explicit unattended mode
for a trusted secret-providing environment. Reports contain safe input identities
and status only. The access helper can separately test account/catalogue access
without downloading an SDK using `check-account` and its hidden prompts.

## Historical recipes

`release/current.json`, `tools/release.py` and `tools/build_public_release.py`
retain build38's earlier blocked contract. They are frozen evidence and are not
the active public release pipeline. The first local package51 and its
`release/public.json`/`tools/build_release51.py` inputs also remain frozen;
release52 adds the separately pinned Apple Silicon NuGet host package. Their old flags do not revoke the later FMOD
permission. Earlier private packages28–37 also retain their original game/input
constraints; never relabel those packages as new public source builds.
