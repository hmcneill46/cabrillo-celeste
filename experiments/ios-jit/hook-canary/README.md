# G2 — real MonoMod hook and resume canary

Build `hook-canary-20260911-09`, version **0.3.2 (9)**, is the next physical test
after the [accepted G1 result](../../../docs/ios-jit/MANAGED_EXECUTION_PASS_2026-09-11.md).
Read [INSTALL.md](INSTALL.md) for the phone procedure and
[the stage report](../../../docs/ios-jit/HOOK_CANARY.md) for findings and limits.
Physical G2 remains pending until the phone's exact-build logs are reviewed.

Build 8's protocol fix worked physically: eight G1 stages and 21 real hook
assertions passed. It then exhausted the 8 MiB code budget. Read
[the crash analysis and build 9 retest](../../../docs/ios-jit/BUILD_8_CAPACITY_AND_BUILD_9.md).
Build 9 gives hooks two 16 MiB arenas using its own matching script; the G1
protocol/source/runtime stay unchanged. `CJHookMemory.h` defines the hook
budget, and `CJHookProtocol.h` supplies the compiled descriptor. The builder
validates compiler dependencies and actual Mach-O constants.

## Components and boundaries

- `monomod/AppleJitSystem.cs` supplies the explicit `ISystem` backend inside
  pinned MonoMod.Core; standard Hook, ILHook, detour factory and ARM64 emitter
  are retained. `patch-monomod.py` applies the narrow hosting/version fixes to
  an isolated clone; `monomod-hosting.patch` records existing-file changes.
- `src/CJHookNative.c` accepts writes only to known Mono method extents or
  explicitly owned hook allocations. Executable patches on device must use
  distinct prepared RX/RW mappings with exact protections, ARM64 alignment,
  original-byte backup, cache flushing and readback. Host tests compile a
  separate macOS x64 branch; it is excluded from the device build.
- `src/CJHookCodeArena.c` compiles the accepted allocator with a callback
  that records and aborts on failed allocation before Mono can use NULL. The
  process cannot recover in place; the existing export retrieves its last run.
- `src/CJHookManaged.m` boots the existing pinned Mono once, runs the original
  eight G1 fixtures, then the hook fixture. It retains the domain for a second
  invocation on another native worker after backgrounding. Both workers use
  the proven balanced invocation / unbalanced detach GC transitions.
- `fixtures/HookCanary.cs` uses actual MonoMod APIs. It imports alongside the
  unchanged G1 `Canary.cs` in the external `HookCanary-v0.3.0.dll`.
- `src/main.m` is the bounded native launcher fork: the existing JIT request,
  import, native checks and Export remain; a second button runs the resume
  phase only after the initial pass and a recorded 20-second background.
  It never reinitializes or overwrites the active code arenas on resume.

The original G1 source and kits remain unchanged. Only JIT experiment staging
and this checkout are writable; the independent AOT checkout is not a build
output or dependency cache.

## Reproduce with the pinned local inputs

The existing managed-canary runtime builders supply
`.build/ios-jit/managed-runtime/`: custom iOS and cooperative macOS Mono 8.0.28,
the matching **separate** official framework packs, and SDK 8.0.422. The iOS
runtime patch/archive is unchanged from physically accepted build 6.

Dependency inputs under `.build/ios-jit/hook-runtime/` are recorded in
`dependencies-pin.json`: a complete MonoMod clone at the exact commit, its
exact Iced submodule, and official `dotnet-sdk-9.0.300-osx-x64.tar.gz` extracted
to `dotnet-sdk-9.0.300`. Verify that archive's pinned SHA-512 before extraction.
SDK 9 is a build tool; no SDK 9 runtime is put in the IPA. NuGet/CLI caches are
also under this private directory. The build receipt records restored package
SHA-512 values and all ten output DLL SHA-256 values.

Run from the repository root:

```sh
python3 experiments/ios-jit/hook-canary/patch-monomod.py
python3 experiments/ios-jit/hook-canary/dependencies-build.py
python3 experiments/ios-jit/hook-canary/tests/check_alias_patches.py
python3 experiments/ios-jit/hook-canary/tests/check_capacity.py
python3 experiments/ios-jit/hook-canary/build.py
python3 experiments/ios-jit/hook-canary/fixture-build.py
python3 experiments/ios-jit/hook-canary/tests/check_mono_hooks.py --fixture artifacts/ios-jit/hook-canary-20260911-09/HookCanary-v0.3.0.dll
python3 experiments/ios-jit/hook-canary/tests/check_package.py
```

The delivered fixture is deliberately compiled **after** packaging the IPA.
For pre-package debugging use `fixture-build.py --development`, then
`tests/check_mono_hooks.py`. The actual host regression embeds the pinned Mono
runtime; it is not a CoreCLR console test. It checks 42 assertions plus two
completion markers, 108 code patches in the observed run, all eight G1 stages,
and two clean worker detachments. JIT counts are evidence, not golden constants.

The alias regression compiles the actual **device** patch branch against real
host RX/RW mappings under ASan/UBSan. Its Mono metadata queries are narrow mocks;
it does not execute ARM64 instructions. It verifies both successful writes and
rejection of out-of-method, unaligned, unowned and wrongly protected ranges.

`build.py --simulator` produces a separate UI-only app. With an explicitly
booted simulator, run `tests/simulator_smoke.py --device <simulator-UUID>` to
check DLL import, disabled execution buttons without JIT, persistent logging,
export and previous-session console recovery. The simulator cannot complete G2. It also exports a request using the exact
native builder and script-binding functions used by the device launcher, with
a local test mailbox and an explicit 16 KiB fixture page size. No JIT request
is sent. After the simulator smoke test, run:

```sh
python3 experiments/ios-jit/hook-canary/tests/check_request_protocol.py
```

This compares the native request with the final IPA's compiled constants and
runs its packaged script against a fake debugserver through all 2,048 page
acknowledgments and detach. It recompiles build 7's preserved source using its
recorded include flags and reproduces the old 64 KiB request rejection. The
16 failure cases also run against the new hook script in
`hook-canary/tests/script.test.cjs`; the original G1 suite remains unchanged.
Static build metadata alone is not protocol compatibility proof.

The device output is `artifacts/ios-jit/hook-canary-20260911-09/`, including the
unsigned IPA and external dSYM. Package validation rejects bundled symbols,
signatures, unexpected assemblies and an embedded test fixture. Preserve older
versioned outputs. Use a new build number after delivering a kit to the owner.

`tests/check_capacity.py` replays the 66 physical build-8 reservation requests
through the actual C allocator with a 16 KiB page size and ASan/UBSan. The old
budget fails at the recorded 66th request. Three complete traces fit the new
budget (25,362,432 of 33,554,432 bytes). A child process checks the terminal
exhaustion diagnostic. This is allocator replay, not full ARM64 fixture proof.

## Limits to carry into the game host

Generic method/source-type hooks are rejected by the pinned public Hook API;
generic IL execution remains supported by the runtime canary. Hook disposal
does not promise arbitrary mod unload. The fixture serializes hook mutations;
concurrent calls occur only while the installed hook is stable. This does not
validate installing a multi-instruction patch while unrelated threads execute
its target. The upstream ARM64 detour is 16 bytes; a target with less than that
much owned method code is rejected instead of writing into a neighboring method.

The code budget is 32 MiB, process lifetime, with no growth/restart. The
backend's bounded hook allocation ledger is not a final game allocator. Native
CoreCLR exception helpers are absent; this is the pinned Mono path. Broader
native interop, culture support, full game/graphics/audio lifecycle, real
Everest packaging/relinking and mod compatibility remain later gates.
