# Cabrillo development handoff

Written 14 September 2026; updated 15 September after build28 phone acceptance
and build31 phone review / build32 first-frame presentation, for a fresh development chat opened in
`/Users/harrymcneill/Projects/Cabrillo`. Read this and [AGENTS.md](AGENTS.md) first.
This file is the entry point; linked reports contain deeper source and evidence.
Recheck current files and owner messages before treating this dated state as live.

## 1. Where to start right now

**Build28 is physically accepted. The browser gate is closed.** The owner
reports all supplied tests visually passed. One complete diagnostics export was
collected from its Results folder at **2026-09-15 07:56:36 UTC**. It contains the
final browser/install/gameplay process and three earlier build28 sessions;
review confirms fresh Cateline installation, reviewed Memorial enabling,
multi-file dismissal, offline behavior, zero-active catalogue quiescence,
26 native/19 graphics checks, exact runtime/modules, saves and complete normal
Quit/native return with a delayed heartbeat. Read
[the acceptance report](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md) and
[ledger](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE_EVIDENCE.json).
No repeat export or successful test is required. The earlier empty-folder check
at14 September23:17:24 UTC is superseded by this evidence.

**Build31 has now been tested on the phone.** One export contains two complete
build31 runs and two older build28 sessions. Both31 runs pass exact runtime/mod
selection, zero-active catalogue quiescence, gameplay/save/Quit and native
heartbeat; one includes12.98s gameplay background/resume. See the
[phone review](docs/ios-jit/BUILD_31_LOADING_REVIEW.md) and its ledger. The owner
reports choppy loading-detail interaction and audible game activity before reveal.
Logs confirm native main-thread steps up to17.29s and a17.7s wait from first game
frame to native window handoff. Preserve31 evidence and sources.

**Build32 is physically accepted.** Read the
[acceptance review](docs/ios-jit/BUILD_32_ACCEPTANCE.md) and its ledger. One export
contains three first-frame handoffs, all on callback1 approximately1.3ms after its
return marker, and a complete SJ room/save/normal Quit/native heartbeat run.
Two older sessions end after background/pause without a Quit record; no new failure
is established. The owner approved the result and requested the next feature.

Build32 is now the accepted fallback,0.16.2 / `launcher-first-frame-20260915-32`.
Preserve28/27/31 and every Results folder. Build29 and30 remain local historical
preparation/intermediate builds. All packaged source lanes remain frozen.
Next is **whole-profile saves/settings backup with staged restore and rollback**,
then the full touch editor. Next unused build is33; recheck before allocation.

The owner explicitly authorized committing/pushing the completed loading work to
GitHub on15 September2026. That publication is in progress; verify Git before
acting. This approval covers completed work through build32 and its acceptance;
future unrelated feature publication still needs owner authorization.

Start in this order:

1. Read this file and `AGENTS.md`, inspect Git status/HEAD and preserve newer work.
2. Build32's export is reviewed. Do not request a duplicate loading/browser suite.
3. Put newly evidenced backend failures ahead of features; none is found here.
4. Implement the saves/settings roadmap: inactive-game-only profile snapshots,
   all unknown persistent sidecars, mod identity manifest, safe staged exact
   restore with retained rollback and a fresh process before restored data runs.
   Game assets/mod ZIPs are excluded from the default portable backup; only
   explicitly owned disposable cache directories may otherwise be excluded.
5. Preserve module identities, game-thread ownership, first-frame handoff and
   zero-active catalogue quiescence. The full native touch editor follows backups.
6. The owner authorized the current loading publication and local next-feature
   development. Check the publication record before another GitHub write.


The owner wants development carried forward autonomously, with concrete tests
and inspectable logs when device help is needed. They dislike unnecessary
confirmation questions. Ask only for missing information that actually changes
the work, or for a specific test/approval that is required. Do not stop at a plan
when implementation is authorized and feasible.

## 2. Project, Git and boundaries

| Item | Current value |
| --- | --- |
| Product | **Cabrillo — Celeste Mod Loader for Apple Platforms** |
| Active repository | `/Users/harrymcneill/Projects/Cabrillo` |
| Public GitHub repository | <https://github.com/hmcneill46/cabrillo-celeste> |
| Default branch / remote | `main` / `origin`, tracking `origin/main` |
| Initial published commit | `bbd86a7680c0a3938fa9715ca27d1dd2e61ce96b` |
| Separate AOT sibling | **Morro**, currently <https://github.com/hmcneill46/celeste-ios> |
| Primary physical target | iPhone 15 Pro Max (`iPhone16,2`), iOS 26.5 |
| Intended next family | iPadOS; declared by the package, not physically accepted |

The owner explicitly authorized the initial commit/push and selected **Public**.
The initial publication is complete. On15 September the owner separately authorized
committing/pushing the completed loading work through build32 and its acceptance.
Continue local next-feature work; future unrelated publication needs authorization. Use `codex/` for
future development branches. Do not rewrite history or force-push.

Keep these directories read-only:

- `/Users/harrymcneill/Projects/Celeste-Everest-JIT-Apple-Platforms` —legacy JIT
  development/archive. Read or copy needed evidence/inputs; never build into,
  switch branches in, clean, reset or edit it.
- `/Users/harrymcneill/Projects/celeste-ios` —actively developed AOT/Morro project.
  Reading its controls/platform work is useful; writes or writable dependencies
  would conflict with ongoing AOT development.
- `/Users/harrymcneill/Projects/Celeste Required Files` —owner's original game and
  SDK inputs. Preserve originals; use new private copies when needed.

`.private`, `.build`, `artifacts`, signing data, device logs and IPAs are ignored.
Never add game binaries/decompiled game source/assets, FMOD SDK contents, pairing
material or private raw logs to the public repository. Keep third-party licenses
and provenance. The public source repository is **not** permission to publish
the current private test IPA: original-IL preparation and FMOD redistribution
remain release gates. No FMOD permission has been established here.

## 3. Current implementation and exact identities

**Build32 is the current physically accepted fallback; preserve28/27/31 too.**
Both use real Everest 1.6531.0; the game and mods run under
Mono 8 JIT. Do not substitute the trimmed AOT game as the dynamic hook target.
The Swift/Objective-C native host remains compiled native code.

| Build 28 item | Expected identity |
| --- | --- |
| Version / build ID | `0.15.0 (28)` / `launcher-catalogue-20260913-28` |
| Immutable source lane | `experiments/ios-jit/launcher-catalogue` |
| Unsigned IPA | `artifacts/cabrillo-build28/CelesteJITEverest-unsigned.ipa` |
| IPA size |23,812,187 bytes |
| IPA SHA256 |`87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2` |
| Executable/dSYM UUID |`98537CA1-09CE-344B-B370-5C27D8F83DC2` |
| Everest source |`d72e94f4b9e62b91cbdea674587ed39d53de9550` |
| Actual version string |`1.6531.0-cjit-d72e94f` |
| RuntimeIdentity SHA256 |`67b284331a08bd3eefb4e3ec5f09ca3b20b9000a4b40f13a0e2e1aa373e63f62` |
| Managed adapter SHA256 |`65b8dca51055627ad8a7da5fb59add7166cf9a39e435b7ac211d9c2df7a4f378` |
| JIT protocol | 1; two 268,435,456-byte arenas; mailbox 96 bytes; response offset 48; error offset 88 |
| Bundled support |`CelesteIOS`1.0.0, ABI 1, required and not user-disableable |
| Content/profile paths |`GameLibrary` and `Profiles/sj-first-play` in the guest's Documents area |

The historical profile name is storage compatibility, not product branding.
Do not rename it or require reimports during UI work. The owner's game, mods,
saves/settings and unknown sidecars should survive app updates.

Build 28 adds native Mods → Browse alongside Installed and Updates: five genuine
server sorts, categories/subcategories, name search, screenshots/details, and
explicit individual file selection. It uses the existing reviewed dependency
installer/reports. The 201 managed assemblies and the native runtime/renderer
are identical to accepted 27. Build 28 does not implement responsive mod-loading
startup, whole-profile backup UI or the full touch layout editor yet.

Key records:

- [Build28 phone acceptance](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md) and
  [physical evidence ledger](docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE_EVIDENCE.json).
- [Build 28 browser report](docs/ios-jit/NATIVE_CATALOGUE_BUILD_28.md) and
  [evidence ledger](docs/ios-jit/NATIVE_CATALOGUE_BUILD_28_EVIDENCE.json).
- [Build 27 phone acceptance](docs/ios-jit/BUILD_27_RUNTIME_ACCEPTANCE.md).
- [Migration report](docs/CABRILLO_MIGRATION.md),
  [migration evidence](docs/CABRILLO_MIGRATION_EVIDENCE.json), and
  [build guide](docs/BUILDING.md).

Older reports and source strings can say “build 23 Results”, “SJ lobby”, no remote,
or no GitHub authorization. Those are historical/debug paths, not instructions
for current normal UI testing. Follow this handoff, the current root instructions
and build 28 phone guide. Preserve delivered 28 bytes; correct display text in a
new version instead of editing the accepted/reproduction target in place.

## 4. Build28 evidence location and collection

Phone Files location:

```text
iCloud Drive → Celeste JIT Tests → 0.15.0-build-28 → Results
```

Exact Mac location:

```text
/Users/harrymcneill/Library/Mobile Documents/com~apple~CloudDocs/Celeste JIT Tests/0.15.0-build-28/Results
```

The parent kit already contains seven files: the unsigned IPA, `README-FIRST.txt`,
`INSTALL.md`, `TEST-IDENTITY.json`, `SHA256SUMS.txt`, third-party notices, and
`celeste-jit-probe-TEMPLATE.js`. Their original upload was confirmed 13 September;
build28 phone execution is now verified by the15 September review. The export
does not measure how the owner downloaded the IPA. Source copies of the
instructions are [PHONE_README.txt](experiments/ios-jit/launcher-catalogue/PHONE_README.txt)
and [INSTALL.md](experiments/ios-jit/launcher-catalogue/INSTALL.md).

Before analysis, copy only relevant new Results files into a new ignored folder,
for example `.private/device-evidence/2026-09-15/build28-review/`. Do not overwrite
old evidence. Hash original and copied bytes, record source path, size, collection
time and SHA256. Require a complete local read and successful JSON parse; a
placeholder, zero-byte file or failed iCloud hydration is not missing/failed
phone execution. Do not clean cloud Results or edit exported files.

The reviewed export is5,370,692 bytes, SHA256
`a07d20eff0f1a9236f7cf42ae6a876b5856e2bd2ce02e20c449271f7945931e9`.
Its unchanged private copy, collection receipt and analysis are in
`.private/device-evidence/2026-09-15/build28-review-075636/`.
The original Results file is preserved. New exports must be collected separately.

Expected exports are `CelesteJIT-<launch UUID>.diagnostics.json`, sometimes with
Files-app numeric suffixes. The **contents identify the session**, not the suffix
or the containing build folder. Separate browser/install and post-Quit exports
are useful for future tests, but build28's single export retained both and is
sufficient. Multiple exports may overlap or represent two snapshots of the same
process. A recovery launch may export an earlier played/crashed process inside
`previous_sessions`; examine that history before asking for another test.

If Results is empty, do not request a reinstall or create another identical IPA.
The existing kit is ready. If the owner needs the steps again, use section 5 and
the supplied phone guide. No new standalone JIT script is required for28.

## 5. Physical test contract

**Installation/run arrangement is fixed:** game in LiveContainer slot1, StikDebug
in LiveContainer slot2. Update the existing game entry while preserving data.
Keep **Launch with JIT OFF**, its saved JIT script blank, and **Fix File Picker ON**.
The latter fixed a real case where a locally downloaded ZIP could not be selected.
Close the previous game process and open28; do not delete/recreate the data container.
Capture actual LiveContainer/StikDebug versions when supplied; do not infer them.

| Area | Requested phone observation and corresponding evidence |
| --- | --- |
| Native browse, without JIT | Scroll/load another page, try Newest/Most downloaded/Most liked, Maps → Standalone, and portrait/landscape. Cards, menus, images and text should fit and respond. Use owner feedback/screenshots for visual facts; diagnostics cannot prove every alignment. |
| Exact reuse | Search Memorial Helper, including its valid Tools-category page. Review an existing exact file without downloading a duplicate. A disabled exact match should present enabling for review. Do not enable/replace unreviewed files. |
| Small install/report | Search Cateline; original 0.1.0 is about 17 KB. If absent, review/download/install and verify the actual installed/enabled report. If already installed, the supplied guide explicitly expects reuse. Record which path really occurred; reuse is not fresh-download evidence. |
| Multiple files | Open a multi-file page such as SpringCollab2020, inspect separate map/audio/extra choices and their sizes, select explicitly and review. Dismissing review must not install anything. No large download is required for this check. |
| Offline, optional | Previously visited data remains with an honest offline state; unvisited search offers Retry. Installed-profile play is independent of catalogue availability. This was optional in the delivered guide; do not invent a compulsory replay if omitted. |
| Fresh JIT | Enable via LiveContainer2 with this running process's inline PID-specific request. StikDebug completes and detaches; return to the same process and pass native memory/execution checks. |
| Play after browsing | Run the existing profile, enter an ordinary map, check controls/audio/progression/saves. Verify Cateline's appearance if enabled. The new browser must be quiescent before managed preparation. |
| Quit/export | In-map Save and Quit returns to the game menu; normal main-menu Quit returns to SwiftUI. Export after native return, ideally after five seconds so the delayed heartbeat is present. A separate browser/install snapshot is useful; the reviewed single28 export already retains both. |

Check actual mod registration and committed transactions, not just a UI “PASS”.
Do not require a specific collaboration or exactly56 module identities: the
owner can change the mod set, and module callbacks can be duplicated. A genuine
new small install is useful if both documented examples were already installed,
but do not delete working mods to force it. Mark that route NOT OBSERVED and ask
for a targeted additional install only if necessary to close the intended gate.

Build 28's guide does not require a fresh second gameplay run or a new 30-second
background test. Report either if present; carry accepted 27's separate coverage
if not. Do not silently enlarge the requested test. A new launch can itself
prove preservation of an earlier save when slot/profile evidence matches.
The current28 session saves slot0 with sidecar194→209→209; its later fresh-process
209 reload is unobserved. An earlier28 session saves slot3 with0→178→178. The old27
latest980 reload is also unobserved and must not be imposed on different slots or
mod selections. Compare actual exports and owner changes before expecting a counter.

**One game per process remains intentional.** After Quit, relaunch before another
game or mod configuration session and obtain fresh JIT. Do not reuse an old
PID/address script. The normal product has no permanent Finish button; old debug
controls and the game main-menu Quit are different paths.

## 6. How to analyze the diagnostics correctly

The authoritative format is implemented in
`experiments/ios-jit/launcher-catalogue/src/main.m` (`CJLog.exportDiagnostics`)
and `src/CJEventStore.m`. Export schema2 has:

- `kind: celeste-jit-launcher-diagnostics`, top-level `session`, `build`, `device`;
- `current_events`, `retention`, `native_console_tail`, `mod_installations`;
- up to three `previous_sessions`, each with `events`, journal metadata, its
  console tail, and sometimes `previous_journal_part.events`;
- owner-entered debugger/container versions, which can legitimately be absent.

Each ordinary event has `event`, `session`, `sequence`, `time_unix`,
`uptime_seconds` and `fields`. For each process, obtain identity from its own
`native_launch.fields.build/device/process`; the top-level export identifies
only the current exporting process. Never label older failures as build 28 merely
because they appear in a build 28 export.

A browser-only process legitimately has no JIT/game checks. Apply the game gates
to a process that actually attempted gameplay, and retain the native-only result
as its own valid part of the review.

Review procedure:

1. Enumerate every process across every export and previous journal part. Group
   by session UUID, associate launch build/device/PID, and deduplicate repeated
   snapshots by sequence plus matching event content. Synthetic counter records
   may have no sequence; preserve their timestamp/fields and provenance. If two
   records conflict, retain both and investigate instead of dropping one.
2. Match build 28's identity to section 3 and `TEST-IDENTITY.json`. Read actual
   `runtime_identity_pass`, `everest_selection_pass`,
   `everest_selection_module_verified` and `everest_module_registered` messages.
   `BuildInfo` alone does not prove that the expected managed runtime executed.
   Frozen28 maps `runtime_identity_pass` through `CJGraphicsMark` to
   `graphics_fixture_message`; the full version/source/manifest message is still
   retained. Account for that mapping rather than requiring the original name.
   `mono_reflection_flags_registered` must report ABI 1. Map identities by exact
   module name/version; distinguish archive count from callback count.
3. Review `mod_installations` and persisted reports/journals against the before/
   after enabled library and actual next-game registration. Successful commits,
   verified cached ZIPs, failures, cancellation, unattempted and enable-only work
   are different results. `applicationState: applied` and actual `changes` prove
   applied changes; downloaded bytes alone do not. `inProgress` read back after
   interruption must not become success. Sources: `native/InstallReport.swift`,
   `InstallJournal.swift`, `DependencyInstaller.swift` and `ModLibrary.swift`.
4. Require `catalogue_quiesced` **before** `graphics_test_start`/managed preparation,
   with zero active catalogue requests. The provider must be suspended, with
   rows/images cleared and no new request launched during the game. Its payload
   is the provider diagnostics dictionary from `prepareForGameWithCompletion`.
   In delivered28 it has top-level `activeRequests`/`suspendedForGame` and nested
   `counts`/`lastFailure`. Inspect the actual schema for later versions.
5. Check native `check_pass`/`check_fail`, JIT protocol/arena mapping and debugger
   detachment. Accepted 27 recorded 26 native checks, two 256 MiB regions with 16,384
   RX pages each and no debugger attached during generated code execution.
   Check individual names/results; absence in a clipped excerpt is not a PASS.
6. Require successful `graphics_start_result`, `graphics_first_frame_returned`,
   actual game/map activity, correct expected registrations and successful
   graphics/readback checks. The prior accepted game suite had 19 graphics checks;
   interpret the names and active profile rather than hard-coding all mod counts.
   Read the logged map SID/room, not an assumption from the test's title.
7. Inspect sampled and final runtime counters: `jit_failed`, `jit_unowned`,
   `managed_errors`, `patch_rejections` should remain zero. Examine explicit
   `mono_jit_failed`, managed exception/details, game error and loader events
   even if later UI looks successful. A caught Everest exception can still expose
   a real runtime failure. Record code reservation/budget and process footprint.
8. Verify saves/sidecars using `game_save_pass`, `everest_mod_save_pass`, shutdown
   records and later-load evidence where present. Same-process readback is not
   fresh-process persistence. The prior 27 route was SJ
   `StrawberryJam2021/1-Beginner/Ceph` (Cassette Cliffs), room4→room5, then a
   fresh room5 reload; counters928→969→980. It was not a Spring/Paint phone run.
9. Verify **all eight shutdown stages** and native return:
   `graphics_bridge_pass` with `shutdown_stage: 8`, successful main-thread detach,
   `graphics_result_presented.passed: true`, and ideally `graphics_post_run_alive`
   emitted five seconds later. Check quit reason/origin. `game_checks_pass` alone
   does not establish a completed native return. A snapshot exported before the
   delayed event is missing that observation, not proof of a hang.
10. Review retention/error fields. The console export is a bounded tail; journal
    excerpts may be clipped; routine events are sampled with counters. Do not
    interpret sequence gaps as dropped execution or count just retained samples
    as the total JIT work. `storage_error`, clipping, partial JSONL tails and
    overflow limit what can be concluded.

Current allocation evidence is `retention.allocation_trace`: base64 of 24-byte
little-endian `<QQQ>` rows `(address, requested_bytes, total_reserved_bytes)`.
Verify decoded length, SHA256, record count and `overflow_records`; use the exact
session's prepared arena/allocation data for coverage claims. Earlier-session
exports do not automatically contain that complete trace. On disk it is
`session-<UUID>.jsonl.allocations.bin`; raw rotated journals may also have
`.previouspart`. Do not claim complete allocation proof from a bounded excerpt.

Shutdown stage names, in order: Finishing pending saves; Verifying saved data;
Ending the game loop; Releasing textures; Closing game and mod hooks; Closing
platform services; Removing host hooks; Complete. `Stop` 3 keeps draining pending
saves, 4 yields, 1/2 represent complete/incomplete. The independent shutdown
heartbeat observes state; it never kills the process. There is no intentional
gameplay timeout. Do not add one to mask a hang.

Record each gate as PASS, FAIL or NOT OBSERVED, with session IDs, event evidence
and limitations. Keep raw data private. Publishable summaries may reference
hashes and sanitized observations, not raw personal/device logs. Write a new
`docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md` plus an evidence ledger **only when
the evidence warrants it**, then update current `AGENTS.md`, this handoff and
the roadmap. Keep original delivery/migration receipts as dated history. If a
gate is incomplete, ask only for the specific missing observation/log.

### Crashes, hangs and direct collection

On a crash, have the owner reopen and export before another game so the failed
process is retained in history. A native crash/Jetsam report or fuller console
may be needed to distinguish a native fault, memory termination, loader failure
or incomplete shutdown; do not diagnose a leak from a high footprint alone.
Use exact matching UUID symbols in `artifacts/cabrillo-build28/`.

The owner authorizes relevant USB collection and useful debugger attachment.
**Never attach concurrently with StikDebug.** Default handoff/return is iCloud;
do not assume the phone is currently connected. If USB is available, identify
the owner's `iPhone16,2`, the actual signed LiveContainer1 bundle and current
guest data UUID; another connected phone or stale UUID is not the target.

[The scoped collector](experiments/ios-jit/device-tools/pull_diagnostics.py) and
[its guide](experiments/ios-jit/device-tools/README.md) describe House Arrest
`VendDocuments`/AFC using `pymobiledevice3==11.12.4`. Set up its environment and
private pairing/inventory inside Cabrillo; the guide's old environment paths
were not imported as runnable dependencies. It reads only the selected guest's
Diagnostics folder, performs stable repeated reads, preserves a partial final
line and does not write to/launch the phone. Its default chooses the latest
process, which can be merely the recovery/export process: choose `--session`
explicitly when appropriate. It collects JSONL and console, not every rotated
part/allocation file; retrieve any additional needed artifact explicitly within
the same authorized scope. Preserve **Export diagnostics** permanently.

## 7. Building in Cabrillo

Use **Xcode 26.6 / build 17F113** at
`/Applications/Xcode-26.6.app/Contents/Developer`, with iPhoneOS SDK 26.5.
Migration was compiled on an Intel Mac. The current app targets arm64/iOS 26.0
minimum and declares iPhone+iPad; SDK declarations are not device acceptance.
Use the developer path per command rather than changing the owner's global
Xcode selection. Root tools use Python3's standard library.

The local folder contains everything needed for the **current launcher rebuild**:

- Public source/docs/vendor files, including the current lane, previous JIT
  patches/tests and the small shared control/artwork subset. No AOT app/project.
- `.private/migration/build28-replay.json` and `inputs.json`: exact dependency,
  package, source and provenance locks; 455 build inputs, 98,059,597 bytes.
- `.private/inputs`: 16 accepted native archives and matching Mono/SDL headers.
- `.private/resources/build28`: 201 managed assemblies plus frozen resources.
- `.private/test-inputs`: 11 dated-service/synthetic-ZIP fixtures, 308,734 bytes.

A GitHub clone does **not** have these private inputs. Do not pretend missing game
IL/FMOD can be downloaded from the public repository. Back up `.private` separately.
The one-time `tools/import_legacy.py` is not a normal build step and must not
overwrite this working project.

From the Cabrillo root, using new work/output names:

```sh
python3 tools/audit_repository.py
python3 tools/build.py --reproduce-build28 \
  --work .build/another-reproduction \
  --output artifacts/another-reproduction
python3 tools/verify_reproduction.py artifacts/another-reproduction
python3 tools/check_catalogue.py --output .build/another-catalogue-check
```

Do not rerun expensive passing checks merely to reread this handoff. The verified
reproduction already exists in `artifacts/cabrillo-build28/`, with receipts/logs
and matching dSYM. It compiled 58 source inputs, generated tables/icons, and
produced the **exact full build 28 IPA hash**, while macOS denied access to all
three legacy/AOT/original-input directories. All 48 default native catalogue/
transaction tests passed from fresh local source and vendor compilation.
`--live` adds ten service/real-install checks but was not repeated during migration;
the original build 28 suite had 58 checks and separate host/simulator gates.

**Important: `tools/build.py` is a locked build 28 reproduction recipe, not a
generic new-release builder.** It requires the exact historical source and
reuses accepted runtime/managed libraries. It retains original ZIP/resource
metadata and permits bounded relinking for the observed Apple linker GOT-order
variation. Only after every non-UUID executable byte matches the locked hash
does it restore 16 historical UUID bytes and synchronize the fresh dSYM. The
full executable and IPA must then match. A changed code byte is rejected.
Actual new compilation provenance is stored outside the historical BuildInfo.
See [BUILDING.md](docs/BUILDING.md); do not use that UUID/metadata restoration for
changed code or claim all Mono/SDK/managed dependencies were rebuilt from upstream.

### Current independent build lanes

- **29:** `launcher-startup`,0.15.1; local preparation only. Its builder/verifier
  and all recorded artifacts remain frozen. It reuses all201 managed DLLs.
- **30:** `launcher-loading`,0.16.0; frozen local loading intermediate. Managed
  source, SDK/upstream pins and `tools/build_loading_managed.py` live here. The
  validated managed receipt is `.build/loading-managed30-d/receipt.json`.
- **31:** `launcher-loading-release`,0.16.1; corrected native delivery lane.
  `ManagedPayload.json` pins that exact managed receipt/resources. Build with
  `tools/build_loading_release.py`; verify with `tools/verify_loading_release.py`.
  See the report/ledger at the top for final package, delivery and phone state.

The managed capsule is `.private/loading-inputs`:19,618 files/2,413,428,206 bytes,
including the source/submodule pins, offline packages, SDK8.0.422/9.0.300,
private original/prepared IL and host inputs. The build runs only in new Cabrillo
stages, with the old checkouts inaccessible. Extra real-game test fixtures are
separately pinned in `.private/loading-host-inputs` and `.private/loading-sj-inputs`.
They are not public source files or dependencies writable by a build.

The next unused number is **32**; recheck owner messages/current files before
allocating it. New implementation requires a new identity and work/output stages.
Use the current independent root tools, preserve all frozen31/30/29/28 inputs,
and keep the existing guest bundle/data paths. Historical experiment builders
can be read for context; they are not guaranteed runnable current entry points.
Never make either old checkout a writable dependency.

## 8. Architecture and regression boundaries

Current native source is `launcher-loading-release`; managed/loading source is
`launcher-loading`. The accepted28 source below is the preserved reference, not
the place for implementation edits.

| Responsibility | Source to inspect |
| --- | --- |
| Native app/lifecycle/JIT/session handoff | `launcher-catalogue/src/main.m`, `CJGraphicsManaged.m`, `CJGraphicsPlatform.m`, `CJSession.*` |
| SwiftUI launcher/browser | `native/LauncherUI.swift`, `CatalogueUI.swift` |
| Catalogue contracts/network/cache | `CatalogueModels.swift`, `CatalogueProvider.swift` |
| ZIP library and dependency transactions | `ModLibrary.swift`, `DependencyPlan.swift`, `DependencyInstaller.swift`, `InstallJournal.swift`, `InstallReport.swift`, `ModUpdates.swift` |
| Managed game/boot/frame/storage | `managed/GameEntry.cs`, `Platform.cs`, `ContentLibrary.cs`, `ContentStore.cs`, `ModSelection.cs` |
| Game-side iOS integration | `support-module/IOSPlatformModule.cs`, `InputSourcePolicy.cs` |
| Native code mappings/protocol | `CJHookCodeArena.c`, `CJHookProtocol.h`, `VMRange*`, `scripts/celeste-jit-probe.js` |
| Runtime identity/pins | `RuntimeIdentity.json`, generated native/managed identity files, `CompatibilityDownloads.json`, `RuntimeCompatibleReleases.json` |

Paths in this table are under `experiments/ios-jit/launcher-catalogue/`.
These are reference inputs for a new lane, not permission to mutate frozen 28.

Preserve these established contracts:

- Native host owns JIT, files, network, lifecycle and presentation. The required
  support module owns game-side Quit and input prompts; bootstrap must work
  before user mods/support registration. Do not import .NET10 Apple bindings
  or trimmed AOT game assemblies into this Mono 8 host.
- Keep accepted Mono allocation/memory fixes, MonoMod literal-field handling,
  build 24 FNA/Metal retained-backbuffer/MSAA/bounds fixes, and build 26 CoreLib
  reflection ABI 1 correction. Their changes solved actual phone/host failures;
  reverting them can revive seemingly unrelated mod errors.
- Build 27 rebuilt actual Everest 1.6531.0 and patched game/hooks. Do not implement
  another runtime upgrade by editing version strings. Verify actual registration.
- Exact YAML module names, file IDs and verified archive metadata govern installs.
  A GameBanana title/category is not a module identity. Memorial Helper is a
  valid indexed mod on a Tools page. Multi-file pages require an explicit choice.
- Three compatibility-pinned releases are GravityHelper 1.2.28, CollabUtils2
  1.13.4 and FemtoHelper 1.15.22. They differ from optional older runtime-compatible
  alternatives in `RuntimeCompatibleReleases.json`. Preserve compatible locals;
  never relax a minimum version. ExtendedVariantMode 0.51.0/MaxHelpingHand 1.40.10
  are supported by runtime 27/28; blocking in older 26 was correct then.
- Updates retain the prior ZIP disabled and preserve an updated mod's disabled
  choice. Dependency resolution can enable a reviewed existing match. Recover
  journals before scans/play; never overwrite unknown changed files/state.
  Reports must describe committed old/new versions and actual enabled changes.
- Update checks are explicit plus optional idle Updates-page checks after 24 h,
  with 1 h automatic failure backoff. Cache eligibility binds actual runtime/pins
  and is re-evaluated offline after policy changes. No automatic mod installs.
- Catalogue work is bounded: four transfers, 4 MiB responses, 200 rows, 24 MiB metadata
  cache, 32 MiB image disk cache, 16 MiB/32 decoded images, two 800 px decodes, 350 ms search
  debounce. Visible images add memory beyond the LRU. Suspend/clear before play.
- Olympus-style name search returns up to 20 relevance matches across categories;
  the paged list supports real sorts/filtering. Do not fake global sorting of
  search matches. Services may use `GameBananaType=Obsolete`; trust verified
  PageURL/file identity. Recheck live contracts when changing provider behavior.
- Retain full arbitrary-mod save/settings/sidecar data. The vanilla strict save
  serializer/allowlist is not a valid general backup policy. Current gameplay
  diagnostics checking standard saves do not define all mod storage semantics.

## 9. Roadmap after the accepted browser gate

### First: responsive real loading, including backend work

Read [the current roadmap](docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md),
especially “Real SwiftUI startup progress”. Desktop Everest uses a separate
splash process and named pipe. Its real mod counts/stages can inform the native
bridge; leave the desktop subprocess disabled on iOS. Revalidate the call sites
against the **current d72e94f runtime**, not only the older research snapshot.

The known blockage is concrete: `main.m` does runtime/content preparation on an
attached worker, then calls `startGraphics` on UIKit's main thread.
`CJGraphicsCall("Start")` requires that main thread; `GameEntry.Start` constructs
`new JitGame()` and calls `CJITBeginExternalLoop`, which synchronously performs
substantial Everest/game startup. Merely queuing SwiftUI progress on the same
blocked thread will not produce a responsive loading screen.

Profile/instrument real phases first. Design resumable/cooperative stages or
move only proven thread-independent work to a correctly attached worker. Preserve
UIKit/window/Metal and thread-affine game/mod calls. Do not move all startup to
an arbitrary background thread, pump a nested UIKit run loop, or fake progress.
Count scanned/loaded/skipped/failed archives/modules where measurable; use an
indeterminate state elsewhere. Mod count is not a percentage of elapsed work.
Keep smooth native presentation, current-stage text, elapsed time and bounded
diagnostics, with a reliable first-frame/window handoff. Respect backgrounding
before presentation and honest cancellation once initialization has begun.

Acceptance should cover real cold/warm loads, multiple-module archives and failed
loads, UI responsiveness, thread affinity, gameplay/save/Quit and preserved
catalogue quiescence. Build 27's observed Run→first-frame 74.71/26.52s and sampled
4.05/3.72 GB footprints justify this work; they are not controlled cold/warm
benchmarks, a leak diagnosis or older-device performance evidence.

### Next: whole-profile saves/settings backup and restore

SwiftUI/Files owns the manager. Default small backups preserve saves, settings
and unknown persistent sidecars plus mod identity/schema manifests, usually
excluding game content and mod ZIPs. Optional full archives can include mods.
Back up while inactive; restore through staging/new profile and rollback,
validate containment and require a fresh process. Never execute a mod to preview
a backup or discard unknown data because vanilla XML validation rejects it.
Automatic cloud save merging is later work.

### Then: complete native touch editor and presentation polish

Port the full D3 interaction feature set from the read-only AOT reference:
fixed/floating movement, four split orientations, duplicate/swap, sliding,
circle/rectangle/shoulder grab, Hold/Invert/Toggle and source-aware behavior,
opacity/visibility, haptics, move/resize, mirror, undo/reset/delete, import/export,
and up to four extras including Crouch Dash/Quick Restart. Use a SwiftUI draft
canvas/inspector with Save/Cancel and normalized geometry shared with hit tests.
Preserve stable simultaneous touch transport; individual SwiftUI taps cannot
replace held/sliding/multitouch controls. Match glyph centering and hit areas.
Existing optional performance metrics are useful, but callback timings are not
GPU timings or an automatically valid 1%-low metric.

### Platforms and distribution

The owner wants iPad support: make new native UI adapt to tablet sizes, safe areas,
resizing and pointer/keyboard/controller input now; verify JIT and gameplay on
real iPad hardware later. macOS is a plausible product after the existing x64
host tests; Apple-silicon packaging/runtime still needs work. tvOS/visionOS need
separate JIT/install, graphics and input investigation. See
[Apple platform direction](docs/APPLE_PLATFORMS.md). No watchOS target is planned.

Public direction is a small reusable launcher, owner-imported original Celeste
files and arbitrary compatible mods, with no end-user Xcode. Current private
prepared game IL and FMOD still prevent treating the test IPA as a public release.
Do not tell users desktop FMOD binaries can serve as the iOS library or infer
permission from another project's reported agreement.

## 10. New test kits and maintaining this handoff

Default to iCloud:

```text
iCloud Drive/Celeste JIT Tests/<version>-build-<number>/
```

The owner allows up to 1 GB total. Include a clearly named unsigned IPA, short
phone README, exact build/runtime/hash identity, checksums and any genuinely
needed fixtures/script instructions. Preserve all existing user data and every
Results folder. Verify bytes locally and on the iCloud copy; distinguish local
placement, confirmed upload, actual phone download and accepted phone execution.
Past iCloud account errors were sometimes misleading: owner download success is
valid evidence of download; local placement alone is not upload proof.

Superseded large cloud installers may be removed only after their exact local
copies are verified. Keep the physically accepted fallback. Direct USB copying
to the owner's LocalSend Documents under the same versioned folder is a fallback,
not the default, and needs verified target/container access. Do not copy to an
unrelated connected device. Keep symbols outside the IPA: an early in-app dSYM
caused LiveContainer “Failed to Sign .../DWARF/...” errors.

Before a new handoff, run the checks appropriate to the actual change. Preserve
exact source/runtime/package/symbol identities and mark host/simulator/phone
results separately. Simulator orientation screenshots must settle after rotation;
`XCUIScreen.main.screenshot()` avoids the previously cropped app-frame capture.
Keep simulator fixture transport out of the device binary. Do not rebuild old
accepted runtime or renderer stages in place just to satisfy copied scripts.

Update this handoff, root `AGENTS.md` and roadmap when actual evidence changes
the next step. Keep the public file inventory current, with a reason and SHA256
for new/changed files; preserve `import_sha256` as historical extraction identity.
The inventory describes itself without a recursive self-hash. The repository
audit still verifies frozen 28's 228 source inputs and 49 native/vendor inputs;
new code should live outside those frozen inputs, with its own checks.

Do not commit/push these handoff edits unless the owner authorizes it. They are
available immediately to a new chat opened in this **local Cabrillo folder**.
