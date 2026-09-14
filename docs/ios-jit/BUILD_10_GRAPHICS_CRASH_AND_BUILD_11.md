# Build 10 graphics crash and build 11 callback-lifetime fix

11 September 2026. Build 10's phone setup was correct. It executed managed JIT,
installed the render hook and passed real Metal render-target clear/readback,
then crashed before its first Draw. The native renderer carried an autoreleased
command buffer across UIKit callbacks. A host regression reproduces the released
object; build 11 fixes the callback boundary and passes that regression. Physical
graphics/input/resume acceptance remains pending.

## Physical evidence

The owner exported diagnostics to the build 10 iCloud Results folder. Untouched
bytes, extracted session events/console, validator and symbolication are private:
`.build/ios-jit/device-evidence/2026-09-11/build-10-crash/`.
The 6,339,247-byte export has SHA256
`7bde6d5594e04802af0ceb67f98509383c6ab00fa102e29d13b4abb0dc047bca`.
The recovery session contains launch/export without another JIT attempt. No OS
crash report or live debugger attachment was needed for this diagnosis.

The crashed session is `e8f22578-9477-46b7-800d-138ce5c04e92`, PID 31301,
iPhone16,2 / iOS 26.5 (23F77). Its packaged BuildInfo, imported DLL, script,
compiled protocol and preserved source hashes match the delivered build 10.
Its exact IPA and matching Mach-O/dSYM UUID were checked.

| Evidence | Observed |
| --- | --- |
| Native execution checks | 26 passed, debugger detached |
| Managed JIT completions | 3,400, every reported range in prepared code allocations |
| Executable hook patches | 3, with no rejection |
| Graphics checks | Original hook result, installed hook result, Metal clear/readback passed |
| Code reservations | 4,161,536 / 33,554,432 bytes; no exhaustion |
| Window | One connected scene; SDL window has a Metal layer, 2796×1290 drawable |
| First Draw / completed frame | Not reached |
| First-frame path | SDL orientation event → GraphicsDevice.Reset → native Metal render pass |

An earlier session contains preparation requests without completed native tests.
It is distinct from the captured graphics crash and does not invalidate the
correct preparation in the crashed session. Reported container/debugger version
preferences are not fresh installation metadata.

## Cause and reproduction

Multiple native frames agree on an inferred image load address of `0x109eb8000`.
The captured return PC `0x10a0d25bc` maps to the instruction after
`mtlMakeRenderCommandEncoder(renderer->commandBuffer, passDesc)` in
`METAL_INTERNAL_UpdateRenderPass`. This is an inferred slide from the matching
binary and named frames, not an OS binary-images record. Native archive debug
lines were absent in build 10; exact disassembly and the pinned source identify
the operation. Build 11's FNA3D archive includes debug information.

The pinned Metal backend begins a frame and pushes an autorelease pool during
LoadContent's offscreen GPU work. Readback submits the first buffer and creates
another autoreleased command buffer; it leaves the frame open until Present.
Build 10 returns from Start without presenting. UIKit later drains its callback
pool, including the outstanding nested pool. The first display-link callback
then uses the renderer's stale command-buffer pointer.

This is consistent with Apple's documented rule that UIKit/AppKit process each
event-loop iteration inside an autorelease pool and that objects must be retained
to survive its drainage. [Apple memory-management documentation](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/MemoryMgmt/Articles/mmAutoreleasePools.html)

Build 10's desktop test had one pool around the whole run, which hid this lifetime
error. Adding a pool around each real managed callback makes the exact build 10
FNA/fixture fail. With NSZombieEnabled, the host identifies a message to a released
`GFX10_MtlCmdBuffer` for `renderCommandEncoderWithDescriptor:`. Its raw logs,
negative-control executable, source and receipt are archived in
`build-10-crash/host-callback-negative/`. The old desktop native library was the
supplied game's library; the positive build 11 test uses freshly built pinned
FNA3D source matching the device adaptation.

## Build 11 change

The isolated patch is
`experiments/ios-jit/graphics-canary/native/fna3d-callback.patch` against FNA3D
`dba98a71514cc30f3c19dc19fc0a479be7c90d52`. It adds a private
`FNA3D_CJIT_EndCallback` API, accepted only for the paired Metal backend.

- Finish pending clears, end an active encoder, submit unfinished GPU work,
  retain its committed buffer, drain the frame's pool and reset transient state.
  The operation adds no drawable acquisition or extra presentation. It is a no-op
  when the frame is already closed.
- Normal Present shares the same completion path. FNA's external begin/frame/end
  methods invoke callback completion in finally blocks, including suppressed Draw.
- Reset realizes pending clears and ends the old pass before releasing backbuffer
  attachments. This also fixes a separate stale-attachment hazard found in review.
- Renderer disposal completes pending work, waits for and releases the final
  committed command buffer before teardown.

`native-build.py` builds into `.build/ios-jit/graphics-native-build11/`, recording
the patch, full source hashes, compiler commands and device/host native hashes.
The IPA builder overlays only this FNA3D archive. The accepted base native
archives and locks, SDL scene adaptation, custom Mono runtime, G1/G2 sources,
hook bridge, 32 MiB code budget and exact StikDebug script are unchanged.
The active AOT checkout was not modified. No commits, pushes or GitHub writes.

The external fixture automatically checks startup completion, clear → Reset →
readback, and GPU work during update 120 followed by SuppressDraw. Update 121
performs another readback, proving the next callback can use the renderer.
The phone's visible animation/touch/background test remains the required gate.

## Verification and next physical test

The actual shared Mono embedding code and paired FNA/fixture passed 540 host
callbacks: 539 rendered Metal frames and one intentionally skipped Draw, startup
cleanup, reset/readbacks, retained hook after resume/GC, hook removal and main
thread detach. Each callback owns a separate autorelease pool. A second run with
NSZombieEnabled and confirmed Metal API validation also passed. The host does not
simulate physical touch, iOS executable aliases or a real iOS background interval.

The simulator passed launcher import gating, persistence through 800 log events,
export and previous-session/console recovery. The actual native request and
packaged ARM64 descriptor/script passed all 2,048 page acknowledgements and
detach in a fake debugserver, including stale PID/nonce and old geometry rejection.
Package verification resolves all 806 distinct __Internal declarations, checks
the paired host/device Metal patch and exact external fixture/FNA bytes, and
confirms no signature, provisioning profile or embedded dSYM.

Build **0.4.1 (11)** is `graphics-canary-20260911-11`. The local unsigned IPA,
external DLL, symbols and receipts are under `artifacts/ios-jit/graphics-canary-20260911-11/`.
The phone kit is **iCloud Drive → Celeste JIT Tests → 0.4.1-build-11**. Exact
hashes and source-snapshot counts are in the
[evidence ledger](BUILD_10_GRAPHICS_CRASH_AND_BUILD_11_EVIDENCE.json). All six
files and Results were confirmed uploaded without error at **16:55:31 UTC**;
11,927,092 copied bytes were verified. Phone download/installation is unobserved.

Install the new IPA over Celeste JIT Graphics in LiveContainer 1. Keep Launch
with JIT OFF and launch script empty; StikDebug stays in LiveContainer 2.
Import **GraphicsCanary-v0.4.1.dll**, enable JIT through the app and wait for native
PASS. Run graphics, drag/release for about 20 seconds, go Home for 30 seconds,
return to the same process, drag/release and wait another 10 seconds. Finish,
wait 10 seconds and export to this build's Results folder. The callback/reset
regressions run automatically; the template script need not be manually run.
On another crash, reopen and export before another JIT attempt.

Physical build 11 results are required before accepting graphics and integrating
Celeste's retained lifetime, content, FMOD and isolated saves. Full game code
capacity, arbitrary mod loading, general thread-safe rendering, and reliable game
restart/unload remain separate work. This kit contains no Celeste/Everest gameplay.
