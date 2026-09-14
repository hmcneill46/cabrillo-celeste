# Native Celeste dependency installs and updates (build25)

Version 0.13.0 (25), `launcher-dependencies-20260912-25`.
This lane adds native dependency transactions, manual/occasional automatic update
checks, individual/batch update review, progress/cancellation and recovery. It
reuses the accepted build24 game IL, Mono, renderer, support module and JIT script.
Start with [the implementation report](../../../docs/ios-jit/MOD_INSTALLS_BUILD_25.md)
and [build24 phone acceptance](../../../docs/ios-jit/BUILD_24_GRAPHICS_ACCEPTANCE.md).

`build.py` produces the private unsigned device IPA; `--simulator` builds the UI.
Use Xcode26.6. `build_managed.py`, `native-build.py`, `build_runtime.py` and
`build_mods.py` are **read-only verifiers**. Never rebuild accepted stages in
place. Native Swift/C dependencies build into `launcher-dependencies-native*`.
The copied managed/support/renderer patch sources document the inherited lane;
they are not recompiled by this build. New native code is under `native/`.

The unchanged private prepared Celeste IL and linked FMOD remain release gates;
owner content is imported persistently. No AOT checkout mutation, public
redistribution, commit or push is authorized.

Useful checks:

- `tests/check_installs.py` with the isolated launcher-dependencies-tools Python:
  production planner/hash/index, coordinator, automatic-check policy, real HTTPS,
  process interruption/rollback, tampered-file preservation.
- `tests/check_mod_library.py`: original ZIP/parser/preflight corpus.
- `tests/check_real_updates.py`: real community updates on an isolated profile.
- `tests/check_host_graphics.py --paint --updated --profile UpdatedPaint`:
  actual Mono/Metal gameplay with that updated selection; host evidence only.
- `tests/simulator_smoke.py` and `tests/check_launcher_ui.py --device <UDID>`:
  actual SwiftUI, picker, alerts, review/cancellation/journal and export.
- `tests/check_package.py` and `tests/check_request_protocol.py`: final IPA gates.

Online metadata remains provisional until actual downloaded ZIPs are verified.
App runtime/support and pinned compatibility versions cannot be replaced. Old
archives stay disabled for recovery; unknown mod save/settings files are not
parsed or altered by installation. One game per process and Export are retained.
