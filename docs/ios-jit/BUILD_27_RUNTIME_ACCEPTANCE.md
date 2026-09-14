# Build27 phone acceptance — 13 September 2026

Build27 is accepted for the recorded Everest upgrade, two helper updates and
their reports, Strawberry Jam gameplay, background/resume, normal Quit and
fresh-process save reload. The owner reports all tests passed. Two exact iCloud
exports contain three build27 processes: one installation/native-check session
and two game sessions. Two older build26 processes are retained separately in
history; repeated journal events were matched by session and sequence.
[The evidence ledger](BUILD_27_RUNTIME_ACCEPTANCE_EVIDENCE.json) records the
assertions and exact input hashes. Private originals and the reproducible review
script are under `.build/ios-jit/device-evidence/2026-09-13/build-27-acceptance/`.

Both current exports and all three build27 launch records match the delivered
IPA's complete BuildInfo. All 224 source inputs and 201 packaged assemblies were
reverified without changing them. The IPA is 23,476,359 bytes; SHA256
`d251a33ee8b08dae94d08d7fe31ac9c3385b919d996fac7843644081a9d2dc45`.
Its retained executable/dSYM UUID is `39E4D88A-33C1-3D2A-A927-A74C1D024EB4`;
the phone metadata match is not an independent phone UUID measurement.
Target is iPhone16,2 / iPhone 15 Pro Max, iOS 26.5 build23F77, 16KiB pages.
LiveContainer/StikDebug versions remain inherited owner-reported fields.

## Updates, runtime identity and preserved choices

| Module | Before | After |
| --- | --- | --- |
| ExtendedVariantMode | 0.50.5 | 0.51.0 |
| MaxHelpingHand | 1.40.9 | 1.40.10 |

The installation process reviews, downloads, verifies and commits both archives,
totalling **1,463,412 bytes**. The report correctly records two version changes,
both remaining enabled, and no failed or unattempted items. The previous ZIPs
remain installed, disabled and marked as retained archives. Both game selections
match the committed files' exact SHA256 and size. The completed report survives
both fresh-process exports. Earlier retained receipts, including an enable-only
operation, are historical and are not counted as new build27 installations.

The update check and plan explicitly use the verified cached index captured at
08:50:29Z. Both releases become eligible against the new runtime. This proves
the cached-index update path on the phone, not a new successful online metadata
refresh or every offline/automatic-cache migration case. Those broader controls
retain their build27 host evidence. Original mod archive downloads do succeed.

Both games boot actual `1.6531.0-cjit-d72e94f`, record the pinned source commit and
matching RuntimeIdentity manifest, and verify all **56 selected/built-in metadata
identities**. There are 53 enabled ZIPs out of 60 installed. The 58 module
registration callbacks contain 56 unique identities: JackalHelper registers
three callbacks, also seen in the preceding build26 game. Callback count must
not be treated as a count of distinct archives. EeveeHelper1.12.6 and
FrostHelper1.80.2 are present but were not newly updated in these build27 sessions.

## Gameplay and complete shutdown

| Process | Recorded route | Sidecar counter | Result |
| --- | --- | --- | --- |
| Earlier build26 `96799db5` | Cassette Cliffs room3 → room4 | 820 → 928 | Historical clean Quit; establishes the pre-upgrade save |
| Build27 `a12f542d`, PID10818 | Cassette Cliffs room4 → room5 | Reload928 → 969, readback969 | 33.12s background/resume; normal Quit, native return and heartbeat |
| Build27 `98a9ec1c`, PID10925 | Brief vanilla room1, then Cassette Cliffs room5 | Reload969 → 980, readback980 | Normal Quit, native return and heartbeat |

The actual SJ map SID is `StrawberryJam2021/1-Beginner/Ceph`. Slot1 survives the
runtime upgrade and then a fresh build27 process. The first build27 session saves
182 deaths; the second visits the same saved room and later saves 186 deaths.
The final980 counter has same-process readback; no further-process980 reload is
claimed. These phone routes are SJ, rather than the suggested Spring route.
That is sufficient for this runtime/update gate; the new-runtime Spring/Paint
host tests and earlier physical Spring acceptance remain separate evidence.

All three build27 processes pass all26 native checks. Both256MiB execution
regions have complete16,384-entry RX coverage; the debugger is detached before
game execution. Both games record corrected reflection ABI1, all19 graphics
checks including seven backbuffer patterns and after-resume readback, all eight
shutdown stages, completed profile saves, native return and delayed heartbeat.
All sampled/final JIT failure, unowned-code, managed-error and patch-rejection
counters are zero. Both packed allocation traces verify with zero overflow.
Final code reservations are173,391,872 and170,016,768 bytes of536,870,912.

## Next work and limits

No new backend failure blocks the next planned native catalogue increment.
Use the existing reviewed installer for discovery → detail/file choice →
dependency review → install → report. Revalidate API contracts before building
the provider, keep bounded page/image caches and support offline/retry states.
A service outage must not prevent an installed complete profile from launching.

Responsive startup remains the immediate follow-up. Run-to-first-frame intervals
are74.71s and26.52s in these two processes; sampled peak footprints are about
4.05GB and3.72GB. These are observations, not a measured cold/warm comparison,
a leak diagnosis, or an older-device performance claim. Do not retain an
unbounded image catalogue during gameplay. Real loading progress must preserve
graphics/game thread requirements and address the synchronous startup work.
Game.Dispose takes7.21s and5.61s but both cleanly complete.

The [updated roadmap](NATIVE_LAUNCHER_ROADMAP_2026-09-12.md) then calls for
whole-profile save/settings backups and the full-parity native touch editor.
Broader map compatibility and memory/performance checks continue across those
increments. Public original-IL preparation and FMOD permissions remain separate
release gates. There is no need to repeat this successful phone test now.

Build27 becomes the current accepted fallback. Preserve27, previous26, graphics/SJ24,
all immutable source/artifact snapshots and every Results folder. Original delivery
receipts keep their historical pending-phone fields; current acceptance is recorded
here and in the current evidence ledgers. This review produced no new IPA, commits,
remote writes, cloud deletions or AOT-checkout changes.
