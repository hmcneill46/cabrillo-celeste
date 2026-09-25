# Cabrillo development

Start a fresh development chat with [HANDOFF.md](HANDOFF.md). It records the
accepted build32 phone fallback, accepted build35 iPad base-game run, accepted build36 phone base-game/Motion Smoothing runtime gate, delivered
build37 Everest upgrade with unexpected phone exits and a pending combined saves gate, evidence review and independent build constraints. Recheck its dated state before acting.

## Scope and ownership

- Cabrillo is the independent Celeste/Everest JIT launcher for Apple platforms.
  Read `docs/CABRILLO_MIGRATION.md`, `docs/BUILDING.md`, the JIT feasibility audit
  and roadmap before changing the build.
- The owner chose Cabrillo for JIT and Morro for the separate fully AOT project.
  The searchable product description is "Celeste Mod Loader for Apple Platforms";
  repository: `https://github.com/hmcneill46/cabrillo-celeste`, with remote
  `origin` and default branch `main`.
- Do not commit, push, create/publish a remote, or write to GitHub without explicit
  owner approval. Local reversible edits, tests and experiments are authorized.
- The owner explicitly authorized the initial commit/push and chose a public
  repository on14 September2026. That first-publication authorization is recorded;
  it does not grant blanket approval for unrelated future GitHub writes.
- On15 September the owner separately authorized committing/pushing the completed
  loading work through build32 and its phone acceptance, then continuing local
  development on the next feature. Verify publication state in HANDOFF.md.
- On25 September the owner requested GitHub Actions for the current source and
  explicitly chose: "Set up CI now; keep IPA publishing gated until public
  packaging is ready". This authorizes publishing the current public source and
  these workflows. It does not authorize publishing private IPAs or clearing
  unresolved distribution gates. See `docs/RELEASING.md` and the latest handoff;
  earlier no-publication statements are historical for this scoped request.
- Both `/Users/harrymcneill/Projects/celeste-ios` and the legacy
  `/Users/harrymcneill/Projects/Celeste-Everest-JIT-Apple-Platforms` are read-only.
  Never build into, clean, reset or otherwise change those checkouts/caches.
- Preserve originals in `/Users/harrymcneill/Projects/Celeste Required Files`.
  No game code/assets, FMOD SDKs, signing identities, pairing data or private
  logs may enter Git. `.private`, `.build` and `artifacts` remain ignored.
- Use Xcode26.6. The local `.private` capsule is an explicit pinned dependency,
  not a Git source directory. Do not silently fall back to a legacy checkout.

## Current state

- Public CI and a gated version-tag release workflow are configured through
  [PR2](https://github.com/hmcneill46/cabrillo-celeste/pull/2). Fresh GitHub-hosted
  runs pass the public inventory audit, 20 Python build/release controls and119 native profile
  checks without private dependencies. `release/current.json` blocks37 IPA
  publication; the dedicated public builder is intentionally absent until game
  preparation, FMOD distribution and public dependencies are resolved. These
  workflow/documentation changes do not alter any frozen app or allocate38.
- The latest37 export contains two owner-confirmed unexpected app exits. Both
  pass26 JIT checks, Everest1.6580 and MotionSmoothing1.8.0 registration with54
  selected archives; one reaches the menu then starts Old Site. No37 gameplay/
  Quit pass is present. Wi-Fi iOS logs confirm jetsam per-process-limit with
  a3376MiB limit; the last sample reaches3.53GB. Earlier32 ran at4GB, and the
  owner confirms SJ alone now fails. Current LiveContainer signing omitted
  Increased Memory Limit; retained earlier profiles grant it. The exact same
  LiveContainer3.8.10 release is now re-signed with the permission and installed
  over Wi-Fi. Installed entitlements and14 unchanged save/settings files are
  verified; native launch passes and iOS confirms the new6144MiB process limit.
  The owner confirms SJ now works. A new exact37 phone journal verifies SJ
  Prologue, Beginner Lobby and NotYourBadeline a_01–03,501 paired touch inputs
  and4.05GB peak footprint with zero runtime errors. The SJ regression is closed.
  This run ends backgrounded without normal Quit/native-return evidence. The
  independent new iCloud export and full lifecycle/save gates remain outstanding;
  do not request a repeat of already-passed SJ gameplay solely for the export.
  Read `docs/ios-jit/BUILD_37_MEMORY_REVIEW.md` and the37 ledger. The matched32/37
  host comparison passes with a slightly lower37 peak. This is a host signing
  repair, not a new Cabrillo implementation. Physical acceptance is scoped to the
  recorded SJ gameplay. `docs/INCREASED_MEMORY_LIMIT.md` documents the owner-requested
  GetMoreRam alternative and the correct LiveContainer/standalone signing target.
  Full SJ mods were added
  between36 and37, so the runs do not isolate Everest alone. Follow the37 report;
  preserve these distinct physical gates. All37 inputs remain frozen; any new
  Cabrillo implementation needs38. No38 package has been allocated for this repair.
- The same export verifies36's base-game/Motion Smoothing gameplay, four resumes,
  save readback, stage8 normal Quit and delayed native heartbeat with zero runtime
  errors. It also confirms standalone StikDebug in the tested LC setup. Most
  gameplay callback windows are around60 despite a120 request; sustained120Hz
  and the native save-manager gate remain pending. Keep32 as the broader fallback.

- Build37 (`launcher-everest6580`,0.20.0) upgrades actual Everest source and both
  runtime identities to stable1.6580.0, commit082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75.
  All16 native archives are exact36; four managed assemblies change,197 remain
  exact. Build34 precision repairs and35 touch polling are preserved. Follow
  `docs/ios-jit/EVEREST_6580_BUILD_37.md`; build/package checks and frozen inputs
  must not be mistaken for physical acceptance. Preserve all earlier artifacts.
  `EverestValidation.json` pins profile, real-game/source, Motion Smoothing60/120
  and original-vanilla save roundtrip receipts. The iPad35 base-game gate and
  scoped36 phone acceptance remains distinct from37 acceptance. All six37 kit files
  are uploaded;37 is installed on the iPad with native-launch identity confirmed.
  Phone37 evidence has arrived and records unexpected exits; iPad37 gameplay
  remains pending. All220 captured37 inputs are frozen; next unused is38.

- Later25 September: phone35 fails before its first frame with Motion Smoothing
  at both60/120Hz, despite passing JIT. An accepted Mono class.c visibility patch
  was omitted in the iOS15 rebuild. Build36 (`launcher-visibility`,0.19.1) restores
  that exact archive member. All201 managed assemblies and fifteen other native
  archives remain35-identical. Follow `docs/ios-jit/VISIBILITY_BUILD_36.md` for
  current delivery/evidence. New implementation work must use the next identity38.
  The older host runtime retained the patch; require the new original-source
  failure control and restored-source test gates before treating host checks as
  evidence for this change. The37 export now verifies the scoped36 runtime gate;
  the native saves gate is still pending. Build37 is the requested stable Everest1.6580
  upgrade lane; do not mix its managed payload with36 metadata.

- 25 September: build35 (`launcher-platforms`,0.19.0) is installed on the owner's
  iPad mini4/iOS15.8.8 via TrollStore with Dopamine active. Native JIT, real base-game
  gameplay/touch, brief resign/foreground, save readback, normal Quit/stage8/native heartbeat
  and owner visual/audio review pass. This is a scoped iPad acceptance; build32
  remains the accepted phone fallback. Read `docs/ios-jit/PLATFORMS_BUILD_35.md`.
- Build35 adds iOS15 UI/native compatibility, explicit JIT routes and optional
  up-to120Hz display callbacks. Seven archives are rebuilt from an explicit pinned
  source capsule; nine remain exact. Only the managed adapter changes relative34:
  touch polling now happens at MInput.Update so render-only ticks cannot consume
  presses. Original Motion Smoothing1.8.0 passes Fast/Fancy at60/120 on the host;
  phone refresh rate, performance and new JIT routes still need physical checks.
- Build35 is frozen and all six iCloud kit files are confirmed uploaded. Use its
  combined guide;33/34 Results were still empty on25 September. Preserve34's
  numerical repairs and backup/transfer gate, now also carried by35. Managed pin:
  `.build/platform-managed35-b/receipt.json` (derived from exact34); native pin:
  `.build/platform-native35-c/receipt.json`. Both hashes are in the lane JSON locks.
  Final package/artifacts: `artifacts/cabrillo-build35-final`. Public source is
  included in the later scoped CI publication above. Next unused identity is38;
  recheck before allocation.

- Accepted physical fallback: build32, Everest1.6531.0; preserve28/27/31 too.
  The15 September review of one export plus retained history closes the native
  browser/install/gameplay/Quit gate. See `docs/ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md`.
  Do not convert a host build or migration hash comparison into a device PASS.
- Build31 phone review passes two complete backend/gameplay/save/Quit runs and
  confirms the owner's loading UI concerns: long main-thread pauses and17.7s of
  hidden game frames before the title menu. See `docs/ios-jit/BUILD_31_LOADING_REVIEW.md`.
- Build32 (`launcher-first-frame`,0.16.2) refines the native display and reveals
  after first draw/post-Present readback in a successful foreground Frame callback.
  It reuses build31's exact phone-tested managed payload. The verified kit is
  uploaded to iCloud. Check its report/ledger
  and Results before requesting testing: `docs/ios-jit/FIRST_FRAME_BUILD_32.md`.
  Build32 is now physically accepted; see `docs/ios-jit/BUILD_32_ACCEPTANCE.md`.
  Retain all original artifacts and Results folders.
- Build33 (`launcher-backups`,0.17.0) adds Saves, portable whole-profile backups,
  staged exact restore and retained rollback. It reuses every32 managed assembly.
  New sources/package are frozen after packaging; phone33 is still unaccepted.
  Preserve its recovery boundaries, all unknown files, exact archive identities,
  disabled choices and fresh-process requirement. Read its report and ledger.
- Build34 (`launcher-save-transfers`,0.18.0) adds individual ZIP/main-file transfers,
  long-press menus, replacement/duplication review and empty slots1–3. The owner
  deferred33 testing; use34's combined backup/transfer/hair phone guide. All six
  files are confirmed uploaded. Check its Results and `docs/ios-jit/SAVE_TRANSFERS_BUILD_34.md`.
  Phone34 is unaccepted; sources/package and repair provenance are now frozen.
  A scoped repair changes four Celeste method bodies for hair, PlayerSeeker, bird
  tutorial and lava arithmetic. Only Celeste.dll changes among201 assemblies;
  all16 native archives match32. Pin `.build/precision-managed34-final/receipt.json`
  as recorded in ManagedPayload.json; do not substitute the older managed payload.
- Build29 is local preparation;30/31 sources and artifacts are frozen. Build32 has
  its own native identity and pins the same managed dependency in `ManagedPayload.json`.
  New implementation changes after packaging require another identity (next unused38;
  recheck before allocating). No historical UUID restoration for changed builds.
- Individual mod/game callbacks can still pause updates; the final pass yields
  between modules without holding its list monitor. Preserve its reentrancy guard,
  optional-cycle decisions, exact load order, game-thread ownership and window
  focus. Do not claim full phone responsiveness from host/simulator checks.
- Original delivered sources/artifacts remain immutable. Reproduction uses exact
  source/resource hashes and historical packaging metadata. New implementation
  changes require a new version/build identity and fresh evidence.
- The standalone build entry point is `tools/build.py`. Historical experiment
  builders are retained for their runtime patches and investigation context.
- `tools/build_development.py` builds the separate native preparation lane with
  fresh metadata/UUIDs against the pinned capsule. Build33 uses
  `tools/build_backups.py` with `tools/verify_backups.py`; the builder
  requires the exact validated managed receipt, with a separate new native UUID.
  Build34 uses `tools/build_save_transfers.py` / `verify_save_transfers.py` and
  the explicit derived managed receipt. Its repair tool and all hashed inputs
  are also frozen. Preserve ten intentional movement precision sites and the
  bounded audit's limits; host repair checks are not physical gameplay acceptance.
- UUID restoration is allowed only for build28 reproduction after matching every
  other byte against the locked executable hash. Never use it to conceal changed
  instructions, data, load commands or resources. Record the actual build time
  outside the historical app metadata and keep dSYM UUIDs consistent.
- `docs/MIGRATION_FILE_INVENTORY.json` records why imported files exist. Keep
  JIT-specific source, tests, documentation, licenses and required shared policy;
  do not pull in the AOT app or unrelated build outputs.
- Preserve exact module identities, compatibility pins, minimum runtime versions,
  reviewed installs, disabled choices, whole transaction recovery and accurate
  reports. GameBanana titles are not dependency identities.
- One game per process; fresh JIT request each time. Preserve normal main-menu
  Quit/native return, saves/settings/unknown sidecars and Export diagnostics.
- Keep catalogue work bounded and cancel it before managed startup; require
  `catalogue_quiesced` with zero active requests in phone evidence.

## Physical testing and delivery

- Target: iPhone15ProMax/iOS26.5. Celeste runs in LiveContainer slot1; StikDebug
  stays in slot2. Launch with JIT OFF, saved script blank, Fix File Picker ON.
  Use the app's fresh PID-specific inline request. Never attach another debugger
  concurrently with StikDebug.
- Owner authorizes relevant log collection and concrete physical tests. Provide
  exact steps and inspectable logs. Use exported map/room evidence directly.
- Default handoff: `iCloud Drive/Celeste JIT Tests/<version>-build-<number>`, up to
  1GB total. Include the unsigned IPA and short guide. Verify bytes and distinguish
  local placement, confirmed upload and actual phone download/execution.
- Preserve every Results folder. Superseded large installers may be removed from
  iCloud only after their exact local copies are verified. Keep the accepted
  fallback. Direct USB transfer to this owner's phone/LocalSend is a fallback.
- Preserve independent Export diagnostics even when automatic USB collection works.

## Roadmap and release boundary

- Build34 combines whole-profile backup, per-slot desktop transfers and numerical
  repairs. Phone34 acceptance is pending; review its Results and
  `docs/ios-jit/SAVE_TRANSFERS_BUILD_34.md` before requesting testing. Build33 stays
  preserved and unaccepted; the owner requested one combined34 test.
  The full-parity SwiftUI touch editor follows that gate; the owner prioritized35 platform/JIT work in the meantime.
  Do not queue fake progress behind blocking main-thread startup or move graphics
  initialization to an arbitrary worker.
- iPadOS is an intended next device target. Resizing, safe areas, pointer/keyboard/
  controller input, touch layout and JIT need tablet-specific evidence. macOS is
  a later product target; tvOS/visionOS remain investigations, not promised support.
- A public Git repository is separate from a publicly distributable IPA. Original
  IL preparation and FMOD permission remain unresolved release gates.
- Detailed historical decisions are in `docs/history/LEGACY_AGENTS_BUILD28.md`
  and `docs/ios-jit`; current instructions above supersede old active-work labels.
