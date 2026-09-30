# CI and public IPA releases

## What the workflow builds

[Build and publish IPA](../.github/workflows/release.yml) builds an unsigned iPhone/
iPad app from the selected Git commit on a fresh GitHub-hosted macOS runner.
The current release recipe is [release/public52.json](../release/public52.json),
version0.24.1/build52. It compiles the accepted build50 launcher source and freshly
builds its managed and native runtime dependencies. It retains shortcut49.

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

- `Cabrillo-0.24.1-unsigned.ipa`
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
gh attestation verify Cabrillo-0.24.1-unsigned.ipa \
  --repo hmcneill46/cabrillo-celeste \
  --signer-workflow hmcneill46/cabrillo-celeste/.github/workflows/release.yml \
  --source-ref refs/tags/v0.24.1 \
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
