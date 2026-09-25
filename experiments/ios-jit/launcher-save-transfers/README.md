# Cabrillo save transfers and numeric compatibility — build34

Version0.18.0, `launcher-save-transfers-20260917-34`. This is a fresh native lane;
packaged33 and accepted32 are preserved. The owner requested these additions
before testing33, then asked to investigate hair physics and related mistakes.

## Saves

Slots1–3 always appear, including empty gaps. Occupied Everest slots beyond3 are
also shown. **Import another save** chooses the lowest unused index. Empty UI rows
do not create fake files; start a new game through Everest's own empty slot. Its
default file selector adds an empty slot after the highest existing one; a custom
Everest `MaxSaveSlots` setting may limit what the in-game selector displays.

Long press or tap the accessible ellipsis menu to:

- Export the slot's original main file and all standard mod files as a plain ZIP.
- Export only the main numbered `.celeste` file for vanilla transfers.
- Replace/import from Files, review both saves, then explicitly confirm.
- Review duplication into the first empty slot.
- Inspect progress, date, game version and filenames.

Desktop slots1–3 are `0.celeste`, `1.celeste`, `2.celeste`. A ZIP contains these
original files at its root plus `cabrillo-save.json` and a short README. Plain
one-slot desktop ZIPs, including a `Saves/` folder, and multi-selected files are
also accepted. All files must belong to one slot and include its main XML save.
Filename prefixes are remapped to the chosen target; internal bytes are unchanged.
Unknown `N-mod*.celeste` data remains opaque. Mod files stored elsewhere require a
whole-profile or separate backup. Mod archives are never installed by a transfer.

A standalone main-file import offers **Keep this slot's existing mod files** for
returning the same climb from vanilla. Turning it off, or importing a complete
slot ZIP, replaces the complete target slot's standard save files. Other slots,
settings, caches, archives, unknown files and disabled choices are copied exactly.
The complete previous profile is retained, using33's durable journal and recovery
phases. Another import requires an explicit retained-copy decision. Relaunch
before starting the game after any import, restore or rollback attempt.

Transfers accept UTF-8 SaveData XML with bounded parsing and no DTD/entities.
Limits:32MiB main XML,128MiB per sidecar,512MiB total transfer,4,096 files;
the existing profile transaction has its original limits. ZIP traversal, duplicate
or ambiguous names, symlinks, unrelated entries, malformed XML, missing main files,
stale reviews and changed source/staged profile bytes are rejected before commit.
The manager supports sparse existing indices; new destinations are bounded below
50,000 to avoid integer-overflow or pathological selector allocation. This is not
an unlimited-capacity guarantee for Everest or mods.

## Compatibility

Original Celeste1.4.0.0 serialization, native reimport with mod-file preservation,
and real Everest loading/save/Quit are tested. Desktop filenames and contents are
preserved. This does not establish compatibility with every historical game
version, console container or custom mod serialization format. Matching game/mod
versions are recommended; vanilla only exposes three slots. Saved dates can change
when copying: compare play time/deaths/name and keep an export before replacing.
This is manual transfer, not automatic cloud sync or merging two progress histories.

Primary references:

- [Everest save locations](https://github.com/EverestAPI/Resources/wiki/FAQ#how-can-i-backup-my-savedata)
- [Everest file selector](https://github.com/EverestAPI/Everest/blob/d72e94f4b9e62b91cbdea674587ed39d53de9550/Celeste.Mod.mm/Patches/OuiFileSelect.cs)
- [Slot index assignment](https://github.com/EverestAPI/Everest/blob/d72e94f4b9e62b91cbdea674587ed39d53de9550/Celeste.Mod.mm/Patches/UserIO.cs)

## Numeric repair

The historical platform adaptation tested a broad `Player*` type prefix and
whether a method contained any double conversion. It consequently widened only
one operand in ten originally float-only multiplications: hair1, seeker6 and bird
tutorial3. Actual Mono8 gameplay reproduces zero hair attraction; removing the
accidental conversions restores motion. The repaired hair method's normalized IL
matches original vanilla exactly. Ten intentionally widened player movement sites
remain unchanged.

The adjacent assembly audit also identifies a missing double conversion on a lava
surface-bubble count constant and two float property setter boundaries. The repair
retains Everest's double arithmetic, widens the missing constant and supplies the
original float arguments to the setters. A256×128 test rectangle changes from4
to the expected40 surface bubbles, keeping163 underlying bubbles and dimensions.

Only four game method bodies change;17,300 others retain their normalized IL.
The straight-line expression audit finds no remaining recognized mixed float/double
arithmetic or double-to-float call/field boundaries. Unknown control-flow joins are
not guessed: this is a bounded audit, not proof of all numerical/game correctness.
Only `Celeste.dll` changes among201 managed assemblies. FNA, adapter, original
content, runtime, renderer and16 native archives remain identical to32.

`tools/repair_player_precision.py` derives this payload from the exact accepted
managed receipt. `tools/save_transfer_inputs.py` validates both provenance and
scope. The native builder/verifier pin the resulting receipt and every resource.
Historical loading tools and all delivered source lanes are unchanged.

Use `tools/build_save_transfers.py`, `verify_save_transfers.py`, and the
`check_save_transfers*`, `check_vanilla_save.py`, `check_precision_repair.py` checks.
Host probes, original-game serialization and simulator fixtures are never shipped.
Phone acceptance remains distinct; see the build34 report and phone guide.
No GitHub publication is authorized for this feature work yet.
