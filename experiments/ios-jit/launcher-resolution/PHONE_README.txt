CELESTE — PRIVATE TEST BUILD 26
Version 0.13.1 (26) • Dependency compatibility and installation reports

1. UPDATE THE APP, KEEP YOUR DATA
   Files → iCloud Drive → Celeste JIT Tests → 0.13.1-build-26.
   Install CelesteJITEverest-unsigned.ipa as an UPDATE to the same app in
   LiveContainer slot 1. Do not delete the existing app or its data.
   Launch with JIT OFF, saved JIT script blank, Fix File Picker ON.
   StikDebug remains in LiveContainer slot 2. No game reimport is needed.
   The dependency/update tests below do not need JIT.

2. DEPENDENCIES AND REPORTS
   Use the SpringCollab2020 ZIP you already imported, or import it normally.
   Do not wipe your saves or existing working profile to make this test fresh.
   Enable SpringCollab2020, then Resolve dependencies and review the plan.
   If ExtendedVariantMode / MaxHelpingHand are missing, this build can choose
   verified earlier versions 0.50.5 / 1.40.9, disclosed in the review.
   Existing compatible copies stay as they are. No newer runtime is installed.
   If any requirements remain blocked, nothing should be applied: export
   diagnostics instead of force-enabling an incompatible version.

   Download and install on Wi-Fi, keeping the app in the foreground.
   A fresh Spring selection needs about 536 MB of dependencies, mostly audio.
   You may need less with existing mods. If practical, Cancel once, inspect
   the report, then retry. Verified complete downloads should be kept.
   Server errors may trigger an Everest community mirror; size/hash checks
   remain mandatory. If actual ZIP requirements differ, review again.

   The final report should list installed versions, any existing dependencies
   enabled, and any updates as OLD → NEW. Failed/cancelled attempts must say
   which downloads were verified, failed or not attempted, without claiming
   mod changes were applied. Reopen “Last installation report” in Mods.
   Export diagnostics now to this folder's Results, before another operation
   replaces the last report. A screenshot helps if the report looks wrong.

3. UPDATE CHECK
   Mods → Updates → Check for updates.
   ExtendedVariantMode 0.51.0 and MaxHelpingHand 1.40.10 require Everest
   1.6531.0. They should be under “Requires an app update” with NO Update
   button. “Update all compatible” must exclude them.
   EeveeHelper 1.12.6 and FrostHelper 1.80.2 are compatible. If already
   installed, they should not be offered again. If still on 1.12.5 / 1.80.1,
   update them and check the report gives those exact old → new versions.
   Disabled mods must stay disabled when updated. Original ZIPs remain as
   retained disabled archives. Do not reinstall old versions just for this test.
   Export diagnostics again if you applied any update.

4. PLAY, QUIT, RELOAD
   Play → Enable via LiveContainer 2; run this process's NEW inline request
   in StikDebug. Wait for success and debugger detach, return, Run Celeste.
   The JS in the kit is the reference template, not a reusable PID script.
   Confirm existing saves are present. Try Spring Collab's Beginner lobby
   and a map, or your familiar working mod if Spring is not ready.
   Play a few minutes, background for 30 seconds, return and jump.
   Save and Quit from the map, then Quit/Exit from the main menu. Wait for
   the native launcher/session result and another 10 seconds, then Export.
   Close and relaunch; reopen the report and verify mod choices persisted.
   Use another fresh JIT request, run and confirm saved progress survived.
   Quit normally and export a final diagnostic to this folder's Results.
   Diagnostics record the map and room; no need to identify them manually.

After a crash, export before enabling JIT or starting another game session.
One game session per process remains. Keep Export for the iCloud fallback.
Build24 in 0.12.1-build-24 remains the accepted fallback.
This is a private test kit, not a public distribution package.
