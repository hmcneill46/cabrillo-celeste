# Metal backbuffer increment — build 24

This isolated lane repairs FNA3D Metal's retained backbuffer descriptor and
read ordering, preserves MSAA samples across interrupted passes, and adds array
segment/rectangle/pin-lifetime validation to the specific FNA readback API.
Original game IL, mod ZIPs, Mono, JIT protocol and build23 support/session code
remain intact. New automatic readback checks provide physical-device evidence.

Read [the report](../../../docs/ios-jit/METAL_BACKBUFFER_BUILD_24.md),
[the roadmap](../../../docs/ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md),
[AGENTS.md](../../../AGENTS.md), and [phone instructions](PHONE_README.txt).

Use Xcode26.6 via DEVELOPER_DIR. `native-build.py` copies the pinned baseline to
`.build/ios-jit/launcher-backbuffer-renderer`, applies the unchanged callback
adaptation and the separate backbuffer patch, and builds host/iOS. Never rebuild
`graphics-native-build11` or a delivered lane in place. `build_managed.py` retains
the accepted MonoMod correction/FNA extension and adds the narrowly checked FNA
backbuffer patch. It preserves all unrelated methods, fields, references and
resources. Module CelesteIOS 1.0.0 / ABI1 remains required and unoverrideable.

`tests/check_backbuffer.py` runs actual Mono8/Metal with validation, including
an `--original` native failure control. The standalone test DLL stays outside the
IPA. Actual Celeste host tests cover full original SJ/Frost, original Paint,
normal Quit/queued saves and new-process reload. Native parser/services/session,
simulator/UI/package and generated JIT-request checks complete the handoff gates.

The canary draws a known pattern once during content load and restores graphics
state before ordinary game frames. It checks pixels, RGBA order, rectangles,
offset guards and continued drawing. Small real-frame reads occur after the
first Present, in a level, and on resume, then close the extra graphics callback.
No every-frame screenshot collection, image export UI or benchmark is added.

Freeze exact inputs, symbols, test evidence and IPA before the versioned iCloud
handoff. Keep23 as fallback and all Results. One game per process, fresh JIT,
complete mod sidecars and independent diagnostics Export remain required.
AOT checkout/private originals are read-only. No commits or remote writes.
