# CI and public IPA releases

## What works now

[Public source checks](../.github/workflows/ci.yml) runs on branch pushes and pull
requests, and can be started from GitHub's Actions page. It needs only this public
checkout. It checks the complete source inventory and private-file exclusions,
runs the Python build/release controls, and compiles the current build38 native
save and backup code for its 119 checks on macOS with **Xcode 26.6 / 17F113**.
The build50 shortcut coordinator adds185 native checks, original43/49 failure
controls,36 generated workflow branches and15 invalid-URL controls. These checks
need neither signed shortcut files nor an Apple account; actual Apple import and
phone evidence remains in the build49/50 reports.
GitHub retains the small JSON reports for 14 days. These are host checks, not an
IPA build, a game runtime test or physical iPhone/iPad acceptance.

[Publish IPA](../.github/workflows/release.yml) is a separate workflow. A `v*` tag
or a manual run against an existing version tag requests a release. Ordinary
branch pushes run CI without publishing. The release workflow checks eligibility
before compiling or uploading anything.

**FMOD runtime redistribution is confirmed; the release workflow still needs an
updated SDK-input and provenance path.** The frozen build38 (0.21.0) manifest
remains blocked. The
[owned-game preparation](ios-jit/OWNED_GAME_BUILD_38.md) removes original and
prepared Celeste code from the IPA. It rebuilds the public dependencies without
private capsules, and prepares the user's original ZIP after import.

## FMOD confirmation —30 September 2026

The owner supplied a reply from Brett Paterson of Firelight Technologies confirming
that a built application may be released with its FMOD runtime libraries. Developers
accessing the GitHub source must download FMOD from **fmod.com** themselves; SDK
components must not be redistributed. This answers the runtime redistribution
question. It does not grant an SDK redistribution exception or relicense FMOD as
open source. The original owner-supplied text is retained privately; it has not
been published as an email transcript.

These conditions agree with the [FMOD EULA](https://www.fmod.com/legal), which
distinguishes the integrated runtime from SDK components. Preserve the applicable
licence and attribution. The30 September package review verified the unchanged
build50 IPA (`e22ca126d8cb5eb829d027267504d0b9c2600efbf3ebf4c88fd762b080ae87ff`)
against the existing public-package validator and inspected its contents. Its
FMOD recipe links the pinned runtime libraries; the only FMOD-named packaged
resource is `licenses/FMOD-LICENSE.TXT`. No FMOD SDK headers, separate development
archives, examples or authoring tools are included. Retained managed-payload
evidence separately verifies the absence of original/prepared Celeste assemblies.

## Remaining release work

[The release manifest](../release/current.json) and build38 recipe are historical
frozen inputs. Their permission flag and receipts describe the state when those
packages were built; they do not override the later email confirmation. Preserve
them and use a new build identity for the release implementation (next51).

The existing builder accepts a local SDK using `--fmod-sdk` but labels that input
private, which the publishing wrapper rejects. The future recipe must obtain its
SDK through FMOD, keep SDK files and download credentials out of the repository,
public logs, caches and release artifacts, and disclose the licensed FMOD binary
dependency accurately. Do not add a Cabrillo SDK mirror for source developers.
Runtime redistribution permission does not require the SDK itself to be public.

Earlier packages28–37 retain their original private game/dependency constraints.
Device acceptance is a separate quality gate before choosing a stable release.

## Local FMOD download verification —30 September

The owner requested local preparation before trying Actions, initially stopping
at credentials, then supplied a temporary FMOD account for the local test.
`tools/check_fmod_access.py` provides a credential-free preflight:

```sh
python3 tools/check_fmod_access.py probe \
  --report .build/fmod-download-preparation/probe.json
```

The live local probe verifies the reviewed public website scripts and receives
HTTP401 from the unauthenticated download catalogue. It reports
`CREDENTIALS_REQUIRED` without attempting sign-in. The observed website uses
`POST /api-login`, then an authenticated `GET /api-downloads`. Its public download
component requests a temporary link for a catalogue entry. These are inspected
website internals, **not a documented stable download API**. The helper checks
the two reviewed script hashes before prompting and stops if the site changes.
Public implementation references: [sign-in](https://www.fmod.com/bundle.js) and
[downloads](https://www.fmod.com/download.chunk.js).

To repeat just the account/catalogue check, enter an FMOD username/email and
password in the hidden local Terminal prompts, never in shell arguments:

```sh
python3 tools/check_fmod_access.py check-account \
  --report .build/fmod-download-preparation/account-check.json
```

Run these commands in your own checkout. The helper uses a new session and logs
it out afterward; it does not read browser sessions, save credentials, follow
redirects or log response bodies. No SDK is downloaded by either access command.
Reports contain fixed public dependency identities and status only, beneath the
ignored `.build` directory. The authenticated catalogue is not saved. Local tests
use synthetic accounts and a loopback redirect trap; they never sign in to FMOD.

The real account check passed. `tools/fetch_fmod_sdk.py` then downloaded the exact
`fmodstudioapi11009ios-installer.dmg` through FMOD's authenticated catalogue and
temporary CDN link. Its143,583,015 bytes match the retained original installer,
whose digest was measured before downloading:
`7f1934f248df7202b8efb6951570f60c52566217e230f26ed3682a6447336e5f`.
The file is a **DMG**, so the old ZIP-only recipe was not suitable.

```sh
python3 tools/fetch_fmod_sdk.py \
  --work .private/fmod-sdk-new-run \
  --report .build/fmod-sdk-new-run.json
```

Choose a fresh work directory each time. The helper confines SDK files to
`.private`, verifies the complete installer before mounting it read-only, stages
only the four required library/licence/revision inputs and detaches afterward.
Both original device archives match the existing build38–50 pins; the licence
also matches. Running the existing arm64 preparation/localization step on these
fresh inputs produced byte-identical runtime archives to the retained build.
Receipts are under `.build/fmod-download-preparation`; the downloaded private SDK
is under `.private/fmod-ci-2026-09-30-a`. The session was closed successfully.
Credentials, account identifiers and signed URLs were not saved in these files.

The download host is now restricted to the exact CDN observed in this test,
`d2m8b09s60for2.cloudfront.net`; its client receives no FMOD account headers/cookies
and follows no redirects. A changed website flow, host, installer or library
checksum stops the helper for review. No SDK mirror or public SDK cache is used.

For a future trusted release job, `--credentials-from-env` explicitly consumes
`CABRILLO_FMOD_USERNAME` and `CABRILLO_FMOD_PASSWORD`. It removes them from its
process environment before spawning mount/build children. Synthetic tests cover
this mode; the real local test used hidden prompts. No GitHub secrets were set.
Keep secrets restricted to that job and keep `.private` out of all cache/artifact
uploads. The28 new credential, transport, selection and staging controls join the
existing20 Python build/release controls.

This establishes the previously unverified authenticated SDK acquisition path.
The fresh51 release recipe still needs the permitted binary-input provenance
contract and this downloader wired into it, followed by a complete local IPA
build. No full native rebuild, new IPA, Actions run or publication is claimed.

## Frozen build38 builder contract

`tools/build_public_release.py` is the dedicated source recipe. It downloads
checksum-pinned public sources, SDK/runtime packs and NuGet packages, builds the
managed and native dependencies, accepts the approved FMOD SDK, and compiles and
audits the unsigned app. It does not consume a Celeste game ZIP, private capsule
or previously compiled Cabrillo. Normal mode still fails before building anything
with the frozen manifest.

The release wrapper supplies fresh absolute `--work` and `--output` paths beneath
`.build/public-release-build`. Public mode requires the exact source checkout and
publicly available, licensed dependency inputs, then produces:

- `Cabrillo.ipa`: an unsigned arm64 iOS app with the manifest's version/build.
- `BUILD_PROVENANCE.json`: schema `1`, the exact Git `source_commit`,
  `private_inputs_used: false`, and a nonempty `dependencies` list. Each dependency
  records `name`, `kind` (`source` or `binary`), `url`, `sha256` and `license`.
- `RELEASE_NOTES.md`: user-facing changes, supported installation requirements,
  tested devices and remaining limitations for this version.

The wrapper checks app identity, executable platform, unsigned status, archive
paths, and known game/signing payload exclusions. It checks provenance and refuses
source modifications during the build. These checks catch known packaging errors;
they cannot establish licensing rights or detect every possible renamed payload.
The future release recipe needs review against the recorded runtime permission
and SDK restrictions.

The wrapper copies only the expected files into a separate release directory,
renames the IPA to `Cabrillo-<version>-unsigned.ipa`, records source/dependency/IPA
hashes and creates `SHA256SUMS`. GitHub attests all four files. A separate publishing
job checks those attestations against this workflow, the tag and commit before
creating a Release. It refuses to overwrite an existing release.

## Enabling and making a release later

1. Use the30 September confirmation for the runtime permission record. Implement
   SDK acquisition from FMOD for the build environment without distributing the
   SDK to source users. Record its version and hash; keep any authentication
   information private. Complete the relevant device gates in the current handoff.
2. Create a fresh release lane and manifest with the next build identity. Update
   its permission reference, notices, SDK-input contract and provenance controls.
   Enable `public_ipa_ready` only after the concrete release passes its checks.
   Do not relabel frozen private packages or rewrite historical receipts.
3. Review the source and device evidence, merge the intended source, and wait for
   its CI checks. Create and push a matching version tag only when choosing to
   release. The workflow reruns CI at that exact commit. A `v<version>-rc.1` tag
   uses the matching app version and creates a prerelease.
4. To retry a failed run, use GitHub's rerun control or manually run **Publish IPA**
   against that existing tag. Selecting `main` is rejected. A published tag/release
   is immutable under this workflow; corrections need a new version.

Public source checks need no repository secrets. The verified FMOD download
requires credentials; restrict them to that build step and never include them
in source URLs, provenance or public logs. Actions are pinned by commit.
Build jobs have read access to source; only the publishing job has Release write
permission. That job downloads this run's verified artifacts without executing
the repository's build scripts.

## Checking provenance as a downloader

Once public releases exist, download the IPA, `BUILD_PROVENANCE.json`,
`RELEASE_NOTES.md` and `SHA256SUMS` from the same release. On macOS:

```sh
shasum -a 256 -c SHA256SUMS
gh attestation verify Cabrillo-0.21.0-unsigned.ipa \
  --repo hmcneill46/cabrillo-celeste \
  --signer-workflow hmcneill46/cabrillo-celeste/.github/workflows/release.yml \
  --source-ref refs/tags/v0.21.0 \
  --source-digest <full-commit-from-BUILD_PROVENANCE.json> \
  --deny-self-hosted-runners
```

Replace the example version and commit. The attestation ties the downloaded bytes
to a GitHub-hosted workflow and source revision. The manifest distinguishes source
dependencies from any permitted binary dependencies. This is not a claim that
proprietary dependencies are open source, that independent builds are byte-for-byte
identical, or that host checks prove gameplay. See GitHub's
[artifact attestation documentation](https://docs.github.com/en/actions/concepts/security/artifact-attestations).

## Running the public checks locally

```sh
python3 tools/ci/check_public_repository.py
python3 -m unittest discover -s tools/tests -v
python3 tools/release.py readiness
python3 tools/ci/check_native_profiles.py --lane launcher-owned-game --work .build/ci/native-profiles-local
```

Use a fresh work directory for the native checks. Locally Xcode defaults to
`/Applications/Xcode-26.6.app/Contents/Developer`; set `DEVELOPER_DIR` for a different
installation path. GitHub uses `/Applications/Xcode_26.6.app/Contents/Developer`.
The exact toolchain is checked. `readiness` reports `BLOCKED` without failing normal
CI; `preflight` fails closed when someone actually requests an ineligible release.
