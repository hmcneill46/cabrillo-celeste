# Imported-DLL Mono JIT canary

Build 5 physically passed all eight managed stages, then aborted during the
native worker's Mono detach. Build 6 fixes that GC-state transition, protects
managed references during invocation, and logs launcher return and survival.
See [INSTALL.md](INSTALL.md) for the physical test and
[the stage report](../../../docs/ios-jit/MANAGED_CANARY.md) for evidence and limits.
The game and real hooks are later gates.

## Isolated build

All dependencies live under `.build/ios-jit/managed-runtime/`. The immutable
source/package/SDK tuple is in [runtime-pin.json](runtime-pin.json):

1. Clone `https://github.com/dotnet/runtime.git` at tag `v8.0.28` into
   `runtime-v8.0.28`; require commit `46295af5828b062bbbf93a9cef50fd8cb9fbcb09`.
2. Download the official NuGet package
   `https://api.nuget.org/v3-flatcontainer/microsoft.netcore.app.runtime.mono.ios-arm64/8.0.28/microsoft.netcore.app.runtime.mono.ios-arm64.8.0.28.nupkg`,
   verify its pinned SHA-512, and extract into `pack-ios-8.0.28`.
3. Download the official osx-x64 SDK archive URL in the pin, verify SHA-512 and
   extract into `dotnet-sdk-8.0.422`. No global SDK/workload changes are needed.
4. Run from this checkout, sequentially:

   ```sh
   python3 experiments/ios-jit/managed-canary/patch-runtime.py
   python3 experiments/ios-jit/managed-canary/runtime-build.py
   python3 experiments/ios-jit/managed-canary/build.py
   python3 experiments/ios-jit/managed-canary/fixture-build.py
   python3 experiments/ios-jit/managed-canary/tests/check_package.py
   ```

The runtime builder uses CMake/Make and Xcode 26.6 directly. It checks the pinned
source and patch hashes. The app builder checks JIT allocator symbols and the
AOT/interpreter-disabled configuration, links custom static Mono components,
copies the matching framework IL, emits an unsigned IPA and an external dSYM,
and records input hashes. Never substitute the pack's stock AOT Mono archive.

`fixture-build.py` compiles the IL DLL **after** IPA packaging and verifies it is
absent from the app. It runs 40 fixture logic checks on host CoreCLR and confirms
the ordinary switch test contains an actual IL switch instruction; these do
not prove iOS Mono execution. The owner imports this same external DLL.

## Checks and diagnostics

- `tests/check_arena.py`: actual patched ARM64 emit/patch macros against a
  read-only host RX view, PC-relative branches, alias bounds, concurrent
  reservations and exhaustion under ASan/UBSan. No ARM64 instructions execute
  on the Intel host.
- `tests/script.test.cjs`: 16 fake-debugserver checks, including every page in
  two 4 MiB allocations and a failure on the 500th write. Run with Node.
- `tests/check_switch_tables.py`: extract and compile both actual runtime
  switch-table cases. Four unpatched negative controls fault on read-only RX;
  patched static/dynamic cases preserve offsets and RX targets under ASan/UBSan.
- `tests/check_native_resolver.py`: the actual library-name resolver against
  matching host System.Native exports, including the three physical failures.
- `tests/build_host_runtime.py` and `tests/check_mono_lifecycle.py`: use the same
  pinned Mono on macOS with cooperative GC to reproduce the detach abort and
  exercise the shared correction, thread reattachment and native worker reuse.
  The host builder fetches verified matching macOS framework IL using
  `tests/host-runtime-pin.json`. Keep the host pack separate from iOS inputs;
  architecture-specific Mono framework packs are not interchangeable.
- `build.py --simulator` plus `tests/simulator_smoke.py --device <booted-UDID>`:
  native launcher, actual import handler, disabled run before JIT, export and
  previous-session/native-console recovery and 800 background log events with
  timer-driven rendering. No runtime is linked into this UI
  test build. Native generated-code paths remain disabled.
- `tests/check_package.py`: archive, missing signature/dSYM, source/runtime/BCL
  hashes, notices and external fixture identity.

Every runtime stage and JIT begin/done event is persisted. An accepted device
result needs matching build/DLL/script identities, verified detach and RX/RW
geometry, actual `MonoJitInfo` code ranges, profiler evidence for the imported
method and both emitted dynamic methods, all eight expected results and a clean
worker detach/launcher return. A label,
`RuntimeFeature` boolean or host pass alone is insufficient.

This is deliberately one-shot: an 8 MiB code budget, process-lifetime arenas,
invariant globalization, no unloading or late arena growth. A new profile/test
attempt requires a fresh app process. Keep the native G0 probe and AOT projects
unchanged; never share their build caches or modify the active AOT checkout.
