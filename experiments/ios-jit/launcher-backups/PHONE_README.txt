Cabrillo 0.17.0 — build 33 — Whole-profile backups

Keep build 32 and every Results folder. Install/update this build in the existing
Celeste LiveContainer slot 1, keeping its data. StikDebug stays in slot 2.

1. Before enabling JIT, open Saves. Check that existing save slots look right.
   Everest can have more than three slots; unfamiliar/mod-only files are preserved
   even when a name, time or death count cannot be summarized.

2. Tap Create whole-profile backup. When Files opens, export it somewhere you can
   find again (for example a personal Saves folder in iCloud). This backup contains
   personal save data; it is separate from Export diagnostics.

3. Under that backup, choose Review restore, inspect the date/counts/mod choices,
   then Cancel review. Your current profile should be unchanged.

4. Import the exported backup from Files, review it and choose Restore this backup,
   then confirm Replace profile. It replaces the complete persistent profile and
   retains your current profile locally for rollback. Keep the app open during IO.
   After success, Run and profile changes must remain blocked until relaunch.
   Mod archives must match; if differences are reported, cancel and keep the export.

5. Close Cabrillo in the app switcher, relaunch, and check Saves. Enable fresh JIT:
   JIT OFF in LiveContainer, saved script blank, Fix File Picker ON. Use this
   process's inline StikDebug request, detach, return, then Run Celeste. Confirm
   your usual save/map loads, play briefly and use Celeste's normal main-menu Quit.
   Keep the native screen open for at least five seconds afterward.

6. Close and relaunch again. In Saves, choose Roll back to previous profile and
   confirm. This restores the profile retained at step 4. Relaunch once more and
   check the original saves/settings. Keep the retained copy until you are happy;
   Discard retained profile is optional and permanently removes that extra copy.

7. Export diagnostics from Settings into this build's Results folder. One final
   export retains recent sessions, but exporting after restore and after rollback
   helps if you perform many relaunches. Tell us whether the visual steps passed.
   Do not deliberately kill the app during a restore on your real saves; forced
   interruption recovery has separate synthetic host tests.

Scope: saves, game/mod settings, launcher preferences and unknown persistent
profile files. Game assets and mod ZIPs are excluded; exact mod identities and
choices are recorded. Files a mod stores outside this profile are not included.
No independent phone acceptance is claimed until these results are reviewed.
