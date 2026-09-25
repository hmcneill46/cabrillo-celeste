Cabrillo 0.20.0 (37) — Everest stable1.6580.0

Keep build32 as the accepted phone fallback. Build37 needs physical testing.
This includes build34’s backup/save-transfer features and hair/lava repairs.

FOCUSED EVEREST UPGRADE CHECK
This build uses Everest stable1.6580.0 (previously1.6531.0), with the build36
Motion Smoothing startup correction and the earlier touch/hair/save repairs.
1. Update Cabrillo in the existing LiveContainer slot, preserving app data.
2. Use a fresh process and fresh JIT request. Keep your selected mods.
3. Check the launcher/runtime information says Everest1.6580.0.
4. With Motion Smoothing and Allow up to120Hz enabled, launch and play a short
   room. In the mod select120 FPS / Interval, normal game speed60. Check camera,
   short taps, hair, room transitions and normal main-menu Quit.
5. Export diagnostics to this folder's Results and share any visible issues.
Build36's startup fix was already reported working on the phone. This checks
the new Everest version; it does not ask you to repeat the older complete suites.
The saves checklist below is still pending and can be done when convenient.

IPHONE / LIVE CONTAINER
1. Import this unsigned IPA into LiveContainer slot1. Preserve your existing app data.
2. Launch with JIT OFF, saved script blank and Fix File Picker ON.
3. Settings → JIT: choose StikDebug in LiveContainer2 (the previous route), or
   Standalone StikDebug if you want to test the installed copy outside LC.
4. On Play, Enable JIT. Complete its fresh PID-specific inline request, return
   to this same running Cabrillo process and wait for the native checks to pass.
5. Run Celeste + Everest. Keep the first frame/loading and normal Quit checks.

STANDALONE INSTALLS
StikDebug requires iOS17.4+. Install Cabrillo with get-task-allow entitlement;
use Settings → Standalone StikDebug. iOS26 uses the fresh inline memory script.
Below iOS26, activation still needs JIT, but no memory script is sent.
On iOS15 with TrollStore2.0.12+, choose TrollStore and enable its URL scheme in
TrollStore Settings, or use Open with JIT manually. Jailbreak tools that already
enable JIT can use Already enabled / another tool → Check JIT for this launch.
Keep only one debugger attached at a time; Cabrillo waits for detach before executing.
The iOS15 memory path samples pages across both arenas; it does not claim every
page has been executed. It avoids committing the entire512MiB during startup.

IPAD MINI4 / iOS15
The original game ZIP is already on the iPad. Preserve app data when updating. On Play, check JIT,
then turn the iPad to landscape and run. First content verification/extraction
can take longer on this device. Start with the base game before large mod packs.
Verify Play/Mods/Saves/Settings, landscape, touch jump/dash/grab/pause, audio,
a short room, normal main-menu Quit and return to the launcher. Export diagnostics.
The mini4 has a60Hz display and approximately2GB RAM; huge mod packs remain untested.

MOTION SMOOTHING (optional mod; not bundled)
Browse → search Motion Smoothing → review and install the original1.8.0 ZIP.
At60Hz, choose60 FPS in the mod’s in-game settings. Camera subpixel smoothing
can still help at60Hz. Start with Fast rendering on the older iPad.
On a120Hz phone, enable Settings → Allow up to120Hz in Cabrillo before starting,
then set the mod to120 FPS / Interval, normal game speed60. Leave Cabrillo at60
when you are not using a frame-rate mod. Higher refresh uses more battery.
Check short taps, holding and releasing jump/dash/grab, pause/menu input, camera,
hair, a room transition, background/resume and normal Quit. Compare60 and120.
Fast and Fancy renderers are checked with the corrected metadata source; phone120Hz smoothness,
sustained performance and battery behavior require the actual device.

SAVES / BACKUPS (combined build34 gate is still pending)
1. Check three empty slots on a fresh profile, and metadata for existing saves.
2. Create/export a whole-profile backup before any replacement or restore test.
3. Long press a save: export ZIP and main-file-only; duplicate into an unused slot.
4. Review importing/replacing a disposable slot. Preserve mod files with a raw
   main-file replacement when that choice is appropriate; complete ZIPs replace
   that slot’s included standard files. Never use your only copy of a save.
5. Restore the backup only after reviewing it. Relaunch as required; verify the
   restored saves/settings/mod choices and retained rollback. Unknown files stay preserved.
6. Check hair movement and lava while playing. Host precision checks are not a
   substitute for the phone’s gameplay review.

Please put the final Export diagnostics file and brief visual observations in
this build’s Results folder. One final export retains earlier sessions too.
No game files or mod ZIPs are included in this IPA. Preserve all older Results.
