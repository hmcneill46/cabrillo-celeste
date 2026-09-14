# Cabrillo repository separation

This is the migration snapshot before GitHub publication. The owner subsequently
authorized the initial public commit/push on14 September2026; see the
[README](../README.md) for the current repository. The pre-publication Git state
and verification evidence below remain historical.

14 September 2026. **Complete: the independent Cabrillo folder produced an
unsigned IPA byte-identical to delivered build28.** The original JIT checkout,
actively developed AOT checkout and owner-owned source inputs were read-only.
No commit, remote repository, push or GitHub write was made.

## Names and location

- **Cabrillo — Celeste Mod Loader for Apple Platforms** is the JIT product.
  Local root: `/Users/harrymcneill/Projects/Cabrillo`.
  Suggested searchable GitHub slug: `cabrillo-celeste`.
- **Morro — Native Celeste for Apple Platforms** is the separate fully AOT
  sibling. Suggested future slug: `morro-celeste`.

The names make a coherent California mountain pair, while the subtitles and
repository slugs make their relationship to Celeste clear. No claim is made
about name/handle availability. Cabrillo's README links to the sibling's current
`celeste-ios` repository. When the owner chooses the final remote names, add
reciprocal README links in the respective projects. This migration does not
rename or edit the actively developed AOT project.

The new Git repository has an unborn `codex/cabrillo-migration` branch, no commits,
no remote and no copied legacy Git history. Its source includes the actual
uncommitted JIT development, not merely the old Git HEAD. The historical source
checkout was at `b65bedd20016dc3482d7702d7f0a9707bc2b1479` on
`codex/ios-jit-feasibility-audit`; those identify provenance, not a new commit.

## What was moved, and why

The extraction copied2,227 existing source/document/license files totaling
12,306,969 bytes. New root documentation, build tools and the inventory are
additional. [The inventory](MIGRATION_FILE_INVENTORY.json) assigns each Git
candidate a purpose and hash; the inventory describes itself without attempting
a recursive self-hash. Git ignores private and generated data.

| Contents | Purpose and boundary |
| --- | --- |
| All `experiments/ios-jit` source | Current launcher plus the runtime, MonoMod, FNA, native bridge, support module, JIT script, build tools, tests, pins and versioned investigations that explain the working JIT system. Historical variants remain because they preserve the source of accepted compatibility fixes. |
| All `docs/ios-jit` documents/evidence ledgers | Feasibility research, physical acceptance, diagnoses, architecture and product roadmap. Earlier dated claims remain historical. |
| `docs/history/LEGACY_AGENTS_BUILD28.md` | Original detailed working notes and constraints, retained as reference. Root `AGENTS.md` governs Cabrillo. |
| Two shared C# policies, nine touch SVGs and their notice | JIT uses the proven control/platform behavior and glyphs. These retain their original relative paths, but no AOT app or project accompanies them. |
| Two shared Python utilities | Touch-art generation and native archive finalization used by the JIT development sources. |
| ZIPFoundation0.9.20 and the CYaml part of Yams6.2.2 | Actual source needed by the native launcher, pinned to the accepted commits; licenses retained. No unused Yams Swift parser or vendored Git history. |
| Root `tools` and new documentation | Standalone reproduction, package verification, host catalogue regression, repository audit and the one-time import procedure. |

Excluded: the AOT application/Xcode project, generated/decompiled AOT game source,
unrelated project docs/assets/tools, old Git history,122GB of historical JIT
working directories, retired installers, unrelated phone files and signing/
pairing credentials. Large old raw device logs and SDK source/build trees stay
in the preserved legacy archive. They are not dependencies of this build.

The old directories were not deleted. They remain historical fallback material
and the active Morro/AOT workspace. Further JIT development belongs in Cabrillo.

## Local private dependencies

The current standalone launcher uses455 locked private build inputs totaling
98,059,597 bytes, under `.private`. They include16 native libraries and matching
headers,201 managed assemblies, frozen resources and historical package metadata.
This preserves the accepted Mono8, renderer, system libraries, audio/Lua, Everest
and original game IL required by the current launcher.

The original launcher executable and original IPA were **not** imported. Compiled
icon assets and Info.plist were rebuilt rather than copied. The original IPA was
read to extract dependency/resources and packaging metadata, and later read-only
compared with the fresh output. Its own bytes were never used as a replacement
for compilation/linking.

The native test folder adds11 small locked fixture files totaling308,734 bytes:
dated public-service responses and synthetic ZIPs. They support fresh isolated
catalogue/installer testing without copying any large collaboration mod or game
content. Input manifests and raw migration/test evidence remain ignored.

These private dependencies must be backed up with the local development folder,
separately from Git. A future public clone needs an authorized input/bootstrap
process; it cannot contain licensed game IL or FMOD. Public original-IL
preparation and FMOD redistribution remain the existing release gates.

## Fresh reproduction result

| Check | Observed result |
| --- | --- |
| Fresh native compilation |58 source inputs compiled from Cabrillo, including the launcher and ZIP/YAML dependencies; symbol tables and icon catalogue generated anew. |
| Isolation |macOS sandbox denied reads/writes to the original JIT checkout, AOT checkout and original required-files folder. Separate negative controls verified all three denials while Cabrillo remained readable. |
| Input identity |228 delivered source inputs,49 native/vendor source inputs and455 private inputs verified. |
| Package identity |All262 entries and the complete ZIP match the original; no resource differences. |
| IPA bytes |23,812,187. |
| IPA SHA256 |`87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2`. |
| Executable and fresh symbols |UUID `98537CA1-09CE-344B-B370-5C27D8F83DC2`; dSYM outside IPA. |
| Unsigned package |No embedded Mach-O code signature or signature directory; ZIP CRCs valid. |
| Strict reproduction control |UUID-only change accepted; a changed executable code byte rejected. |
| Fresh native regression |48 catalogue/installer checks passed with newly compiled host libraries and production code. |

Output: `artifacts/cabrillo-build28/CelesteJITEverest-unsigned.ipa`.
The full new command/verification receipts are alongside it; isolation,
repository and comparison evidence are in `.private/migration`. The public
[evidence summary](CABRILLO_MIGRATION_EVIDENCE.json) records the build and test
receipt hashes and points to the repository audit.

Exact reproduction required preserving historical timestamps and resource
metadata, normalizing debug source path strings, and a narrow UUID restoration.
The linker also demonstrated two Objective-C GOT orders from the same objects;
the tool permits up to eight relinks and accepts only the complete historical
non-UUID hash. This fresh run matched on link2. Only then were the16 UUID bytes
restored and the complete executable/IPA hashes checked. No code/data patch or
weakened comparison was used. [The build guide](BUILDING.md) documents this
explicitly, including why the actual new build date lives in a separate receipt.

The root recipe recompiles the launcher against pinned dependencies, as the
original build28 did. It is not a claim that all runtime/renderer/SDK dependencies
were rebuilt from upstream during migration. Those source/patch histories are
retained for future isolated dependency changes. Default native tests use dated
responses; new live-service, simulator UI, managed gameplay or phone acceptance
are not claimed by this migration.

## Continue from here

Build27 remains the physically accepted fallback; build28's existing browser
phone gate is still pending. This identical IPA needs no new install just to
prove a folder move, and no duplicate iCloud handoff was created. Keep the
existing build28 phone instructions, JIT flow, bundle identifier and saved data.

Use Cabrillo for the next source changes. Preserve this locked reproduction
target, create a new version for implementation changes and the Cabrillo app
display name, and issue honest fresh build metadata. The current root tool
deliberately does not pretend to be a generic new-release builder. Derive that
next builder here using the already isolated source and dependency inputs.

After phone28 acceptance, the roadmap remains real responsive startup/loading,
whole-profile saves/settings backup and staged restore, then a full-parity
SwiftUI touch editor. iPadOS is the next intended device family; its requirements
should guide the native UI now. macOS is a plausible later product target;
tvOS/visionOS need independent runtime, graphics, input and JIT/install evidence.
See [Apple platform direction](APPLE_PLATFORMS.md). This migration did not change
runtime behavior or add an untested platform claim.
