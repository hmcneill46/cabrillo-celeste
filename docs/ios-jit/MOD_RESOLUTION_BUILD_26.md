# Dependency compatibility and installation reports — build26

13 September 2026. **[Build26 is physically accepted](BUILD_26_INSTALLS_ACCEPTANCE.md)**
for the recorded fresh Spring installation/reports, ARM64 reflection, gameplay,
resume, Quit and saved-room reload. Two exports cover three processes. Physical
old-to-new updates and cancelled/failed installs were not performed in these
exports; those retain their existing host evidence. Native installer, real-Mono
game, final package and six simulator UI tests plus a landscape check also pass.
All ten private kit files are confirmed uploaded to iCloud.
Source: `experiments/ios-jit/launcher-resolution`, version 0.13.1 (26),
`launcher-resolution-20260913-26`. Build26 is the current accepted fallback;
build24 remains the separate accepted graphics/SJ fallback.
Build25 source, delivered artifacts and runtime stages remain immutable.

## What the owner's build25 feedback establishes

The owner observed EeveeHelper 1.12.5 → 1.12.6 and FrostHelper 1.80.1 → 1.80.2,
with the old ZIPs retained and disabled. Those two current releases are compatible
with Everest 1.6458.0. This behavior is expected. The owner is not certain whether
any other mod changed. A direct regression compiled from original build25 rejects
blocked update selection, forged Apply and a blocked dependency plan without
files or state changing. This does not replace phone diagnostics: no exact build25
export was available in its Results folder during this review. An unsupported
update actually being installed is not established by the screenshot or account.

The screenshot does establish a confusing error and a fresh-resolution limitation.
Its older Everest requirements, including 1.1643.0 and 1.808.0, are satisfied by
1.6458.0 under Everest's numeric version policy. Only two requirements for
1.6531.0 are unsatisfied: indexed ExtendedVariantMode 0.51.0 and MaxHelpingHand
1.40.10. Build25 aggregated every requirement, including the satisfied ones,
without naming the requesting mods. Its current index contained only the latest
candidate; it could keep a compatible local version but could not fetch an earlier
one for a fresh SpringCollab2020 import.

## Build26 changes

Warnings now name each requesting mod/version and only the unsatisfied runtime
requirement. Updates are separated into compatible and app-update-required groups;
blocked rows have no Update action. Update all compatible explicitly excludes
blocked entries. Review puts blockers and “Nothing has been installed” before
proposed downloads, with no Apply action. Coordinator and planner guards remain;
an explicit disabled-target update cannot bypass the runtime requirement either.

The generic resolver can use a bounded catalog of verified earlier releases.
This build contains only metadata, URLs and exact original hashes for:

| Module | Earlier candidate | Minimum Everest |
| --- | --- | --- |
| ExtendedVariantMode | 0.50.5 | 1.6458.0 |
| MaxHelpingHand | 1.40.9 | 1.6418.0 |

Both originals were independently fetched and checked against the retained
original ZIPs, including complete actual required/optional dependency metadata.
A compatible installed copy stays installed. A compatible current indexed release
is preferred. Earlier choices must meet every accumulated minimum and are disclosed
in review. Actual fetched metadata is re-planned before a journaled commit.
These are alternatives, not permanent app-managed pins or mod-specific branding.
They do not provide arbitrary history search, global backtracking, automatic
runtime upgrades or a guarantee that every map works. The existing three runtime
compatibility pins remain separate and unchanged.

Reports use actual committed archive identities and the prior selection. They
list updates as old → new, same-version refreshed archives separately, new installs,
and existing mods enabled/disabled. Explicit updates preserve enabled choices.
Failed/cancelled operations distinguish downloaded-and-verified files kept for retry,
failed/cancelled downloads and those not attempted. Downloads are not called installs.
The report is saved during the attempt and at completion, can be reopened in Mods,
and is included in diagnostics alongside bounded transaction receipts. A process
interruption without a terminal receipt is marked unconfirmed; it does not invent
success or rollback. Any download without a saved result is marked “Result not
recorded” after interruption; it must not claim that the transfer never started.
The next operation recovers the journal before inspecting or
changing the library. The last-attempt report has a 2 MiB cap; older committed
receipts remain available to bounded diagnostics. Report persistence errors are
visible. This version does not add a full browsable installation history.

## Download failure and fallback

A real GameBanana redirect reached an unavailable file cache, then returned HTTP
503 during the fresh install. Existing mod files and choices remained untouched;
verified complete downloads were retained. The error now includes the actual HTTP
status, or announced/received/expected size when a byte-count mismatch occurs.

Everest and Olympus already map a GameBanana file ID to community mirrors. Build26
tries the original URL, then the CelesteMods and Jade mirrors, at most once each.
Only recognized HTTPS numeric GameBanana download URLs are mapped; arbitrary URLs
are not rewritten. Cancellation stops retries. Every transport retains the same
reviewed size, published hash and actual ZIP metadata checks; a successful HTTP
response never bypasses integrity checks. Mirror retries are visible and logged.
[Everest's pinned mirror implementation](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Helpers/ModUpdaterHelper.cs).

A later real failure records seven verified downloads, one failed transfer and
ten unattempted files, with zero applied changes. A direct recheck of the earlier
ExtendedVariantMode returned exact expected bytes, while MaxHelpingHand returned
503: availability is intermittent. For this private test the handoff also includes
the two exact original earlier ZIPs (1,462,341 bytes total), outside the IPA, plus
`DOWNLOAD-HELP.txt`. They are optional manual imports if the servers remain down;
they do not bypass archive validation or change the app's general product flow.
The complete original fresh install and the final replay from verified original
archives are recorded separately; a replay is not a new network-availability proof.

The service still supplies a current per-identity update/graph snapshot, not a
complete historic constraint solver. Exact YAML identities remain the resolver
keys. GameBanana page titles and inferred download filenames are not identities.
[Current index builder](https://github.com/maddie480/RandomBackendStuff/blob/904284430da1e72218696cac6e4d0aebea663d1a/src/main/java/ovh/maddie480/randomstuff/backend/celeste/moddatabase/ModUpdater.java).

## Fresh-profile runtime correction

The real fresh Spring install exposed a separate Mono reflection failure during
FrostHelper startup. Its attribute scanner reached methods whose signatures
reference absent CommunalHelper types. Mono's `GetPseudoCustomAttributesData`
requested a full `MonoMethodInfo`, which resolves the return type even though
the caller only needs flags. The full SJ test set already contains CommunalHelper
and therefore concealed this dependency on an unrelated installed mod.
The original failure, native source, log and exact original ZIPs are preserved.
CommunalHelper is not declared a required dependency of this FrostHelper release;
adding it silently would obscure the runtime problem.

Build26 changes three existing CoreLib methods and adds one private internal-call
binding. Method implementation flags are read through Mono's existing public
`mono_method_get_flags` accessor; method attributes use the existing cheap
attributes accessor. Attribute construction and P/Invoke field values remain
unchanged. Explicit return-type resolution still reports an absent dependency.
The patch preserves every unrelated method, field, resource and assembly reference
and writes deterministic new module identities. Original packs stay read-only.
The host bridge registers the binding before loading game or mod assemblies.
[Mono reflection source](https://github.com/dotnet/runtime/blob/v8.0.28/src/mono/System.Private.CoreLib/src/System/Reflection/RuntimeMethodInfo.Mono.cs),
[native flag accessor](https://github.com/dotnet/runtime/blob/v8.0.28/src/mono/mono/metadata/loader.c).

Thirty independent reflection controls pass on CoreCLR and on patched real Mono:
absent return/parameter/generic types, implementation flags, ordinary attributes,
PreserveSig and complete P/Invoke attributes. Explicit missing return-type errors
still fail correctly. The real fresh Spring selection boots and registers, then
passes normal host gameplay, save, resume and shutdown, including another process.
This proves startup with the actual Spring dependency set; that host route plays
a vanilla map and is **not** a Spring map gameplay claim. Everest still logs
handled optional-integration warnings; no propagated managed/JIT failure occurs.

## Validation and next gate

The native suite covers numeric runtime requirements, only-unsatisfied warnings,
compatible earlier candidates, retained local versions, strict minimums, disabled
updates, actual reports, cancellation/retry, mirror bounds, integrity failures,
transaction crash/recovery and preserving unknown changes. A real original
EeveeHelper/FrostHelper transaction records exactly the owner's two old/new pairs.
Fresh Spring tests use only its original 1.7.10 ZIP plus arbitrary save-sidecar
sentinel data, current captured service metadata and real downloaded helpers.
The real fresh install contains 19 archives: the original Spring ZIP and 18
dependencies (536,304,151 downloaded bytes, mostly audio). The report lists all
18 installed/enabled dependency identities. The separate real update transaction
records exactly EeveeHelper 1.12.5 → 1.12.6 and FrostHelper 1.80.1 → 1.80.2,
with previous archives retained. The fresh Spring fixture also preserves unknown
mod save data. Source-bound
checks include 555 pure controls, 20 engine checks, seven automatic-policy checks,
five blocked-command controls, nine crash recoveries, three preservation checks
and five real HTTPS controls. The import corpus adds 42 controls.

Managed game/Everest, 167 other BCL assemblies, native Mono archives, FNA/Metal,
CelesteIOS, JIT geometry and script are reused unchanged from accepted build24.
Only the CoreLib reflection correction and its native registration extend the
runtime scope. The original Paint intro and complete Lua sequence pass with updated EeveeHelper
and FrostHelper, retained-texture GPU readback, resume and save 0 → 8/readback8.
Both final real-Mono runs pass 30 reflection and 37 support-module/input controls
with Metal API validation enabled. Fresh Spring selection reloads counter3 in
another process, writes6 and reads6. Host checks do not establish ARM64 phone
acceptance. The device needs dependency/report UI tests plus normal
play, Quit and fresh-process save reload. A fresh Spring map test is especially
useful; do not delete an existing working profile to manufacture a fresh install.

The subsequent [phone acceptance](BUILD_26_INSTALLS_ACCEPTANCE.md) and
[runtime assessment](EVEREST_RUNTIME_UPGRADE_ASSESSMENT_2026-09-13.md) complete
those gates. Next, implement an isolated stable Everest1.6531.0 upgrade before
broad catalogue installs. Then follow the existing native loading,
whole-profile backup and touch-editor roadmap. This focused correction does not
move the project toward per-mod branding or waive the private game-IL/FMOD public
release gates. No commits, pushes, messages to third parties or AOT writes occurred.

## Delivered kit and physical test

Use Files → iCloud Drive → Celeste JIT Tests → **0.13.1-build-26**. The ten-file
kit totals **24,954,962 bytes**; the unsigned IPA is **23,468,277 bytes**.
`README-FIRST.txt` gives the normal test and `DOWNLOAD-HELP.txt` explains the
optional original earlier helper ZIPs if a server is unavailable. Keep the app's
existing data when updating LiveContainer slot1; no game reimport is required.
Check dependency/update reports and blocked actions before enabling JIT, then
play, background/resume, Quit and verify progress in another fresh process.
Export each important installation report and both game sessions to Results.

The final IPA SHA256 is
`4b77c9ec39f73b66c2f0e7c2de446ac67067cc6ac56d04698c56f2b9732d0dbd`;
executable/dSYM UUID `25ECF962-06E7-3C73-A339-FAE899A4ED9D`. All 210 source
inputs match the final simulator and device builds. Frozen snapshot receipt:
`693adecf17130a55fc1a6a581ffcea3d1982db33148ca9a034807a2662893c29`.
The ledger is [MOD_RESOLUTION_BUILD_26_EVIDENCE.json](MOD_RESOLUTION_BUILD_26_EVIDENCE.json);
private final records are in `device-evidence/2026-09-13/build-26-ready/handoff`.
The phone checksum manifest covers final kit bytes; the frozen build-time local
manifest's one preceding protocol result is explained in its separate manifest
notes. Current package/protocol gates both bind the final IPA above.

Apple's upload state is confirmed for all ten files. Actual phone download and
execution have not been observed. Build25's cloud installer was removed only
after verifying its exact local copy; build24's fallback and every Results folder
remain. Source, artifacts and runtime stages for delivered24/25 remain unchanged.
