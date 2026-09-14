# Celeste Everest JIT Apple-platform development

## Scope and owner instructions

- This checkout is the JIT investigation/development lane. Start with
  [the feasibility audit](docs/ios-jit/FEASIBILITY_AUDIT.md) and
  [its evidence ledger](docs/ios-jit/EVIDENCE.json).
- Preserve the working vanilla iOS AOT product. Keep static-AOT Everest and
  Strawberry Jam work independent from runtime JIT implementation.
- `/Users/harrymcneill/Projects/celeste-ios` is an actively developed AOT checkout.
  Read it when useful, but do not edit, build into, reset, switch branches in,
  clean, or otherwise mutate it. Do not use its caches or generated outputs as
  writable dependencies.
- **Do not commit, push, publish, create a remote repository, or write to GitHub
  without the owner's explicit approval.** Local inspection, isolated edits,
  branches and experiments are authorized. Finish reviewable work before asking
  for approval; do not ask again for routine reversible steps.
- User-owned inputs are in `/Users/harrymcneill/Projects/Celeste Required Files`.
  Read/copy as needed; preserve originals. Never track or publish game binaries,
  decompiled game code, assets, FMOD SDK contents, signing identities,
  provisioning profiles, pairing files or private logs.
- Primary physical target: **iPhone 15 Pro Max, iOS 26.5**. Intended install/run
  path: **unsigned IPA → LiveContainer → StikDebug JIT**. Exact container and
  debugger versions must be captured with device evidence.
- Owner clarified the arrangement: probe/game in **LiveContainer slot 1**,
  StikDebug already running in **LiveContainer slot 2**. Preserve this setup.
  The native M1 probe forwards its PID-specific request through
  `livecontainer2://open-url`; it deliberately starts with Launch with JIT OFF.
  See [the physical test guide](experiments/ios-jit/native-probe/INSTALL.md).
- The owner is willing to perform physical-device tests and answer questions.
  Ask when a concrete test is ready; provide exact steps and inspectable logs.
  Do not request a vague “try it” or infer a device PASS from host compilation.
- The owner authorizes fetching relevant test logs and, when useful, attaching
  a debugger to the test process. Never attach concurrently with StikDebug.
- Prefer direct USB collection of automatically saved canary logs when the
  phone is connected and accessible; the owner need not tap Export first.
  **Preserve Export diagnostics** as the owner's explicit iCloud/share fallback.
- **Default future handoffs to iCloud**, as the owner requested during build 13.
  Direct phone transfer remains an available fallback. When using it, copy
  files onto the owner's **iPhone 15 Pro Max**, into LocalSend's Documents under
  `Celeste JIT Tests/<version>-build-<number>/`. Include the unsigned IPA and a
  short README; keep previous phone versions. Verify the transfer and state the exact
  Files-app location. Match the device by model/identifier: another connected
  iPhone is not the target. If connection/container access fails, report it
  honestly and retain the local kit. Do not collect unrelated phone files.
- The owner authorizes iCloud Drive handoffs up to **1 GB total**
  (updated 11 September 2026; supersedes the initial 50 MB limit). Use `iCloud Drive/Celeste JIT Tests/<version>-build-<number>/`, include
  a short phone README and clearly versioned folder. The owner explicitly
  authorizes removal of **superseded large test installers from iCloud** to save
  space. Verify and retain their exact local artifact copies first; preserve
  Results, small instructions/receipts and historical local snapshots. Do not
  remove unrelated iCloud files. Verify copied bytes and distinguish local placement, confirmed
  cloud upload, and actual phone download; do not claim the latter unobserved.

## Product reuse and release direction (11 September 2026)

- Read [iOS reuse and distribution](docs/ios-jit/IOS_REUSE_AND_DISTRIBUTION_2026-09-11.md).
  Reuse the proven controls, presentation, lifecycle and storage interaction,
  adapting native services to this Mono 8 host. Do not import .NET 10 Apple
  managed bindings or silently use the trimmed AOT game as a dynamic hook target.
- Public target: reusable launcher IPA, owner-imported original game files,
  on-device preparation/cache, mod ZIPs and separate profiles; no end-user Xcode.
  The private reconstructed game canary is not the final original-IL importer.
- Preserve complete mod save/settings/sidecar data; the vanilla strict serializer
  and file allowlist are not the JIT product's arbitrary-mod save contract.
- FMOD redistribution permission is unresolved. Owner may contact Firelight;
  no message has been sent. Desktop FMOD is not an iOS binary, and the present
  iOS SDK archives need build-time linking. Do not promise runtime SDK import
  or infer this project's permission from PortMaster's reported arrangement.

## Latest physical acceptance and active work

- **Current delivered phone candidate: build28 native catalogue**, authorized
  after accepted27. Isolated `experiments/ios-jit/launcher-catalogue`, 0.15.0(28),
  `launcher-catalogue-20260913-28`. Read [the browser record](docs/ios-jit/NATIVE_CATALOGUE_BUILD_28.md)
  and evidence. All local gates and all seven iCloud kit files pass, at
  `Celeste JIT Tests/0.15.0-build-28`. Phone execution/acceptance is unobserved.
  IPA 23,812,187 bytes; SHA256
  `87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2`;
  executable/dSYM UUID `98537CA1-09CE-344B-B370-5C27D8F83DC2`. All 228 source
  inputs match the simulator and frozen snapshot. Keep delivered28 immutable;
  corrections require a new identity. Preserve accepted27 and all Results.
  The complete 201 managed assemblies, runtime, renderer, protocol and user paths
  match accepted27. Builders verify accepted inputs read-only. No game/mod reimport.
  Native Browse supports five actual server sorts, categories/subcategories,
  20-match all-category name search, screenshots/details and individual files.
  Join file IDs to the verified index, never infer module names from page titles.
  Tool pages can contain valid mods (Memorial Helper); decide by exact indexed
  file/metadata, not page category. Multiple files remain explicit choices.
  Reuse exact installed ZIPs; review enabling disabled matches. Existing runtime,
  pin, dependency, recovery and result-report contracts still apply. Previous or
  unindexed archives remain manual imports. Cache/transfer/decode budgets are
  recorded in the report. Suspend catalogue requests and clear thumbnails before
  managed preparation; require `catalogue_quiesced` with zero active requests in
  phone evidence. Offline catalogue failure must not block installed-profile play.
  Real HTTP installs of memorialHelper1.0.4 and Cateline0.1.0, actual host game/
  save/resume/Quit, 58 catalogue checks, installer recovery, both native UI suites,
  simulator smoke and package/protocol checks pass. External simulator fixtures
  are absent from the device binary. Phone gate: browser/layout, exact reuse,
  small Cateline download/report, multi-file review, optional offline behavior,
  fresh JIT and usual gameplay/Quit; export separate browser/install and game
  sessions. Host tests are not phone/all-mod acceptance. After acceptance:
  responsive real loading, then complete-profile backup/restore and full-parity
  SwiftUI touch editor. Public preparation/FMOD gates remain. No commits/pushes/
  AOT writes. Frozen source and final handoff records are in private build-28-ready.

- **Current physically accepted fallback: build27**: `experiments/ios-jit/launcher-runtime`,
  0.14.0(27), `launcher-runtime-20260913-27`; read
  [the report](docs/ios-jit/EVEREST_RUNTIME_BUILD_27.md) and its evidence ledger.
  Rebuilt pinned Everest1.6531.0/d72e94f and original game IL/hooks in isolated
  launcher-runtime* stages. Four managed replacements; preserve accepted26
  CoreLib and accepted24 FNA/renderer/MonoMod/CelesteIOS plus accepted19 Mono.
  RuntimeIdentity.json generates native/managed expectations and version patch;
  require actual managed registration. Schema2 update caches bind built-ins/pins
  and re-evaluate from verified cached metadata after policy changes, including
  offline, opt-out and backoff. No automatic mod installation.
  Current ExtendedVariantMode0.51.0/MaxHelpingHand1.40.10 are eligible here;
  prior build26 blocking remains correct for its older runtime. Keep installed
  compatible versions until reviewed updates, older originals disabled/retained,
  all profiles/saves/Export and one game per process. Physical27 acceptance is
  recorded in [the phone review](docs/ios-jit/BUILD_27_RUNTIME_ACCEPTANCE.md).
  Preserve accepted26/24 source and every Results folder. Subsequent catalogue,
  loading, backups/editor and public preparation/FMOD gates retain their order.

- Simulator acceptance must use settled orientation captures. XCUIScreen.main
  avoids app-frame cropping, but capture after the rotation animation finishes.
  Before a copied blocked/fresh-review runner, move only previous simulator
  fixture result folders into private evidence; its fixed cleanup basenames can
  otherwise collide with results retained from earlier builds. Restore the
  current test fixture after an interrupted runner. This is not phone data.

- **Latest phone evidence:** two exact exports cover three build27 processes,
  one installation/native-check session and two games; two older26 processes
  are separate history. ExtendedVariantMode0.50.5→0.51.0 and
  MaxHelpingHand1.40.9→1.40.10 download/verify/commit (1,463,412 bytes), remain
  enabled and report accurately; old ZIPs remain disabled/retained. Actual
  Everest1.6531.0/source/manifest and all56 selected/built-in identities match.
  53 enabled ZIPs/60 installed; JackalHelper's three callbacks are one identity.
  Phone routes are SJ Cassette Cliffs room4→room5, then room5 reload, not Spring.
  Sidecar928→969→980, slot1, 33.12s background/resume, all26 native/19 graphics
  checks per game, stage8/native return and delayed heartbeats pass. Final980
  fresh-process reload is not claimed. Runtime error counters are zero. The
  update plan uses a verified cached index; fresh live refresh is not proven.
  Build27 is the current accepted fallback; keep26/24 and all Results.
  The approved next increment is delivered as build28 above: neutral SwiftUI
  catalogue/search/details/file choice using existing reviewed installs/reports. Revalidate service contracts, bound
  page/image caches and preserve offline launch. Then responsive real startup,
  whole-profile backup/restore, full-parity touch editor; public preparation and
  FMOD remain release gates. Observed Run→first-frame74.71/26.52s and sampled
  footprints4.05/3.72GB inform loading/cache work, not a leak diagnosis or a
  cold/warm/older-device benchmark. No repeat successful test is needed now.

- Build27 final local gates and iCloud upload pass. Seven kit files at
  `Celeste JIT Tests/0.14.0-build-27`; matching phone execution is now observed.
  Keep its source/artifacts/managed/preparation stages immutable after delivery.
  Further corrections require a new identity. See the exact IPA, symbols,
  snapshot and gate identities in its evidence ledger and delivery receipt.
  The two new eligible helper versions pass actual native update transactions,
  fresh Spring Starjump plus saved-session reload, updated Paint, full SJ/Frost,
  main-menu Quit and queued-save Quit on the host. Simulator UI/import/export
  and blocked/current-release reviews pass. The final fresh-review UI uses a
  verified prior official index through production cache fallback after two
  live server timeouts, also reproduced with curl. Retain this distinction.
  That handoff's requested runtime/update/gameplay gates are now accepted above.
  Keep its original delivery receipts unchanged as historical snapshots.

- **Earlier physical acceptance: build26.** Two exact exports cover three fresh
  processes. Fresh Spring plus separately imported audio resolves 17 helpers
  (22,892,303 bytes); all installed/enabled changes and a separate AdventureHelper
  enable-only report match committed files and actual registration. No physical
  old-to-new update or cancelled/failed transaction occurs in these exports;
  retain their existing host evidence separately. All 26 native checks pass per
  process, with 23 registered identities, corrected reflection ABI1 and no
  CommunalHelper installed. Spring Prologue/gym/lobby and Starjump progression
  pass; 37.24s background/resume, clean Quit/native return, counter 0→65→167→168
  and fresh-process reload of Starjump's strawberry room are recorded. All
  runtime failure counters are zero. Final export precedes the delayed heartbeat;
  the earlier two sessions record it, and all three prove native return.
  Read [acceptance](docs/ios-jit/BUILD_26_INSTALLS_ACCEPTANCE.md). Use map/room
  diagnostics directly. Keep accepted26 as current fallback, and retain build24
  as the accepted graphics/SJ fallback; preserve all source/artifacts/Results.
  Approved follow-up, now delivered above: isolated stable Everest1.6531.0 at
  d72e94f4b9e62b91cbdea674587ed39d53de9550. Read the
  [runtime assessment](docs/ios-jit/EVEREST_RUNTIME_UPGRADE_ASSESSMENT_2026-09-13.md).
  Nine upstream commits change three runtime files and two TAS files; no dependency
  project/submodule change. Rebuild actual patched game/hooks in new stages;
  never just change version strings. Consolidate runtime identity and invalidate
  or re-evaluate cached update eligibility across runtime/pin changes (also offline,
  auto-check disabled and downgrade). Preserve verified download/hash caches.
  Keep accepted native Mono/renderer/FNA/MonoMod/CoreLib fixes unless evidence
  requires changing them. The recommendation is implemented and accepted as27.
- **Preserved accepted build26**, isolated `experiments/ios-jit/launcher-resolution`,
  version 0.13.1 (26). Read [the resolution/report record](docs/ios-jit/MOD_RESOLUTION_BUILD_26.md).
  Owner reports EeveeHelper/FrostHelper updates and fresh Spring dependency blockers.
  These two updates are compatible; an unsupported install is not established.
  Original25 direct coordinator/Apply controls reject blocked updates with zero writes.
  Only ExtendedVariantMode0.51.0 / MaxHelpingHand1.40.10 require Everest1.6531.0;
  older requirements in the screenshot are satisfied by app1.6458.0.
  New warnings name only unsatisfied source modules; blocked rows have no Update
  action and batch is explicitly compatible-only. Generic earlier-candidate metadata
  offers original ExtendedVariantMode0.50.5 / MaxHelpingHand1.40.9 when needed.
  Keep these alternatives separate from the three permanent compatibility pins;
  verify original hashes and actual ZIP requirements, preserve compatible locals,
  prefer compatible latest releases and never relax minimum versions.
  Reports use committed actual old/new identities and enabled choices. Preserve
  update disabled state; dependency resolution may enable existing files. Separate
  verified cached downloads from applied changes, failures and unattempted work.
  Reopen the last report and include it in Export; interrupted/unconfirmed must
  never claim success. Recover journals before library scans or gameplay.
  Real GameBanana HTTP503 prompted bounded original/CelesteMods/Jade fallback,
  following upstream file-ID mirrors without changing size/hash/metadata checks.
  Fresh Spring startup exposed Mono attribute queries loading absent CommunalHelper
  signature types. Build26 patches three CoreLib reflection methods and one private
  icall registration, using existing mono_method_get_flags; explicit missing-type
  errors remain. Preserve all other methods/fields/resources. Build isolated copies
  with build_reflection.py; never mutate accepted packs. Thirty real-Mono/CoreCLR
  attribute/PreserveSig/PInvoke controls pass; fresh Spring selection boots and saves
  on the host. The later phone26 acceptance above establishes the recorded
  Spring map and ARM64 gates; it does not establish arbitrary-mod compatibility.
  Keep accepted24 native Mono archives, renderer, game IL, CelesteIOS and script
  unchanged. Final native/package/six UI gates pass, plus a full-screen landscape
  capture. Use XCUIScreen.main.screenshot for rotated UI evidence; app.screenshot
  crops the rotated surface in this simulator. Optional original earlier helper
  ZIPs accompany the private kit for intermittent HTTP503/404 fallback.
  All ten kit files / 24,954,962 bytes are confirmed uploaded to
  `Celeste JIT Tests/0.13.1-build-26`, including the optional original earlier
  helper ZIPs and DOWNLOAD-HELP.txt. Exact phone26 execution is now observed and
  accepted; the original delivery records retain their historical pending state.
  Preserve delivered26 source/artifacts; further corrections need a new identity.
  IPA 23,468,277 bytes, SHA256
  `4b77c9ec39f73b66c2f0e7c2de446ac67067cc6ac56d04698c56f2b9732d0dbd`;
  executable/dSYM UUID `25ECF962-06E7-3C73-A339-FAE899A4ED9D`.
  All 210 device/simulator source inputs match. Frozen receipt SHA256
  `693adecf17130a55fc1a6a581ffcea3d1982db33148ca9a034807a2662893c29`
  under private device-evidence/2026-09-13/build-26-ready; final records in handoff.
  Build25's superseded cloud IPA is removed after exact local verification;
  build24 fallback and every Results folder remain. The build-time local checksum
  manifest includes one earlier protocol-test result; preserve it as history and
  use the final handoff/phone manifests for completed gate identities. Read
  handoff/BUILD-TIME-MANIFEST-NOTES.json. Future builders should exclude previous
  validation outputs from the initial manifest.
  No commits, pushes or AOT writes. Runtime assessment is complete; implement and
  test the isolated upgrade before broad catalogue/loading/backups/editor work.

The following build25 delivery snapshot is historical where superseded above.

- **Current delivered phone candidate: build25**, `experiments/ios-jit/launcher-dependencies`, 0.13.0 (25).
  Native dependency installs and updates; [implementation record](docs/ios-jit/MOD_INSTALLS_BUILD_25.md).
  Owner explicitly added individual Update / Update all and occasional automatic
  checks: explicit Check button, idle Updates-page check after 24h, optional in
  Settings, 1h automatic failure backoff, cached results/hashes. No automatic ZIP
  install or background/gameplay scheduler.
  Review all operations, preserve disabled choices and compatible versions,
  protect app-managed pins and built-in modules, validate fetched metadata,
  retain verified downloads after cancellation and journal recovery before scans.
  Keep build24 source/artifacts/managed payload/renderer immutable and retain it
  as fallback. Build25 passes all local gates; all seven kit files / 23,428,401
  bytes are confirmed uploaded to `Celeste JIT Tests/0.13.0-build-25`.
  Phone25 download/execution and acceptance are unobserved. No reimports needed.
  IPA 23,409,096 bytes, SHA256
  `27885f04db1dd6926f78106cca5e8e4e7c4e3059c3ccd3fb10cffdc1b8e07ba4`;
  executable/dSYM UUID `9160ACFD-56F9-360A-A765-92A4A68065CD`.
  All 198 source inputs and simulator build match. The frozen source receipt is
  `b965e4bc55ea3c4d103d31dd56b1046b7269c67682e65112bf3a4347f04c70fe`
  under private `device-evidence/2026-09-13/build-25-ready`; final records live
  in `handoff`. Keep delivered25 source/artifacts immutable; corrections need
  a new identity. Build23's superseded cloud IPA was removed after exact local
  verification; build24 and every Results folder remain.
  Indexed ExtendedVariantMode 0.51.0 / MaxHelpingHand 1.40.10 require Everest
  1.6531.0 and are blocked in this 1.6458.0 app; EeveeHelper 1.12.6 / FrostHelper
  1.80.2 pass a real transaction and host Paint/save/resume. Assess an isolated
  runtime update after phone25 before broad fresh-profile compatibility claims.
  The build25 managed and native renderer builders are read-only build24
  verifiers. Do not restore copied builders that rebuild accepted24 in place.
  Its updated Paint host gate is isolated and explicitly uses the external
  Paint fixture, real updated ZIPs, saves and resume. Simulator fixture transport
  is excluded from the device payload. Old install ZIPs remain disabled/retained;
  Enable all skips them. Recovery must run before scanning or starting Celeste,
  preserve unknown changed files/state, and export bounded transaction receipts.
  Later catalogue, loading, backups and editor remain deferred.
  No commits/pushes/AOT writes.


The following build23/24 delivery notes are historical where superseded above.

- **12 September earlier acceptance:** build23 title and modded main-menu Quit
  both pass all shutdown stages, native detach/return and post-run heartbeat.
  See [phone acceptance](docs/ios-jit/BUILD_23_SESSION_ACCEPTANCE.md). Two build23
  processes match exact delivered metadata. 56 ZIPs / 59 identities, zero runtime
  failures. Mod counter 320→403; latest 403 reload is not in the export and must
  be checked in the next kit. Touch-to-controller observed; keyboard/disconnect
  and new-build gameplay resume remain unrecorded. Build23 becomes the complete
  shutdown fallback. Preserve its delivered lane and all Results.
- **Historical build24 delivery snapshot**, `experiments/ios-jit/launcher-backbuffer`,
  0.12.1 (24), `launcher-backbuffer-20260912-24`. Isolated renderer staging is
  `.build/ios-jit/launcher-backbuffer-renderer`; never rebuild the accepted
  `graphics-native-build11` stage. Investigate retained backbuffer surface,
  deferred clear, MSAA preservation and array/rectangle readback bounds.
  Read [the build24 report](docs/ios-jit/METAL_BACKBUFFER_BUILD_24.md) and evidence.
  All local gates pass, including original native crash versus 107 fixed GPU/API
  checks, full SJ/Frost, normal/queued Quit, Paint and save reload. Phone acceptance
  is pending. FNA patch changes only two GetBackBufferData overloads, adds two
  internal helpers, preserves 5,242 other methods/4,469 fields and releases pins
  in finally. Use actual element stride and reject reference-containing structs.
  Retained colorBuffer is the source; flush deferred clears and preserve MSAA
  storage across readbacks. No drawable dependency or every-frame capture.
  Automatic phone pattern + after-Present/level/resume samples need the extra
  CJITFinishGraphicsCallback before the outer callback autorelease pool closes.
  CelesteIOS/MonoMod/game IL/Mono/script remain identical to23. Keep one game per
  process. Versioned kit: 0.12.1-build-24; no reimports. Check delivery ledger for
  cloud state. After phone acceptance: general dependency transactions.
  Final kit: eight files / 23,164,143 bytes, all confirmed uploaded to
  `Celeste JIT Tests/0.12.1-build-24`; phone24 download/execution unobserved.
  IPA 23,145,454 bytes, SHA256
  `f7ed94140ee4b181f667a9901b9d769662e196eb51139b7f593c1d2933da6a58`;
  dSYM UUID `919E08E6-E087-31D7-8D83-AE26372D1BFF`. Frozen snapshot receipt
  `bf2a73f5e9d2efa9ba31b5e1245f1e1c5256268fc1728aeb717b5aa51f4053b4`.
  Keep delivered source/artifacts immutable; further corrections need a new ID.
  Build19 cloud installer is removed after exact local verification; build23
  cloud fallback and every Results folder remain. Final delivery records and
  current document copies are under private build-24-ready/handoff.

The following build23 delivery notes are historical where superseded above.

- Preserved session foundation: build23 `experiments/ios-jit/launcher-session/`,
  0.12.0 (23), `launcher-session-20260912-23`. Required bundled CelesteIOS
  1.0.0 / ABI1 owns Game.Exit and input prompts; register before user mods and
  reject identity overrides. Native host owns commands/stages/presentation/files.
  Stop3 drives pending save frames;4 yields;1/2 are complete/incomplete. Require
  stage8 plus graphics_bridge_pass and graphics_result_presented for native return.
  Main-menu Quit returns to SwiftUI; in-map Save and Quit leaves the map. Normal
  play has no permanent Finish. Keep one game per process and independent Export.
  Phone title/modded Quit, all eight stages and post-run heartbeat pass. Game.Dispose
  remains synchronous (phone4.79s title /7.99s modded), with independent heartbeats
  and no kill timer. Latest-counter403 fresh-process reload is carried into24.
  Source snapshot receipt `b6a232e9c0595c32d1ab935029d1444890a9d771c7b98757a0649b127904ad6d`.
  Preserve all build23 artifacts and `0.12.0-build-23` as the current fallback.

- **12 September, latest review:** build22's recorded normal gameplay and save
  readback pass. Read [the phone acceptance](docs/ios-jit/BUILD_22_GAMEPLAY_ACCEPTANCE.md).
  Almost 24 minutes, 26 native/13 graphics checks, 56 enabled ZIPs/58 identities,
  normal room progression including the prescribed Paint route, zero recorded
  JIT failures. Mod counter 102→320 and slot 1 readback pass. The exported current
  process only collected logs; the played session is in history alongside two
  failed build21 sessions. Never conflate them. The journal ends 9.5 seconds after
  Finish during teardown, without a final native return marker; no shutdown
  crash is proven. Owner cannot remember whether SESSION SAVED appeared.
  Final shutdown and a subsequent game/checkpoint reload remain unverified.
  Keep build19 as the complete-shutdown fallback and all Results.
- Owner reactivated and expanded product work after this gameplay pass. Read
  [the current native launcher design](docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md)
  and [service evidence](docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_EVIDENCE.json).
  Target a general Celeste launcher with native dependency planning/downloads,
  browsing, real loading progress, saves/settings and a full-parity touch editor.
  A required bundled/version-matched iOS support module should own game-side
  Quit and input prompts. Keep JIT, downloads, files and native session state in
  the host; early bootstrap must work before the support module is registered.
  No new IPA was produced by that design review. Do not edit delivered build22.
- Build23 implements the approved session step: classify requested Quit separately from runtime failure,
  let ordinary mod saves complete before ending frames, instrument teardown
  stages, return to SwiftUI, verify fresh-process reload and touch/controller
  glyphs. Current native Frame treats result 0 as failure; simply hiding Finish
  or calling Game.Exit early is insufficient. Never force-kill on a timer.
  Preserve one game per process until a separate restart solution is proven.
- Use exact YAML identities for dependency resolution, not GameBanana title
  search. Keep compatible installed versions, account for disabled dependencies,
  preserve originals, validate actual fetched ZIP metadata and journal the whole
  transaction. Online graphs describe indexed versions, not arbitrary older
  imports. No desktop runtime updater, hot unloading or silent broad updates.
  Current Olympus data uses GameBananaType=Obsolete; trust supplied PageURL and
  opaque identifiers. Online database parsing needs distinct limits from the
  existing 1 MiB per-archive metadata parser. API source snapshots are dated/pinned.
- Native loading progress needs real main-thread responsiveness: current managed
  Start synchronously boots Everest on UIKit's thread. Do not just enqueue
  labels behind it, move all graphics/mod startup to an arbitrary worker, or
  pump a nested run loop. Keep thread-affine work on its required thread.
- Touch UI parity includes D3 split/duplicate/extras/sliding/shape/mirror/undo,
  import/export and source-aware grab/haptics. SwiftUI owns the editor, with
  versioned normalized geometry matching gameplay hit tests. Retain stable
  multi-touch transport; support-module prompts reuse the same glyph artwork.
  Saves use whole-profile backups including unknown mod sidecars/settings;
  restore through staging/rollback while inactive, never vanilla validation.

- Build21 failed physically while loading Paint's `intro`, due to MonoMod fast
  reflection emitting static-field instructions for literal `Celeste.Decal.Root`.
  Original EeveeHelper DynamicData enumeration triggers it. All 26 native/six
  graphics checks and 56 selected identities pass; code use 180/512 MiB, no setup
  error/timer. Everest catches two failures; native host stops on the profiler
  counter. Save shutdown is incomplete. Do not mark build21 accepted. Read
  [the diagnosis](docs/ios-jit/LITERAL_FIELDS_BUILD_22.md) and
  [phone evidence](docs/ios-jit/BUILD_21_SESSION_STOP_EVIDENCE.json).
- Separate backend follow-up found during build22 testing: the desktop
  `GraphicsDevice.GetBackBufferData` test crashes in FNA3D. The accepted Metal
  `METAL_ReadBackbuffer` constructs a local MetalTexture without assigning its
  native handle before GetTextureData2D consumes it. Do not attribute this solely
  to callback lifetime; that was a preliminary inference. Build22's final Paint
  readback uses the retained Gameplay texture and passes. Preserve build22/old
  renderer; use a new isolated renderer lane to investigate exact surface/MSAA,
  format, frame-lifetime and suspend/resume semantics before general mod browsing
  or screenshot/performance capture features. This did not cause the phone failure.
- Preserved accepted gameplay baseline: `experiments/ios-jit/launcher-reflection/`,
  **0.11.2 (22)**, `launcher-reflection-20260912-22`; stages `launcher-reflection*`.
  Preserve build21 and all delivered bytes. MonoMod literal reads emit constants;
  writes throw FieldAccessException. Original field validation, caches and
  nonliteral paths stay unchanged. Preserve the accepted Mono8 corlib patch.
  One internal helper is merged, not a separately shipped dependency. Pin input
  hash and preserve all other methods/fields/dependencies/resources.
  JIT error UI now names the failed method when Everest catches the exception;
  propagated managed errors retain priority. Never simply ignore JIT failures.
  Test original/fixed actual Mono literals and original Paint room loading before
  phone delivery, including fresh-process saves. Keep original ZIPs/game IL,
  FNA extension, Mono/native renderer, profile and protocol unchanged.
  Real Mono/Metal tests pass original/fixed Paint, full original Lua intro,
  retained-texture GPU readback, controls after resume and save/readback in two
  processes; all 137 literal controls and previous full-SJ/Frost/normal tests pass.
  The Paint test starts a new map session after reading the existing slot; do not
  claim exact-room resume or normal lobby-door progression from the host test.
  IPA is about 23.1 MB; use `0.11.2-build-22` with existing data and a fresh inline
  request. Repeat normal Paint entrance, play, 30-second background/resume,
  Finish and fresh-process save verification; export separate sessions to Results.
  All eight iCloud kit files (23,133,578 bytes) are confirmed uploaded; matching
  phone execution is now observed as described above. IPA SHA256 is
  `b9a89008136a1dbf0e409c5fd22095df876a1430992a5110348a6cf5f88dd17e`,
  executable/dSYM UUID `EB66D6A0-13F1-3231-885C-02A5AC681617`. Build21 cloud
  IPA was removed after exact local verification; build19 and all Results remain.
  Recorded build22 gameplay/save acceptance is above; final shutdown and new
  game/save reload remain open. Owner's product requests are now active.


- Earlier deferred product direction (now expanded/reactivated above):
  make this a **general Celeste mod launcher**, analogous to Olympus on iOS.
  Do not brand or structure the normal product around Strawberry Jam or any
  single mod. Preserve existing profile paths/data during any UI migration.
  Add a reviewed dependency-resolution/download flow with progress (owner hit
  missing MemorialHelper 1.0.0 importing SpringCollab2020), explore popular/new
  mod browsing and direct installs, and use real Everest startup milestones for
  a SwiftUI game-loading screen. Investigate official Olympus/Everest mechanisms
  before implementing. Owner explicitly deferred this until the current fix is
  finished; build21 remains frozen. For its immediate lava regression, temporarily
  disable the incomplete new SpringCollab import and retain the accepted SJ set.
  Broad mod support is the target; per-version iOS compatibility limits remain
  evidence-based. These product requests follow the immediate graphics retest.
- Build20 physically stopped in normal Beginner-lobby play with a caught
  `MissingMethodException`: original FrostHelper 1.80.1 lava rendering calls
  FNA `GraphicsDevice.GetRenderTargetsNoAllocEXT`, absent from the older FNA.
  **There is no intended session timer.** Setup/JIT passed, 54 ZIPs/56 identities
  verified, 205,930,496 / 536,870,912 code bytes used; error/save shutdown is
  incomplete. Do not mark build20 accepted or infer fresh-process SJ save reload.
  Read [the diagnosis and fix](docs/ios-jit/FNA_GRAPHICS_BUILD_21.md).
- Previous build21 candidate was isolated `experiments/ios-jit/launcher-compat/`,
  **0.11.1 (21)**, `launcher-compat-20260912-21`, with stages `launcher-compat*`.
  Keep build20 immutable. It adds exactly one FNA API using existing state;
  all 5,243 old methods and 4,469 fields are preserved. Original ZIPs, prepared
  game IL, Mono archives and native renderer stay unchanged. The pinned upstream
  contract accepts oversized buffers, preserves unused tail entries, rejects
  undersized buffers, supports a null count query and does not allocate.
  Never implement this by allocating `GetRenderTargets()` on every call.
- Build21 real Mono/Metal passes 33 graphics checks, including original Frost
  holder save/restore and original lobby lava rendering with nonempty GPU pixels.
  All 3,222 FNA member references across 49 original helper DLLs resolve; three
  runtime array intrinsics are separate. This does not prove all-map compatibility.
  The external desktop test DLL is never bundled; the build21 phone run failed
  later during Paint room setup, as recorded above.
  Failure UI records/displays the first managed error and stop origin; incomplete
  shutdown must not claim latest progress was saved. Use
  `iCloud Drive/Celeste JIT Tests/0.11.1-build-21` and repeat the failed lobby
  route before broader UI/save-manager work. New JIT script per process; no
  game/SJ reimport, profile change or runtime geometry change is required.
- Build 19 is physically accepted for the original full SJ dependency graph,
  Beginner lobby/Bing, music, save/readback and background/resume. Read
  [the acceptance](docs/ios-jit/STRAWBERRY_JAM_PASS_BUILD_19.md). All 26 native
  and nine game checks pass, exact bytes match, final code use 211,156,992 /
  536,870,912 bytes, zero runtime errors. Save counter 0 → 139; slot 29 deaths.
  Keep build19 as fallback. Fresh-process SJ save reload and natural lobby-door
  progression remain unaccepted; never claim all-map compatibility.
- Build20 introduced `experiments/ios-jit/launcher/`, **0.11.0 (20)**,
  ID `launcher-20260912-20`. Read [its report](docs/ios-jit/LAUNCHER_BUILD_20.md)
  and [evidence](docs/ios-jit/LAUNCHER_BUILD_20_EVIDENCE.json). Native SwiftUI
  portrait/landscape launcher, general ZIP catalogue, dependency preflight,
  persisted toggles/blacklist and normal play are implemented. Keep one selected
  mod set per process; no hot unload or runtime restart. A new process needs JIT.
- Keep `Profiles/sj-first-play`, original 52 SJ ZIPs and shared `GameLibrary/v1`.
  No reimport/extraction from old IPAs is required. Library choices are in
  `launcher-mod-state.json`; Run rehashes and atomically writes individual
  `Mods/blacklist.txt` / `launcher-run.json` files before any consumption. Managed
  startup checks actual module registration against the frozen selection.
  Corrupt state fails closed, preserving the file. Original ZIPs are immutable.
- Native catalogue mirrors Everest's numeric version policy (including 0.0.*,
  missing Build/Revision = -1), required/present optional dependencies, duplicates
  and cycles. Metadata-free ZIP names retain their installed basename. Full
  native import tests cover 53 ZIPs and invalid/corrupt inputs. This is not a
  guarantee that every arbitrary mod or desktop native plugin runs on iOS.
  GravityHelper/CollabUtils2/FemtoHelper remain gated by their accepted ZIP hashes.
- Normal play uses Celeste menus and the actual save slot; the optional Settings
  SJ regression mode retains strict lobby/Bing/resume controls. The tiny independent
  `CJITLauncherExample-v1.0.0.zip` tests normal code import and real registration.
  Real Mono host tests pass full SJ, example enabled with SJ disabled, then example
  disabled in a fresh process, with saves 0 → 3 → 6 → 9. The build20 phone export
  confirms normal menus/lobby play before the missing FNA method failure.
  Normal door progression, clean Finish and fresh-process SJ save reload remain
  physical gates now target build22.
- Diagnostic schema2 bounds samples/journals, keeps exact routine event counts
  and a separate packed allocation trace (65,536 records, explicit overflow).
  Preserve startup identity, critical milestones, meaningful failures and Export.
  Current/previous journal parts cap at 4 MiB; old exports use bounded excerpts,
  not every old event. Actual build19 replay matches all 12,642 allocations and
  120,096 event counts with 802 sync checkpoints under ASan/UBSan. The prior
  lossless raw-log policy in historical sections does not describe this schema.
- Optional overlay measures callback FPS and elapsed frame-callback time including
  waits, not GPU time or pure CPU usage; last 600 intervals, 1% low after 120,
  reset on pause. Loading stalls count. Do not present loading gaps as an in-game
  benchmark or attribute the entire prior 4.33 GB footprint to logging.
- Build20 reuses build19 Mono/renderer/prepared IL read-only; native dependency
  commits live in `native-dependencies.json`. Read-only builders verify accepted
  runtime/mod inputs; redundant old test drivers that target accepted stages were
  removed. Reuse inherited runtime/compatibility controls only with matching
  implementation/archive hashes. New build outputs go under `launcher*`.
- Historical build20 handoff: small unsigned IPA + tiny example ZIP + guide through
  `iCloud Drive/Celeste JIT Tests/0.11.0-build-20`. LC1 update retaining data;
  JIT OFF/script blank/Fix File Picker ON; StikDebug LC2, fresh inline script.
  Check the artifact's delivery receipt for exact cloud, source snapshot and
  executable identity. Keep build19 fallback; preserve all Results. No commits.
- Next priorities: phone acceptance and longer SJ/memory/code-headroom checks;
  full-profile backup/restore with rollback (no vanilla schema/allowlist); native
  normalised touch layout editor and versioned settings; broader mod compatibility.
  Public on-device original-IL preparation and FMOD permissions remain release
  gates. Build20 still contains private prepared game IL/FMOD; do not distribute.

## Build 19 implementation history (physically accepted)

- Read [the full SJ report](docs/ios-jit/STRAWBERRY_JAM_BUILD_19.md) and evidence.
  ID `sj-lobby-20260912-19`, 0.10.0 (19), source `experiments/ios-jit/sj-lobby/`.
  Full 52-node original SJ graph plus own canary (53 ZIPs) passes real Mono host
  lobby/Bing/music/hooks/save/resume/detach. Physical full SJ remains pending.
- New profile `Documents/Profiles/sj-first-play`; shared `GameLibrary/v1` reused.
  Fresh SJ save is expected. Preserve complete earlier helper profiles. Never
  validate arbitrary mod saves through the strict vanilla save allowlist.
- Explicit Wi-Fi download fetches 1,237,284,560 original ZIP bytes directly to
  the phone. Keep foreground, hash/size verify, atomically install; cancel/retry
  keeps completed ZIPs. Only own tiny canary ZIP belongs in the small IPA/kit.
  Do not upload the original 52-ZIP set to iCloud or split to evade the limit.
- Scoped runtime: copy accepted build16 archives, replace only mini.c.o,
  mini-runtime.c.o, method-to-ir.c.o and mono-codeman.c.o. 256 members unchanged.
  FemtoHelper beforefieldinit only is deferred until actual static-field access;
  original IL/readonly fields remain. Explicit cctors/unrelated assemblies stay
  unchanged. Original-failure, 13-case and unrelated-assembly controls pass.
  Do not reintroduce the abandoned managed particle-initializer rewrite.
- Keep exact-version Gravity and Collab optional CelesteNet compatibility in
  separate hash-keyed caches; original ZIPs/upstream cache remain untouched.
  Collab moves one cache field and four operands; 2×1,073 structural controls
  pass. Actual CelesteNet networking is untested, never install fake modules.
- Mono floor 16 KiB (page/granule-clamped; large allocations and ARM64 thunk
  space preserved). Two 256 MiB arenas: 512 MiB total. Final host trace rounded
  183,287,808 bytes; two traces + 16 MiB native reserve use 383,352,832. Full
  ARM64 code/memory usage is still a device gate; no reclamation or fallback.
- Every VM page is inspected; compact diagnostics retain full trace hash and
  first/last 8 rows, not a complete entries array. Acceptance must use full
  covered_bytes/entry_count/permissions, not infer coverage from samples.
  Production logger hash and 16,384 actual Darwin entries pass sanitizer tests.
- Physical steps: update LC1 keeping data, JIT OFF/script blank/Fix File Picker
  ON; download missing SJ mods on Wi-Fi to 53/53, then fresh LC2/StikDebug script.
  Old build18 geometry is incompatible. Run Celeste, SJ lobby 15 seconds, Bing
  15 seconds with music, Home 30 seconds, return/jump ten seconds, Finish,
  wait ten seconds, Export to `0.10.0-build-19/Results`. Export first after crash.
- IPA 22,812,410 bytes; SHA256
  `1a64be05f4454a3dcee601e6b244f7e6a44142ad69a97fa10ee8967500edb180`;
  executable/dSYM UUID `C32B2B24-459D-3182-95E9-852A4ACE8370`. Check the artifact
  delivery receipt for cloud upload, phone download and frozen snapshot status.
  Preserve delivered bytes and keep accepted build18 as fallback. Local kit
  `artifacts/ios-jit/sj-lobby-20260912-19/`. No AOT mutations/commits/pushes.
- Historical sections below record earlier handoff states; their old pending
  tests and fallback choices do not supersede current acceptance/candidate.

## Build 18 implementation history (physically accepted)

- Read [build 17 stop / build 18 fix](docs/ios-jit/BUILD_17_VM_LIMIT_AND_BUILD_18.md).
  Build 17 setup was correct: five ZIPs retained, two correct new ZIPs imported,
  all seven ready, matching script successful and debugger detached. The app
  stopped cleanly before aliasing or execution because the shared VM checker
  had a 4,096-entry limit. All recorded entries are RX, but they cover only
  64 MiB of the first 128 MiB region. Do not infer the uninspected remainder,
  second arena or native/managed execution from the mailbox reply alone.
- Source `experiments/ios-jit/sj-memory-check/`; output stages
  `.build/ios-jit/sj-memory-check*`; ID `sj-memory-check-20260912-18`,
  version 0.9.1 (18). Preserve build 17 and every accepted earlier lane.
  New local VMRange source/header computes the bound from intersected OS pages,
  including partial boundaries and overflow checks. Production uses getpagesize;
  complete coverage and uniform current permissions remain required. Log the
  page size and entry_limit. Never fix this by accepting just the old prefix.
- Original recorded-prefix failure control and 18 ASan/UBSan cases pass,
  including late permission/gap/query/missing-tail negatives beyond entry
  4,096 and 8,192 actual Darwin VM entries. Full real-Mono Gravity/Lua/Max
  host replay with the new checker passes save 6 → 9, gravity/platform/Lua,
  hooks and detach. The original build 17 adapter, all seven ZIPs, all native
  archives and script bytes are unchanged; read-only builders verify them.
- Keep the same 256 MiB arena (two 128 MiB regions) and 64 KiB Mono floor.
  Require a fresh process script despite the unchanged template. Keep LC1
  Launch with JIT OFF, script blank, Fix File Picker ON; StikDebug LC2.
  **No game or mod imports are needed.** Preserve existing content, seven ZIPs
  and saves. Native checks first, then the same Gravity map, red zone,
  ceiling-platform underside, exit to normal gravity, Home 30 seconds, return
  and jump, all three passes, Finish, ten-second wait and Export to
  `iCloud Drive/Celeste JIT Tests/0.9.1-build-18/Results`. Export first after
  a crash before enabling JIT again. Physical gravity acceptance now passes; see the acceptance above.
- Final IPA: 22,780,024 bytes, SHA256
  `8ae85ea014c6f301ed7a065eb8a506e3b726301fc14ed5c0e0a1209548dd1272`,
  executable/dSYM UUID `E1A7F78F-0879-3C6A-8E3E-B223641BF855`.
  All 135 source inputs and final package/simulator/16,384-page protocol checks
  pass. The frozen build 18 snapshot inherits verified build 17; receipt SHA256
  `a289573596cc4fcee266a5cea301f7d677392c014f1b2fb477d207e03007e227`.
  All 13 files (24,566,084 bytes) have confirmed iCloud upload; phone download and execution are confirmed by the exact build 18 export. The failed build 17 cloud IPA was removed
  after its exact local copy was checked; keep all Results and build 16 fallback.
- Local kit `artifacts/ios-jit/sj-memory-check-20260912-18/`; consult its stage
  evidence and delivery receipt for exact final IPA/symbol/snapshot identity
  and confirmed iCloud upload versus actual phone download. Preserve delivered
  bytes. No commits, pushes, public distribution or AOT changes are authorized.

## Build 17 implementation history (VM checker stopped before execution)

- Read [the build 16 physical pass](docs/ios-jit/SJ_HELPERS_PASS_BUILD_16.md)
  and [the build 17 report](docs/ios-jit/GRAVITY_HELPER_BUILD_17.md). Build 16
  passes original LuaCutscenes 0.2.13 / MaxHelpingHand 1.40.9 gameplay, real
  retained Lua coroutine, moving-platform travel/carry, saved counter 15 → 23,
  cached content, 37-second Home/return, post-resume jump and clean detach.
  All 26 native/nine game checks pass, no runtime errors, final code usage
  58,408,960 / 134,217,728 bytes. Existing five ZIPs were retained without
  reimport. The exact export is under `build-16-results/` in private evidence.
- Build 17 source is `experiments/ios-jit/sj-gravity/`; outputs use
  `.build/ios-jit/sj-gravity*`, ID `sj-gravity-20260912-17`, version 0.9.0 (17).
  Preserve accepted build 16 source, stages and artifacts. Reuse its exact
  `.build/ios-jit/sj-budget-runtime` archives; the new runtime builder is a
  read-only verifier. Do not rebuild accepted dependencies in place.
- This stage adds original GravityHelper 1.2.28 and CJITGravityProbe 1.0.0.
  Keep the existing game library, five ZIPs and full save/profile data; import
  only the two new ZIPs (seven total). Old ZIPs in the kit are identical recovery
  copies. The room SID is `CJITGravityProbe/RuntimeRoom`. Keep the old
  CJITSJHelpers ZIP; the new mod deliberately has a different identity.
- GravityHelper eagerly loads its optional CelesteNetModSupport type during
  Load/Unload on Mono. `managed/GravityOptionalIntegration.cs` hooks only the
  pinned GravityHelper 1.2.28 ZIP's Everest `LoadRelinkedAssembly`, creates a
  separate hash-keyed `Cache/CJITCompat/gravity-optional-v1` copy and rewrites
  exactly two type references/calls. Resolve the optional integration only
  after detecting `CelesteNet.Client`; unload an existing integration even if
  its module has disappeared. Keep original ZIP/upstream cache, types, fields
  and every other method body. No fake modules or broad exception suppression.
  Present-integration errors retain their original exception. Actual CelesteNet
  networking remains untested. Unsupported versions/shapes fail explicitly.
- The original real GravityHelper negative control reproduces its CelesteNet
  TypeLoadException. 17 checks each on original and Everest-relinked assemblies
  pass under the accepted Mono archive: only two of 2,008 method bodies change,
  all type/field shapes and optional implementation remain, absent resolution
  is skipped, present operation/errors execute, duplicate/tampered inputs fail.
  Preserve these controls and the pinned input hashes before generalizing.
- Full real-Mono host gravity/Lua/Max runs pass. Final packaged adapter bytes
  reuse the compatibility cache, save 3 → 6, invert gravity, land on the
  underside of the ceiling platform, return to normal gravity, retain/resume
  Lua, render and detach without errors. Host runs do not establish iOS
  background survival or physical ARM64 capacity. Native logs now retain
  `sj_` and `mono_` event names instead of folding their payloads.
- **New script geometry: two 128 MiB arenas, 256 MiB total.** Gravity's real
  16 KiB-page/binding-room host model uses 2,321 chunks / 147,144,704 rounded
  bytes. The actual alias replay plus 1,161 extra chunks and 16 MiB native
  reserve uses 235,569,152 bytes; exact build 15 failure and terminal guard
  controls pass with ASan/UBSan. Keep build 16's 64 KiB ordinary chunk floor.
  No reclamation, interpreter fallback or runtime restart is introduced.
- Keep LC1 Launch with JIT OFF, script blank, Fix File Picker ON; StikDebug LC2.
  Older templates cannot prepare the new geometry. Enable this process's
  fresh PID/nonce script, wait for detach, run Celeste, tap **Gravity map**.
  Let Lua walk, enter the red zone, stand on the underside of the ceiling
  platform, exit the red zone and land normally. Home 30 seconds, return and
  jump, require LUA/GRAVITY/PLATFORM PASS, Finish, wait ten seconds and Export
  to `iCloud Drive/Celeste JIT Tests/0.9.0-build-17/Results`. Export first after
  a crash, before another JIT request. Preserve saves for the next update.
- Final unsigned IPA is 22,780,995 bytes, SHA256
  `d53c7399946ef11150cbcfdcf2d797865f9175d28e4894dc1ac9f950b8223b40`,
  executable/dSYM UUID `82EA42B3-CD0A-38B2-8073-A552F044DBF7`. All 155 source
  inputs, package/native imports, simulator seven-ZIP readiness and 16,384-page
  protocol checks pass. The frozen build 17 snapshot inherits verified build 16;
  its receipt SHA256 is
  `7b807d8c184a90d8104178b577703e7dc871899b17655a118b03f51fc710c773`.
  The delivered kit is 24,567,275 bytes; all 13 files have confirmed iCloud
  upload. Phone download/physical gravity acceptance remain pending. Consult
  delivery-receipt.json and preserve delivered bytes.
- Local kit: `artifacts/ios-jit/sj-gravity-20260912-17/`; exact IPA/symbol and
  delivery/snapshot identities are in the stage evidence. Phone gravity
  acceptance is pending. Full SJ's 52-node dependency graph and Beginner
  lobby/Bing remain later gates. This is still a private prepared-IL/FMOD kit;
  public on-device original-IL preparation is separate. No commits/pushes.

## Build 16 implementation history (physically accepted)

- Read [the build 15 crash and build 16 fix](docs/ios-jit/BUILD_15_CAPACITY_AND_BUILD_16.md)
  and its evidence. **Build 15 setup was correct; its 128 MiB JIT arena filled
  before the title while MaxHelpingHand loaded.** All 26 native checks passed,
  all five mod ZIPs were ready and cached game content verified in 2.107 seconds.
  Physical build 14 → 15 content/mod retention and fresh content reuse now pass.
  No additional save-reload or helper-gameplay acceptance follows from that crash.
- Build 16 source is `experiments/ios-jit/sj-code-budget/`, stages
  `.build/ios-jit/sj-budget*`, ID `sj-code-budget-20260912-16`, version 0.8.1 (16).
  Host/package/simulator checks and **physical helper acceptance pass**.
  Read [the build 16 acceptance](docs/ios-jit/SJ_HELPERS_PASS_BUILD_16.md).
  Local kit `artifacts/ios-jit/sj-code-budget-20260912-16/`; phone folder
  `iCloud Drive/Celeste JIT Tests/0.8.1-build-16/`.
  IPA 22,777,560 bytes, SHA256
  `3fe02d4b0e56681c4b6aa21dbbf18c2b5644b272353392e3889a931744d1cbe6`,
  executable/dSYM UUID `3E088E90-C3AC-3EDF-A402-6DB882CBD91D`.
  Confirm delivery-receipt.json for actual cloud/phone status; preserve delivered bytes.
- Keep the existing guest, content, all five ZIPs and complete save sidecars.
  **No game/mod imports are needed for this update.** ZIPs supplied are identical
  recovery copies. Keep LC1 Launch with JIT OFF, script blank, Fix File Picker
  ON, and StikDebug LC2. Use this process's fresh script. Geometry remains
  two 64 MiB arenas, 128 MiB total; the template matches build 15.
- The fix is an ordinary Mono chunk minimum of max(64 KiB, page size, granule),
  replacing the old 16-page minimum (256 KiB on the phone). Preserve larger
  requests, dynamic allocation, ARM64 branch room, aliases and terminal guard.
  `build_runtime.py` replaces only mono-codeman.c.o in copied build 15 archives;
  the other 259 members, including its access-check fix, stay identical.
  Do not edit any accepted runtime source/archive or earlier delivered lane.
- **Never size the device arena from ordinary Intel-host chunk totals.** This
  omission caused build 15 despite build 8's prior evidence. Host tests now
  compile the real code manager with 16 KiB page/granule overrides and binding
  divisor four. These overrides are absent from the iOS binary. Exact-function
  tests cover 4/16/64 KiB geometry and ARM64 alignment; actual alias replay must
  include physical failure controls, real host chunk requests and native reserve.
  Host x64 sizing/execution is still not actual ARM64 code-size acceptance.
- Full helper host runs pass cold import and fresh reuse, canary save 0 → 3 → 6,
  real Lua wait/walk/resume/end, platform travel/carry, On/IL, audio and clean
  detach. The final run has 932 chunks, 54,589,024 raw / 56,213,504 rounded bytes;
  two such traces plus 16 MiB native reserve fit in 129,204,224 / 134,217,728 bytes
  without recycling. The physical build 15 failure is reproduced exactly.
- Phone steps remain helper map, Lua walk, ride platform, jump, Home 30 seconds,
  return and **jump after resume**, both helper passes, Finish, ten-second wait
  and Export to build 16 Results. Export first after a crash before new JIT.
  Check actual device allocation totals and full helper/save/lifecycle evidence.
  This physical test now passes; build 17 implements the GravityHelper step.
  Do not claim full SJ support yet.
- Frozen build 16 inputs are under
  `.build/ios-jit/device-evidence/2026-09-12/build-16-ready/`, inheriting build 15.
  Raw build 15 crash evidence is in the adjacent `build-15-crash/` folder.
  Export remains available. No commits, pushes or publication are authorized.

## Build 15 implementation history (startup crash diagnosed)


- Read [build 15](docs/ios-jit/SJ_HELPERS_BUILD_15.md) and its evidence before
  continuing. **Physical startup exhausted the code arena; build 16 supersedes it.** Source `experiments/ios-jit/sj-helpers/`, version 0.8.0 (15), build
  ID `sj-helpers-20260911-15`. The similarly numbered `content-picker/`
  simulator draft was never delivered and is not this release.
- Unsigned IPA is 22,777,253 bytes; SHA256
  `f04f2ff49aeb6dfd3da071f676cc3373644d37bf37b3d2cf925a0aa5cd32ac97`;
  executable/dSYM UUID `DC33EC80-FF01-3824-8531-60C1365045B9`.
  Local kit `artifacts/ios-jit/sj-helpers-20260911-15/`; iCloud handoff folder
  `Celeste JIT Tests/0.8.0-build-15/`. Confirm delivery-receipt.json for actual
  placement and phone download status. Preserve exact delivered bytes.
- Same guest/profile/content identity as build 14. Update its existing guest,
  check stored game data and initial 2/5 retained ZIPs before importing the
  three new ZIPs. Do not reimport Celeste or restore the intentionally deleted
  save. The physical export last saved canary counter 12; subsequent play may
  change it. Require `reused=True` and inspect update/save retention.
- Actual original LuaCutscenes 0.2.13 and MaxHelpingHand 1.40.9 plus authored
  CJITSJHelpers 1.0.0: total five ZIPs including the unchanged old canaries.
  Helper map measures Lua walking and the same coroutine finishing after
  resume, plus MultiNodeMovingPlatform travel/contact/carry. Require LUA and
  PLATFORM PASS, jumps before/after Home 30 seconds, Finish and delayed export.
  Keep Launch with JIT OFF, script blank, LC1 Fix File Picker ON, StikDebug LC2.
- **Build 15 geometry: two 64 MiB arenas, 128 MiB total.** Real helpers raised
  ordinary Intel-host allocations to ~52 MB/~900 chunks. This estimate missed
  16 KiB-page chunk inflation and proved insufficient on the phone. Exact native/script regression passes 8,192
  mocked page acknowledgements and rejects build 14 geometry. Use only the
  current process's generated script; do not use old templates/session files.
- Runtime member-access fix and MonoMod layout correction are isolated:
  `build_runtime.py` recompiles class.c into copied archives and checks the
  other 259 members unchanged; it honors existing IgnoresAccessChecksTo for
  protected/family-and-assembly members. Fifteen grant/absent/wrong-assembly
  cases pass per original/patched runtime. Type visibility is unchanged.
  `build_managed.py` removes the obsolete SetMonoCorlibInternal native byte
  write only in a copied MonoMod.Utils. Do not apply either in accepted outputs.
- Preserve MonoTypeDiscovery: original GetTypesSafe can throw an individual
  optional-dependency exception or expose failed RuntimeTypes. Use only the
  active Everest context's retained relinked Cecil metadata; force failed-base
  reporting before Lua's Namespace scan. The tested MaxHelpingHand retains
  443 types and skips four optional-dependent types. No fake dependencies or
  global resolver fallback. Original ZIPs/game/FNA remain unchanged.
- GravityHelper 1.2.28 is **deferred, not supported by this kit**: optional
  CelesteNetModSupport fails Mono type loading during GravityHelperModule.Load.
  Three-helper source/logs are frozen privately in
  `.build/ios-jit/sj-helper-gravity-investigation/`. Investigate a narrow
  optional-integration fix next, then restore its gravity/platform room and
  continue required helpers → SJ Beginner lobby/Bing. Full SJ is not accepted.
- Final actual-Mono host run uses the packaged adapter bytes: cached content,
  Lua checkpoints, moving platform, On/IL hooks, FMOD, save 6 → 9 and clean
  detach pass; earlier fresh processes passed 0 → 3 → 6. Host background calls
  do not prove iOS background survival. Package verifies 200 DLLs, 1,294 static
  game/FNA imports and 126 Lua imports. The helper DLLs have zero native imports.
- Source/input snapshot is under `.build/ios-jit/device-evidence/2026-09-12/build-15-ready/`,
  inheriting verified build 14/13 inputs. Export remains available. The small
  private app still contains prepared game IL and linked iOS FMOD. No public
  distribution, commits or pushes are authorized; AOT checkout remains read-only.

## Earlier physical acceptance: build 14 original-game content and Everest

- Read [the physical import acceptance](docs/ios-jit/CONTENT_IMPORT_PASS_2026-09-11.md)
  and its evidence. **Original FNA ZIP import and bounded Everest gameplay pass
  on the phone.** Exact IPA/template/assemblies and 137 frozen build inputs
  match; 1,216 files / 1,158,665,183 bytes imported in 4.638 seconds. Existing
  mod ZIPs and settings were retained. All 26 native/nine game checks, twelve
  On/IL hooks, real NLua callback, FMOD, touch, XML/YAML saves, 36-second resume,
  worker cleanup, detach and delayed liveness pass with no JIT/managed errors.
- The owner saw the previous save survive, then deliberately deleted it.
  Record that observation; do not classify the deletion or current mod counter
  0 → 12 as an importer failure. The old counter 50 was not independently
  observed reloading in this log. Do not restore an intentionally deleted save.
- The export contains one successful cold import (`reused=False`), plus older
  startup/build 13 sessions. **Build 15 now physically verifies fresh content reuse and the post-import
  content/mod update.** Save reload still needs a successful gameplay session;
  preserve the current save and do not restore the intentionally deleted one.
- Next development: actual LuaCutscenes script/coroutine and real SJ helper
  coverage, then Beginner lobby/Bing. Start from preserved build 14 in a new
  source/staging lane. The exploratory `content-picker/` build-15 simulator
  is not the next release. Raw export/validator/derived evidence are private at
  `.build/ios-jit/device-evidence/2026-09-11/build-14-pass/`.

## Build 14 implementation and delivery history

- **Picker resolution:** the owner confirms enabling **LiveContainer 1 →
  long-press Celeste JIT Everest → Settings → Fixes → Fix File Picker** resolves
  the local-ZIP/Open-button stall. Keep this setting in future setup guides.
  Continue build 14; no replacement is needed for selection. Read
  [the resolution](docs/ios-jit/BUILD_14_FILE_PICKER_RESOLUTION.md). The initial
  picker export proved retained mods only; the later export above proves import
  and gameplay after applying the setting.
  `content-picker/` and build 15 simulator output are exploratory **drafts**,
  not delivered/accepted and not the active phone build. Preserve build 14.

- Read [build 14](docs/ios-jit/CONTENT_IMPORT_BUILD_14.md) and its evidence before
  continuing. **Phone import/gameplay now passes; cached reuse and the
  post-import update still need the check described above.**
- Source `experiments/ios-jit/content-import/`; version 0.7.0 (14), same Everest
  bundle/profile as build 13. Unsigned IPA 22,774,779 bytes, no Content files.
  IPA SHA256 `44f9f20b5387845dfc7b6f8094492cddab5ce45c4c6364fb7cbab5c94a6fe57b`;
  executable/dSYM UUID `1CDBC62C-5B15-38C8-AA39-376CC3D1A939`.
- The owner wants a normal store download, not a build 13 dependency. The
  intended first input is itch.io **Celeste Windows (FNA) 1.4.0.0**,
  `celeste-win-opengl.zip`, selected directly in Files. All 1,216 Content files
  in the supplied original archive match the trusted manifest. Linux's actual
  ZIP and direct folder import are not yet validated; do not advertise them.
  Build 13 extraction is only an optional private fallback, never required.
- Persistent `Documents/GameLibrary/v1/<identity>/<generation>/Content`, atomic
  relative active pointer, full hashes, staged/cancellable import, bounded ZIP
  parsing and marked interrupted-stage recovery. Keep original Files sources,
  complete mod saves and current guest data. Rebuild only the isolated adapter;
  never regenerate accepted Everest/AOT outputs in place.
- 39 content-store checks and native copy/cancel/error tests pass. Real pinned
  Mono cold import/gameplay passes; a fresh process reuses content and reads
  mod save 3 → 6. Expected cancellation/invalid-input retries pass in the same
  runtime. Simulator staging/update, export/recovery, exact package and
  4,096-page protocol regression pass. The subsequent physical import/gameplay
  acceptance is recorded above.
- Existing ZIPs, original FNA import and game execution now pass on the phone.
  The owner intentionally deleted the previous save. At the next guest update,
  run without importing anything and export before repairing/reimporting data
  if retention fails. Use the new saved counter, not the deleted save, as the
  reference. Preserve Export for iCloud/share diagnostics.
- Kit `artifacts/ios-jit/content-import-20260911-14/`; iCloud folder
  `Celeste JIT Tests/0.7.0-build-14/`. Freeze exact bytes before delivery;
  corrections need a new version. Source/input evidence is in
  `.build/ios-jit/device-evidence/2026-09-11/build-14-ready/`, inheriting verified
  immutable build 13 dependencies. Preserve local accepted installers/symbols.
- This private small app retains prepared game IL and iOS FMOD. Full on-device
  original-IL preparation/public game-free packaging remain separate gates.
  Proceed to real LuaCutscenes/SJ helper development, then Beginner lobby/Bing;
  include cached-content/update retention in the next physical test. No
  commits/publishing authorized.

## Earlier physical acceptance: build 13 Everest

- Read [physical Everest acceptance](docs/ios-jit/EVEREST_EXECUTION_PASS_2026-09-11.md)
  and its evidence. Exact build/ZIP/script/frozen-input validation passes.
  Both normal ZIPs load through real Everest; the custom entity, 50 normal and
  50 IL hooks, ARM64 NLua callback, FMOD, XML/YAML saves, 35-second resume and
  clean shutdown pass on iPhone16,2 / iOS 26.5. No repeat baseline is needed.
- The sole export contains one cold process: mod save prior 0, written/readback
  50. Fresh-process reload is not evidenced; include it in the build 14 update
  test and verify that the current guest's saved counter survives.
- Runtime: 15,891 owned JIT completions, 43 patches, no JIT/managed/patch errors,
  code reservations 22,102,016 / 67,108,864 bytes. Peak sampled footprint is
  1,469,171,736 bytes, not an SJ memory/performance result.
- Private evidence: `.build/ios-jit/device-evidence/2026-09-11/build-13-pass/`.
  Preserve the frozen build 13 source. Build 14's independent source root is
  `experiments/ios-jit/content-import/`, with `.build/ios-jit/content-*` staging.
  Prioritize persistent content and a small IPA as described below.

## Build 13 implementation and delivery history

- Read [build 13](docs/ios-jit/EVEREST_BUILD_13.md) and
  [its evidence](docs/ios-jit/EVEREST_BUILD_13_EVIDENCE.json) first.
  **Physical Everest now passes as recorded above.** Build 12 remains the
  earlier vanilla baseline. Do not claim Strawberry Jam support from build 13.
- Source: `experiments/ios-jit/everest-canary/`; private stages
  `.build/ios-jit/everest-*`. Actual Everest 1.6458.0, pinned dependencies,
  original Celeste IL conversion/patching, HookGen and legacy relinking replace
  the build 12 game reconstruction. Preserve the original owner inputs.
  The accepted Mono 8.0.28 runtime and paired FNA/build 11 Metal lifecycle stay
  in use. AOT/interpreter remain disabled; the AOT checkout is untouched.
- **Celeste JIT Everest 0.6.0 (13)**, separate bundle
  `io.github.hmcneill46.celeste.everest.jit.everest`, imports exactly two normal
  ZIPs: `CJITCodeCanary-v1.0.0.zip` and `CJITTestMap-v1.0.0.zip`. No external
  game DLL is needed. Its dedicated profile preserves complete Everest save
  sidecars. Arbitrary mod import, on-device base-game preparation, multiple
  profiles and mod unloading remain future work.
- The actual code ZIP loads/relinks in EverestModuleAssemblyContext, uses
  generated On/IL Player.Jump hooks and a CustomEntity counter sign. Preserve
  the narrow generated-DMD resolver: unique exact identity, already loaded
  Everest context only, no disk loads. Do not replace normal Everest loading.
- Native Lua 5.4.8 with real KeraLua/NLua passes a Lua-to-managed callback on
  host. Compression and Apple cryptography use matching 8.0.28 native shims.
  LuaCutscenes scripts/coroutines and iOS callback ABI remain separate gates.
- Preserve the documented platform fixes: ContentManager root before wrapping;
  clear Cecil PInvokeImpl after null PInvokeInfo; optional FMOD DSP CPU query
  returns ERR_UNSUPPORTED; FNA IsTextInputActive queries real SDL. Twenty
  Everest Player precision sites explicitly widen both multiplication operands
  and narrow the float argument. Mixed-width host Mono IL previously returned
  zero and broke gravity; retain the generated probe and real movement test.
- Worker cancellation/disposal, per-worker autorelease pools, frame-pumped
  normal saves and retained graphics/audio shutdown are required. The embedded
  profile gates desktop startup/updating/Discord/watchers. Do not copy those
  changes into the accepted AOT or earlier canary sources.
- Final cold host test passes real room/movement/hooks, Lua, FMOD, suspend/
  resume, module save readback 0 → 3, clean workers and detach. A separate warm
  process reads 5 and writes 8. Confirmed Metal API Validation and requested
  NSZombieEnabled pass. Host reports 14,849 JIT completions, 223 chunks and
  9,662,143 code bytes; these are not phone memory/performance results.
- **New geometry: two 32 MiB arenas, 64 MiB total.** Use only build 13's
  automatically generated PID/nonce script. Build 12's script is incompatible.
  Actual binary/simulator request/template passes 4,096 mocked acknowledgements,
  detach and stale/old-geometry rejection. Device geometry now passes in the accepted build 13 export.
- Simulator ZIP import/JIT gating/800-event persistence/export/recovery pass.
  Package validation resolves all 1,294 game/FNA/FMOD and 126 Lua imports and
  verifies exact IL/content/native hashes. dSYM stays outside the unsigned IPA.
- Artifact: `artifacts/ios-jit/everest-canary-20260911-13/`.
  IPA SHA256 `33f75af49dfbf64e2e3a948b25fb94acf4de4ada56a38b236a8c05abaed13942`;
  executable/dSYM UUID `D4A8C72A-0615-3971-B447-EFAAF0A5E4A8`.
  Private snapshot: `.build/ios-jit/device-evidence/2026-09-11/build-13-ready/`,
  4,900 unique verified files, including 140 build sources, all five pinned
  upstream trees, originals/patched IL, native inputs, symbols and regressions.
  Delivery receipt freezes this ID: corrections require a new versioned kit.
  The nine-file private kit is 890,186,809 bytes, including owner game assets.
  Read the report/current delivery receipts for verified phone/cloud placement;
  an interrupted transfer or a local iCloud copy is not full delivery.
- Physical procedure: LC1 new guest, Launch with JIT OFF/script blank, import
  both ZIPs, enable via LC2, return to same process, Run Celeste + Everest,
  Test map. Move/jump/dash 20 seconds; Home 30 seconds; return/jump 10 seconds;
  Finish, PASS, wait 10 seconds, export to build 13 Results. Then fresh-process
  JIT/run verifies a nonzero saved counter; repeat and export a second log.
  On crash, reopen and export before another JIT request. Preserve Export.
- The owner wants a small IPA with one-time owned game imports, ideally build
  14. Follow [the content import plan](docs/ios-jit/CONTENT_IMPORT_NEXT.md).
  If build 13 passes, prioritize persistent content import/small app updates
  before the full SJ handoff. The measured non-Content compressed members are
  22,707,700 bytes (about 23 MB before importer changes/ZIP overhead); this is
  an estimate, not an actual build 14. Keep the same guest identity and verify
  update retention. The first private asset-only split may retain prepared IL;
  full on-device original-IL preparation/public packaging is a later gate.
  Retain build 13's IPA as a possible exact private content-import source;
  its validated Content can avoid another large initial download. Implement
  and test that option before claiming it works.
  If build 13 crashes, fix it first rather than force the importer into build 14.
- Then test actual LuaCutscenes and real SJ helpers, followed by Beginner
  lobby/Bing. The full 52-archive SJ set exceeds the current
  1 GB handoff limit. No commits, pushes or public distribution are authorized.

## Latest accepted stage: build 12 physical Celeste gameplay

- Read [physical game acceptance](docs/ios-jit/CELESTE_EXECUTION_PASS_2026-09-11.md)
  and [evidence](docs/ios-jit/CELESTE_EXECUTION_PASS_2026-09-11_EVIDENCE.json).
  **Build 12 passes bounded Celeste JIT gameplay/audio/saves/resume** on the
  target iPhone. Exact IPA, imported DLL, script, 114 build inputs and 925 game
  inputs match the delivered snapshots. Owner reports all visible checks passed.
- Logs show Prologue through Forsaken City, 8,382 callbacks, 6,455 level frames,
  58 hooked jumps (22 after resume), 158 touch presses/releases and 34.829
  seconds background in the same process. All nine game/graphics assertions,
  actual FMOD 1.10.09 with six bank-load events, XML settings/slot-0 readback,
  seven completed workers, hook disposal and managed detach pass.
- Delayed foreground liveness is present; export occurred 16.583 seconds after
  PASS. The owner used the ordinary menu rather than the Prologue button, which
  is valid. No repeat baseline test is needed. Fresh-process save reload was
  optional and remains untested; do not claim arbitrary mod save compatibility.
- 9,579 JIT completions are owned; zero JIT/managed/patch errors. Code reservation
  is 9,961,472 / 33,554,432 bytes. Peak sampled physical footprint is
  1,209,288,368 bytes; this is not managed heap or an SJ capacity estimate.
  Controller play, older devices, later chapters and sustained performance are
  untested. LC/StikDebug version preferences are not fresh measured metadata.
- Raw iCloud export, validator and extracted events/console tail are private at
  `.build/ios-jit/device-evidence/2026-09-11/build-12-pass/`; export SHA256
  `d50e2a6c5cf951e9667c27f89802f4ed8f7124c6576d987e2f0586ac52b66c0f`.
  No new debugger attachment was needed. Preserve the accepted source, kit,
  receipts, symbols and build-12-ready snapshot; do not rewrite delivery history.
- **Everest implementation now exists in build 13 above; SJ follows**, using
  [the next-stage contract](docs/ios-jit/EVEREST_INTEGRATION_NEXT.md).
  The separate everest-canary source/staging lane prepares original IL with
  pinned Everest 1.6458.0 and generated hook surface, preserving the iOS backend
  and paired FNA/Metal callback semantics. Its assembly-context loading and
  small normal map/code ZIPs await phone acceptance. Native Lua/NLua and real callback/cutscene coverage
  are required work for SJ; do not substitute the AOT helper/cutscene shims.
- The existing SJ graph pins 52 archives / 1,237,284,560 compressed bytes,
  including StrawberryJam2021 1.0.12 and LuaCutscenes. This is metadata, not a
  freshly verified local ZIP set or JIT compatibility evidence. First SJ target:
  real dependency closure, Beginner lobby and Bing, then expand coverage.
  Full SJ alone exceeds the current 1 GB total handoff limit; use owner imports
  or resolve a larger transfer when a concrete kit exists. Do not silently split
  a large kit into batches to bypass the limit. Build 13's kit has no SJ ZIPs.

## Build 12 implementation and delivery history

- Read [build 12](docs/ios-jit/CELESTE_BASELINE_BUILD_12.md) and
  [evidence](docs/ios-jit/CELESTE_BASELINE_BUILD_12_EVIDENCE.json). Physical game
  acceptance was pending at delivery and now passes as recorded above.
  Everest/mod compatibility remains unverified.
- Source: `experiments/ios-jit/celeste-canary/`; private staging
  `.build/ios-jit/celeste-*`. Preserve accepted G1/G2/graphics source and the
  build 11 FNA/native renderer pair. Do not regenerate into the AOT checkout.
- **Celeste JIT Game 0.5.0 (12)**, bundle
  `io.github.hmcneill46.celeste.everest.jit.game`, runs real untrimmed Celeste
  1.4.0.0/FNA IL on Mono 8.0.28. No Everest or ZIP loader is included yet.
  Native components stay compiled; do not enable AOT/interpreter as a fallback.
- Reuse the pure iOS touch policy/artwork and virtual-input delegate extension
  through the new binding-free adapter. Existing .NET Apple managed bindings,
  the complete layout editor and vanilla Save Manager are not imported.
  Save roots are this guest's `Documents/Profiles/vanilla-jit-canary/`.
- Native frame callbacks own a retained game; all Metal callback cleanup stays
  paired. Preserve worker autorelease pools and balanced Mono transitions.
  Finish waits for loading/saving while pumping frames; never block the main
  thread joining a loader that needs GPU work. Suspend/resume the Celeste-owned
  FMOD mixer and native AVAudioSession. Preserve the after-resume jump assertion.
- Exact owned Mac/FNA input validates. ILSpy 8.0.0.7246-preview3 must run under
  the private pinned .NET 6.0.36 tool runtime to reproduce canonical raw source
  logical hash `db7b722159fbdef8625c81608165aea162957dce956fcd5b16eeceaa1089a273`.
  The raw manifest normalizes csproj reference paths; snapshot hashes retain
  actual bytes. Generated source, game binaries/assets and FMOD stay ignored.
  The private reconstruction is not the future original-IL importer.
- Host real game passes title/Prologue, 760 level frames, reused touch input,
  two Player.Jump hook calls including one after resume, FMOD initialization,
  XML save/readback and clean stop/detach. Host touch uses injected SDL finger
  snapshots; host FMOD 1.10.14 differs from device 1.10.09. NSZombieEnabled plus
  confirmed Metal API Validation passes. Physical picture/audio/control testing
  is now accepted above. Default Mono GC policy handles the specifically unsupported
  SustainedLowLatency override; do not suppress unrelated exceptions.
- FMOD version digits are BCD: the actual host/header value `0x00011014` means
  1.10.14, despite inherited notes/frozen canary README labelling it 1.10.20.
  The exact iOS Studio creation check masks the low byte and requires
  `0x00011000`, so this header passes. Its linked core must match `0x00011009`.
  Record raw values and preserve this documentation correction without changing
  frozen build 12 inputs. Bounded vanilla audio now passes physically; mod-bank
  compatibility remains a separate test gate.
- Code planning: 113 host chunks / 5,062,192 bytes, 8,806 JIT completions;
  fourfold 16 KiB-rounded estimate 20,824,064 bytes. The phone still uses two
  16 MiB arenas. This is not physical capacity, performance or mod headroom.
- Simulator exact import/JIT gating, console/current/previous-session recovery
  and 800-event burst pass. Exact binary/request/script passes 2,048 mocked
  acknowledgements/detach and rejects old geometry/stale identity. All 1,294
  declared FNA/FMOD native imports resolve; no signatures/profile/dSYM in IPA.
- Artifact: `artifacts/ios-jit/celeste-canary-20260911-12/`.
  IPA SHA: `6b72dfb799bceeb31a9978e5d948ba37aa902c87c831fbad13591cbcfe578d76`.
  External `CelesteJITGame-v0.5.0.dll` SHA:
  `6fcb34e8a9799d6b94e4caba8b37dc6aaae50da6863c03c35dd851427c47ad5b`.
  UUID: `4995D4CF-76A3-3619-955C-A62CFC6C09E7`. Script matches accepted build 9.
  Snapshot: `.build/ios-jit/device-evidence/2026-09-11/build-12-ready/`,
  2,631 unique inputs plus symbols, packaged IL and complete test evidence.
  Delivery receipt freezes this ID; corrections need a new versioned kit.
- **Build 12 is on the phone:** nine files and Results, 883,114,836 bytes, at
  `On My iPhone/LocalSend/Celeste JIT Tests/0.5.0-build-12`. All files were
  copied over Wi-Fi and read back by SHA-256 at **2026-09-11 18:43:26 UTC**.
  The identical iCloud folder `iCloud Drive/Celeste JIT Tests/0.5.0-build-12`
  reports all nine files/Results uploaded without error at **18:42:57 UTC**.
  Host did not install/launch the IPA; the owner's later physical pass is above.
  This private kit includes the owner's full game content; no extra download
  is needed. Use README-FIRST and export into the adjacent LocalSend Results;
  the INSTALL guide's iCloud Results path remains a valid alternative.
- A direct Wi-Fi fallback also works through the existing Apple native tunnel
  and `com.apple.mobile.house_arrest.shim.remote`, even when usbmux's network
  list is empty and CoreDevice appDataContainer fails. Read
  [the Wi-Fi handoff](docs/ios-jit/WIFI_FILE_HANDOFF_2026-09-11.md). Verify the
  target UDID/model, vend only LocalSend Documents, stream to `.uploading`, read
  back by SHA-256 and rename only after verification. The build 12
  `phone-wifi-handoff.json` confirms overall completion. Preserve this method
  for future handoffs; small-file/partial progress alone is not full delivery.
- Install as a separate LC1 guest, JIT OFF/script blank; import matching DLL,
  enable through LC2, return to the same process, Run Celeste. Wait for title,
  tap Prologue, move/jump 20 seconds, Home 30 seconds, return and jump/play
  10 seconds, Finish, wait 10 seconds, export to build 12 Results. Ask for
  picture/audio/multi-touch/resume observations. On crash export before another
  JIT request. Optional second launch checks slot 0 persists.
- After physical baseline acceptance, prepare real pinned Everest patches and
  hook surface, then one small map/code mod. Preserve originals and full module
  save sidecars. No claim of arbitrary mod compatibility or public distribution.

## Latest accepted graphics stage: build 11 physical pass

- Read [physical graphics acceptance](docs/ios-jit/GRAPHICS_EXECUTION_PASS_2026-09-11.md)
  and [evidence](docs/ios-jit/GRAPHICS_EXECUTION_PASS_2026-09-11_EVIDENCE.json).
  Build 11 passes bounded JIT FNA/Metal/touch/resume: 3,758 draws, 24 presses and
  releases, 53.487 seconds background in the same process, 2,562 post-resume
  frames, all 10 graphics checks and clean game/hook/thread cleanup.
- 3,974 JIT completions were owned; 7 executable patches, no runtime/patch errors.
  Code reservations were 4,685,824 / 33,554,432 bytes. This is not full-game
  capacity. Real orientation Reset and all build 10 regressions passed.
- The owner visually confirmed the test. Export occurred 1.334 seconds after
  PASS, before the delayed liveness marker; record this bounded timing limit,
  without requiring another build solely for the longer dwell.
- Exact delivered build/DLL/script/snapshot match. Untouched export/validator:
  `.build/ios-jit/device-evidence/2026-09-11/build-11-pass/`; SHA256
  80593a97bcc3d6617e8ad97c95e85348ffb29b698802fb6da62dac4f8c0443b1.
- Preserve accepted graphics-canary source/kits and the paired native/FNA build.
  New Celeste integration must use a separate canary/source/staging lane. Reuse
  the native callback-boundary contract, single UIKit/SDL lifecycle, custom Mono
  runtime and hooks deliberately. Celeste gameplay/Everest/mod acceptance pending.

## Build 11 implementation history: Metal callback-lifetime correction

- Read [build 10 crash / build 11 fix](docs/ios-jit/BUILD_10_GRAPHICS_CRASH_AND_BUILD_11.md)
  and [evidence](docs/ios-jit/BUILD_10_GRAPHICS_CRASH_AND_BUILD_11_EVIDENCE.json).
  **Physical graphics now passes as recorded above.** Build 10's owner setup/DLL/script were
  correct: 26 native checks, 3,400 owned JIT completions, render hook and Metal
  GPU readback passed. First Draw was not reached. The first orientation reset
  used a command buffer released when UIKit drained the startup callback pool.
- Raw build 10 export, validator, exact disassembly and host negative are in
  `.build/ios-jit/device-evidence/2026-09-11/build-10-crash/`. Raw SHA:
  7bde6d5594e04802af0ceb67f98509383c6ab00fa102e29d13b4abb0dc047bca.
  Correct recovered export did not run JIT again. No OS crash report/debugger
  attach was needed. Code use was only 4,161,536 / 33,554,432 bytes.
- **Never let the pinned Metal frame/autorelease pool span native callbacks.**
  Per-callback host pools reproduce the old deallocated command-buffer failure;
  one pool around the whole host run hides it. Keep that regression.
- Build 11 pairs private FNA begin/frame/end finally blocks with
  `FNA3D_CJIT_EndCallback`: submit pending GPU work and drain its pool without
  acquiring a drawable or adding a Present. Normal Present shares completion.
  Pending clears precede old backbuffer release during Reset; destruction waits
  for/releases the final committed buffer. Pair the DLL and native API strictly.
- Patch: `experiments/ios-jit/graphics-canary/native/fna3d-callback.patch`.
  Build with `native-build.py` into `.build/ios-jit/graphics-native-build11/`.
  Overlay only FNA3D; accepted foundation archives/locks remain unchanged.
  Keep the pinned source/patch/native receipts and symbols. A future native
  change needs a new private stage/version; preserve delivered build 11 inputs.
- **Celeste JIT Graphics 0.4.1 (11)**, bundle
  `io.github.hmcneill46.celeste.everest.jit.graphics`. Update in LC1, Launch with
  JIT OFF/script empty, StikDebug in LC2. Import `GraphicsCanary-v0.4.1.dll`,
  use the app's fresh enable-JIT route, then Run graphics. The automatic tests
  include pending-clear Reset, startup completion and a suppressed Draw/readback.
- Artifact/symbols/receipts: `artifacts/ios-jit/graphics-canary-20260911-11/`.
  IPA SHA: e43de74fc9e09d6bd22b3255f2c6cbd0d09e5bd04886d09b253daf42986e380f.
  Fixture SHA: 4ef16eb0793ca8109f0c1fb2763fd68e7491139784d5e002b71b161074cb2f89.
  FNA SHA: 802b6dd2fe0a6c386d1b29b48dfea358ce85fe4f2530332410bcfaa015bfcbf0.
  Mach-O/dSYM UUID: B911C775-CB28-3A99-A569-A9851A4B6723.
  Snapshot: `.build/ios-jit/device-evidence/2026-09-11/build-11-ready/source-snapshot/`,
  97 build inputs + 321 FNA + 322 native sources, 739 unique files.
- Host passed 540 callbacks / 539 Metal draws plus a deliberate skipped Draw,
  reset/readbacks, retained hook after resume/GC, removal and clean detach.
  It uses the same patched FNA3D source as iOS. NSZombieEnabled plus confirmed
  Metal API validation also passed. This is not physical iOS acceptance.
  Simulator import/export/recovery and 800 events passed. Exact native request/
  script protocol passed 2,048 acknowledgements and detach in a fake server.
  All 806 native imports resolve; dSYM remains outside the unsigned IPA.
- Kit: `iCloud Drive/Celeste JIT Tests/0.4.1-build-11`, six files plus Results,
  11,927,092 bytes. All six files/Results are confirmed uploaded with no error
  at **2026-09-11 16:55:31 UTC**; copied hashes match. Phone download/installation
  is unobserved.
- Phone test: drag/release ~20 seconds, Home 30 seconds, same-process return,
  drag/release and wait 10 seconds, Finish, wait 10 seconds, export to build 11
  Results. Require visible graphics/touch plus logs. On crash reopen/export
  before another JIT request. Keep Export even with direct USB collection.
- UIKit owns one scene; main-thread display link drives one retained FNA game.
  Bootstrap worker detaches; main-thread GC transitions and final detach remain
  balanced. Pause frames before inactivity, forward SDL lifecycle, reset clock
  and verify hook after resume. Never reinitialize arenas over a live runtime.
- G1/G2 runtime, allocator, hook bridge, exact script and two 16 MiB arenas are
  unchanged. General game capacity/unload/restart are still unresolved.
  Celeste needs an explicit retained lifetime adapter: returning early from its
  existing using/Run scope would immediately dispose it. Build 12 implements
  that adapter, native FMOD, content and isolated saves; its bounded physical
  game test now passes. Full Everest/mod behavior remains pending.
- Historical build 10 implementation/immutable kit:
  [original graphics report](docs/ios-jit/GRAPHICS_BRIDGE_BUILD_10.md).
  Direct USB collection selects this graphics bundle and discovers its verified
  guest UUID; never reuse Hook Canary's UUID or another connected iPhone.

## Latest accepted stage: build 9 physical Hook/ILHook pass

- Read [the physical G2 result](docs/ios-jit/HOOK_EXECUTION_PASS_2026-09-11.md)
  and [evidence](docs/ios-jit/HOOK_EXECUTION_PASS_2026-09-11_EVIDENCE.json).
  **Build 9 is accepted for bounded G2**: 42 assertions, 108 patches, 2,989
  JIT completion events, all ranges owned, two clean worker detachments and
  retained/fresh hooks after 65.299 seconds background in the same process.
- Code high water is 13,959,168 / 33,554,432 bytes (87 reservations). No
  allocation, patch, JIT or managed failure occurred. This is code reservation,
  not total resident memory or a game capacity estimate.
- Exact build/DLL/script/source snapshot match. Native checks executed all
  2,048 prepared pages. The initial foreground dwell was 4.907 seconds rather
  than the requested 10; its timer ran just after backgrounding. Resume had
  a further 5.237 seconds foreground liveness. This timing deviation does not
  invalidate bounded execution/resume acceptance.
- Untouched raw export and validator: `.build/ios-jit/device-evidence/2026-09-11/build-9-pass/`.
  Export SHA f1d44cdfae2f42c6b25872997cbe28813dc385e5ee5043efc3f1caeef30723f3.
  No new crash or device debugger attach was needed. LC/StikDebug versions in
  this export are carried-forward preferences, not fresh installation metadata.
- G3 preparation is isolated under `.build/ios-jit/game-native`,
  `game-native-output` and `game-foundation`. All five device/simulator native
  libraries rebuilt with Xcode 26.6 and match accepted native logical hash
  `9fb302d221180e39f270ea5ebf48e18433b67bd0a40943c042a227fe0f8ad6a2`.
  Next is a JIT-managed FNA/Metal/input/lifecycle bridge before the full game.
  Do not treat native compilation or a graphics probe as G3 gameplay acceptance.

## Build 9 implementation and retained history

- Current retest: **hook-canary-20260911-09, 0.3.2 (9)**. Read
  [build 8 capacity failure and build 9 correction](docs/ios-jit/BUILD_8_CAPACITY_AND_BUILD_9.md)
  and [its evidence](docs/ios-jit/BUILD_8_CAPACITY_AND_BUILD_9_EVIDENCE.json).
  Physical G2 was pending at delivery; its accepted result is recorded above.
  Preserve the build 6 G1 and build 8 failure evidence as earlier gates.
- The owner's build 8 setup/DLL/script were correct. The build 7 protocol fix
  worked: 26 native checks, eight G1 stages, 21 Hook/ILHook assertions and 54
  verified executable patches passed. There were 2,863 JIT completion events,
  all owned, with 2,617 distinct entry addresses / 963,708 reported code bytes.
  The struct-return SyncProxy compilation then exhausted the 8 MiB arena.
  After 8,192,000 reserved bytes, a 262,144-byte request failed. Mono's thunk
  memset precedes its code-pointer null check, causing SIGSEGV. Struct-hook
  execution, remaining cases, initial clean detach and resume were not reached.
- Raw export, extracted events/console, validation, inferred-slide symbolication
  and actual binary disassembly are preserved privately at
  `.build/ios-jit/device-evidence/2026-09-11/build-8-crash/`. Do not publish logs.
  Export SHA: 52414eae61af815d85ece23fa6f0e57a572d314c08c7a6ee3b91d09de6ad4f7f.
  Exact delivered build 8 symbols/source/IPA remain preserved; no OS report or
  debugger attach was needed to reproduce this capacity failure.
- Source is `experiments/ios-jit/hook-canary/`. `CJHookMemory.h` now defines
  **two 16 MiB arenas (32 MiB total)**. `CJHookProtocol.h` explicitly imports
  the G1 mailbox layout, but the hook launcher uses CJ_HOOK_ARENA_LENGTH, not
  the G1 capacity constant. Descriptor __TEXT,__cjprotocol, compiler-dependency
  checks, request builder and reply bounds must agree with the packaged script.
  Keep actual binary/request checks: build 7 previously selected the 64 KiB
  native header while BuildInfo claimed 4 MiB. Static metadata was insufficient.
- The matching script now lives in **hook-canary/scripts/celeste-jit-probe.js**.
  It requires 16 MiB arenas and individually acknowledges **2,048 page writes**.
  Do not accidentally package the managed-canary 4 MiB script. The native
  builder/binder + exact IPA script integration completes all pages/readback/
  detach in a fake debugserver and rejects build 7/8 capacities, wrong PID and
  stale nonce. Sixteen failure/success mock cases run in hook-canary/tests.
  Run check_request_protocol.py after simulator_smoke.py with Node on PATH.
- `CJHookCodeArena.c` compiles the unchanged G1 allocator with an event wrapper:
  persist allocation failure and jit_code_budget_exhausted, then abort before
  Mono can use NULL. This is terminal, not graceful runtime recovery. Preserve
  export of previous sessions/console. Hook stage/patch logs include reserved
  bytes, budget and allocations. Do not reuse live code to satisfy exhaustion.
- Actual-allocator replay with 16 KiB pages and ASan/UBSan reproduces build 8 at
  request 66. Three traces fit build 9: 198 reservations, 25,362,432 / 33,554,432
  bytes. A child process verifies the terminal event/SIGABRT. This is host
  allocator replay, not ARM64 execution or proof that a game fits.
- Pinned macOS Mono rerun passed eight G1 stages, 42 hook assertions plus two
  completion markers, 108 patches and two clean worker detachments. It recorded
  99 host code chunks / 4,078,956 cumulative bytes. Fourfold scaling with 16 KiB
  rounding suggests 16,908,288 bytes; this is only a planning estimate. Require
  physical memory high-water results. The unchanged native patch alias test
  receipt was retained after checking all its source hashes, not rerun.
- Mono 8.0.28 runtime archives, seven-file runtime patch, 168 framework DLLs,
  ten MonoMod/Cecil DLLs, native hook bridge, resolver, GC helpers and external
  fixture bodies remain unchanged from build 8. G1 source/kits and independent
  AOT work are unchanged. AOT and interpreter are disabled in this JIT runtime.
- MonoMod is pinned to dfc30a1506d37fb88a2c2be004f525205f46a24c in the private
  hook-runtime clone. Its hosting patch fixes initial platform installation,
  .NET 8's _mhandle DynamicMethod field and Apple OS/arch detection. Explicit
  AppleJitSystem keeps actual Hook/ILHook, Mono detour factory and ARM64 emitter.
  SDK 9.0.300 is a private build tool; device runtime is Mono 8.0.28.
- Device hook writes must fit actual Mono method code or explicit hook
  allocations, with prepared ownership, exact RX/RW protections, alignment,
  backup, RW stores, cache flush and readback. Padding does not authorize a
  patch. Host-only RWX code must remain compiled out on device. Generic source
  methods and generic declaring types are rejected by the public Hook API;
  the fixture verifies the restriction. Mutations are serial; concurrent
  patch installation, inlined callers and recompilation remain unverified.
  The upstream ARM64 detour requires 16 owned method bytes.
- App: **Celeste Hook Canary**, same bundle ID/data. Fully close the old process,
  update in LC1, import **HookCanary-v0.3.0.dll**, keep Launch with JIT OFF and
  launch script empty. StikDebug stays in LC2. App sends its NEW fresh script.
  After initial hooks pass, wait 10 seconds, go Home for 30 seconds, return to
  the same process and tap **4. Run resume tests**. Require retained/fresh hooks,
  new DynamicMethod, clean second detach, g2_hooks_pass, result UI and liveness.
  Never rerun native rewrite tests or arena initialization over active Mono.
- Kit: **iCloud Drive/Celeste JIT Tests/0.3.2-build-9**, six files totaling
  **10,906,448 bytes**, plus Results. All files/Results report uploaded with
  no error at **2026-09-11 10:38:29 UTC**. Copied hashes match; phone download
  and installation are unobserved. Preserve previous versions. On crash,
  reopen/export before another JIT request. Export remains required fallback.
- IPA SHA: ac730cd2847dedce41b93a5de8f6f0a1369e8f53b7c7bb0499e250d9abb5b532.
  DLL SHA: c4256d9f5f6400fe5b23a7b1590c4b343c280a90d882fbce3efb37999dc28157.
  Script SHA: bfd36579c919cd060bb28fa201fa3056b4a7e19793d9d835539bb62abe24b413.
  Mach-O/dSYM UUID: 3CA3AD77-C8F4-3B16-8D6C-A3ABB1ACD9DF.
  Artifacts/symbols/receipts: `artifacts/ios-jit/hook-canary-20260911-09/`.
  All 80 source files are snapshotted at
  `.build/ios-jit/device-evidence/2026-09-11/build-9-ready/source-snapshot/`.
  Builder rejects overwriting delivered kits. Future corrections need a new
  version/build number. No GitHub writes/commit/push are authorized.
- Review physical G2 before Celeste integration, then Everest and small mods.
  The 32 MiB budget is process-lifetime canary capacity, with no late growth,
  reliable unload or runtime restart. Code-manager sizing, generated assembly
  pooling and reclamation need separate lifetime/branch/cache/concurrency tests
  before becoming a game allocator policy. No arbitrary mod acceptance yet.

## Current research baseline

- Audit base: `b65bedd20016dc3482d7702d7f0a9707bc2b1479`.
  Local audit branch: `codex/ios-jit-feasibility-audit`.
- At audit time `origin` points to `https://github.com/hmcneill46/celeste-ios.git`.
  The folder name does not imply a separate remote. Inspect status/remotes before
  integration, and preserve other contributors' uncommitted work.
- The audit is a conditional go for runtime/hook prototypes. It does not prove
  managed JIT, LiveContainer game execution or arbitrary Everest compatibility.
  Update the evidence and development status as actual milestones are completed.
- Pinned Everest `stable-1.6458.0` is at
  `4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00` (net8.0).
  Pinned MonoMod `dfc30a1506d37fb88a2c2be004f525205f46a24c` has ARM64 support but
  throws for `OSKind.IOS`; its CoreCLR adapter stops at major version 9.
- Better references: Webleste for actual Everest/custom-Mono detours; Amethyst
  for native launcher/embedded-runtime JIT startup; StikJIT and LiveContainer
  for the actual iOS 26 protocol. MeloNX's managed library is NativeAOT and its
  JIT translates guest instructions; it is not proof of dynamic CLR loading.

## Architecture rules

- Keep one managed runtime for Celeste, managed FNA, Everest and active mods.
  Use a native pre-JIT launcher/bootstrap and a narrow native bridge.
- Initial JIT game payloads retain IL and reflection metadata. Do not enable
  full trimming or transplant the fully trimmed AOT closure into a dynamic
  loader. Selective managed AOT is a later measured optimization.
- Standard `UseInterpreter=true` means interpretation, not JIT. Current
  supported CoreCLR iOS R2R/interpreter work is not an off-the-shelf JIT option.
- Preserve one UIKit application/scene lifecycle, one SDL handoff, one FNA game
  and one Celeste-owned FMOD system. Do not nest `UIApplicationMain` or start
  `SDL_UIKitRunApp` a second time from an already running launcher.
- Reuse existing native Metal/audio/input/lifecycle behavior deliberately.
  .NET Apple UIKit/Foundation bindings are not automatically usable from a
  manually embedded runtime; verify the bridge and registrar/runtime boundary.
- Use real Everest metadata, dependency, relinking, module and content behavior.
  Keep original ZIPs. Never claim compatibility from successful ZIP parsing,
  finding a DLL, metadata resolution or a first frame alone.
- Freeze a mod profile before game startup. Initially require a fresh launch to
  change active code mods; do not promise reliable arbitrary assembly/hook unload.
- Keep saves in a JIT-specific, profile-specific app-private root. Retain full
  Everest/module files and backups. Transfer vanilla saves by explicit copies;
  never share a live writable directory with the AOT apps.
- Adapt/disable desktop process restart, updater, Steam/Discord and native-plugin
  paths. JIT does not make macOS/Windows libraries into iOS libraries.
- Do not add an iOS-style JIT assumption to tvOS. Assess a tvOS JIT product
  separately if requested.

## JIT protocol requirements

- On the target iOS 26 device, implement the allocator side of the matching
  StikDebug protocol before claiming support. A debugger flag or script alone
  does not retrofit the CLR's executable-memory allocator.
- Do not execute breakpoint calls without the expected debugger/script ready.
  Do not broadly swallow SIGTRAP/SIGBUS or bypass failed preparation checks.
- Manage writable/executable aliases, instruction-cache coherence, alignment,
  unwind/ABI correctness and all JIT/hook/trampoline allocations together.
  Prepare required regions before detach; handle later growth explicitly.
- Verify executable code, then managed JIT, then actual hooks. A callback,
  entitlement, `CS_DEBUGGED` or `RuntimeFeature` boolean alone is insufficient.
- In LiveContainer, use the actual host PID and signing context. Guest bundle
  identity or guest entitlement files do not grant host-process capabilities.
- Use external StikDebug first. An embedded helper is later convenience work;
  it requires a separate process and does not solve the runtime port.
- Pin a runtime/Everest/MonoMod/platform-patch/script tuple. Deliver the exact
  matching script; never substitute an unrelated emulator script by guesswork.

## Build and filesystem boundaries

- Use `.build/ios-jit/` for reference clones, private staging, runtime builds and
  probes. Use `artifacts/ios-jit/<build-id>/` for local unsigned deliverables.
  Both roots are ignored. Avoid existing AOT staging/output directories.
- Proposed product source root is `jit-ios/`; bounded probes live under
  `experiments/ios-jit/`. Do not add JIT flags to `build-ios.sh`, `build-tvos.sh`,
  the vanilla projects or AOT canary builders as a shortcut.
- Use task-local SDK/NuGet/CLI/intermediate directories. Some existing projects
  have hard-coded `obj`/staging paths; a ProjectReference alone is not isolation.
- Use Xcode 26.6 via
  `DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer` for each build.
  Expected audit toolchain: Xcode `17F113`, iPhoneOS SDK `26.5`.
  Do not change global `xcode-select` or global workload configuration.
- Audit host is Intel x86_64, not Apple silicon. No modern dotnet SDK was on the
  audit shell PATH; inspect available tools before invoking build commands.
  The existing repository SDK pin is 10.0.302; keep JIT experiments independent.
- Use the existing exact-input validator where applicable and keep its output
  under the ignored JIT root. The supplied Mac game passed the validator during
  the audit; do not assume changed inputs retain that identity.
- Inspect licenses/provenance before vendoring code. Preserve notices and keep
  reference-only clones separate from product dependencies.

## Verification and physical test handoffs

- Follow the report's G0–G7 gates: native execution → managed JIT → real hooks →
  game baseline → small mods → SJ → hardening/optimization.
- The current ABI probe can be rerun with
  `python3 experiments/ios-jit/protocol-abi/compile.py`. It only cross-compiles
  and disassembles code; never describe it as device/JIT/runtime acceptance.
- A native executable-memory IPA is implemented in
  `experiments/ios-jit/native-probe/`. Build with its `build.py` and read
  [the stage report](docs/ios-jit/NATIVE_PROBE.md). Its M1 mailbox protocol
  establishes fresh PID/nonce identity while the debugger has the process
  stopped; it does not use the breakpoint ABI. Scripts are generated for each
  running process. The distributed template is intentionally not runnable by
  itself. Host/mock/simulator checks do not complete the physical G0 gate.
- G0 probe execution requires acknowledged page preparation, distinct RX/RW
  aliases and verified debugger detach. Every debugserver memory write is
  checked. Do not replace this with a bare CS_DEBUGGED check, use a stale
  session script, or silently fall back to RWX/interpreted/precompiled code.
- The first physical report (11 September 2026; LiveContainer 3.8.9,
  StikDebug 3.1.9) confirms M1 reply/detach but stops before execution because
  build 1 incorrectly required one VM entry to cover a 64 KiB allocation.
  Build `native-probe-20260911-02`, version 0.1.1 (2), walks every entry while
  retaining strict RX/RW checks. Its follow-up reports confirm three native
  execution passes in one LiveContainer process (80 checks, no failures),
  including two runs after about 30 seconds in the background. Read
  [the native execution result](docs/ios-jit/NATIVE_EXECUTION_PASS_2026-09-11.md).
  Native execution in this configuration is established. Later managed results
  are recorded below; standalone-device behavior and the broader G0
  failure/reboot matrix remain unproven.
- Use native startup logging before the managed runtime initializes, followed
  by structured runtime/hook/loader logs with launch/build/profile identifiers.
  Persist enough context to diagnose a failed launch on the next launch.
- G1 implementation lives in `experiments/ios-jit/managed-canary/`; read
  [the original managed canary report](docs/ios-jit/MANAGED_CANARY.md) and
  [build 4 crash / build 5 retest](docs/ios-jit/BUILD_4_CRASH_AND_BUILD_5.md).
  Historically, build 4 executed framework code and recorded 405 JIT completion
  events (344 distinct code entry addresses), all inside prepared allocations.
  Both 4 MiB arenas passed native execution on all 512 pages. Runtime startup
  then crashed before the imported DLL ran. Full G1 was not accepted at that
  stage; build 6's accepted result is recorded below.
- Exact build 4 binary/symbolication identified a missed RX store in the
  `MONO_PATCH_INFO_SWITCH` offset table in `mono_postprocess_patches`. Build 5
  fixes both that write and the absolute target table in
  `mono_resolve_patch_target`. Retain logical RX pointers; only store addresses
  translate through RW. Instruction patches, final copies, literals, thunks,
  data tables, allocator reuse and cache flushes must all follow this contract.
  Run the actual-source switch regression, including four unpatched negative
  controls, when changing these paths. The active runtime patch covers 7 files.
- The pinned BCL requests **libSystem.Native**. Build 4's resolver accepted only
  System.Native and failed 8 lookups across 3 entry points. Build 5 accepts the
  exact BCL name and explicit aliases, preflights those entries, and tests a
  managed GetEnv round trip. EventPipe is compiled out; supply the matching
  System.Diagnostics.Tracing.EventSource.IsSupported=false app-context switch.
  Native console and Mono/JIT profiler logging stay active. Full globalization
  and tracing support are later capability decisions.
- Earlier result: **all eight managed stages passed physically in build 5**.
  Read [build 5 execution and build 6 cleanup fix](docs/ios-jit/BUILD_5_EXECUTION_AND_BUILD_6.md).
  The correct build/DLL/script and LC2 route were verified, with a fresh process,
  successful native preparation and detach. There was no observed user procedure
  error. The host then aborted at mono_thread_detach: GC-safe STATE_BLOCKING
  attempted a second DO_BLOCKING. Execution passed, but clean return/resume was
  pending at that stage; build 6 resolves it below.
- **Latest result: build 6 passes the physical G1 canary**, including all eight
  stages, managed-thread clearing/detach, PASS UI, foreground liveness and
  same-process return after 21.73 seconds in the background. Read
  [the managed execution pass](docs/ios-jit/MANAGED_EXECUTION_PASS_2026-09-11.md).
  Logs verify the exact delivered build/DLL and correct LC2 protocol. Installed
  host metadata confirms both LiveContainers are 3.8.9; StikDebug 3.1.9 is still
  the prior reported value. This bounded acceptance does not cover new managed
  invocations after resume, longer stress/reboot/failure tests, hooks or gameplay.
- Latest physically validated G1-only canary: **managed-canary-20260911-06, version 0.2.2 (6)**.
  The Mono 8.0.28 source/archive, framework IL, allocator and script match build 5.
  Runtime source remains `46295af5828b062bbbf93a9cef50fd8cb9fbcb09`; AOT and the
  interpreter stay disabled. Host CoreCLR or simulator passes do not substitute
  for iOS Mono acceptance. Use new versioned external **Canary-v0.2.2.dll**;
  its eight fixture bodies are unchanged and it is compiled after IPA packaging.
- Worker detach must first make an unbalanced GC-unsafe transition. Detach
  consumes it and leaves the native worker GC-safe; do not exit that region a
  second time or simply remove detach. Use the shared CJMonoThread.c helper and
  require the managed thread object to be cleared. Bracket managed invocation
  and returned-object/exception inspection in balanced GC-unsafe regions.
- The actual pinned host Mono regression reproduces the old post-test abort,
  then verifies the shared correction and 160 attach/invoke/detach cycles across
  five native threads and both entry modes. Reproduce with
  tests/build_host_runtime.py and tests/check_mono_lifecycle.py under managed-canary.
  The isolated host regression requires the separately pinned macOS Mono pack;
  iOS framework IL caused recursion on this x64 host and must not be reused
  there. Never put macOS components into the device IPA.
- Expected stages: NativeImports, Arithmetic, SwitchTable, Dynamic,
  DynamicSwitch, GenericAbi, ExceptionsAndGC, ThreadAndCallback. After those,
  require managed_worker_detached, g1_managed_pass, managed_result_presented
  and managed_post_run_alive. Build 6 asks for 10 seconds foreground followed
  by about 20 seconds background, return and diagnostics capture. That clean
  physical G1 result is now reviewed and accepted. Build 9 retains the next
  real Hook/ILHook stage with original calls, ordering, removal/re-addition and
  execution after background/return; see the current-stage notes above. Physical
  bounded hooks are now accepted in build 9; game compatibility is unverified.
- The process-lifetime 8 MiB code budget is a canary constraint, not the final
  game policy. No late growth, unloading or runtime restart is implemented.
  Fully close the old process before updating/rerunning. Keep Launch with JIT
  OFF/script empty; the app supplies its fresh script to StikDebug in LC2.
- Build 6's complete six-file kit was **copied over USB and read back by SHA-256**
  at `Files > On My iPhone > LocalSend > Celeste JIT Tests > 0.2.2-build-6`.
  It is 10,175,173 bytes and includes an empty Results subfolder. The host did
  not install/launch it. IPA SHA-256:
  `5618c57a3d1189d091c577774ddec43e86e36dbd911cf7be14667e7bd64a8cb5`.
  DLL SHA-256:
  `4e29d1b7d7b301e1addd6a99c22002122d1b1ed3933de5afb656e73bc49e6094`.
  An iCloud copy is also placed in the same version folder; check its recorded
  upload state separately. The verified LocalSend copy is the primary handoff.
- **Working USB file-transfer path:** CoreDevice appDataContainer still fails,
  but LocalSend's House Arrest VendDocuments / AFC works. Use the isolated
  `.build/ios-jit/device-transfer-tools/bin/python` with pymobiledevice3, select
  the USB iPhone16,2 explicitly and request documents_only=True. The remote root
  still contains `/Documents`; write known versioned paths under it and read
  every file back to verify SHA-256. Do not infer that Finder-style file sharing
  is unavailable from a devicectl appDataContainer error. The successful script
  is `.build/ios-jit/device-transfer/2026-09-11/copy-build6-localsend.py`.
  Keep pairing cache/UDIDs private; do not read unrelated app files. Future
  known Results folders can be fetched through this same authorized service.
- **Direct no-export diagnostics now verified:** LiveContainer 1 also vends
  its Documents over AFC. Read the canary's
  `Data/Application/<verified-guest-data-UUID>/Documents/Diagnostics/` through
  the installed host's signed bundle ID. The current folder starts
  `3C268B63-02B6-…`; exact IDs are in the private build-6-pass retrieval receipt.
  Use [the USB collector](experiments/ios-jit/device-tools/README.md), selecting
  the latest session or an explicit prior session after a crash. It validates
  physical guest identity, reads a session JSONL and full console twice, and
  saves a new private snapshot with hashes. Build 6's 1,274 raw events match
  the 1,273 exported events plus one later background event. Collection makes
  no phone writes, export action, JIT request or debugger attach. User-entered
  version preferences remain in the optional exported bundle.
- Preserve old delivered IPA/DLL/guide folders and external dSYMs. Build 4's
  original source snapshot and raw diagnostics/crash evidence are under
  `.build/ios-jit/device-evidence/2026-09-11/build-4-crash/`. Its crash was fetched
  from systemCrashLogs without attaching a debugger. Do not infer the Mono root
  cause from the OS report's top UI frame alone; match original console PC,
  image UUID, external dSYM and disassembly. CoreDevice LocalSend access
  failed; the later AFC path above now supports direct USB handoffs.
- After a crash with USB available, collect the persisted raw session/console
  before relaunch or another JIT request. Otherwise reopen and export first;
  native console tails and five previous sessions are included. Keep logs lossless while
  throttling UI rendering: never enqueue TextKit updates for every JIT event.
- Every device test should include: IPA/script hashes, exact versions, numbered
  reproduction steps, expected visible behavior, the log-export or console
  capture procedure, and the question that its result resolves.
- Offer Files/share export of a diagnostic bundle from the launcher/recovery UI.
  Include the stage reached, allocator failures, runtime build, exceptions and
  selected package hashes. Redact pairing records, tokens, UDIDs and private
  paths. Never require pairing secrets to be pasted into chat.
- Use Xcode/Console or device logs when persistent app logs cannot capture a
  native crash. With LiveContainer, identify the actual hosting process. Explain
  debugger conflicts: Xcode and StikDebug must not compete for the same target;
  use non-attaching log capture when exercising the StikDebug protocol.
- Record owner-reported results separately from captured logs and reproduce
  only as far as evidence permits. Host, simulator, standalone device and
  LiveContainer results are distinct.
- Test unseen DLLs/dynamic methods, generic/struct ABIs, exceptions/GC/callbacks,
  hook original-call chains, ordering, removal and re-addition. Measure memory,
  launch cost, frame pacing and thermal behavior before claiming AOT/JIT wins.

## Delivery

- When an installable stage exists, produce a genuinely unsigned conventional
  IPA and state its **absolute path**. Clearly label a probe versus a game app.
- Never include `.dSYM` bundles or debug-only `MH_DSYM` files inside an app/IPA.
  Builds 1 and 2 accidentally included clang's implicit symbol output and
  triggered LiveContainer's signing error. Build `native-probe-20260911-03`,
  version 0.1.2 (3), compiles objects before linking, emits symbols only beside
  the IPA, and rejects embedded symbols. Its native instruction bytes and
  script match physically tested build 2. The owner confirmed that build 3
  downloads and installs without error; no further packaging-only retest is
  needed. Development is now authorized to proceed to the managed-runtime
  canary, with the same isolated checkout and unsigned/iCloud handoff rules.
- Include the exact matching JIT script when needed, `INSTALL.md`, checksums,
  a build receipt, third-party notices and the tested LiveContainer/StikDebug
  procedure. Do not promise an unsigned IPA carries working entitlements before
  the installer signs the actual host process.
- Keep private artifacts local. Ask before any commit, push or publication.
- Update the report/evidence or add a linked stage report so later development
  can distinguish proposals, source findings, host checks and physical results.
