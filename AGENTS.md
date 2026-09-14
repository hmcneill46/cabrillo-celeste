# Cabrillo development

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
- Both `/Users/harrymcneill/Projects/celeste-ios` and the legacy
  `/Users/harrymcneill/Projects/Celeste-Everest-JIT-Apple-Platforms` are read-only.
  Never build into, clean, reset or otherwise change those checkouts/caches.
- Preserve originals in `/Users/harrymcneill/Projects/Celeste Required Files`.
  No game code/assets, FMOD SDKs, signing identities, pairing data or private
  logs may enter Git. `.private`, `.build` and `artifacts` remain ignored.
- Use Xcode26.6. The local `.private` capsule is an explicit pinned dependency,
  not a Git source directory. Do not silently fall back to a legacy checkout.

## Current state

- Accepted physical fallback: build27, Everest1.6531.0. Build28's native browser
  passes local tests; phone28 acceptance is still pending. Do not convert a host
  build or a migration hash comparison into a physical-device PASS.
- Original delivered sources/artifacts remain immutable. Reproduction uses exact
  source/resource hashes and historical packaging metadata. New implementation
  changes require a new version/build identity and fresh evidence.
- The standalone build entry point is `tools/build.py`. Historical experiment
  builders are retained for their runtime patches and investigation context.
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

- After phone28: responsive real startup progress, whole-profile save/settings
  backup with staged restore/rollback, then full-parity SwiftUI touch editing.
  Do not queue fake progress behind blocking main-thread startup or move graphics
  initialization to an arbitrary worker.
- iPadOS is an intended next device target. Resizing, safe areas, pointer/keyboard/
  controller input, touch layout and JIT need tablet-specific evidence. macOS is
  a later product target; tvOS/visionOS remain investigations, not promised support.
- A public Git repository is separate from a publicly distributable IPA. Original
  IL preparation and FMOD permission remain unresolved release gates.
- Detailed historical decisions are in `docs/history/LEGACY_AGENTS_BUILD28.md`
  and `docs/ios-jit`; current instructions above supersede old active-work labels.
