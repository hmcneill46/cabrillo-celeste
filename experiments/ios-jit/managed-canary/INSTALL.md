# Managed JIT canary — 0.2.2 (build 6)

This is the next runtime test toward Celeste + Everest. It does not launch the
game or accept game mods yet. It contains a custom Mono .NET 8.0.28 ARM64 JIT,
with AOT and the interpreter disabled, and imports a separate test DLL.
Build 5 passed all eight managed stages, then crashed while detaching the native
worker from Mono. Build 6 fixes that cleanup transition and records return to
the launcher plus a five-second survival check. Your recorded build 5 steps
were correct; no different StikDebug configuration is needed.
Import the **new DLL**, even if the previous one is still in the app's storage.

## Files

On the phone, open **Files → iCloud Drive → Celeste JIT Tests → 0.2.2-build-6**.
Download both the IPA and DLL before starting:

- `CelesteJITCanary-v0.2.2-build-6-unsigned.ipa`
- `Canary-v0.2.2.dll` — a small test assembly, compiled after packaging the IPA.
- `README-FIRST.txt`, this guide, and checksums.

The matching StikDebug script is built into the app. It creates a fresh script
for the actual LiveContainer host PID on every launch. The separate
`celeste-jit-probe-TEMPLATE.js` is reference material, not a script to run.
**Do not reuse a build 1–3 script:** this build prepares two 4 MiB arenas.

## Physical test

1. Fully close the old canary, then install/update the IPA in **LiveContainer 1**.
   Preserve its app data and old diagnostics. It is a separate app named
   **Celeste JIT Canary**; the earlier native probe can remain installed.
   In this app's LiveContainer settings, leave **Launch with JIT OFF** and the
   **JIT Launch Script empty**. If LiveContainer offers a file-picker fix,
   enable it as in your working setup.
2. Open **StikDebug in LiveContainer 2** and prepare its usual connection/VPN.
   Open Celeste JIT Canary in LiveContainer 1. Keep other debuggers detached.
3. Tap **1. Import Canary DLL**. Pick `Canary-v0.2.2.dll` from the same iCloud
   folder. The app should say **Test DLL imported ✓**.
4. Tap **2. Enable via LiveContainer 2**, complete StikDebug's script request,
   then return to the existing canary in LiveContainer 1. The larger request
   prepares 512 pages, so allow it to finish. Do not relaunch the canary during
   preparation. Its native checks run automatically after verified detach.
5. At **NATIVE PASS · READY FOR MONO**, tap **3. Run managed JIT test** (scroll
   down if needed). Leave the app in the foreground. It runs once per launch.
6. At **PASS · MANAGED JIT**, keep it in the foreground for **10 seconds**, then
   switch to Files or the Home Screen for about **20 seconds** and return to
   the same canary. Do not close/relaunch it or request JIT again.
7. Whether it passes or stops, tap **Export diagnostics** and send the resulting
   `CelesteJIT-<session>.diagnostics.json` here or save it in this build folder's
   `Results` subfolder as before. Record the LiveContainer and
   StikDebug versions if they changed from 3.8.9 / 3.1.9.

The target is your **iPhone 15 Pro Max on iOS 26.5**. Do not install this build
on tvOS. No separate Xcode attachment is needed for this initial test.

## Expected result and recovery

**PASS · MANAGED JIT** means all eight canary checks completed: native framework
imports, imported IL arithmetic, ordinary switch tables, a new `DynamicMethod`,
a dynamically emitted switch, generic/struct/floating-point returns, exceptions
with GC, and a managed thread calling native code and back into a managed
delegate. Diagnostics also require JIT profiler evidence and method
addresses inside the prepared code arenas. The exported report still needs
review; this is not Everest/mod compatibility acceptance.

If it **closes/crashes**, reopen the canary and immediately **Export diagnostics**
before enabling JIT or rerunning anything. The export includes the previous
five sessions and the tails of their native console logs. Do not delete the app
or its data. If it **hangs**, allow about a minute, note the last visible stage,
then close/reopen and export. A crash or stopped stage is useful evidence.

If preparation fails, also share StikDebug's script log. Do not run a completed
script again. Start a fresh app process for another attempt. If the phone
offers an iOS crash report for the hosting LiveContainer process, retain it;
we can inspect that if the persistent runtime log is insufficient.

## Manual script fallback

Only if the inline route fails: in the running canary tap **Export session
script (manual setup)**, save that exact `.js`, import it into StikDebug in
LiveContainer 2, then tap **Use imported script in LiveContainer 2** in the
same running canary. Match the PID in both apps. Never assign an old session
script as a future LiveContainer launch script.

## Build limits

This first canary reserves a fixed 8 MiB of code memory and retains it for the
process lifetime. It uses invariant globalization and disables the unsupported
EventSource/EventPipe backend; native and JIT logging remain active. It links the native
framework functions needed for these tests. It has no MonoMod, game assets,
SDL, FNA or FMOD. A successful test unlocks the real Hook/ILHook canary, followed
by bringing up Celeste and Everest in this runtime. No AOT checkout was changed.
