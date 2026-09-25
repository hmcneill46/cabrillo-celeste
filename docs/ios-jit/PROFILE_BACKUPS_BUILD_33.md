# Whole-profile backups — build 33

15 September 2026. **Local validation passes; the phone kit is confirmed uploaded to iCloud.**
Build32 remains the accepted physical fallback. Build33 phone acceptance is
pending. Exact receipts and boundaries are in the
[evidence ledger](PROFILE_BACKUPS_BUILD_33_EVIDENCE.json).

## Resulting behavior

Saves lists every discovered nonnegative Everest slot ID, including mod-only
sidecars and sparse/high slot indices. It reads optional name, time, deaths and
file modification time without loading managed code. Unsupported or corrupt
summaries do not exclude files. The pinned Everest source dynamically adds an
empty slot unless MaxSaveSlots is configured; no three-slot cap is introduced.

Whole-profile backups preserve game saves/settings, mod settings, launcher
preferences, unknown persistent sidecars and empty directories. Files export
keeps a separate portable ZIP outside the guest. Local backups remain available
for later export, review or explicit removal. Profiles retain their existing
`Profiles/sj-first-play` identity; game assets remain in `GameLibrary`.

The manifest includes file lengths/SHA-256, exact mod ZIP identities, module
names/versions, disabled choices, bundled runtime and launcher/layout schemas.
Root mod ZIPs are omitted. The only other exclusions are the explicitly owned
`Cache`, `Mods/Cache`, `LauncherDownloads` and `LauncherIndex` directories.
Unknown profile files are included. External storage chosen by a mod is not
covered. ZIP export is limited to2GiB persistent data,512MiB per file and50,000
entries;100 local archives can be retained without automatic deletion.

A restore must match the currently installed archive set and bundled runtime.
The review lists missing, changed or additional archives and blocks replacement
until they are resolved. It restores recorded disabled choices. It does not
download mod archives or merge an old save tree into the current one.

## Transaction and lifecycle

Import copies into a private review folder, validates the complete archive and
stages persistent files. Bounds, path containment, case/Unicode collisions,
symbolic links, hard links, conflicting parents, ZIP CRC, sizes and SHA-256 are
checked before the active profile changes. The old profile is rechecked against
the reviewed revision, installed archives are copied and verified, and staged
files/directories are synchronized before the durable journal and renames.

Before the committed journal is durable, recovery selects the complete old
profile. Afterward, restored data is active and the old profile remains available
for rollback. Interrupted rollback finishes selecting the old profile. Recovery
runs before seeding/scanning mods or enabling Run. A changed/missing recovery
copy blocks startup and retains evidence. Explicit discard atomically detaches
the completed journal before deleting its retained tree.

All operations run under the launcher's existing mutation lock before managed
startup. After playing, relaunch before backing up or restoring. Restore/rollback
require another fresh process before game startup; no JIT/game work is introduced
by preview or backup. Export diagnostics remains available on error. Known iOS
system path aliases are resolved at the trusted Documents boundary; symlinks in
the profile or vault remain rejected.

## Local validation

- 59 native checks pass in a fresh compiled host harness, including exact restore,
  rollback, cancel/stale review, disabled choices, unknown data and empty folders,
  350 sparse slots, optional safe XML summaries, hostile ZIPs and local symlinks.
- Eight separate processes deliberately exit at the durable journal/rename
  boundaries. Fresh processes recover complete data, and repeated recovery is
  idempotent. No destructive interruption is requested on the owner's real saves.
- A cloned real game profile passes native backup/restore/rollback, then the exact
  accepted game/adapter/FNA/support payload passes startup, gameplay, save/resume
  contracts and normal Quit under the existing macOS host harness.
- The native arm64 launcher compiles with Xcode26.6/iOS26.5. No game or mod code
  was rebuilt. The final package and all six deliberately damaged package controls pass.
- Five UI tests pass on each of iPhone17ProMax and iPadPro11M5 simulators: extra
  slots/larger text/rotation, create/review/cancel/export, restore/relaunch/rollback,
  used-process controls and independent diagnostics on failure. The fixture uses
  the production store/view with synthetic data; it does not replace the phone
  document-picker/JIT/game test. Screenshots were inspected and both simulators
  returned to their original shutdown state.

Raw profiles, archives, diagnostics and screenshots remain ignored local artifacts.
Host/simulator checks establish their stated boundaries, not physical iPhone
acceptance. Public IPA original-IL/FMOD permission gates remain unresolved.

## Publication

The owner-approved loading work through accepted build32 was committed and
fast-forward pushed to `origin/main` as
`16ff42ca62438ccfa1c3ea14e76a6606da1bc820`. The remote ref was independently
verified. Build33 is local work on `codex/profile-backups`; its publication is a
separate owner decision. This does not block local implementation or phone delivery.

## Package and delivery

| Item | Value |
| --- | --- |
| Version / identity |0.17.0 (33) / `launcher-backups-20260915-33` |
| IPA |`artifacts/cabrillo-build33/Cabrillo-0.17.0-build-33-unsigned.ipa` |
| Bytes |24,000,196 |
| SHA-256 |`a66a44bd1e477fadb4df8d9127912fca2412babf87b3d3603b9f67461f5de79d` |
| Executable/dSYM UUID |`B0843965-0FC8-3020-B7D3-3E5421C8FE13` |
| Compilation |65 source inputs;135 source hashes; Xcode26.6 / iOS26.5 SDK |
| Unchanged vs32 |All201 managed assemblies,16 native archives and all resources except BuildInfo, Info.plist, executable and notices |
| iCloud folder |`Celeste JIT Tests/0.17.0-build-33` |

All six kit files match their local originals. The shared tests folder is
770,419,328 bytes after placement, below the owner's1GB allowance; no prior build
or Results folder was removed. All six uploads are confirmed with no remaining upload error. Phone download
and execution remain unconfirmed. Follow `README-FIRST.txt`
for one focused create/export/review/cancel/import/restore/relaunch/gameplay/Quit/
rollback check. Deliberate interruption tests used disposable synthetic profiles,
not the owner's saves. Retain the original exported backup and rollback copy.
