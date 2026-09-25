# CI and public IPA releases

## What works now

[Public source checks](../.github/workflows/ci.yml) runs on branch pushes and pull
requests, and can be started from GitHub's Actions page. It needs only this public
checkout. It checks the complete source inventory and private-file exclusions,
runs the Python build/release controls, and compiles the current build37 native
save and backup code for its 119 checks on macOS with **Xcode 26.6 / 17F113**.
GitHub retains the small JSON reports for 14 days. These are host checks, not an
IPA build, a game runtime test or physical iPhone/iPad acceptance.

[Publish IPA](../.github/workflows/release.yml) is a separate workflow. A `v*` tag
or a manual run against an existing version tag requests a release. Ordinary
branch pushes run CI without publishing. The release workflow checks eligibility
before compiling or uploading anything.

**Build37 (0.20.0) is blocked from public IPA publishing.** On 25 September 2026,
the owner chose to activate CI now and keep IPA publishing gated until public
packaging is ready. No current private IPA is uploaded by either workflow.

## Why the current IPA is blocked

[The release manifest](../release/current.json) records these remaining tasks:

1. Prepare the user's owned Celeste installation without distributing prepared
   game assemblies in Cabrillo's IPA. Current packages contain `Celeste.dll` and
   `Celeste.Content.dll`.
2. Resolve permission to distribute the linked FMOD iOS runtime, or implement a
   distributable alternative. An open-source launcher license does not grant
   rights to FMOD or Celeste.
3. Implement a fresh public dependency/build recipe. The current launcher build
   consumes pinned private compiled managed and native dependencies; running that
   recipe on GitHub would not make those dependencies publicly reproducible.

See the [distribution review](ios-jit/IOS_REUSE_AND_DISTRIBUTION_2026-09-11.md) and
[local build scope](BUILDING.md). Physical testing and distribution eligibility
are separate requirements. The existing reports retain the precise device gates
that passed and those still pending.

## Public builder contract

`tools/build_public_release.py` **does not exist yet**. It must be implemented as
part of the packaging work above. The release gate requires this dedicated recipe;
it refuses existing private/reproduction builders. Do not bypass the gate with a
prebuilt IPA, private capsule, signing secret or self-hosted runner.

Once implemented, the builder will receive fresh absolute `--work` and `--output`
paths beneath `.build/public-release-build`. It must use this exact source
checkout and publicly available, licensed dependency inputs, then produce:

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

1. Complete public packaging, its meaningful tests and distribution review. New
   app changes need a new identity (next unused is38; recheck the handoff). Do not
   replace frozen37 inputs or label them a public build.
2. Update `release/current.json` to the new lane/version/build. Point to the public
   builder, resolve the documented blockers and set `public_ipa_ready` to `true`.
   Update the test that deliberately keeps today's private build blocked.
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
python3 tools/ci/check_native_profiles.py --work .build/ci/native-profiles-local
```

Use a fresh work directory for the native checks. Locally Xcode defaults to
`/Applications/Xcode-26.6.app/Contents/Developer`; set `DEVELOPER_DIR` for a different
installation path. GitHub uses `/Applications/Xcode_26.6.app/Contents/Developer`.
The exact toolchain is checked. `readiness` reports `BLOCKED` without failing normal
CI; `preflight` fails closed when someone actually requests an ineligible release.
