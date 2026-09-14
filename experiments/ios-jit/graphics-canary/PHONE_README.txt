CELESTE JIT GRAPHICS — 0.4.1 (BUILD 11)

This fixes build 10's startup crash. It is a graphics test, not Celeste gameplay yet. No game assets or audio.
It tests real JIT FNA + Metal, GPU readback, touch, a live hook and pause/resume.

Files on your phone:
iCloud Drive > Celeste JIT Tests > 0.4.1-build-11

1. Fully close the old LiveContainer 1 process. Install the versioned unsigned
   IPA in LiveContainer 1. This updates the existing “Celeste JIT Graphics” entry.
   Check its version is 0.4.1 (11); do not launch the old build.
   Keep Launch with JIT OFF and its launch script EMPTY.
   StikDebug stays in LiveContainer 2, as before.

2. Launch Celeste JIT Graphics and hold the phone landscape.
   Tap “1. Import GraphicsCanary DLL” and select GraphicsCanary-v0.4.1.dll
   from THIS folder. Tap “2. Enable via LiveContainer 2”. Let StikDebug finish
   the script, then return to the graphics app. Wait for NATIVE PASS.
   The app sends its own fresh script. Do not manually run the TEMPLATE file.

3. Scroll down if needed and tap “3. Run graphics test”.
   Expect a dark grid, moving blue squares and a pink marker. Drag the marker
   BELOW the top controls; release your finger. Repeat a few times.
   Let it animate for about 20 seconds. A controller is optional.

4. Go to the Home Screen for 30 seconds. Keep LiveContainer running.
   Return to the SAME app/process. The animation should resume.
   Drag and release again; wait another 10 seconds. Tap “Finish test” at the
   top right. Expect to return to the launcher with PASS · FNA GRAPHICS + RESUME.

5. Wait 10 seconds, then tap “Export diagnostics” > Save to Files >
   iCloud Drive > Celeste JIT Tests > 0.4.1-build-11 > Results.
   Please tell me whether the scene was visible, touch worked, and resume
   looked correct. A short screen recording is useful if anything looks wrong.

IF IT STOPS OR CRASHES:
Reopen the graphics app and EXPORT FIRST, before enabling JIT again. The export
includes previous sessions and native console tails. Save it in this Results
folder. Partial results are useful. Send StikDebug’s script log too if the
script fails. A fresh app process is required for each full attempt.

Keep the build 9 app/results and old folders. They are the accepted hook baseline.
No Xcode debugger should be attached while StikDebug is preparing this process.
INSTALL.md has the manual-script fallback. SHA256SUMS.txt identifies this kit.
