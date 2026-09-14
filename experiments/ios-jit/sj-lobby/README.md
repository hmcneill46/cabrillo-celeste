# Build 19: original Strawberry Jam first play

This isolated lane loads all 52 nodes of the pinned Strawberry Jam 1.0.12
release graph, then runs the actual Beginner lobby and Bing. The native
launcher downloads or imports original ZIPs into `Profiles/sj-first-play/Mods`
and reuses `GameLibrary/v1`. Its own 3.6 KB hook/save diagnostic mod is bundled.
Accepted build 18 and earlier helper profiles remain unchanged.

Build stages use `.build/ios-jit/sj-lobby*`. In order, run `fetch_sj.py`,
`build_mods.py`, `build_managed.py`, `build_runtime.py`, then `build.py` using
Xcode 26.6. `build.py --simulator` builds only the native launcher test. Source,
private original inputs, runtime archives, logs and artifact hashes are frozen
before delivery; no commits or public uploads are authorized.

The new runtime replaces four members of a copied accepted Mono archive. It
uses a 16 KiB ordinary code-chunk floor (clamped to page/granule, preserving
large requests and ARM64 binding room), and defers `beforefieldinit` only in
the pinned FemtoHelper image until actual static field access. It preserves
original Femto IL/readonly fields; explicit cctors and unrelated assemblies
retain their previous behavior. The native code budget is 512 MiB in two
256 MiB arenas. Every page is verified. VM diagnostics retain a hash of all
rows plus first/last samples, bounding export memory.

CollabUtils2's optional CelesteNet delegate-cache field is moved into its
existing optional type in a separate hash-keyed compatibility cache. Its
original ZIP, optional implementation and upstream relink cache are preserved.
The earlier GravityHelper optional integration adjustment is retained.
Actual CelesteNet networking is not tested.

Tests cover the full real-Mono game through lobby/Bing/music, hooks, save,
suspend/resume and shutdown; exact cctor/optional-cache controls; actual code
allocation/capacity; full VM inspection; atomic import/download/cancel; and
native launcher/protocol/package integrity. Host tests do not establish
physical iOS acceptance, all maps, or normal lobby-door progression.

See [the phone guide](PHONE_README.txt) and
[the report](../../../docs/ios-jit/STRAWBERRY_JAM_BUILD_19.md).
