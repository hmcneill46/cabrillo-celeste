# Metal backbuffer readback — build 24

Status: all local Mono/Metal, game, native, simulator, UI, package and JIT-request
gates pass. The unsigned IPA is 23,145,454 bytes. Physical build24 execution is
pending. All eight iCloud kit files (23,164,143 bytes total) are confirmed
uploaded; phone download has not yet been observed.
The current identities, gate results and delivery status are in
[the evidence ledger](METAL_BACKBUFFER_BUILD_24_EVIDENCE.json).

## Decision from the phone export

[Build23's two matching phone sessions](BUILD_23_SESSION_ACCEPTANCE.md) pass
main-menu Quit, ordinary modded play/save/Quit, complete native return and a
post-run heartbeat. There are no recorded runtime failures. The 7.99-second
modded cleanup completes, so there is no new evidence requiring a teardown
rewrite before the planned graphics increment. Build23 becomes the fallback.
The export does not contain another process reloading its final sidecar counter
403; carry that check into this kit without claiming it already happened.

New lane: `experiments/ios-jit/launcher-backbuffer`, **0.12.1 (24)**,
`launcher-backbuffer-20260912-24`. The AOT checkout, original inputs, delivered
build23 and older renderer remain untouched. No commit or remote write.

## Cause and native correction

The pinned FNA3D Metal `METAL_ReadBackbuffer` populated the dimensions and format
of a stack-local MetalTexture but never initialized its `handle`. Its downstream
GetTextureData2D used that invalid pointer as the GPU blit's source texture. A
fresh original-renderer control reproduces SIGSEGV in Metal's copy validation,
with METAL_GetTextureData2D and METAL_ReadBackbuffer in the native stack. The
managed caller is the real FNA GetBackBufferData API on the accepted Mono8.
This isolates the native defect even with the new managed bounds guard present.
[Original FNA3D source](https://github.com/FNA-XNA/FNA3D/blob/dba98a71514cc30f3c19dc19fc0a479be7c90d52/src/FNA3D_Driver_Metal.c).

The new renderer is built in `.build/ios-jit/launcher-backbuffer-renderer`.
It initializes the descriptor to zero and supplies the retained game backbuffer's
single-sample colorBuffer. That is also the resolve destination when MSAA is
active; the CAMetal drawable is only the final presentation destination. It is
not the source for this API, and its callback lifetime was not the original bug.

Readback now encodes deferred clears before ending the pass. It does not change
the current render target. The existing private-texture staging/blit/CPU-sync
path is retained. Rectangle and destination-capacity checks reject invalid
native requests before GPU commands. The inherited external-callback and reset
patch remains byte-identical.

Ending a pass for readback must also preserve multisample storage for subsequent
drawing. The renderer uses StoreAndMultisampleResolve instead of resolve-only
for MSAA attachments. The deployment targets support that action; ordinary
non-MSAA passes are unchanged. This can add MSAA storage bandwidth, so it is a
correctness fix, not a performance claim. The source delta from the accepted
renderer is confined to the Metal driver and its enum header.
[Apple's store-and-resolve contract](https://developer.apple.com/documentation/metal/mtlstoreaction/storeandmultisampleresolve).

## Related managed boundary correction

Inspection found the older FNA overload ignored elementCount and supplied the
whole array length after advancing its pointer by startIndex. Fixing only the
native texture pointer would leave malformed array segments able to overrun
managed storage. The inspected newer upstream overload also retains this length
pattern; this is a deliberately scoped local correction, not a wholesale FNA
update or a claim that upstream already supplies the complete fix.
[Inspected pinned FNA API](https://github.com/FNA-XNA/FNA/blob/76b1aef1fd0fa913ac53726fab9d230291c15327/src/Graphics/GraphicsDevice.cs).

The deterministic patch accepts only build23's exact FNA output. It changes two
GetBackBufferData overload bodies and adds two internal helper methods. It
preserves the other 5,242 methods, all 4,469 fields, assembly identity/references
and embedded resources, including the accepted GetRenderTargetsNoAllocEXT API.
Validation covers disposal, null arrays, reference-containing element types,
actual managed element stride, array offsets/counts, rectangle containment and
integer overflow. It passes the exact required byte count to the native method,
leaves unused array entries untouched, and releases the GC pin in a finally.
The build-time helper and patching tools are not shipped as separate DLLs.

Celeste.dll, Celeste.Mod.mm.dll, CelesteIOS.dll, MonoMod.Utils.dll, all original
mod ZIPs, Mono archives and the JIT script remain byte-identical. The game adapter
only gains bounded graphics diagnostics. This does not patch original game IL
or rewrite a mod to avoid its call to the affected API.

## Evidence and device instrumentation

The standalone real Mono8/Metal test passes **107 checks** with Metal API
validation: 86 API/format/lifetime checks and 21 exact pattern checks across
0×, 2× and 4× MSAA. Coverage includes deferred clears, RGBA/row orientation,
cropped reads, nonzero offsets/guard bytes, byte versus Color strides, repeated
reads, continued partial drawing, an offscreen target remaining bound, resize,
after Present, across autorelease callbacks, and disposed-device rejection.
Nine additional format cases cover BGRA, single/vector floats, half formats,
HDR blendable and 10:10:10:2; these are host results, not phone format acceptance.

Full Celeste runs use the repaired native library, guarded FNA and final game
adapter. Gates cover original SJ lobby/Bing/Frost rendering and audio; normal
title Quit; repeated Quit during queued saves; a second process reading and
advancing sidecar 3→6; full-mod-set normal Quit; and original Paint intro, Lua,
retained texture readback, controls, resume and a second save process. Every
positive session must finish managed shutdown and native detach without errors.
The separate FNA scan resolves all 3,222 references across 49 original helper
assemblies. The unchanged MonoMod literal control remains inherited, explicitly
bound to its unchanged implementation/runtime hashes.

During phone startup, seven automatic pattern checks exercise the actual game
backbuffer and restore graphics state before normal frames. After the first
Present, during a level and after resume, the host reads a small 32×18 region,
logs its dimensions/hash and closes the extra graphics callback. The small
samples demonstrate readable frame lifetime; they do not assert that a whole
scene is visually correct or that a uniform sample is a rendering failure.
There is no every-frame capture or new screenshot UI, and these checks are not
GPU performance measurements. A failed pattern check follows the existing
explicit error path.

Simulator tests cover startup, streaming import, update preservation, diagnostics
history/recovery, generated requests, native portrait/landscape closing UI,
real ZIP picker and persisted selection. They do not execute the phone JIT or
Metal game. Packaging excludes symbols/signatures/profiles/game assets and the
standalone test assemblies. Native services/session tests and exact package/
protocol receipts bind the remaining gates.

## Handoff and roadmap

The kit is a small unsigned app in **iCloud Drive / Celeste JIT Tests /
0.12.1-build-24**. Follow [the phone guide](../../experiments/ios-jit/launcher-backbuffer/PHONE_README.txt):
update LC1 preserving data, fresh inline request through StikDebug in LC2,
regression off, load existing progress, play, background 30 seconds, resume,
Save and Quit, main-menu Quit, wait at SESSION SAVED, export. Repeat in a fresh
process and confirm the newly saved change. Keep both Results exports.
No game or mod reimport, extra download, manual graphics action or new script
format is required. The template is reference only.

Build23 remains the complete-shutdown fallback. Preserve every Results folder
and exact local historical IPA/symbols. Only superseded cloud installers may be
removed after matching their local hashes. Original-IL preparation and FMOD
redistribution remain separate public-release gates. One game per process,
no timer, complete mod sidecars and independent Export remain unchanged.

After physical graphics/save acceptance, the next planned increment is general
mod installation with dependency planning, downloads, progress, actionable errors
and recoverable transactions. Then come responsive game boot, catalogue/profile
backup UI and the full-parity native touch editor. Update
[the roadmap](NATIVE_LAUNCHER_ROADMAP_2026-09-12.md) if new device evidence changes
that order; no broad product features are mixed into this renderer test.

## Final delivery record

The exact IPA SHA256 is
`f7ed94140ee4b181f667a9901b9d769662e196eb51139b7f593c1d2933da6a58`;
executable/dSYM UUID is `919E08E6-E087-31D7-8D83-AE26372D1BFF`.
The private `build-24-ready` snapshot preserves 2,191 new files and 310 matching
inputs inherited from a fully verified 18,157-file build23 tree. Its receipt is
`bf2a73f5e9d2efa9ba31b5e1245f1e1c5256268fc1728aeb717b5aa51f4053b4`.
The simulator build receipt and final delivery records are beside it in handoff.
The handoff-only INSTALL link uses README-FIRST.txt; the source guide correctly
uses PHONE_README.txt. Compiled inputs, IPA and symbols were unchanged.

All eight cloud files were read back by SHA256 and Apple's resource metadata
reports uploaded with no error. The superseded build19 cloud IPA was removed
only after its exact local copy was verified. Build23's cloud IPA, every Results
path, original local installers and their symbols remain. Physical build24
execution is the outstanding acceptance gate. No commit or push was made.
