# Celeste dependency resolution and installation reports (build26)

Version 0.13.1 (26), `launcher-resolution-20260913-26`.
Read [the implementation report](../../../docs/ios-jit/MOD_RESOLUTION_BUILD_26.md)
and [build24 phone acceptance](../../../docs/ios-jit/BUILD_24_GRAPHICS_ACCEPTANCE.md).
This isolated lane clarifies runtime blockers, offers verified earlier dependency
releases, adds durable installation reports and retries unavailable GameBanana
file servers through the same file-ID mirrors used by Everest.

The accepted build24 game IL, native Mono archives, renderer, CelesteIOS and JIT
script remain identical. A scoped CoreLib reflection correction avoids loading
absent integration types merely to query method attributes; it preserves explicit
signature errors. `build_reflection.py` creates isolated host/iOS CoreLib copies
from the accepted packs and verifies all unrelated methods, fields and resources. `build_managed.py`, `native-build.py`, `build_runtime.py` and
`build_mods.py` verify accepted inputs read-only. Use Xcode26.6 and this lane's
`build_reflection.py` then `build.py` for the unsigned device IPA or `build.py --simulator` for native UI.
New outputs use `launcher-resolution*`; never rebuild accepted stages in place.

`RuntimeCompatibleReleases.json` contains metadata and exact SHA256 identities
for two verified earlier releases. It is a generic candidate list, separate from
`CompatibilityDownloads.json` and its three app-managed runtime compatibility
pins. Prefer a compatible current release, retain compatible installed versions,
and never relax a mod's declared minimum version. This is not a full historical
release database or a guarantee of arbitrary mod compatibility.

Reports record applied module identities and old/new versions from committed
transactions. Dependency installs can enable existing mods; explicit updates
preserve disabled choices. Interrupted, cancelled or failed attempts distinguish
verified retained downloads from applied changes. Reopen the last report in Mods;
Export includes bounded current-attempt and transaction details.

Relevant gates under `tests/`:

- `check_installs.py`: native planner, hashes, reports, mirror fallback, automatic
  checks, real HTTPS and process-crash recovery. Use the existing read-only
  `launcher-dependencies-tools/bin/python` environment for PyYAML and xxhash.
- `check_build25_blocking.py`: direct rejection controls against immutable25.
- `check_fresh_resolution.py --install`: original SpringCollab2020 plus the real
  latest index, fetched original ZIPs, earlier releases and installation report.
- `check_real_updates.py`: original EeveeHelper/FrostHelper version transitions.
- `check_mod_library.py`: complete original import/preflight corpus.
- `simulator_smoke.py`, `check_launcher_ui.py`, `check_blocked_ui.py`: actual
  native UI, reports, blocked actions, fresh review and diagnostics.
- `build_reflection_controls.py`: CoreCLR reference contract for absent method
  signature types, method flags, PreserveSig and P/Invoke attribute values.
- `check_host_graphics.py --spring --normal --without-example`: real Mono
  fresh Spring loading, reflection controls, normal play, save and resume.
- `check_host_graphics.py --paint --frost --updated`: real updated helper ZIPs,
  original Paint intro/Lua, retained-texture GPU readback, saves and resume.
  Both host modes use external test DLLs which are never bundled in the IPA.
- `check_package.py`, `check_request_protocol.py`: identity and payload gates.

The small IPA still contains private prepared Celeste IL and linked FMOD. These
remain public distribution gates. Owner-imported Content, original mod ZIPs,
unknown mod saves/settings, one game per process and Export are preserved.
No commits, pushes or AOT-checkout writes are authorized.
