# Private Celeste JIT baseline — 0.5.0 (12)

Use [the phone checklist](PHONE_README.txt), shipped as `README-FIRST.txt`.
Target: iPhone 15 Pro Max / iOS 26.5; LiveContainer 1 hosts the game and
LiveContainer 2 hosts StikDebug. Install `CelesteJITGame-unsigned.ipa`, import
`CelesteJITGame-v0.5.0.dll`, use the launcher's fresh JIT route, then Run Celeste.
Keep LiveContainer Launch with JIT off and its launch-script field empty.

The private IPA bundles all 1,216 validated content files from the supplied game.
The separately imported game DLL is derived locally from the canonical Celeste
1.4.0.0 source, built as untrimmed net8 IL. Both are proprietary test inputs,
not the future public launcher payload. The new guest bundle is
`io.github.hmcneill46.celeste.everest.jit.game`; the accepted graphics guest is
preserved. Saves and backups live in this guest's
`Documents/Profiles/vanilla-jit-canary/` and never touch AOT saves.

Required physical check: title graphics/music, at least 20 seconds playing
Prologue with movement and jumping, Home for 30 seconds, same-process return,
move and jump again for at least 10 seconds, Finish, wait 10 seconds, then export.
Use `iCloud Drive/Celeste JIT Tests/0.5.0-build-12/Results`. On crash, recover/export
before another JIT request. A visible/audio result report is required alongside
logs. The optional second launch checks persistence through a fresh process.

This is a game baseline, not an Everest release. A real runtime detour counts
normal `Player.Jump` calls without changing their behavior. Touch ownership,
direction/hysteresis, safe-area layout, toggle grab and attributed icons are
reused from the iOS port, adapted without Apple managed bindings. Full layout
editing, the product save manager, file imports and mod ZIP support remain ahead.
The XML serializer is the normal JIT-capable .NET path; vanilla AOT serializers
and their restricted save schema are not imported.

The native host pauses the game before inactivity, suspends FMOD, restores the
audio session before resuming, and clears touch ownership. Interruptions,
route changes, unusual loader suspension and controller hotplug need broader
acceptance later. First-run JIT stalls and memory behavior are diagnostic targets,
not performance benchmarks. One game lifetime per process; no hot reload/restart.
The same 32 MiB prepared code budget and physical build 9 script are retained.
General chapter/mod capacity remains unproven.

Build with Xcode 26.6 through the scripts in this directory. Symbols, build
receipts, full input hashes, runtime logs and owner content remain in ignored
local output. The IPA is unsigned and contains no dSYM or provisioning profile.
