# Build 28: native catalogue phone acceptance

15 September 2026. **ACCEPTED** on the owner's iPhone 15 Pro Max, iOS26.5.
The owner reports that all supplied tests visually passed. The single export
contains the final browser/install/gameplay session and three earlier build28
processes. It supplies the evidence needed for this gate; a second export or
repeat of the successful test is unnecessary.

Build28 is the current accepted fallback. Preserve27, both builds' original
sources/artifacts and every Results folder. Build29 remains local startup
preparation, without a phone handoff or physical acceptance. Responsive loading
is the next feature; this acceptance does not claim that it is implemented.

## Collection and identity

The file in `iCloud Drive/Celeste JIT Tests/0.15.0-build-28/Results` was read in
full twice, parsed successfully and copied unchanged into a new ignored private
review directory. Collection time: **2026-09-15 07:56:36 UTC**. The source and copy
are **5,370,692 bytes**, SHA256
`a07d20eff0f1a9236f7cf42ae6a876b5856e2bd2ce02e20c449271f7945931e9`.
The filename is `CelesteJIT-b0ee56b8-f872-4afa-b5ca-50dd15978475.diagnostics.json`.
Raw logs and the collection receipt remain private. The
[sanitized evidence ledger](BUILD_28_CATALOGUE_ACCEPTANCE_EVIDENCE.json) records
session IDs, exact event sequences, module identities, checks and limitations.

The export and **each process's own launch BuildInfo** exactly match the locked
build28 package: `0.15.0 (28)`, `launcher-catalogue-20260913-28`. All devices are
`iPhone16,2`, iOS26.5 (`23F77`), physical rather than simulator.

Executed-runtime evidence in all three played processes confirms Everest
`1.6531.0-cjit-d72e94f`, source
`d72e94f4b9e62b91cbdea674587ed39d53de9550`, RuntimeIdentity SHA256
`67b284331a08bd3eefb4e3ec5f09ca3b20b9000a4b40f13a0e2e1aa373e63f62`, and ABI1.
The adapter identity is
`65b8dca51055627ad8a7da5fb59add7166cf9a39e435b7ac211d9c2df7a4f378`.
This is more than a comparison of packaging metadata: actual Everest registration
and exact selection verification also succeed.

One diagnostic naming detail matters: `ModSelection.Verify` emits
`runtime_identity_pass`, but the frozen native `CJGraphicsMark` prefix filter
records it as **`graphics_fixture_message`**, retaining the full version/source/
manifest message. Current sequence70789 is that record. Its absence under the
original event name is not missing runtime identity. See
[ModSelection.cs](../../experiments/ios-jit/launcher-catalogue/managed/ModSelection.cs)
and [CJGraphicsPlatform.m](../../experiments/ios-jit/launcher-catalogue/src/CJGraphicsPlatform.m).
The phone export does not independently measure the executable UUID; the locked
local IPA/dSYM identities remain in the original delivery/reproduction receipts.

## Process inventory

Times below are UTC. Short IDs are prefixes of the full UUIDs in the ledger.

| Process | Retained interval | Observed work | Result / limit |
| --- | --- | --- | --- |
| `b0ee56b8` / PID7575 | 15 Sep07:42:11–07:53:52 | Browser, reviewed reuse/enabling, fresh Cateline install, multi-file dismissal, offline browsing, vanilla gameplay and normal Quit | **PASS**, including saves, complete native return and delayed heartbeat |
| `c71d8c52` / PID22437 | 14 Sep08:08:08–08:39:17 | Modded gameplay across SJ and VanillaContest maps; normal Quit | **PASS**, 26 native and19 graphics checks, 59 verified metadata identities, complete return |
| `26871f24` / PID1651 | 14 Sep19:41:30–20:45:21 | Smaller four-identity profile; Forsaken City gameplay | Startup/gameplay **PASS**; Quit/native return **NOT OBSERVED**. Last events are background, audio deactivation and lifecycle state2; they do not establish a crash |
| `129a9d93` / PID22292 | 14 Sep07:56:10–08:07:48 | Browser activity and a fresh JIT request | Valid native-only history; no game start, so game acceptance gates are **NOT OBSERVED** |

The primary current stream has594 events. Its routine first/last samples add
eight unique records and eight exact duplicates. Previous journals contain
2033,1403 and52 records, including120 synthetic counter snapshots without sequence
numbers. All were retained; deduplication found **zero conflicting records**.
The three previous journals report no clipped excerpt or invalid/partial line.
They are retained histories, not exhaustive unsampled execution traces.

## Browser and installation gate

All sequence references in this section belong to `b0ee56b8`.

| Gate | Evidence | Decision |
| --- | --- | --- |
| Browse, paging, sorts, categories and portrait/landscape layout | Owner's report that all supplied tests visually passed; active browser/cache/request diagnostics corroborate use | **PASS — owner observation**. Telemetry does not prove every visual detail |
| Exact installed reuse, including a Tools page | Memorial Helper file870370 is selected at13/20; review16/23 has no downloads or changes and cannot apply | **PASS**, no duplicate download |
| Disabled exact match requires review | Owner disables `memorialHelper` at28; review35 proposes only enabling1.0.4; explicit Apply37 precedes committed receipt/report40 | **PASS**, enable-only, zero downloaded files |
| Fresh small install and truthful report | Cateline file1324068: review50 → Apply52 → download/verification54–56 → committed receipt58; report says `applied`, `installed`,0.1.0,enabled | **PASS**, genuine new download/install |
| Multiple files and dismissal | Explicit three-file selection65; review68 names SpringCollab2020, Audio, OldGMHS and required ClutterHelper, total569,949,864 bytes; close70/71 | **PASS**, this plan is never applied or downloaded |
| Optional offline behavior | Events75–81 show error−1009,19 failed requests and19 stale-cache hits; owner reports visual PASS; installed-profile play then succeeds | **PASS**, offline browsing does not block play |
| Catalogue stopped before managed preparation | Quiesced140 precedes graphics start141; activeRequests0, suspendedForGame=true; no subsequent catalogue diagnostics/request activity recorded | **PASS**, backed by the cancellation/drain and fetch-rejection source contract |

Cateline is **16,792 bytes**, SHA256
`089c66c696c622c64f84be5f02a5b0682805e6d39bfc4a3bce06159fb1b98f7c`,
xxHash64 `038383b0282ff16f`. Committed receipt
`4F85F8E2-0CE0-4FEE-B199-4FDB88E0970B` matches the enabled library ZIP and the next
game's actual `Cateline 0.1.0` registration70247/verification70737. Memorial
Helper's enable receipt is `D6B70BE4-2C76-49FA-9427-A022056FE20C`; registration70279
and verification70785 confirm `memorialHelper 1.0.4`.

The final library contains64 entries,60 enabled. Those identities plus the three
actual built-in modules exactly match **63 verified metadata identities**. There
are65 registration callbacks because `JackalHelper 1.7.7.1` has three instances.
`EverestCore` is a dependency alias, not an additional registered module.
The older EeveeHelper1.12.5, ExtendedVariantMode0.50.5, FrostHelper1.80.1 and
MaxHelpingHand1.40.9 ZIPs remain disabled. The earlier owner action enabling all
current choices is explicit in the UI log; it is not an unreviewed installer action.

Seven committed receipts are retained, of which **two** belong to this current
session. Older VanillaContest and helper-update receipts are historical, not new
download evidence for today's browser test. The last persisted report remains
Cateline's applied transaction after the Spring review is dismissed.

Quiescence records142 cache hits,152 image requests,28 metadata requests and43
cancellations. These are cumulative browser counters before startup, not active
game-time requests. The source clears retained entries/decoded images, sets the
provider suspended, cancels/drains pending requests and rejects new fetches:
[CatalogueUI.swift](../../experiments/ios-jit/launcher-catalogue/native/CatalogueUI.swift),
[CatalogueProvider.swift](../../experiments/ios-jit/launcher-catalogue/native/CatalogueProvider.swift),
[LauncherUI.swift](../../experiments/ios-jit/launcher-catalogue/native/LauncherUI.swift).
This is a bounded implementation and observed zero-active gate, not a packet capture.

## JIT, gameplay and runtime

All three played processes pass the same **26 individual native checks**. Review
covered debugger detachment, valid mailbox, both RX regions and distinct writable
aliases, expected generated/patched values, all16,384 pages per arena, arena ends,
argument/return, cross-arena branch, a different execution thread and128 rewrites
with16,384 executions. Both arenas are268,435,456 bytes; protocol1 uses a96-byte
mailbox with response/error offsets48/88. Execution checks report known tracing
state with `traced=0` and `cs_debugged=1` after the process-specific JIT request.

The current process passes19 graphics checks, including Metal GPU/readback and
backbuffer orientation/stride/bounds/target preservation, retained jump hooks,
final save queue and XML settings/SaveData round trips. The19 events include
settings write/readback at startup and shutdown. Graphics start79395 and first
frame80500 pass; FMOD1.10.09 reports ready and native audio is active. Owner
feedback supplies the audible/visible/controls observation.

Actual current map evidence is **`Celeste/1-ForsakenCity`**, normal mode,
rooms **6 → 6z → 6 → 6a → 6b**. Hook execution records15 matching On/IL jumps.
Do not relabel this as SJ because a historical diagnostic message says
“original SJ maps.” Earlier `c71d8c52` genuinely visits:

- `StrawberryJam2021/1-Beginner/Ceph`, room5;
- `VanillaContest2023/0-Lobbies/Lobby`, Center, then
  `VanillaContest2023/1-Submissions/Flagpole1up`, a→b→c→d;
- SJ prologue00→01, beginner lobby, and
  `StrawberryJam2021/1-Beginner/coffe`, c-01→c-07.

All sampled/final `jit_failed`, `jit_unowned`, `managed_errors`,
`patch_rejections` and native failed-check counters are **zero** in all played
processes. There are no explicit failure events in retained events/counter
snapshots. Nonfatal Mono warnings about optional CelesteNet types in BrokemiaHelper
and GravityHelper are followed by the established type-discovery recovery and
exact module verification. They were inspected, not discarded as harmless merely
because the UI passed. Console tails remain bounded.

The current complete allocation trace independently validates:236,880 decoded
bytes,9870 records, SHA256
`c6811e4f11683cad396a5aac4bc71a19f76c1523588bb03675546c90c0249fdf`,
zero overflow, page-aligned nonoverlapping allocations entirely inside the first
prepared RX arena. Rounded allocation sizes exactly reproduce the monotonic
reservation total **165,249,024 /536,870,912 bytes**. Final totals are34,857 JIT
completions and12,605 patches. Earlier `c71d8c52` ends at240,664,576 reserved bytes;
its complete allocation trace is not included in this export. VM-range records
contain sampled rows and complete-range checks/digests, not all underlying rows.

Largest recorded physical footprints are4,010,528,904 bytes in the current run
and4,278,702,264 bytes in `c71d8c52`. They justify retaining memory budgets but do
not prove a leak or an absolute peak. Current graphics preparation/start takes
about30.43s before start result, and30.70s before the first returned frame. These
coarse build28 intervals motivate the next loading work; they do not demonstrate
responsive startup or isolate individual managed phases.

## Saves, normal Quit and limits

The current process loads existing settings, writes/reads4883-byte settings and
232,534-byte SaveData for slot0, and verifies the real canary YAML sidecar:
**prior194 → written209 → readback209**. Profile verification reports complete.
Game.Exit is accepted at99256, after return to the main menu. Shutdown records
stages1–8 in order, completion of work stages1–7, then the terminal stage8 in the
successful bridge result110128. The main Mono thread detaches at110127; native
result110129 passes; heartbeat110130 arrives **5.24s later** in the foreground.
The longest recorded shutdown work stage is game/mod hooks,6.23s; it completes.

Earlier `c71d8c52` also completes normal Quit, all stages, detach and delayed
native heartbeat. Its final save is slot3, sidecar0→178→178. Its recorded
background interval is6.62s. The smaller-profile process has no final Quit event;
acceptance uses the two completed runs, without converting that absence to a crash.

Fresh-process reload of the current209 sidecar is **NOT OBSERVED**. Different
slots/mod selections prevent interpreting the earlier27 counter980 as a required
current value. Accepted27's separate reload/33.12s background coverage remains
valid history. Build28's supplied guide required neither another fresh gameplay
run nor a new30-second background test.

Current retention reports zero storage error, selected-event eviction, oversize
event, journal rotation or allocation overflow. Sampling explains sequence gaps.
LiveContainer3.8.9 and StikDebug3.1.9 fields explicitly say “previous test”; these
are not freshly confirmed installed versions. Screenshots, exhaustive network
traces and a later209 reload are not present and are not claimed.

## Development consequence

The physical browser gate is closed. No new backend failure takes priority over
the roadmap. Continue from [build29's prepared native recipe and managed startup
analysis](STARTUP_PREPARATION_BUILD_29.md): independently pin/stage the required
managed inputs, add real managed phase measurements and implement cooperative
startup that preserves required thread affinity. Do not queue fake progress
behind a blocked main thread or move graphics/mod initialization to an arbitrary
worker. Use a new identity for code changes;30 is next unused, subject to recheck.

Whole-profile backup/restore and the full touch editor follow loading. iPadOS
needs its own physical evidence. Public IPA distribution and FMOD permission
remain separate unresolved gates. This review makes no commit, push, GitHub write
or new iCloud delivery; the existing build28 Results file remains untouched.
