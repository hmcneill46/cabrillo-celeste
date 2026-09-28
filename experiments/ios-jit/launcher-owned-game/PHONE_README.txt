Cabrillo 0.21.0 — build 38
Owned-game import and one-time preparation

Update your existing Cabrillo installation/LiveContainer slot to preserve data.
This IPA contains no Celeste game code or assets. Select your original,
unmodified celeste-win-opengl.zip once after this update, even if the old app
already imported its assets. Keep the original ZIP somewhere safe.

PHONE: Keep the working Increased Memory Limit setup for LiveContainer if
playing Strawberry Jam. Launch Cabrillo with LiveContainer JIT OFF and its saved
script blank; Fix File Picker ON. Use Cabrillo's fresh PID-specific inline JIT
request with StikDebug. Never attach another debugger at the same time.

IPAD: The previously tested TrollStore/Dopamine setup can use its local JIT
permission. Tap Check JIT for this launch, then Run Celeste + Everest.

1. Import the original game ZIP and start with a fresh JIT request.
2. The first run says Preparing your copy of Celeste, with real preparation
   stages. Keep Cabrillo open. This extra work is saved for future launches.
3. Confirm the title screen, sound and a short gameplay run. Use normal Quit.
4. Close and relaunch Cabrillo, make a fresh JIT request, and launch again without
   reselecting the ZIP. Check that the game opens and the save is intact.
5. On the phone, use your existing working mods, including Motion Smoothing and
   Strawberry Jam if desired. Report any difference from build37.
6. Export diagnostics to this kit's Results folder. Note whether the first run
   and the second, cached run both completed.

An interrupted preparation cannot replace a completed cache. Damaged prepared
files are rebuilt from saved originals; if the originals are damaged, import
that original ZIP again. Do not delete saves or profiles to retry.

The outstanding native save-manager backup/transfer/restore tests remain
separate; successful gameplay alone does not close them. Keep build32 and the
prior Results folders. This kit is for private testing; FMOD redistribution
permission is still pending.
