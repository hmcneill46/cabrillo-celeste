Cabrillo 0.18.0 — build 34 — Save transfers + hair/precision fixes

This includes build33's backups, so test this build instead of doing a separate33
suite. Keep accepted build32 and all Results folders. Install/update in the same
Celeste LiveContainer slot1, preserving data; StikDebug stays in slot2.

BEFORE PLAYING (no JIT needed)
1. Open Saves. Check your names, times, deaths and dates. Slots1–3 should appear
   even when empty; occupied extra Everest slots should remain visible.
   Hold a filled slot, then try its ••• button: both should offer the same menu.
   Inspect Save details. You can review Duplicate into empty slot, then Cancel.

2. Create a whole-profile backup and export it to your personal Files folder.
   Also export one slot as both "save + mod data" (ZIP) and "main .celeste file".
   Keep these copies: they contain your personal saves, separate from diagnostics.

3. Tap Import another save and select that slot ZIP from Files. Check the incoming
   and destination details; the destination should be empty. Cancel once. Repeat,
   confirm Import save, then close Cabrillo in the app switcher and relaunch.
   Check that the new slot has the same progress and the original slot is intact.
   After imports/restores, Play and profile changes must wait for a fresh process.

PLAY AND HAIR CHECK
4. Enable fresh JIT: LiveContainer JIT OFF, saved script blank, Fix File Picker ON.
   Use this process's inline StikDebug request; detach, return, then Run Celeste.
   Load the imported save. Check hair while standing, walking, turning, jumping
   and dashing. It should follow normally instead of bunching/sticking strangely.
   Play briefly, then use Celeste's normal main-menu Quit. Leave the native screen
   open for five seconds. Export diagnostics to this build's Results folder.

ROLLBACK AND WHOLE-PROFILE BACKUPS
5. Close and relaunch. In Saves, Roll back to previous profile and confirm.
   Relaunch again; verify the original slots/settings. The test copy should be
   gone. If happy, Discard retained profile to allow the next restore. This removes
   the retained post-test profile; keep an exported backup if you want that progress.

6. Import the whole-profile backup from step2, inspect its review, and Cancel.
   Import it again, confirm Restore, then relaunch. Check the original saves and
   settings, play briefly if practical, and Quit normally. Close/relaunch, Roll
   back to previous profile, relaunch once more and check the original profile.
   Export diagnostics again into Results and tell us which visual steps passed.
   Do not intentionally interrupt a restore on real saves; interruption recovery
   is tested separately using synthetic copies.

OPTIONAL DESKTOP ROUNDTRIP
Close Celeste on both devices. Back up the desktop Saves folder first.
For desktop Everest, unzip the slot export and copy its numbered .celeste files
TOGETHER into Saves. For vanilla use the main file; only 0,1,2 are visible slots.
If changing the target index, rename every file's numeric prefix consistently.
When replacing a complete slot, retain a backup then remove its old -mod*.celeste
files so unrelated progress is not mixed. The ZIP includes these instructions.

To bring it back, long press the chosen Cabrillo slot > Replace from Files.
Select its main file plus mod files together, or a ZIP containing just that slot.
Review before confirming. For a standalone vanilla main file, keep existing mod
files ON for the same climb; turn it OFF if replacing with a different climb.
All other slots/settings stay intact, and the previous profile is retained.

Windows Saves: <game folder>/Saves
macOS: ~/Library/Application Support/Celeste/Saves
Linux: ~/.local/share/Celeste/Saves (or $XDG_DATA_HOME/Celeste/Saves)
Compatible game, Everest and mod versions are needed. Dates alone do not establish
which save is newest; compare progress. This is manual transfer, not automatic sync.
Original Celeste1.4.0.0 and the pinned Everest are host-tested; other versions and
console-specific containers are not universally guaranteed. No phone PASS is
claimed until your build34 results are reviewed.
