# Build 12 physical Celeste JIT gameplay pass

11 September 2026. **Accept the real Celeste baseline on the owner's iPhone
15 Pro Max, iOS 26.5 (23F77), in LiveContainer 1 with StikDebug in slot 2.**
The owner reports that everything passed. The exported diagnostics independently
verify the exact delivered build, real gameplay, touch input, the jump hook,
FMOD, XML saves, background/resume and clean shutdown. Everest and Strawberry
Jam have not run in this app yet.

| Check | Captured physical result |
| --- | --- |
| Build, imported game DLL, script and source snapshot | Match Celeste JIT Game 0.5.0 (12); 114 build inputs and 925 game inputs verified |
| Native executable-memory checks | 26 passed |
| Managed JIT | 9,579 completions; all reported code ranges owned |
| Game | Title, Prologue rooms 0–3, transition into Forsaken City rooms 1, 2, 3, 4 and 3b |
| Frames/input | 8,382 frame callbacks; 6,455 level frames; 3,296 movement observations; 158 touch presses and releases |
| Real Player.Jump hook | 58 calls, including 22 after resume; retained across resume/GC, removed at stop |
| Background/resume | 34.829 seconds; same process, 2,488 subsequent level frames |
| Audio | FMOD 1.10.09 initialized; six named bank loads; speaker session restored and mixer resumed |
| Saves | Settings XML written/read back twice; slot 0 SaveData XML written/read back, 14,794 bytes |
| Cleanup | All seven tracked workers completed; game/hook stopped; bootstrap worker and main managed threads cleared/detached |
| Result | All nine game/graphics assertions; PASS UI, delayed foreground liveness, export 16.583 seconds after PASS |
| Runtime failures | Zero JIT failures, unowned JIT results, managed errors or rejected patches |
| Code reservation | 9,961,472 / 33,554,432 bytes; 83 allocations and seven executable patches |
| Peak sampled memory | Physical footprint 1,209,288,368 bytes; resident memory 704,167,936 bytes |

The owner used the ordinary game menu rather than the special Prologue button.
Room/scene events show progression through Prologue and into Forsaken City.
That is a valid test path: the required gameplay, resumed jump, save/readback,
Finish and foreground dwell assertions all passed. No procedure correction or
repeat baseline test is needed.

The six logged bank names are `Master Bank`, `music`, `sfx`, `ui`, `dlc_music`
and `dlc_sfx`. Instrumentation proves initialization and lifecycle operations;
the owner's report supplies the visual/audio confirmation. The device runtime
reports `0x00011009`, or **1.10.09**, consistent with the linked iOS SDK. See the
[build report's version correction](CELESTE_BASELINE_BUILD_12.md) for the
different host/header version; do not change frozen build inputs to edit a label.

Code used about **9.50 MiB of 32 MiB**. That is encouraging for the next stage,
but does not establish Everest/SJ capacity. Physical footprint peaked around
**1.13 GiB**; this is neither managed heap size nor a steady-state benchmark.
The largest recorded foreground frame gap was 0.1323 seconds, including loading;
do not turn this session into a smooth-60-fps or AOT/JIT performance claim.

Fresh-process save reload, controller play, later vanilla chapters, full mod
save sidecars, thermal behavior, older devices and long sessions remain
untested here. The optional second-launch save test was not performed.
Container/debugger version strings in the export are carried-forward user
preferences, not newly queried installation metadata.

The untouched iCloud export is preserved privately at
`.build/ios-jit/device-evidence/2026-09-11/build-12-pass/`, alongside its
retrieval receipt, reproducible validator, current event stream, console tail
and validation result. It contains **19,383 current events**, no previous
sessions and no storage error. The exported native console is a 128 KiB tail,
not a separately collected full console. No debugger attachment was necessary.

Raw export: 10,239,196 bytes, SHA256
`d50e2a6c5cf951e9667c27f89802f4ed8f7124c6576d987e2f0586ac52b66c0f`.
IPA SHA256:
`6b72dfb799bceeb31a9978e5d948ba37aa902c87c831fbad13591cbcfe578d76`.
Imported DLL SHA256:
`6fcb34e8a9799d6b94e4caba8b37dc6aaae50da6863c03c35dd851427c47ad5b`.
[Machine-readable acceptance](CELESTE_EXECUTION_PASS_2026-09-11_EVIDENCE.json).

**Next: real Everest integration, then Strawberry Jam.** Read the
[implementation sequence and test contract](EVEREST_INTEGRATION_NEXT.md).
Preserve the accepted build 12 source, kit, symbols, receipts and snapshots.
New work belongs in a separate versioned JIT stage; the active AOT checkout
remains untouched. No commits, pushes or external publication were made.
