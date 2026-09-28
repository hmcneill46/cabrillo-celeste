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

**Build38 (0.21.0) remains blocked from public IPA publishing.** The new
[owned-game preparation](ios-jit/OWNED_GAME_BUILD_38.md) removes original and
prepared Celeste code from the IPA. It rebuilds the public dependencies without
private capsules, and prepares the user's original ZIP after import.

## Remaining distribution gate

[The release manifest](../release/current.json) records **FMOD redistribution
permission and an authorized SDK download for release CI** as the remaining
known distribution dependency. The permission must cover the actual FMOD1.10.09
iOS libraries in this independent launcher. It has not been granted or inferred
from another port. Source licenses and component notices remain included.

Private local builds explicitly provide the SDK with `--fmod-sdk`; their
provenance discloses a private input and the publishing wrapper rejects them.
Earlier packages28–37 retain their original private game/dependency constraints.
Device acceptance is a separate quality gate before choosing a stable release.

## Public builder contract

`tools/build_public_release.py` is the dedicated source recipe. It downloads
checksum-pinned public sources, SDK/runtime packs and NuGet packages, builds the
managed and native dependencies, accepts the approved FMOD SDK, and compiles and
audits the unsigned app. It does not consume a Celeste game ZIP, private capsule
or previously compiled Cabrillo. Normal mode fails before building anything
until the FMOD gate is explicitly resolved.

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
The public recipe and distribution permissions still need review.

The wrapper copies only the expected files into a separate release directory,
renames the IPA to `Cabrillo-<version>-unsigned.ipa`, records source/dependency/IPA
hashes and creates `SHA256SUMS`. GitHub attests all four files. A separate publishing
job checks those attestations against this workflow, the tag and commit before
creating a Release. It refuses to overwrite an existing release.

## Enabling and making a release later

1. Obtain and record FMOD redistribution permission, including authorized SDK
   delivery for CI. Complete the device gates in the current handoff. Do not
   relabel frozen private packages as public builds.
2. Review `release/current.json`: record `fmod_distribution.approved`, a concrete
   permission reference, an authorized HTTPS SDK ZIP URL and SHA256, then clear
   the documented blockers and enable `public_ipa_ready`. The archive must have
   the SDK's `api/` and `doc/` directories at its root. Use a new build identity
   when changing frozen packaging inputs and update the deliberate blocked test.
3. Review the source and device evidence, merge the intended source, and wait for
   its CI checks. Create and push a matching version tag only when choosing to
   release, for example `v0.21.0`. The workflow reruns CI at that exact commit.
   A tag such as `v0.21.0-rc.1` uses app version `0.21.0` and creates a prerelease.
4. To retry a failed run, use GitHub's rerun control or manually run **Publish IPA**
   against that existing tag. Selecting `main` is rejected. A published tag/release
   is immutable under this workflow; corrections need a new version.

No repository secrets are needed for this workflow. Actions are pinned by commit.
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
