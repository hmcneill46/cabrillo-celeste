# Native iOS JIT probe

Build and package a small unsigned native app for the owner's iPhone 15 Pro Max
on iOS 26.5. The app runs in LiveContainer 1 and asks an already-running
StikDebug in LiveContainer 2 to prepare two executable regions. Start with
[INSTALL.md](INSTALL.md) for the actual device procedure and
[the stage report](../../../docs/ios-jit/NATIVE_PROBE.md) for architecture and
limits. The broader [feasibility audit](../../../docs/ios-jit/FEASIBILITY_AUDIT.md)
still controls the runtime/hook roadmap.

This source is independent of all AOT projects, game assets and build outputs.
There is no managed runtime or game in this app.

```sh
python3 experiments/ios-jit/native-probe/build.py
```

The builder explicitly selects `/Applications/Xcode-26.6.app`, without changing
global `xcode-select`. It compiles an ARM64 Mach-O, verifies the absence of
`LC_CODE_SIGNATURE`, and packages `Payload/CelesteJITProbe.app` as an unsigned
IPA. It keeps the dSYM outside the app and rejects embedded debug symbols.
It also emits source/build/script hashes and a receipt. Staging is under
`.build/ios-jit/native-probe/`; deliveries under `artifacts/ios-jit/`.

For native UI/log checks only:

```sh
python3 experiments/ios-jit/native-probe/build.py --simulator
```

The simulator app is ad hoc signed for simulator installation. It disables
generated-code execution and JIT requests. Launch argument
`--probe-ui-test-export` exercises the real diagnostic serializer without
opening a share sheet. Neither simulator signing nor a simulator result is
part of the physical IPA/JIT proof.

Run the debugger state-machine tests with a local Node runtime:

```sh
node experiments/ios-jit/native-probe/tests/script.test.cjs
python3 experiments/ios-jit/native-probe/tests/check_arm64.py
python3 experiments/ios-jit/native-probe/tests/check_vm_range.py
```

The first test uses an isolated fake debugserver to check happy/failure paths.
The second assembles/disassembles the exact instruction encodings emitted by
the native tests. Neither executes them on a device. The build uses warnings
as errors; suppressed deprecation diagnostics concern Apple's still-available
cache/VM/legacy system interfaces, not ignored compilation failures.

The VM-range regression uses the same C walker and Darwin adapter as the app,
with ASan/UBSan. It covers the first phone report's 16 KiB-fragment/64 KiB-range
case, holes, mixed/RWX permissions, overflow and a real fragmented macOS map.
See [the first device result](../../../docs/ios-jit/DEVICE_TEST_2026-09-11.md).

After receiving an export:

```sh
python3 experiments/ios-jit/native-probe/scripts/summarize_diagnostics.py /path/to/CelesteJIT-session.diagnostics.json
```

All results must distinguish host, simulator and physical evidence. A green
native-memory result remains scoped to this bounded test; it is not a G1/G2
managed-JIT/hook result.

The [build 2 phone result](../../../docs/ios-jit/NATIVE_EXECUTION_PASS_2026-09-11.md)
records three native execution passes in the intended LiveContainer setup.
Build 3 changes packaging only. Check the real old/new archives with:

```sh
python3 experiments/ios-jit/native-probe/tests/check_package.py --previous-ipa artifacts/ios-jit/native-probe-20260911-02/CelesteJITProbe-unsigned.ipa --ipa artifacts/ios-jit/native-probe-20260911-03/CelesteJITProbe-unsigned.ipa
```
