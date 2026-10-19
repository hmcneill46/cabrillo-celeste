# Build55 — Everest stable1.6642

19 October 2026. Cabrillo0.25.0, `launcher-everest6642-20261019-55`.
The owner requested the latest Everest. The selected target is the official
[stable1.6642.0 release](https://github.com/EverestAPI/Everest/releases/tag/stable-1.6642.0),
published17 October2026 at20:15:26 UTC, commit
`5abd7876821223c20711c1844a5187321d6e904c`. GitHub's latest-release API identifies
this stable release; it is not a prerelease. The commit's28 September date is
separate from the release publication date.

This is the local implementation and verification record. Fresh hosted managed
and native compilation, a complete55 IPA, package audits and physical55 testing
remain pending. No55 tag or Release has been published, and no device action was
dispatched for this work. The current public fallback remains
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
There is no cache-schema change or manual deletion step. This describes the
retained implementation; the resulting55 recipe and device cache transition
still need their hosted/runtime checks.

All253 captured build54 app inputs remain byte-identical. The55 lane adds new
source/identity/recipe inputs rather than editing that frozen set. It retains
build54's copy-based game/mod Files imports, standalone signing compatibility,
original bundle identifier, JIT/detach/recovery policy and signed49 Shortcuts.
The accepted54 original-ID Feather game-ZIP selection/staging result is retained
as earlier evidence; it does not establish55 gameplay, JIT or physical mod import.
No new JIT entitlement or certificate-only JIT mode is introduced.

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
any package installation; fresh managed compilation and NLua strong-name signing
remain assigned to the existing hosted macOS build.

## Remaining gates and publication identity

Before calling55 a completed trial, require fresh pinned public-source managed
and native compilation, the actual positive55 metadata audit and negative
controls, NLua strong-name verification, complete IPA/package checks, and exact
source/ref/workflow hosted attestations. Physical testing then needs the actual
new Everest registration, first/cached preparation, the owner's mod selection,
gameplay/save/resume/normal Quit and native return. Earlier save-manager, iPad
and sustained120Hz gates remain separate. No local compile closes these gates.

The owner selected `hmcneill46` with a GitHub noreply identity for repository
attribution. The parent task verified the authenticated repository account and
sole collaborator as `hmcneill46`. This identity setting does not itself publish
source or authorize a new tag/Release. No private signing, pairing, game code,
assets, SDK components or private logs belong in the public source/output.
