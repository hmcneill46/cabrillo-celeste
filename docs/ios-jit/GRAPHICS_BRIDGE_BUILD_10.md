# Build 10: JIT FNA / Metal graphics bridge

Follow-up: [the physical test found a startup Metal callback-lifetime crash;
build 11 fixes it](BUILD_10_GRAPHICS_CRASH_AND_BUILD_11.md). The original build 10
readiness record below is retained as history.

**An unsigned physical test app is implemented, following the accepted
[build 9 Hook/ILHook gate](HOOK_EXECUTION_PASS_2026-09-11.md).** It renders a small
animated scene through real FNA and FNA3D Metal, exercises touch, retains a real
MonoMod render hook over pause/resume, and returns to the native launcher.
It contains no Celeste assets, Everest game payload or FMOD. Physical graphics
acceptance remains pending; this is preparation for G3, not the game baseline.

The source is `experiments/ios-jit/graphics-canary/`, with isolated outputs under
`.build/ios-jit/` and `artifacts/ios-jit/graphics-canary-20260911-10/`. App identity:
**Celeste JIT Graphics, 0.4.0 (10)**,
`io.github.hmcneill46.celeste.everest.jit.graphics`. It has its own data container
so the accepted Hook Canary and its logs remain available.

## What changed

The native bootstrap retains the build 9 request geometry, script, memory
allocator, custom Mono 8.0.28 and MonoMod bridge. Their accepted source and
runtime archive hashes remain unchanged. The script still prepares two 16 MiB
arenas with 2,048 acknowledged page writes and verifies detach before native
execution. There is no interpreter or AOT fallback.

All five native libraries were rebuilt at the existing iOS dependency pins in
JIT-only staging using Xcode 26.6. Device and simulator archives pass the
existing native verifier and match logical set
`9fb302d221180e39f270ea5ebf48e18433b67bd0a40943c042a227fe0f8ad6a2`.
SDL source fetching initially stalled on a full mirror; exact-commit shallow
fetches completed and verified the same pins. The build did not use mutable
outputs from the separate AOT checkout.

FNA source at `d52b4ce61e4086b785c51a96d331dbf106975a58` is compiled as
untrimmed net8.0 IL using SDK 8.0.422. Stock effects and all notices are embedded.
The binding source keeps the existing static import and stable touch-ID changes.
All **805 distinct declared `__Internal` imports** resolve through an explicit
static address table. This avoids relying on LiveContainer's global symbol
lookup. Two unused Emscripten declarations are not iOS capabilities. No
Microsoft.iOS assembly or Apple managed registrar is used.

The native launcher owns one UIApplication/scene lifecycle. SDL creates its
game window in that scene; `SDL_UIKitRunApp` is never called a second time.
A CADisplayLink drives bounded main-thread managed calls. The private FNA copy
adds a partial modifier and a narrow external-loop adapter with the full
BeginRun/RegisterGame/frame/OnExiting/EndRun/UnregisterGame sequence.
Calling `RunOneFrame` alone would omit necessary lifecycle setup.

Mono initializes on a worker and that worker detaches. The main thread attaches
once, protects each managed call with balanced GC-unsafe transitions, and
detaches after the game stops. Native notifications pause the display link
before inactivity and forward lifecycle events to SDL. Resume checks the hook
after GC and resets the FNA clock. If bootstrap finishes in the background,
window/GPU startup waits for the app to become active.

The fixture renders to a 320×180 texture and presents it with point sampling.
It verifies GPU clear/readback, draws orbiting squares and a touch-controlled
marker, and uses a real hook to alter the marker colour. Stop disposes graphics,
removes the hook, verifies the original method, detaches and restores the
launcher. The runtime remains alive; restarting a game or unloading arbitrary
mod assemblies is not implemented.

## Verification and limits

| Check | Captured local result |
| --- | --- |
| Native foundation | Device/simulator archives match accepted lock |
| Actual host Mono + FNA | 540 real Metal frames, GPU readback, retained hook after GC/resume, hook removal, main-thread detach |
| Host input scope | No synthetic phone touch; Stop correctly reports incomplete touch requirements |
| Native simulator launcher | Import gating, 800-event log burst, export, prior-session/console recovery, real request generation |
| Packaged script integration | Native request and actual ARM64 protocol descriptor agree; 2,048 page acknowledgements and detach in fake debugserver |
| Device IPA | Unsigned, no embedded dSYM/profile/signature, separate external fixture, exact runtime/source hashes |
| iPhone graphics/gameplay | Not yet tested |

The desktop regression uses the exact shared embedding code and fixture on the
pinned cooperative macOS Mono runtime, with copies of user-owned desktop
SDL/FNA3D libraries. It uses ordinary host executable pages, not iOS aliases.
Only RID and profiler ownership checks have explicit host-test conditionals;
those flags are absent from the device build. Desktop windowing, simulated
managed pause/resume and real Metal readback do not substitute for LiveContainer
graphics, UIKit backgrounding or touch acceptance.

The graphics test deliberately creates no sound. FMOD initialization, banking,
audio interruptions, full-game content compatibility, saves and mod loading are
still pending. A successful first frame cannot grant those capabilities. The
32 MiB code reservation remains a bounded test budget; measure physical high
water before selecting a full-game policy. Frame timing with detailed JIT logs
is diagnostic evidence, not an AOT-versus-JIT performance comparison.

Celeste's existing `Run` entrypoint also needs a deliberate startup/lifetime
adapter. Returning early from `Game.Run` inside its original `using` scope
would immediately dispose the game. This probe roots and owns its test game
explicitly; do not transfer its external-loop methods without adapting the
real game's initialization, exception handling and disposal boundaries.

## Physical handoff and next decision

The kit belongs in **iCloud Drive → Celeste JIT Tests → 0.4.0-build-10**, with
`Results/` for exports. The owner has now authorized up to **1 GB total** per
iCloud handoff, superseding the initial 50 MB limit. This particular kit is
about 12 MB. Exact file sizes, hashes, UUID, copied-byte verification and cloud
upload state are in [the evidence ledger](GRAPHICS_BRIDGE_BUILD_10_EVIDENCE.json).
An uploaded state does not imply that the phone has downloaded or installed it.

Install in LiveContainer 1, keep Launch with JIT OFF and its launch script
empty, import `GraphicsCanary-v0.4.0.dll`, then enable through StikDebug in
LiveContainer 2. After native checks, run graphics, drag/release the marker,
go Home for 30 seconds, return, drag again, wait 10 seconds and finish. Require
the visible scene, responsive input, same-process resume and return to the
launcher. Then wait 10 seconds and export to this build's Results folder.
The [full guide](../../experiments/ios-jit/graphics-canary/INSTALL.md) includes
the fresh-script fallback and crash-recovery procedure.

Persisted logs include each JIT range, native import, code allocation and patch;
graphics stages, GPU readback, touch counters, frame counts, native Metal/window
geometry, memory footprint, lifecycle boundaries, detach and result liveness.
Export still includes five prior sessions and native console tails. Reopen and
export first after a crash. The direct USB collector can select this distinct
bundle when the target iPhone is available; exact private guest IDs should be
discovered from installed metadata rather than reusing the Hook Canary UUID.

After this physical boundary passes, proceed to a single vanilla Celeste game
with the user's validated content, native FMOD and JIT-specific storage. Then
integrate the pinned Everest loader and small real mods. Keep the separate
AOT checkout and accepted probe artifacts unchanged. No commit, push or GitHub
write has been made or authorized.
