# Cabrillo profile backups — build 33

Version 0.17.0, `launcher-backups-20260915-33`. The Saves tab discovers existing
Everest slots, including sparse indices and mod-only sidecars, and provides
whole-profile ZIP backups, Files export/import, reviewed exact restore and rollback.

The format preserves every persistent profile file and empty directory without a
save-file allowlist. Optional XML summaries never execute mod code. It excludes
root mod ZIPs (recording exact filenames, hashes, module names/versions and enabled
choices) and only four owned cache locations: `Cache`, `Mods/Cache`,
`LauncherDownloads`, `LauncherIndex`. Game assets live outside the profile.
External mod storage is not portable in this format. Limits are 50,000 entries,
512 MiB per persistent file, 2 GiB persistent data, and 100 retained local backups.

Restore requires the installed archive set and bundled runtime to match. Import
checks bounded extraction, paths, case/Unicode collisions, file types, length,
CRC and SHA-256. Files are staged; existing ZIPs are copied and reverified. A
synchronized journal and directory renames select the complete old/new profile.
Before the commit record is durable, recovery selects the old profile; afterward,
new data is active and the previous profile is retained. An interrupted rollback
finishes selecting the old profile. Explicit discard detaches a completed record
before deletion. No game can start before recovery, or in the process that restored.

Operations run under the launcher mutation lock before managed startup. They are
available after a fresh relaunch; no managed calls or catalogue work are added.
Launcher preferences now have a profile-owned file and retain their old defaults
on first use. Existing game/profile identities stay compatible with upgrades.

All 201 managed assemblies, 16 native archives and the first-frame handoff are
unchanged from accepted build32. `ManagedPayload.json` pins the same validated
build30 payload reused by31/32. Build with `tools/build_backups.py`; validate with
`tools/verify_backups.py` and `tools/check_backups_package.py`. Native host,
UI and real restored-game checks are `tools/check_backups.py`,
`tools/check_backups_ui.py` and `tools/check_backups_host.py`. Test fixtures are
outside the IPA. See `docs/ios-jit/PROFILE_BACKUPS_BUILD_33.md` for evidence.

Build32 publication is complete. Build33 local development/delivery is authorized;
GitHub publication of the new feature has not been requested separately.
