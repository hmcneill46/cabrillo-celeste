# Build55 — Everest stable1.6642

19 October 2026. Cabrillo0.25.0, `launcher-everest6642-20261019-55`.
The owner requested the latest Everest. The selected target is the official
[stable1.6642.0 release](https://github.com/EverestAPI/Everest/releases/tag/stable-1.6642.0),
published17 October2026 at20:15:26 UTC, commit
`5abd7876821223c20711c1844a5187321d6e904c`. GitHub's latest-release API identifies
this stable release; it is not a prerelease. The commit's28 September date is
separate from the release publication date.

The complete unsigned55 trial is built and independently verified from source
`e1e78a3511df5642537a75d86ae46e98e0411f34`.
[Hosted run39320628794](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39320628794)
passes all five active jobs, including fresh managed/native compilation and
separate Ubuntu attestation verification. Its publisher is skipped because
`publish=false`. No55 tag or Release has been published, and no device action was
dispatched. All physical55 gates remain pending. The public fallback remains
[v0.24.3/build54](COPY_PICKER_BUILD_54.md).

## Upstream change and compatibility

The [comparison with the retained1.6580 commit](https://github.com/EverestAPI/Everest/compare/082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75...5abd7876821223c20711c1844a5187321d6e904c)
contains seven commits and17 changed files. Runtime changes include:

- A separately rebindable `MenuSearch` input, replacing the use of QuickRestart
  for menu search. Its keyboard default is R; it has no default controller
  binding. Controller/touch search needs runtime verification.
- A new `TeleportTrigger` using the existing `Level.TeleportTo` API.
- Update-mirror handling based on `ModUpdateInfo.MirrorName`.

The comparison also contains TAS-check dependency/workflow updates. It makes no
project target-framework, runtime-source or submodule-pin change. The Cabrillo
recipe continues to use its existing Mono8.0.28 and other dependency pins.

The mirror change removes the public `ModUpdateInfo.GameBananaType` and
`GameBananaId` members and replaces `GetAllMirrorUrls(string)` with
`GetAllMirrorUrls(ModUpdateInfo)`, returning `IEnumerable<string>`. An external
mod compiled against the removed members can need an update. This is an upstream
API compatibility risk, not a confirmed failure of an installed mod. See the
pinned [ModUpdateInfo](https://github.com/EverestAPI/Everest/blob/5abd7876821223c20711c1844a5187321d6e904c/Celeste.Mod.mm/Mod/Helpers/ModUpdateInfo.cs)
and [ModUpdaterHelper](https://github.com/EverestAPI/Everest/blob/5abd7876821223c20711c1844a5187321d6e904c/Celeste.Mod.mm/Mod/Helpers/ModUpdaterHelper.cs)
sources. New-version mod/gameplay acceptance remains open.

## Source, identity and cache preparation

The public source archive is pinned by commit and SHA256:

- URL: `https://codeload.github.com/EverestAPI/Everest/tar.gz/5abd7876821223c20711c1844a5187321d6e904c`
- Size:6,971,655 bytes.
- SHA256: `e5b4b25d332390e53c46e33115629ab9bbdb38ef408000a81ada2698a6aa988e`.

The separate `launcher-everest6642` overlay preserves every existing platform
patch and injects `1.6642.0-cjit-5abd787`. Its patch provenance records exact
original/patched hashes for all five Everest patch files. MonoMod/runtime patch
rows and explicit import records remain unchanged. Actual `git apply --check`
and application pass on a fresh verified6642 archive; the retained loading patch
then applies successfully with four edits/additions. This checks source
application, not compilation or execution.

`RuntimeIdentity.json` and its generated managed/Swift expectations agree on
Everest and EverestCore1.6642.0 and the exact upstream commit. Celeste1.4.0.0,
CelesteIOS1.0.0 and compatibility policy1 remain unchanged. The55 recipe selects
the new identities and source overlay together; changing the label alone is
insufficient.

The existing `OwnedGameRecipe.json` generator hashes preparation components,
including `Celeste.Mod.mm.dll`. A rebuilt Everest therefore changes the recipe
hash used for the prepared-game generation. The first launch prepares a new
generation; subsequent launches can reuse its verified result. Verified original
game files retain the same `source_id`
`4b665aa3b550b262100dbe59512d5736379af0a5c4e0e6c0c277f10bcc50a09c`.
Old published generations and saves remain retained by the existing store.
There is no cache-schema change or manual deletion step. The actual downloaded55
recipe is now audited: its hash/generation is
`9e0cef654c0845c5246ea951ead3557a83c8c6641a81bf2aacd0dba01442c73e`,
compared with54's
`ea7ced9b2c8cec90ff9f33d519f7f93a03fa3cb983813f3939f2e31505346af4`.
The original source/input pins are exact; nine compiled preparation-tool hashes
differ. Source dependency pins other than Everest remain unchanged. This proves
the recipe selects a new generation; actual first/cached preparation on a device
is still untested.

All253 captured build54 app inputs remain byte-identical. The55 lane adds new
source/identity/recipe inputs rather than editing that frozen set. It retains
build54's copy-based game/mod Files imports, standalone signing compatibility,
original bundle identifier, JIT/detach/recovery policy and signed49 Shortcuts.
The accepted54 original-ID Feather game-ZIP selection/staging result is retained
as earlier evidence; it does not establish55 gameplay, JIT or physical mod import.
No new JIT entitlement or certificate-only JIT mode is introduced.
All261 captured55 source inputs are now frozen in the downloaded provenance.
Use56 for new app implementation and preserve the55 kit.

## Completed local checks

- 89 Python build/release controls pass. The log is
  `.build/everest55-python-controls.log`.
- The89 include13 new native-compile selection, source-preservation and
  runtime-identity rejection controls. Their separate run also passes; receipt
  `.build/everest55-native-controls.json`.
- Production compilation passes with Xcode26.6 /17F113, SDK26.5, target
  `arm64-apple-ios15.0`. It snapshots263 inputs and compiles42 Swift sources,
  six CYaml C sources and the retained54 main/compatibility Objective-C pair,
  using the actual Swift bridge. The production compatibility object has no
  test-seam symbol. Other selected native sources are hash-checked only; this
  run links no app and builds no managed/runtime payload or IPA. Receipt:
  `.build/everest6642-production-compile-a/receipt.json`.
- The new C# metadata auditor compiles with pinned SDK8.0.422, public-release
  Mono.Cecil and163 reference assemblies. The exact published54 payload's199
  managed DLLs and recipe are rejected at the intended1.6642 VersionString
  check. Its control-constructor check uses a synthetic string fixture. This
  establishes an actual old-version rejection and early auditor compilation,
  not a positive55 audit or game execution. Receipt:
  `.build/everest55-auditor-compile/receipt.json`. Independent read-only review of
  the Python runner/Cecil auditor found no blocking issue; its feature checks
  match the pinned source and the55 builder invokes it before packaging.
- All119 actual native profile/backup/save-transfer checks pass under the new55
  generated runtime identity. The wrapper denies network and private/legacy
  inputs during execution. Receipt: `.build/everest55-profiles-b/receipt.json`.

The initial macOS profile harness included iOS-only ShortcutViews and did not
produce a pass; only the new55 wrapper was corrected to exclude both iOS view
files. The successful rerun above uses that corrected wrapper. The separate
production iOS compilation includes those views. These are native storage tests;
they do not run the new Everest payload or establish physical save acceptance.

Receipt paths, hashes and precise scopes are in the
[evidence ledger](EVEREST_6642_BUILD_55_EVIDENCE.json). The local SDK/Cecil tools
are explicit public audit inputs only. Homebrew Mono setup was stopped before
any local package installation. The completed hosted macOS build supplies
Mono6.14.1 and its `sn` signing tool. Independent verification of the actual55
NLua strong-name signature also passes as recorded below.

## Completed hosted trial and downloaded kit

The full run uses `refs/heads/codex/actions-release`, attempt1, at the exact source
commit above. Eligibility, source controls, native checks, fresh build/attestation
and independent Ubuntu verification all pass. Official pinned FMOD acquisition,
cleanup, package audits and the five-file allowlist pass. SDK archives/build
inputs, signing credentials and original game files remain excluded from public
outputs.

The [five-file Actions artifact12221245338](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39320628794/artifacts/12221245338)
expires2 November2026 at20:48:01 UTC. Its byte-verified local kit is
`artifacts/cabrillo-build55-hosted`:

- Unsigned IPA:18,765,294 bytes; SHA256
  `abd79be029902c301778f8b11044484d00cedc07988f14b3243cf42cde8b04cd`.
- `BUILD_PROVENANCE.json`: SHA256
  `8bf9c834515f4d167df5c124a26a8fcc4527e12d050c924d8ca75214ecce8fd8`.

The independent download check verifies all261 captured source hashes and151
dependency inputs, with only Everest's source input changed. It confirms the
original bundle ID, retained copy-import BuildInfo, production picker symbol,
absence of the test seam and exact signed49 Shortcuts.

The actual199-DLL payload passes434 compiled-metadata checks, including the
injected1.6642 VersionString, adapter/native identity agreement, TeleportTrigger,
MenuSearch metadata, new mirror API and preparation-tool hashes. The hosted
checker also rejects an isolated wrong compiled version and stale recipe hash
at their intended checks. An independent local metadata-only audit of the
downloaded DLLs produces the exact hosted report hash
`cfa519b51ac67044201731c7c0f57dfd10630381552d764ab578e6bf6083e2fd`.
Neither metadata audit executes the game, adapter or native runtime.

The actual55 `NLua.dll` independently passes strict RSA/PKCS1 v1.5 SHA1 CLI
strong-name signature verification, with both covered-byte and signature-byte
tamper controls rejected. This metadata-only check uses pinned SDK8 PEReader and
Python RSA verification; it loads no payload assembly and installs no software.
The DLL SHA256 is
`f4fd0bfb1740b2bae4ae44b1336ce78d6b40d86c3f2b1865a8e2ed8c094b3052`,
which differs from54. Receipt
`.build/everest55-hosted/nlua-strong-name/receipt.json` has SHA256
`3ddf2a2b8e1a46bb9bfe26522e50c784bf79c22d01395a8a0b26c0fa9b77c661`.

All five downloaded files independently pass GitHub attestation verification.
Parsed certificate/statement checks bind their actual bytes to the exact source,
branch ref, `.github/workflows/release.yml`, GitHub-hosted runner and
run39320628794/attempt1. The kit remains unchanged.

| Verification | Ignored receipt | SHA256 |
| --- | --- | --- |
| Download, package and source checks | `.build/everest55-hosted/download-verification.json` | `e246ad4b7729c9c089ad780421b0eb3a0a61b0cf78c6ef0a122a3ac4b1dbd3b1` |
| Independent packaged metadata | `.build/everest55-hosted/packaged-managed-audit.json` | `cfa519b51ac67044201731c7c0f57dfd10630381552d764ab578e6bf6083e2fd` |
| All five exact-run attestations | `.build/everest55-hosted/attestations/receipt.json` | `e04f272440fef2c6ac8f8a800c42bc5d3dbdff5a6d95d67e704c18576607f541` |

## Remaining physical gates and publication identity

Physical testing still needs actual new Everest registration, first/cached
preparation, the owner's mod selection, gameplay/save/resume/normal Quit and
native return. Controller/touch MenuSearch and the new upstream behavior remain
runtime checks. Earlier save-manager, iPad and sustained120Hz gates stay separate.
Hosted compilation and metadata checks establish no physical55 acceptance.

The owner selected `hmcneill46` with a GitHub noreply identity for repository
attribution. GitHub links both the author and committer of
[the hosted source commit](https://github.com/hmcneill46/cabrillo-celeste/commit/e1e78a3511df5642537a75d86ae46e98e0411f34)
to that account, with the selected noreply address. Receipt
`.build/everest55-publication/source-identity.json` has SHA256
`148ccbbf91f518c7011019d867814a1445cb9fcc30720ae7cf71bb6bec2acbee`.
This completed source/trial publication creates no55 tag or public Release.
No private signing, pairing, original game code/assets, SDK archives/build inputs
or private logs belong in the public source/output.
