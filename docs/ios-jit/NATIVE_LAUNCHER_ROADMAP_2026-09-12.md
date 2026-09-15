# Native Celeste launcher: product design after build22

**15 September build32 acceptance:** [the phone export confirms callback1 handoff](BUILD_32_ACCEPTANCE.md),
approximately1.3ms after its first-return marker, plus SJ saved-room gameplay,
normal Quit and delayed native heartbeat. The owner requested the next feature.
Proceed with whole-profile saves/settings backup and staged restore/rollback,
then the full touch editor. Build32 is the accepted fallback.

**15 September loading review:** [both build31 phone runs pass backend/gameplay](BUILD_31_LOADING_REVIEW.md).
The owner reports choppy loading controls and audio before game reveal. Logs
confirm long main-thread callbacks and17.7 seconds of game frames hidden behind
the title-menu gate. [Build32](FIRST_FRAME_BUILD_32.md) keeps useful loading details
visible without disclosure/scroll controls and reveals after first draw/readback.
Its managed loader/runtime is unchanged. The focused physical presentation gate
comes before whole-profile backup/restore, then the full touch editor. Build28
remains fallback; all31 sources, artifacts and Results are preserved.

**15 September phone acceptance update:** [build28 is accepted](BUILD_28_CATALOGUE_ACCEPTANCE.md).
The owner's visual PASS and one export containing four build28 processes close
the browser gate: reviewed Memorial reuse/enabling, fresh Cateline installation,
multi-file dismissal, offline use, zero-active catalogue quiescence, real JIT and
gameplay, saves, normal Quit and native heartbeat. No repeat export is required.
Build28 is the current fallback; preserve27 and all Results. Independent
preparation has produced local [build29](STARTUP_PREPARATION_BUILD_29.md): a fresh native
build recipe, Cabrillo branding and passive startup phase timings/retention.
The current d72e94f startup/loader call sites and splash-count limitations are
documented there. Build29 remains local. [Build31](RESPONSIVE_LOADING_BUILD_31.md)
now implements cooperative boot/archive/delayed-module steps and the native
loading screen. Local checks/package verification pass; its test kit is in the
versioned iCloud folder. Phone acceptance remains open.
Complete loading acceptance before the backup/restore and touch editor sequence.
Preserve28/29; build31 has its own identity and managed input capsule.

**14 September repository update:** ongoing JIT work now lives in the independent
**Cabrillo — Celeste Mod Loader for Apple Platforms** repository. The fully AOT
sibling is Morro. See [the migration report](../CABRILLO_MIGRATION.md) and
[standalone build guide](../BUILDING.md). The separation preserves delivered28
and accepted27; it is not another phone acceptance. After phone28, keep the
loading → whole-profile backup/restore → touch editor order below. iPadOS is the
next intended device family, with [separate platform gates](../APPLE_PLATFORMS.md).
Apply the new in-app branding in a new version, preserving installed data paths.

Historical status at13 September2026: **build27 is physically
accepted for actual Everest1.6531.0, both newly eligible helper updates and reports,
SJ gameplay, resume, complete Quit and fresh-process saved-room reload.**
Build28 implements a focused native mod catalogue built on the accepted installer;
its final handoff and phone gate are tracked in [the browser record](NATIVE_CATALOGUE_BUILD_28.md).
Responsive loading, whole-profile saves/settings and the touch editor follow.
The15 September update above supersedes the historical pending states below.
The following implementation history predates repository publication.

## 13 September build28 implementation

The owner explicitly approved native browsing. Build28 adds Mods → Browse with
five genuine server sort orders, categories/subcategories, native cards and
details, screenshots, creator/studio/statistics and explicit file selection.
Search is labelled accurately as up to20 relevance matches across all categories.
Selected files enter the existing reviewed dependency transaction and report.
Exact installed files are reused, disabled matches are reviewed for enabling,
and runtime/pin constraints still block incompatible selections.

Fresh primary-source inspection found that a valid helper can live on a
GameBanana Tool page: Memorial Helper is one. Eligibility therefore follows
indexed file identity and actual Everest metadata, not a page-category guess.
Real HTTP installs of that helper and the small Cateline skin pass and their
actual modules run under the preserved Mono/FNA/Celeste host. Cache/transfer/image
budgets and explicit quiescence before game startup address the earlier memory
concern without claiming a total process-memory ceiling.

The phone gate covers browsing/layout, file choice, exact reuse, a small real
download/report, optional offline behavior and gameplay/Quit after browsing.
Keep accepted27 as fallback and inspect exact exported diagnostics. After that
acceptance, proceed with **responsive real startup progress**. Retain the thread
affinity and genuine-progress requirements below; native browser completion does
not remove the long synchronous managed-startup work.

Whole-profile save/settings backup with staged restore/rollback follows loading,
then the native touch editor with all current layout functionality. Compatibility
and memory/code-headroom checks continue. Public game preparation and FMOD are
still release gates. Build28 source and artifacts become immutable on delivery.

## 13 September build27 acceptance and the next increments

[Build27 acceptance](BUILD_27_RUNTIME_ACCEPTANCE.md) verifies two exports, three
current processes and two older processes retained separately. ExtendedVariantMode
0.50.5→0.51.0 and MaxHelpingHand1.40.9→1.40.10 download, verify, commit and register
under actual Everest1.6531.0. Their old ZIPs remain disabled. Cassette Cliffs
room4→room5, 33.12s background/resume, normal Quit/native return and the next
process's room5/counter969 reload pass. The phone played SJ; do not describe it as
a new Spring/Paint test. There is no newly recorded runtime failure to fix first.

The approved next build, now implemented as28, focuses on **Mods → Browse**,
alongside Installed and Updates:

- Native search, New/Most downloaded ordering and a compact category filter.
  Keep cards simple; details can show screenshots, author, description, size,
  requirements and supported public statistics. Add other fields only where the
  validated service supplies them and they improve the screen.
- Resolve a selected game mod/file into the existing dependency review,
  verification, transaction and report flow. Multiple files can represent audio,
  alternatives or extras; do not choose every file on a page automatically.
  Exact module identities, minimum versions and app-managed pins remain enforced.
- Refresh the existing primary-source/API fixtures before implementation. Keep
  search debounced, paging bounded, image decoding downsampled and caches limited.
  Preserve useful cached browsing and explicit retry/error states. A metadata
  outage must not block complete installed profiles from launching. Keep JIT
  unnecessary for browsing and installation, and release large previews before
  gameplay. No account, comments or liking actions are needed for this increment.
- Use neutral Celeste/profile presentation. Keep existing data directories and
  saves; collab-specific regressions belong in internal testing.

Follow it with **real responsive loading**. The new phone evidence records74.71s
and26.52s from Run to the first frame, so this remains a near-term priority even
though startup succeeds. Display actual bootstrap/module/content stages and
honest indeterminate progress where total work is unknown. Address the long
synchronous main-thread startup; do not queue updates behind it or move all
thread-affine game/graphics initialization onto an arbitrary worker.

Then implement **whole-profile saves/settings backup and restore**, preserving
unknown mod sidecars through staging and rollback, followed by the **SwiftUI
touch editor** with all existing split/duplicate/extra-button/import/export and
multi-touch behavior. Continue compatibility and performance checks throughout.
Build27 sampled roughly4.05GB/3.72GB footprints: that is a reason to budget new
native cache memory, not evidence of a leak. Public original-IL preparation and
FMOD redistribution permission remain separate release gates.

Build27 is the current accepted fallback; keep26 and24 and every Results folder.
No repeat of build27's successful phone test was required for that review. The
subsequently approved build28 adds its separate browser/install phone gate above.

## 13 September phone26 acceptance and runtime assessment

[Two exports contain three successful processes](BUILD_26_INSTALLS_ACCEPTANCE.md):
17 helpers installed for fresh Spring/audio, a separate AdventureHelper enable-only
report, Prologue/gym/lobby/Starjump gameplay and same-room reload with counter167.
JIT, graphics and complete native Quit pass; the middle process resumes after
37.24 seconds in the background. Runtime-blocked updates stay blocked. No
old-to-new update or cancellation/failure operation occurs in these phone exports;
those retain the existing host test evidence. No repeat of the successful test is
needed to proceed. Build26 is the current fallback; keep24 for its accepted SJ
and graphics coverage as well.

[The runtime assessment](EVEREST_RUNTIME_UPGRADE_ASSESSMENT_2026-09-13.md)
pins stable1.6531.0 at d72e94f4b9e62b91cbdea674587ed39d53de9550. Only three
runtime files change upstream; no project/submodule dependency changes are in
the comparison. Implement actual new managed source/prepared game/hooks in an
isolated lane, keep the accepted native stack, align native/managed version
identity and re-evaluate cached update availability across runtime changes.
Then validate the now-eligible ExtendedVariantMode/MaxHelpingHand updates and
existing Spring/Paint/SJ regressions before the next phone handoff. That historical
recommendation is now implemented and physically accepted as build27 above.

## 13 September correction before the next feature

[Build26](MOD_RESOLUTION_BUILD_26.md) addresses owner-reported dependency/update
confusion first: precise runtime blockers, verified earlier candidates, accurate
old/new installation reports and bounded upstream mirror fallback. EeveeHelper and
FrostHelper's reported updates are compatible. Original25 rejects the blocked
commands in a direct control; exact phone exports are still needed to establish
anything else. Fresh Spring startup also exposed eager signature loading in Mono
attribute queries; build26 includes a scoped CoreLib correction with real-Mono
reflection and game regression controls. Keep accepted game IL, native runtime
archives, renderer and source lanes immutable. The later phone26 acceptance above
establishes the corrected CoreLib's recorded ARM64 gate.

The ten-file 0.13.1-build-26 handoff is uploaded; it includes optional original
earlier helper ZIPs for intermittent download-server errors. Build24 remains the
retained graphics/SJ fallback; build26 is now the current accepted fallback.
The physical installation/gameplay gates and runtime assessment above supersede
the original pending handoff. Next: isolated Everest runtime implementation,
followed by the planned catalogue, real
loading, whole-profile saves/settings and native touch editor. A two-release
historical fallback is a bounded compatibility measure, not a broad claim that
current or arbitrary older mods work on this runtime. Preserve this distinction
in product UI and diagnostics.

## Recommendation

Proceed toward a general Celeste mod launcher now. The owner’s proposed
features fit together: native management before JIT, ordinary Everest mods
during play, and reliable native recovery afterward. We do not need every map
to be proven compatible before improving management. We do need reliable
shutdown, transactions and honest failure handling before broadening installs.

Build22 establishes substantially more normal gameplay than the earlier short
tests: almost 24 minutes, multiple rooms, no recorded JIT failures and successful
save readback. [The acceptance report](BUILD_22_GAMEPLAY_ACCEPTANCE.md) separates
that from the still-unverified final shutdown and fresh-process checkpoint reload.

The changes I recommend to the proposal are:

- Make the **editor and save manager SwiftUI**. Retain the responsive gameplay
  input path and a shared, versioned layout contract underneath them.
- Resolve the complete required dependency set in one reviewed operation.
  Do not present a modal for every missing helper or update every installed mod.
- Use a **required bundled iOS support module** for game-side integration.
  Keep runtime/JIT, native file management and rendering infrastructure outside it.
- Use the game’s Quit command, returning to the native launcher after saving.
  Another game session still requires a fresh process with the current runtime.
- Show actual loader progress. Supporting a smoothly updating native screen
  also requires addressing the current long main-thread startup call.
- Keep catalogue cards simple; put detailed metadata and available files on a
  detail page. Avoid reproducing the whole GameBanana website inside the app.

## What the reference implementations actually provide

Olympus is the closest functional reference for this part of the product.
Its current browsing source supports newest, last updated, downloads, views
and likes, category filtering, screenshots and file selection. Its UI framework
is LÖVE, so we should adapt the behaviour into native navigation rather than
porting its desktop widgets. [Pinned Olympus browsing source](https://github.com/EverestAPI/Olympus/blob/568cc5fc846836d480e41f928a3db7c06e87798d/src/scenes/gamebanana.lua).

The service Olympus uses exposes paged mod lists, search and category data.
I fetched and checked real newest/popular lists, Maps/Helpers filters, search,
categories and subcategories. List pages contain 20 results. The current service
already returns an obsolete legacy `GameBananaType` field; use its supplied
page URLs and opaque IDs rather than constructing URLs from that field.
[Pinned service implementation](https://github.com/maddie480/RandomStuffWebsite/blob/c9a933911eceac9022930bcdcdc7cf53552c62df/src/main/java/ovh/maddie480/randomstuff/frontend/CelesteModSearchService.java).

Everest separately discovers update and dependency databases through
`everestapi.github.io/modupdater.txt` and `modgraph.txt`, with official mirror
locations. Its downloader handles compatible installed versions, enabling
disabled dependencies, transitive requirements, unavailable versions and
ambiguous downloads. These are the relevant contracts for a native resolver.
[Everest database discovery](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Helpers/ModUpdaterHelper.cs),
[dependency downloader](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/UI/OuiDependencyDownloader.cs).

The old EverestUpdateCheckerServer repository is now archived and points to
the current backend. This audit followed that link and pinned the current
backend as well. Its file integrity hash is xxHash64 with seed zero; it is an
integrity check, not a publisher signature. Retain a local SHA256 identity and
download provenance alongside it.
[Current backend](https://github.com/maddie480/RandomBackendStuff/blob/904284430da1e72218696cac6e4d0aebea663d1a/src/main/java/ovh/maddie480/randomstuff/backend/celeste/moddatabase/ModUpdater.java).

Direct GameBanana profiles also return preview media, submitter, likes,
downloads, views, downloadable files and a contributing-studios field. The
three profiles sampled here had empty studio lists. Studio presentation is
therefore feasible but a populated fixture is still needed; a full studio
release feed or complete historical release API was not validated.
[Spring Collab profile API](https://gamebanana.com/apiv11/Mod/150813/ProfilePage),
[Memorial Helper profile API](https://gamebanana.com/apiv11/Tool/6850/ProfilePage).
Available files are not interchangeable with releases: a page may contain
required audio, alternative versions and optional extras simultaneously.

The current metadata snapshot contains 6,166 update entries and 6,166 dependency
entries. The reproducible experiment is
`experiments/ios-jit/product-audit/check_service_snapshots.py`; captured public
responses, URLs, dates, hashes and results are in
`.build/ios-jit/launcher-product-audit-20260912/`. No mod archives were downloaded
or executed for this experiment. The sanitized manifest is
[the roadmap evidence](NATIVE_LAUNCHER_ROADMAP_EVIDENCE.json).

## Native screens and flow

Use four destinations: **Play, Mods, Saves, Settings**. Mods keeps
Installed, Browse and Updates inside one destination. Keep the launcher
comfortable in portrait; use landscape for gameplay and the actual-size layout
editor. iPad can use a sidebar and wider detail views later.

| Screen | Primary content | Main action |
| --- | --- | --- |
| Play | Current profile, imported game, enabled-mod count, concise readiness | Run Celeste |
| Mods / Installed | Search, toggles, direct installs, dependency groups, issues | Import or resolve dependencies |
| Mods / Browse | Featured/new/most downloaded, search and a compact filter sheet | Open a mod detail |
| Mod detail | Artwork, author, summary, category, size, requirements, available files | Install with dependencies |
| Saves | Slots, profile backups, import/export, settings transfer | Back up or restore |
| Settings | Controls, optional performance overlay, JIT setup, diagnostics | Edit controls |

“Play” should surface one actionable readiness message, not eight repeated
warnings. Tapping Run rechecks the selection and either starts or shows a sheet
such as “3 dependencies are missing” with **Resolve**, **Review mods**, and
**Cancel**. The same final gate must apply to deep links and automation; the
game must never start on a stale successful scan. Keep inline issue badges for
review, use alerts for failed requested actions, and use quiet confirmations
for successful imports. Cancellation is a normal outcome.

Remove Strawberry Jam profile branding, the dedicated SJ download section and
normal-user regression switches. Keep existing `Profiles/sj-first-play` data
in place, with a neutral display name in profile metadata. Regression presets
and pinned compatibility fixtures belong in internal diagnostics/tests.
Installing a mod must never silently switch profiles or discard saves.

Browse defaults should emphasize New and Most downloaded. Show a thumbnail,
title, author, category and one or two useful statistics on a card. Put views,
dates, credits, studio information when present, screenshots and available
files on the detail screen. “Popular” needs a clear meaning: all-time downloads
and GameBanana’s featured selection are different lists. Categories observed
include Maps, Skins, Helpers, Assets, Dialog, Effects, Mechanics, UI, Tools and
WiPs. Obtain the hierarchy from the service, and preserve unknown categories.
Desktop executables/editor tools may be listed but should link to their page
rather than get an enabled **Install in Celeste** action.

A native `CatalogueProvider` should normalize the community service and direct
GameBanana detail responses behind typed models. Cache pages/images, deduplicate
requests, debounce search, respect HTTP cache headers and retry/backoff signals,
and expose offline/retry states. No GameBanana account is needed for these
read-only calls. Show public counts; leave liking, comments and account actions
on the website initially. Sanitize descriptions and use only approved link/image
schemes. Preserve source content-visibility flags. No website markup should
execute in the native catalogue. A catalogue outage must not block installed,
complete profiles from launching.

## Dependency resolution and installation

Use the actual installed archive’s `everest.yaml` as authority for its module
names, versions and requirements. The online graph describes indexed candidate
files, not every historical ZIP. Link requirements by exact internal identity,
then apply Everest’s version rules, including major-version compatibility and
its `0.0.*` exception. Keep optional dependencies absent by default; when already
present, check their compatibility. Multi-module ZIPs are one archive operation.

The reviewed plan should distinguish **enable existing**, **download missing**,
**replace incompatible**, and **cannot resolve automatically**. Show total
download bytes, new dependencies, affected existing mods and any replacement
before applying. Prefer compatible installed versions, including versions
pinned by the iOS compatibility layer. Runtime/Everest updates are app updates;
the resolver must not replace bundled runtime DLLs with a desktop installation.

For example, the database identifies `memorialHelper` 1.0.4 (13,965 bytes), which
satisfies Spring Collab’s 1.0.0 requirement. The owner already has 1.0.4 enabled
in the new phone export. Searching the browser service for `memorialHelper`
returned nothing, whereas “memorial helper” found its page. This is a concrete
reason not to implement dependency resolution as title search.

An illustrative plan for the currently indexed Spring Collab 1.7.10 against the
56-ZIP build22 selection adds Spring Collab, its audio archive and ClutterHelper:
569,790,262 bytes total, preserving compatible installed helpers. This is an
experiment over captured metadata, not an instruction to update the owner’s
different or previously imported ZIP, and not proof those additions execute on
iOS. It also demonstrates why the download screen must show archive sizes.

Implementation contract:

1. Snapshot the current library revision and required graph. Resolve to a
   deduplicated plan; detect cycles, duplicates, unavailable versions and
   ambiguous source files before applying anything.
2. Download to a separate transaction directory with `URLSessionDownloadTask`.
   Stream progress in bytes plus completed/total files. Save verified completed
   downloads on cancellation; partial resume is best effort. Do not buffer a
   large ZIP in memory. Foreground downloads are sufficient for the first
   supported LiveContainer flow; do not promise reliable background completion
   until tested in that environment.
3. Verify source integrity, local SHA256, archive structure and actual metadata.
   Recompute transitive dependencies if the fetched metadata differs. Show a
   revised plan for additional downloads or replacements. An ambiguous or
   incompatible result remains staged and cannot become active.
4. Recheck the original library revision and build a new validated selection.
   Keep the old archives/profile snapshot until the new revision is complete.
   A journal and startup recovery are required: several individual file renames
   are not an atomic whole-library transaction. Never mutate active-game files.
5. Present a concise result and re-run preflight. Keep installed helpers needed
   by other mods when disabling/removing a top-level mod. Disabling dependents
   should be an explicit plan; do not silently cascade changes.

Reuse native ZIP/YAML validation and original-archive immutability. The current
per-archive YAML parser intentionally caps input at 1 MiB and 20,000 events; the
captured online graph is 3.19 MB. Give catalogue parsing its own bounded streaming
contract, without relaxing the untrusted per-mod limits. Keep an exportable
install receipt with source, hashes, metadata and transaction outcome.

## Required iOS support module

The owner’s proposed bundled compatibility mod is a good architectural fit.
Use a small `EverestModule` shipped and versioned with the IPA, with a stable
module ID such as `CelesteIOS` once chosen. Mark it as required platform support;
show its version in About/diagnostics, not among user-disableable mods. Reject a
user ZIP claiming the same identity. Do not let GameBanana updates replace it.

| Component | Responsibility |
| --- | --- |
| SwiftUI/native host | Navigation, files, downloads, save transactions, JIT handoff, application lifecycle |
| Early managed bootstrap | Runtime/platform setup and hooks needed before Everest loads any modules |
| Bundled iOS module | In-game Quit integration, touch/controller glyphs, game-side settings and lifecycle callbacks |
| Input/graphics bridge | Existing low-latency touch/controller transport, layout application, rendering, audio |
| Ordinary mods | Original Everest ZIPs; their own content, hooks and saved data |

This extracts product responsibilities from the current `Platform.cs` and
`TouchPort.cs` rather than adding a second overlapping set of hooks. Keep
Mono/MonoMod/FNA correctness fixes in their respective components. Keep narrowly
required, version-bound third-party compatibility transforms separate and
documented; a bundled support mod must not become a collection of unexplained
mod-specific behaviour changes.

Use a small versioned native/managed interface: readiness snapshot, active
input source, applied layout revision, startup-stage events and a queued quit
request. The native host remains authoritative for session state and file
operations. Avoid synchronous cross-thread callbacks that can deadlock the
main thread. Register support in the correct order relative to game modules;
early loading progress cannot depend on waiting for this module’s own Load.

For glyphs, hook the central Everest/Celeste prompt APIs and reuse the same
attributed artwork as the touch controls. The local AOT implementation already
maps Jump/Confirm/Talk, Dash/Cancel, Grab, Pause and Journal to touch prompts;
adapt the policy without importing its Apple managed bindings. Switch prompts
from actual recent input, with stable controller-family selection and a short
hysteresis against idle-controller noise. Keep keyboard/controller bindings
working and defer to ordinary rendering for unrecognized mod actions.
Arbitrary mods drawing hard-coded keyboard images will not automatically change.
[Everest input/prompt integration](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Patches/Input.cs).

## Quit and session lifecycle

The current managed frame method returns 0 when FNA’s game loop ends. Native
`graphicsFrame:` treats every non-1 result as failure. Additionally, Stop starts
a save coroutine and drives normal frames until it completes. Allowing Game.Exit
to disable those frames too early could prevent saving from completing.

The support module should translate the game’s normal Quit action into an
idempotent host request **before** disabling the frame loop. The host transitions
through Saving and Stopping, lets the ordinary Everest save path and mod sidecars
complete, then ends the external loop, releases resources and returns to SwiftUI.
Keep normal quit distinct from a runtime exception. Handle repeated requests,
quit during loading/saving and backgrounding without double disposal or a
forced timed exit. Route unsupported desktop restart/update actions through an
explicit native “relaunch required” result rather than spawning another process.

Remove the permanent Finish panel once normal Quit and recovery are verified.
With metrics off, no launcher panel should cover gameplay; optional performance
metrics remain independent. A diagnostics-only recovery control can be tested
separately, but should not be permanently visible in normal play. Do not use
`Environment.Exit`, process killing or a fabricated successful result to imitate
desktop quitting inside LiveContainer.

The current Mono host has one game session per process. After graceful Quit,
native browsing/settings/export can remain available, but another Run needs a
fresh guest process and a new JIT request. An automatic LiveContainer relaunch
would be a separate tested integration, not a promised in-process restart.

## Real SwiftUI startup progress

Everest’s desktop splash is a separate process communicating through a named
pipe. Its handler counts candidate archives/directories, adjusts totals for
multi-module archives, advances completion and signals that mod loading is
finished. That signal precedes the end of all game-content work.
[Pinned splash handler](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Everest/EverestSplashHandler.cs),
[loader call sites](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Everest/Everest.Loader.cs).

Adapt those events into the native bridge; retain the iOS disabled desktop
splash. Display stages such as Checking files, Preparing runtime, Loading mods
24/58, Loading game content, and Starting. Use counted progress only where
the source measures it, with an indeterminate indicator for uncounted stages.
Do not turn number-of-modules into an asserted percentage of wall-clock work.
Separate scanned, loaded, skipped and failed states. Keep current-mod text,
elapsed time and an expandable diagnostic detail; use restrained animation,
clear typography and the launcher’s mountain motif rather than scrolling logs.

This is a backend task as well as a view. Build22 calls managed Start from
UIKit’s main thread; its game constructor synchronously boots Everest. Merely
dispatching progress labels to that same thread will leave the screen frozen.
Profile stage boundaries and make preparation resumable/cooperative, or move
only proven thread-independent work to an attached worker. Keep UIKit, window,
Metal and thread-affine mod calls on their required threads. Do not move all
Everest initialization to an arbitrary worker or pump a nested UIKit run loop.
Test cold/warm loading with UI responsiveness and final first-frame handoff.

Before managed startup, cancellation can return to the launcher. Once a runtime
or mod Load has begun, cancellation needs the supported shutdown path; it cannot
pretend that partial initialization was safely undone for another Run.

## Native touch editor and gameplay controls

The read-only AOT checkout contains a richer D3 editor than the current JIT
TouchPort. Preserve its complete interaction feature set, not just the default
fixed controls. This requires connecting the D3 layout/input policy as well as
building a native editor.

Parity includes fixed/floating movement, separate or split Jump/Dash, all four
split orientations, swapping halves, button sliding, circle/rectangle/shoulder
grab shapes, source-aware Hold/Invert/Toggle grab behaviour, opacity, visibility,
haptics and directional haptics, movement/resize, mirror, undo, reset, duplicate,
delete, and up to four extra controls including Crouch Dash and Quick Restart.
Retain layout import/export/share and preview-before-apply. The existing schema
is version 2 with four extras; expanding it needs a deliberate migration.

Use SwiftUI settings and a landscape canvas with a selection inspector,
alignment guides and explicit Save/Cancel. Keep a draft separate from the saved
layout. Import opens a preview. An export should travel through Files/iCloud.
Preserve normalized coordinates, safe-area rules and defaults across devices.
Native preview geometry and managed hit geometry must have shared fixtures.

The gameplay input state machine should keep receiving stable simultaneous
touch contacts through the existing native/SDL bridge. A SwiftUI tap recognizer
per button is insufficient for held buttons, sliding and multi-touch. Initially
retain game-side rendering of the overlay, using consistently padded artwork,
shared sizes, proper visual centering and matched hit areas. Native editor
rendering does not require moving every game-frame control into SwiftUI.

Validate split-half glyph centers, press feedback, controller connect/disconnect,
touch cancellation, orientation, safe areas and duplicate actions on hardware.
Test Quick Restart/Crouch Dash semantics in ordinary play; drawing a new button
alone does not implement the action. Keep the current optional FPS metrics;
do not mislabel callback timings as GPU timings.

## Save and settings management

The primary safe unit is a **profile backup** containing saves, game settings,
Everest/mod settings and unknown persistent sidecars, plus a manifest of the
required mod archive identities and launcher/layout schema versions. Ordinary
Everest files include slot-specific mod saves and module settings, and modules
can override their storage routines. A vanilla-only XML schema or file allowlist
would lose legitimate mod data.
[Everest save/settings storage](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Module/EverestModule.cs).

Use native slot cards with optional name, time, deaths and last-played summaries;
parse a small read-only summary without rewriting the underlying save. If a
summary is unfamiliar, still allow backup/export of the data. Offer a simple
full-profile backup and a separate settings export. Single-slot transfer should
include its standard Everest sidecars and clearly identify that custom
cross-slot data is better transferred with the whole profile.

Keep game assets and mod ZIPs out of the default small backup; include their
identities so missing mods can be resolved on restore. A separate full archive
option may include mods. Only exclude directories explicitly owned as disposable
cache by the launcher; preserve unknown persistent files under the profile.
Mods writing outside the managed profile are an explicit advanced portability
limit, not something a filename guess can solve.

Back up only when the game is inactive and saves are quiescent. Restore into a
staging directory or a new profile, verify structure and containment, retain a
rollback copy, and require a fresh process before the restored data is consumed.
Offer exact whole-profile restore rather than blindly merging contradictory
files from two snapshots. Never execute mod code just to preview a backup.

All of this belongs in SwiftUI/Files. Keep the Export diagnostics option separate
and available for iCloud as requested. Automatic save sync and conflict merging
are later work; manual, inspectable transfer is the first reliable contract.

## Implementation order and acceptance gates

| Increment | Deliverable | Required proof |
| --- | --- | --- |
| Session foundation — build23 accepted | Bundled iOS module/bridge, normal Quit classification, teardown stages, input prompts | Phone title/modded Quit, sidecar writes, native return and touch-to-controller observed; carry latest-save reload and keyboard/disconnect coverage forward |
| Backend graphics — build24 accepted | Isolated Metal backbuffer and managed buffer-bounds correction | 107 host GPU/API checks and physical graphics/resume/save reload; later builds retain identical graphics bytes |
| General installs/runtime — builds26/27 accepted for recorded gates | Dependency resolution, reviewed updates/reports, runtime-aware caches and actual Everest1.6531.0 | Fresh Spring installs/enabling on26; two version updates and SJ save/resume/Quit/reload on27; negative/recovery cases retain host evidence |
| Native catalogue — next | Browse/search/filter, details, clear file selection and installation through existing transactions | Refreshed API fixtures, paging/cache bounds, outages, ambiguous files, dependencies, report and physical install/play |
| Loading presentation — immediately after catalogue | Real startup stages and responsive native screen | Cold/warm loads; multi-module and failed loads; no blocked animation loop; correct game/window thread affinity |
| Protect data | Native whole-profile saves/settings backup and restore | Complete unknown-mod-sidecar round trip, staging/rollback, inactive-game guard and process isolation |
| Controls polish | Native D3-parity editor and consistent gameplay artwork | Shared geometry/input fixtures, safe-area/rotation checks, physical sliding/multi-touch/extra buttons |

The required backend foundation now passes its recorded physical gates. Keep
newly discovered runtime failures ahead of feature work, and keep each increment
independently reviewable. Do not make one IPA depend on completing the catalogue,
loading redesign, backups and editor together.

For the next physical kit, use a new source/output lane and identity after27.
Keep diagnostics that identify each shutdown stage, exact mod identities/SIDs,
profile/save revision and first failure. The test instructions must distinguish
save success from complete shutdown and ask for a fresh-process save check.
The next handoff remains a small unsigned app via the versioned iCloud folder;
existing game content/mod ZIPs remain on the phone. No new phone files or IPA
were created by this review.

## Repository and release boundaries

Keep the JIT work in this checkout and the AOT checkout read-only. Use build27’s
frozen sources as the reference; new changes belong in a new lane. Separate
native launcher services, platform-module/bridge, runtime compatibility patches,
and fixture tests as the code becomes a product. Do not reorganize every accepted
experiment as part of adding one UI feature. Copy only the needed AOT policies
and attributed artwork with recorded source identities; no writable dependency
on its generated outputs. Commits and remote writes still require owner approval.

The launcher and required support module can remain small. Public distribution
still needs on-device preparation of owner-imported original game IL and the
separately recorded FMOD permission decision; a polished UI does not resolve
those gates. See [the distribution design](IOS_REUSE_AND_DISTRIBUTION_2026-09-11.md).

## Implementation update — build 23, 12 September 2026

The owner approved the first increment. [Build23](SESSION_FOUNDATION_BUILD_23.md)
implements required `CelesteIOS` 1.0.0 / ABI 1, normal Quit, queued-save-aware
stages, shared source-aware prompts and a SwiftUI closing screen. See its
[evidence ledger](SESSION_FOUNDATION_BUILD_23_EVIDENCE.json) for current handoff
status; physical acceptance is pending. Build22 remains immutable.

New measurements locate substantial shutdown work in Game.Dispose's ordinary
mod detour removal: 12.50 seconds after full SJ lobby/Bing play on the Mac, versus
4.60 seconds with the same mod set on a vanilla map. Both close successfully.
This does not prove the cause of build22's truncated phone journal. The stage
label and independent native heartbeat now make the phone check diagnostic.
The main thread can still be busy during a disposal callback. Do not claim a
continuously responsive shutdown animation; investigate cooperative cleanup
if new device evidence shows excessive delay or watchdog termination.

Next gate: phone menu Quit → saved native return → fresh-process progress check.
Then address the isolated Metal backbuffer bug before general installs. The
dependency/catalogue/loading/profile-backup/editor sequence above is otherwise
retained. Log new evidence here before changing priority or expanding scope.

Build23 is now delivered: all local gates pass and its eight-file iCloud kit is
confirmed uploaded to `Celeste JIT Tests/0.12.0-build-23`. Phone acceptance is the
next decision point; no further runtime/product increment has been started.

## Physical update — build 23 accepted, 12 September 2026

[Two exact build23 phone sessions](BUILD_23_SESSION_ACCEPTANCE.md) pass normal
Quit and full native return. Teardown is measured at 4.79 seconds from title /
7.99 seconds after modded gameplay, with surviving heartbeats and no runtime
failure. This supports the planned Metal backbuffer increment next. Keep23 as
the complete-shutdown fallback; carry latest counter403 fresh-process reload,
resume, keyboard/disconnect checks forward. Current next lane is build24,
`launcher-backbuffer`; dependency transactions and the later sequence remain.

Readback inspection also finds the old FNA managed overload ignores array
segment capacity. Correct this specific API alongside the isolated native fix;
require negative buffer/rectangle controls, actual GPU results and continued
rendering. Do not change game IL or mod ZIPs to avoid the defective API.

## Implementation update — build24, 12 September 2026

[The isolated backbuffer increment](METAL_BACKBUFFER_BUILD_24.md) passes all
local gates. Original native failure is reproduced; corrected pixels, bounds,
formats, MSAA and callback lifetime pass 107 real Mono/Metal checks. Full SJ/Frost,
normal and queued-save Quit, original Paint and fresh-process save tests pass
with the final candidate. The phone kit adds automatic startup/frame/resume
checks and requests two separate save sessions. Preserve build23 as fallback.

The native descriptor repair also required a narrow managed array-segment guard;
it does not replace original game IL/mod ZIPs or change the support-module ABI.
After physical graphics/save acceptance, proceed to general install/dependency
transactions. Keep profile data and remove remaining single-mod presentation
during that product increment, rather than renaming stored directories now.


Build24 delivery is complete: eight files / 23,164,143 bytes, all confirmed
uploaded to `Celeste JIT Tests/0.12.1-build-24`. Existing phone game/mod data is
reused. The next decision is its automatic graphics/resume checks and fresh-process
save reload. General dependency transactions follow acceptance; no dependency
feature has been bundled into this graphics test.


## Build24 accepted; build25 scope update

Both supplied phone exports pass; see [acceptance](BUILD_24_GRAPHICS_ACCEPTANCE.md).
General dependency transactions are now active in build25. The owner requested
an Updates page during implementation, so individual updates and Update all
join the same review/download/verification/recovery machinery. Disabled mods
stay disabled; app-managed versions remain protected. Catalogue browsing,
loading presentation, backups and the touch editor retain their later order.


### Update check scheduling (owner request during build25)

Keep an explicit Check for updates button. Visiting the Updates page may check
when the last successful check is over 24 hours old, only while the launcher is
idle. Make automatic checks optional, never automatically install, back off
automatic failures for an hour, and allow manual retry immediately. Reuse the
already scanned inventory and SHA-keyed xxHash results to avoid rereading large
ZIPs on every visit; fresh transaction review/apply still rehashes the library.
No background scheduler, in-game poll, push permission or wakeup is needed.


### Runtime currency discovered while testing updates

The 12 September service snapshot offers EeveeHelper1.12.6 and FrostHelper1.80.2
that pass build25 native installation plus real Mono/Metal Paint/save/resume.
ExtendedVariantMode0.51.0 and MaxHelpingHand1.40.10 require Everest1.6531.0,
while the accepted embedded runtime is1.6458.0. Show them as unavailable and
preserve current compatible versions. After phone25 acceptance, assess a new
isolated runtime lane before broad fresh-profile browsing/download promises.
Do not treat a desktop updater or relaxed version checks as a solution.

### Build25 handoff — 13 September 2026

All local gates pass: planner/installer and recovery controls, actual published
mod downloads, updated-helper Paint/save/resume on Mono/Metal, native simulator
UI and export, final package identity and the unchanged JIT request protocol.
The seven-file kit totals 23,428,401 bytes and is confirmed uploaded to
`Celeste JIT Tests/0.13.0-build-25`. Phone25 execution is unobserved.
The next decision is its dependency/update/gameplay/Quit/fresh-process acceptance,
followed by the isolated runtime-currency investigation above. Keep24 as the
accepted fallback; all Results and local historical artifacts remain. The
superseded build23 cloud installer has been removed after local hash verification.
The [build25 report](MOD_INSTALLS_BUILD_25.md) and its evidence ledger contain
the exact frozen source, IPA, symbol and delivery identities.


## Build26 accepted; build27 runtime upgrade — 13 September 2026

[Build26 acceptance](BUILD_26_INSTALLS_ACCEPTANCE.md) records actual fresh Spring
dependency installs/reports, gameplay, normal Quit and saved-room reload. The
owner approved the isolated1.6531.0 runtime step. [Build27](EVEREST_RUNTIME_BUILD_27.md)
rebuilds Everest and the original-IL game/hooks, unifies native/managed runtime
identity and re-evaluates cached update eligibility after runtime/pin changes.
Current ExtendedVariantMode and MaxHelpingHand satisfy its runtime minimum.
Keep accepted26 as fallback; actual build27 phone acceptance remains required.

After that gate, resume native general catalogue discovery/install design on the
existing reviewed transaction machinery. Follow with real responsive startup
progress, complete-profile saves/settings backup/restore and the full-parity
SwiftUI touch editor. Retain scope from the earlier product roadmap; specific
collabs remain regression fixtures. Performance overlays must label actual
measurements, and new iOS compatibility limits need evidence. Public preparation
and FMOD permissions stay independent release gates.
