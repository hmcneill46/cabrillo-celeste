# Build26 phone acceptance — 13 September 2026

Build26 is accepted for fresh Spring Collab dependency installation, installation
reports, ARM64 reflection, the recorded Spring gameplay routes, background/resume,
normal Quit and fresh-process saved-room reload. The owner reports everything
worked. The two iCloud exports contain three distinct build26 processes; duplicate
history events were compared and merged by session and sequence, not counted as
extra tests. [Exact evidence](BUILD_26_INSTALLS_ACCEPTANCE_EVIDENCE.json) records
the raw-file hashes, assertions, transaction results and separate session findings.

Both exports and all three launch records exactly match the delivered IPA's
complete BuildInfo. All 210 source inputs and 201 packaged managed assemblies
were reverified. The IPA remains 23,468,277 bytes, SHA256
`4b77c9ec39f73b66c2f0e7c2de446ac67067cc6ac56d04698c56f2b9732d0dbd`.
Its recorded executable/dSYM UUID is `25ECF962-06E7-3C73-A339-FAE899A4ED9D`;
the diagnostics bind BuildInfo, rather than independently measuring that UUID.
Target: iPhone16,2 / iPhone 15 Pro Max, iOS 26.5 build23F77, 16KiB pages.
LiveContainer 3.8.9 and StikDebug 3.1.9 remain inherited owner-reported version fields.

## What was installed and enabled

The first process starts with only the bundled canary. The owner imports original
SpringCollab2020 1.7.10 and its separate audio archive before resolving dependencies.
The reviewed transaction downloads, verifies, installs and enables **17 helper
archives, 22,892,303 bytes**. Audio was already imported, explaining the difference
from the host fixture's 18 downloaded dependencies. There are no failed downloads
or unapplied items in this recorded operation.

| Installed helper | Version |
| --- | --- |
| AdventureHelper | 1.6.0 |
| CanyonHelper | 1.1.6 |
| CavernHelper | 1.3.7 |
| ClutterHelper | 1.2.1 |
| CollabUtils2 | 1.13.4 |
| DJMapHelper | 1.13.4 |
| ExtendedVariantMode | 0.50.5 |
| FactoryHelper | 1.4.1 |
| FrostHelper | 1.80.2 |
| IsaGrabBag | 1.7.3 |
| LuaCutscenes | 0.2.13 |
| LunaticHelper | 1.1.1 |
| MaxHelpingHand | 1.40.9 |
| MoreDasheline | 1.7.1 |
| OutbackHelper | 1.7.3 |
| PandorasBox | 1.0.49 |
| memorialHelper | 1.0.4 |

The dependency plan explicitly explains its verified earlier ExtendedVariantMode
and MaxHelpingHand choices. Every committed file's size/hash matches all three
subsequent game selections. The final library has 20 enabled archives and all
23 selected/built-in identities match actual Everest registration.

The owner then disables AdventureHelper and resolves again. This second operation
correctly reports **AdventureHelper 1.6.0 enabled**, zero downloads, and no version
change. Both transaction receipts survive. The final enable report is reopened
in a later process and included in both exports.

The Updates page performs an initial due check, reuses cached results on another
visit, and performs explicit refreshes. ExtendedVariantMode 0.51.0 and
MaxHelpingHand 1.40.10 remain `canUpdate=false`, with the precise Everest 1.6531.0
requirement. They are never installed in these sessions. The currently installed
versions remain 0.50.5 / 1.40.9.

No old-to-new update transaction was performed in these exports: FrostHelper is
installed fresh and EeveeHelper is absent. The earlier real host update receipt
remains the evidence for Eevee 1.12.5→1.12.6 / Frost 1.80.1→1.80.2 reporting.
Cancellation, server failure and interrupted/recovered installation are also
covered by the existing host tests, not newly observed phone actions. Those
limits do not invalidate the successful operations recorded here.

## Gameplay, saves and shutdown

| Process | Recorded route | Mod sidecar counter | Native result |
| --- | --- | --- | --- |
| `606d3a1e`, PID9326 | Spring Prologue a00→a01→a10, Beginner lobby, Beginner gym | 0→65, readback 65 | Quit, stage 8, return, delayed heartbeat |
| `5758b66c`, PID9450 | Reload gym, lobby, Starjump pre pre1→pre1→1→2→strawberry room | Reload 65→167, readback 167 | 37.24 s background/resume; Quit, stage 8, return, delayed heartbeat |
| `ec33b533`, PID9506 | Reload Starjump, strawberry room | Reload 167→168, readback 168 | Quit, stage 8, return, exported result |

Starjump's internal SID is `SpringCollab2020/1-Beginner/Lichtbaulb`; its friendly
name was checked against the exact original ZIP's English dialogue. The second
process saves slot 0 with 26 deaths, and the third re-enters the same saved room
before saving with 28 deaths. This establishes actual saved-room reload as well as
the independent sidecar chain. It does not claim a fourth-process reload of 168.

Every process passes all 26 native checks. Both 256MiB execution regions have
complete 16,384-entry RX coverage, and the debugger is detached before execution.
All three register reflection-flags ABI 1 before mod boot. CommunalHelper is absent,
so this phone run exercises the fresh dependency configuration that exposed the
build26 CoreLib issue. The corrected original FrostHelper boots and plays.

Graphics checks total 18/19/18, including all seven backbuffer patterns each time;
the middle run also verifies readback after resume and 32 hooked jumps afterward.
Phone output is Color, 2796×1290, MSAA0. Each process finishes pending saves,
verifies the profile and completes stages 1–7 before the terminal stage 8/native
return. Game.Dispose takes 1.60/1.54/0.45 seconds. The last export occurs about
three seconds after result presentation, before the delayed heartbeat; it still
contains successful detach/return and the native Export action. Both preceding
processes record the delayed heartbeat.

All recorded JIT, managed-error, unowned-code and patch-rejection counters are
zero. Final code reservations are 91,308,032 /89,341,952 /62,373,888 bytes out of
536,870,912. Both exported packed allocation traces verify exactly with zero
overflow; the first session's historical counter snapshots also report zero
overflow. Peak sampled physical footprints are approximately 2.75/2.51/2.51GB.
These short routes are not a long-duration leak or older-device memory benchmark.
The legacy hook-pass message mentions SJ; map/module records establish Spring
gameplay, and that generic message must not be used to claim an SJ retest here.

## Decision and preserved state

Build26 becomes the current accepted fallback; keep build24 as the separate
accepted graphics/SJ fallback. Preserve both delivered source/artifact trees,
all cloud Results and the exact private raw copies under
`.build/ios-jit/device-evidence/2026-09-13/build-26-results/`.
No repeat of the successful phone test is needed to proceed.

The [runtime upgrade assessment](EVEREST_RUNTIME_UPGRADE_ASSESSMENT_2026-09-13.md)
selects pinned stable Everest 1.6531.0 for the next isolated implementation. It
also identifies runtime-aware update-cache invalidation as part of that change.
Broader catalogue installs, real loading progress, full-profile backups and the
native touch editor retain their roadmap order. No new IPA, accepted-lane edits,
commits, GitHub writes, cloud cleanup or AOT-checkout mutations were performed
during this acceptance review.
