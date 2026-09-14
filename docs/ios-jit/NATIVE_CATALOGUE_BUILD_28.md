# Native mod browser — build28

Ready for physical testing; all local gates and iCloud upload pass, 13 September
2026. The owner authorized the next native catalogue step after build27's
physical acceptance. The new lane is
`experiments/ios-jit/launcher-catalogue`, version 0.15.0(28). Build27 remains
the accepted fallback; its managed runtime, renderer and delivered sources are
read-only inputs. No commit or public distribution is authorized.

## Experience and installation flow

Mods contains Installed, Browse and Updates. Browse offers native cards, search,
clear sorting, categories and subcategories, screenshots, readable descriptions
and individual file selection. The UI is general Celeste, with no preferred
collaboration or fixture. The existing installer owns reviewed dependencies,
compatibility, verification, cancellation, recovery and results.

Olympus's name search returns at most 20 relevance-ranked matches across all
categories. Its list endpoint supports genuine paged category filtering and
newest/updated/download/like/view sorting. The UI must describe these distinct
scopes, never pretend to filter or sort the entire search catalogue locally.

Every selected archive maps by its exact file URL/identity to verified
dependency metadata. Page titles are not module identities. Multi-file pages
may contain music, separate modules, alternatives or older versions; never
silently select every file. App-managed releases and built-ins stay protected.

The five sort choices are Most downloaded, Newest, Recently updated, Most liked
and Most viewed. Categories have native nested lists, including Maps → Standalone
and Skins. Portrait uses illustrated cards; landscape has a compact filter bar
so the introduction does not consume the short viewport. Larger accessibility
text uses a single-column grid. Cards show creator, category, downloads and likes.
Details add screenshots, page description, author/studio, views and dates when
the service supplies them. Screenshots preserve their aspect ratio in details.

A single eligible file is selected initially. Multi-file pages require an
explicit choice; the bottom **Choose files** button scrolls directly to the
downloads. Each row shows its description, filename, size and date. **Review
installation** goes through the existing native dependency review. Nothing is
installed before the owner's confirmation. The final report records actual
installed/updated/enabled changes, verified downloads retained after interruption,
and failures. Exact installed ZIPs are reused; a disabled exact match becomes an
explicit enable action. Compatible existing dependencies remain. Runtime minimums,
built-ins and app-managed compatibility releases still apply.

Previous or unindexed files link to GameBanana for manual ZIP import. Direct
installation does not guess a module from its page title or silently substitute
a different release. A page category alone cannot decide whether a file is a
mod: **Memorial Helper is a Tool page containing a valid indexed Everest mod**.
Its metadata and verified file identity make it eligible. Ordinary desktop tools
without those contracts are not installed as game mods.

Loading, empty, retry and offline states are native. Refresh keeps visible cards
until their replacement arrives. Returning from details preserves loaded pages
and browsing position; changing the query or explicitly refreshing loads a new
result set. The underlying search service returns at most
20 name matches and ignores list filters; the search header explicitly says
all categories and clearing it restores the previous browse filters. There is
no local reordering of a partial search pretending to be a global sort.
Connection errors use readable offline/timeout/retry guidance; technical domain,
code and endpoint are kept in diagnostics rather than shown as Foundation errors.

A simulator run exposed repeated animation of an open sort menu. The native host
polls every 0.5 seconds; its SwiftUI bridge previously published identical state
on every tick. Sampling showed repeated `updateVisibleMenuWithBlock` work, while
XCTest waited 60 seconds for animation completion before each subsequent gesture.
The bridge now compares its previous dictionary and publishes only actual state
changes. The regression holds the menu open across polling ticks, checks the
selected sort and verifies loaded pages/visible row survive a details visit.
The interrupted run, app/runner samples and screenshot are retained privately.
A supplemental settled capture verifies the native title/search/segments return
after Back; the earlier immediate capture caught the navigation transition.
The repeated existing navigation regression passes without a production change.

## Native implementation and resource policy

`CatalogueModels.swift` defines service contracts, category trees, inert text,
validated URLs and exact file-to-index selection. `CatalogueProvider.swift`
owns bounded asynchronous transfers, cache envelopes, coalescing, cancellation
and failure backoff. `CatalogueUI.swift` owns the SwiftUI browser/details and
downsampled images. `DependencyPlan.swift` and `DependencyInstaller.swift` extend
the existing reviewed transaction with selected catalogue roots. The host bridge
records browsing diagnostics and waits for catalogue cancellation before starting
managed preparation.

| Resource | Policy |
| --- | --- |
| Concurrent transfers | At most four; no account cookies or persistent URLSession cache |
| Response body | At most 4 MiB, checked while streaming and before parsing |
| Retained catalogue rows | 200; continue into a new window, with 20 results per page |
| Metadata disk cache | 24 MiB / 64 records, validated URL/schema/hash |
| Image disk cache | 32 MiB / 96 records |
| Decoded image cache | Strict LRU, 16 MiB / 32 images; visible view images are additional |
| Image decoding | At most two; off the main thread; 800-pixel thumbnails |
| Source image bounds | At most 8192 per dimension and 16,777,216 pixels |
| Freshness | Lists/search 15 min; categories 24 h; details 10 min; images 7 days |
| Failed request backoff | One minute per URL; a dated validated cache may be shown |

Search waits 350 ms after typing and cancels stale work. Repeated requests for the
same URL share a transfer; cancellation of one consumer does not abandon others.
The last consumer cancels the transfer. Cache pruning touches only the browser's
own Library/Caches directory. A memory warning clears decoded images. These are
cache/work limits, not a claim about the total app's memory footprint.

On Run, the host sets the session state, clears browser rows/images, suspends new
requests and awaits cancellation of active catalogue transfers. It records
`catalogue_quiesced` before managed preparation. Late image decodes cannot refill
the cleared cache. Browsing remains paused for this game process, consistent
with the existing restart-before-changing-mods contract. Offline catalogue
failure does not participate in the installed profile's launch checks. ZIP
downloads retain the installer's separate Wi-Fi/cellular preference.

Links, redirects and media are limited to the expected HTTPS services. GameBanana
profile data must name Celeste (game 6460) and match the requested page. Hidden
pages and unavailable/archived/infected files do not become selectable through
the richer profile response. HTML is rendered as bounded inert text. There are
no embedded web views, account actions, posting or automatic installation.

## Preserved foundation

The complete 201-assembly payload is reused from accepted27: Everest1.6531.0,
the prepared original game IL, CelesteIOS, FNA, MonoMod and the accepted CoreLib
reflection correction. Native Mono, the accepted24 Metal renderer, JIT geometry
and StikDebug template remain unchanged. The managed/renderer/runtime builders
in this lane are read-only verifiers. New native builds use isolated
`launcher-catalogue*` stages and their own pinned ZIP/YAML dependencies.

Existing GameLibrary and `Profiles/sj-first-play` data paths remain. No game/mod
reimport is required. All saves, settings and unknown mod sidecars remain under
the existing profile contract. Export diagnostics, installation reports and the
normal game Quit path remain available. Keep one game per process and accepted27
as fallback. No AOT checkout writes, commits or remote writes were made.

## Validation and phone gate

The native catalogue suite passes 58 contract/cache/transaction checks.
It fetches all five live sort orders, performs a fresh dependency-index refresh,
finds Memorial Helper on its real Tool page and Cateline in Skins, then uses the
production coordinator to download, verify, install and report their original
ZIPs (13,965 and 16,792 bytes). Fixtures separately exercise multi-file selection,
dependency expansion, no-op reuse, disabled-to-enabled changes, blockers, unsafe
inputs, coalescing, cancellation, invalid-cache rejection and startup suspension.
The existing dependency/update/recovery suite also passes after these changes.

Both final native XCUITest suites pass against the exact packaged simulator
build. They cover sorting, nested categories, paging, search cancellation, empty
and offline states, file choice, dependency review, installation reports, exact
reuse, the real ZIP picker, persisted choices, update cancellation and the
existing launcher. Live GameBanana browsing and details were captured in portrait
and landscape. The simulator smoke test also passes import, preserved-container
update, diagnostic export and console recovery. Fixture transport is excluded
from the device payload.

The original downloaded Cateline0.1.0 and memorialHelper1.0.4 modules register
and run in actual Mono/FNA/Metal Celeste on the Mac. All 37 session and 30 reflection
checks pass, including graphics readback, controls after resume, save counter
0→3→readback3 and clean Quit. This is one macOS x64 process, not a phone or
fresh-process save reload test. The final live ZIP downloads match those host
test inputs byte for byte.

The unsigned-package gate and the native-generated request against the packaged
StikDebug script both pass. All 228 source inputs match the final simulator and
device receipts; all 201 managed assemblies and the native runtime/renderer match
accepted27. Exact gate and artifact identities are recorded in
`NATIVE_CATALOGUE_BUILD_28_EVIDENCE.json`. These host/simulator results do not
claim phone28 acceptance or compatibility of every downloadable mod.

The planned phone kit is `iCloud Drive/Celeste JIT Tests/0.15.0-build-28`.
Its README tests native browsing first without JIT, exact existing-file reuse,
a small Cateline download, multi-file review and optional offline behavior. Then
use the normal fresh LC2/StikDebug request, play an existing map, Save and Quit,
and export separate browsing/install and game diagnostics to Results. No large
test asset handoff or standalone new script is necessary.

After physical browser acceptance, the next roadmap increment is **responsive
real startup progress**, followed by whole-profile saves/settings backup/restore
and the full-parity SwiftUI touch editor. Public on-device original-IL preparation
and FMOD permission remain separate release gates; this IPA stays private.

## Primary references

- [Olympus browser](https://github.com/EverestAPI/Olympus/blob/568cc5fc846836d480e41f928a3db7c06e87798d/src/scenes/gamebanana.lua).
  Its current main commit was verified unchanged on 13 September.
- [Everest updater](https://github.com/EverestAPI/Everest/blob/d72e94f4b9e62b91cbdea674587ed39d53de9550/Celeste.Mod.mm/Mod/Helpers/ModUpdaterHelper.cs).
- [Celeste catalogue service](https://maddie480.ovh/celeste/gamebanana-list?page=1&sort=downloads),
  [categories](https://maddie480.ovh/celeste/gamebanana-categories),
  [subcategories](https://maddie480.ovh/celeste/gamebanana-subcategories).
- [GameBanana profile API example](https://gamebanana.com/apiv11/Mod/150813/ProfilePage).

Private dated response snapshots and fetch receipts are under
`.build/ios-jit/launcher-catalogue-service`. All current list/file formats,
legacy `GameBananaType=Obsolete`, exact PageURL, separate audio files and search
limits have been inspected. Current main and runtime commits are pinned above;
failed guessed endpoints are retained as failed fetches rather than evidence.
The older API source audit is in `launcher-product-audit-20260912/references`.
No phone28 acceptance is claimed until exact diagnostic exports are reviewed.


## Final handoff identity

All seven files / 23,833,385 bytes are confirmed uploaded to
`Celeste JIT Tests/0.15.0-build-28`. The kit contains the unsigned IPA, phone
README, installation guide, reference script, notices, TEST-IDENTITY.json and
checksums. Phone download/execution remain unobserved. The local artifact is
`artifacts/ios-jit/launcher-catalogue-20260913-28/`.

IPA 23,812,187 bytes; SHA256 `87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2`;
UUID: 98537CA1-09CE-344B-B370-5C27D8F83DC2. All 228 source inputs match the tested simulator and
frozen snapshot. The snapshot receipt SHA256 is
`fab464c37eb3716b2afe70d5c71bc3ec88e93b32dd26e9aec363a774caccc485`. Exact evidence is in
`NATIVE_CATALOGUE_BUILD_28_EVIDENCE.json` and the artifact delivery receipt.
Keep the delivered lane immutable. No commits, pushes, AOT changes or public
redistribution occurred. Accepted27 and all historical Results remain.
