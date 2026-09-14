# Celeste embedded Everest runtime upgrade (build27)

Version0.14.0(27), `launcher-runtime-20260913-27`. This isolated lane rebuilds
Everest1.6531.0 from commit d72e94f4b9e62b91cbdea674587ed39d53de9550, prepares the
original licensed Celeste IL and generates new hooks. Read
[the upgrade report](../../../docs/ios-jit/EVEREST_RUNTIME_BUILD_27.md) and
[accepted26 evidence](../../../docs/ios-jit/BUILD_26_INSTALLS_ACCEPTANCE.md).

RuntimeIdentity.json generates native/managed expectations and the upstream
VersionString patch. Actual game registration verifies that contract. The update
cache uses schema2 and fingerprints built-ins plus app-managed pins/policy.
Old or mismatched results are recomputed from the verified cached index, even
when offline, automatic checks are off or a failed check is in backoff. Index,
ZIP/hash caches and user choices are preserved. Installs still require review.

Keep accepted26/24 source, bytes and outputs immutable. The isolated sequence is
prepare_sources.py → build_dependencies.py → prepare_game.py → build_managed.py.
All source, SDK caches and generated outputs use launcher-runtime* stages.
The read-only build_reflection.py/native-build.py/build_runtime.py/build_mods.py
verify the accepted26 CoreLib, accepted24 renderer and accepted19 Mono/mod inputs.
Use Xcode26.6 and build.py, or build.py --simulator, for packages.

The four replaced managed assemblies are Celeste.dll, Celeste.Mod.mm.dll,
MMHOOK_Celeste.dll and CelesteJITEverest.dll. Retain the accepted FNA graphics fixes,
MonoMod fixes, CelesteIOS ABI1, native runtime/renderer and StikDebug protocol.
The regenerated FNA differs only by the new inert Dust patch marker; its old
methods/fields/resources are audited and the accepted FNA bytes remain shipped.

Validation uses production native transactions with real original helper ZIPs,
fresh Spring resolution/current helpers, cache policy transitions, cancellation
and crash recovery, plus actual simulator UI. External host fixtures execute new
Everest version/Dust/enumeration controls, original Spring Starjump/save/resume,
updated Paint, full SJ/Frost, shutdown and reflection/input checks. These host
fixtures are excluded from the device payload. Local passing gates are never
reported as physical iOS acceptance. Check package-validation.json and the report
for the exact final results and remaining phone steps.

The native catalogue, loading screen, whole-profile backups and touch editor
remain subsequent roadmap steps. RuntimeCompatibleReleases.json stays a generic
verified fallback list; compatible current or installed releases take priority.
Public original-IL preparation and FMOD permission remain separate release gates.
No commits, pushes or AOT-checkout writes are authorized.
