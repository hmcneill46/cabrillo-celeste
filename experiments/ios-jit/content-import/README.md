# Persistent content / small IPA experiment

Build 14 isolates the content importer from the physically accepted build 13
source. The same guest bundle and `Documents/Profiles/everest-jit-canary` keep
mods and complete save sidecars. Native Foundation stages a picked ZIP before
JIT; a separately attached Mono worker streams, hashes and installs its Content
before constructing Celeste. UIKit polls progress and supports cancellation.

Content lives under `Documents/GameLibrary/v1/<content identity>/<generation>/Content`.
An atomic active pointer selects only a fully verified generation. Each fresh
launch verifies stored bytes. Failure/cancellation preserves installed data;
own marked unfinished generations are recovered on the next attempt. Original
Files sources remain untouched. App updates do not change the content identity.
Only the small trusted hash catalog is bundled; no Content files are packaged.

`build_managed.py` copies verified build 13 prepared dependencies into isolated
`.build/ios-jit/content-managed` and recompiles only the new adapter. `build.py`
uses Xcode 26.6 and generates an unsigned device IPA plus external dSYM. It
refuses to rebuild a delivered kit. Do not edit the AOT checkout or regenerate
accepted build 13 patches/dependencies in place.

Checks: ContentStore unit/negative/interruption tests, actual pinned-Mono
cold import and fresh cached gameplay, native staging/cancel and simulator
update/export, exact package/native imports, actual request/script protocol.
Host/simulator evidence is separate from physical iOS acceptance.

See [INSTALL.md](INSTALL.md) and [the import plan](../../../docs/ios-jit/CONTENT_IMPORT_NEXT.md).
Full on-device original IL preparation and arbitrary mods/SJ remain later work.
