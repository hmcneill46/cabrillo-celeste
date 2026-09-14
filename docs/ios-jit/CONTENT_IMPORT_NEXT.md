# After build 13: a small IPA and persistent game imports

11 September 2026. **Build 13 is now physically accepted**; see
[the acceptance report](EVEREST_EXECUTION_PASS_2026-09-11.md). Implementation is
in `experiments/ios-jit/content-import/`. The owner prefers ordinary store game
ZIPs, and does not need build 13 extraction. The owner's original
`celeste-win-opengl.zip` (itch Windows FNA 1.4.0.0) was verified to contain all
1,216 identical Content files with no extras. It is build 14's intended first
input. Linux's actual archive has not yet been validated here; retain it as an
additional input gate. ZIP selection works without manual extraction.

The original plan follows. The owner wants to import their Celeste files once, then
transfer only small app updates. **Target this for build 14 if build 13 passes
the physical Everest/mod test.** If build 13 exposes a runtime failure, its
correction takes priority; do not mix an unresolved crash with an import/storage
migration merely to keep that build number.

## Measured opportunity

The exact build 13 ZIP central directory reports:

| Component | Files | Uncompressed bytes | Compressed member bytes |
| --- | ---: | ---: | ---: |
| Celeste Content | 1,216 | 1,158,665,183 | 867,038,873 |
| Managed runtime/game/Everest | 201 | 47,468,736 | 19,374,103 |
| Native app and other resources | 52 | 8,751,438 | 3,333,597 |

Total current IPA: 890,087,879 bytes. Without Content, its remaining compressed
members total **22,707,700 bytes**. This supports an approximately **23 MB**
private app target before importer changes and archive overhead; it is not a
newly built/tested IPA size. The measurement is preserved privately in
`artifacts/ios-jit/everest-canary-20260911-13/size-breakdown.json`.

## First implementation: persistent content, small private updates

- Keep the current Everest guest bundle identifier so LC1 can update that
  guest. Preserve its mod imports, profile and complete save sidecars. Verify
  actual update/data retention on the phone; do not assume a new guest or a
  delete/reinstall preserves data.
- Add **Import Celeste files** with a progress/result screen. Start with an
  explicitly verified owned game format/version. The current preparation uses
  the validated Mac/FNA 1.4.0.0 inputs; Linux/Windows ZIP layout/content support
  needs its own input validation before being advertised. Do not ask the owner
  to redownload a different edition speculatively.
- Keep the already downloaded private build 13 IPA for the transition. Its ZIP
  contains the complete validated Content tree, so the first importer can
  support that exact IPA as an additional private content source. Extract only
  its expected Content entries against the trusted manifest. This avoids
  another large download merely to test content import; normal owned-game
  imports remain the product direction. This convenience is planned, not yet
  implemented or physically tested.
- Copy/extract the selected owned input into the guest's persistent Documents
  game library, verify the expected content manifest and required banks, then
  switch the active content root only after completion. Check free space and
  ZIP entry paths/expansion limits; keep partial imports separate and leave a
  previously working library intact on cancellation/failure. Preserve the
  owner's source archive in Files. App-owned staging can be removed once the
  installed library is verified.
- The native launcher may select/stage the archive before JIT. The already
  integrated managed ZIP/compression services can validate/extract it after
  JIT is ready, before constructing the game. A first-use preparation screen
  should explain that ordering; later launches reuse the prepared content.
- Read content from that persistent library instead of the app bundle. Keep
  source-data identity separate from runtime/preparation-version identity:
  replacing an IPA or updating Everest should not require another asset
  download. Do not erase Saves, Settings, module sidecars or imported mods when
  invalidating generated runtime caches.
- For the first private size reduction, the small prepared managed game may
  remain bundled. This saves almost all transfer cost while the existing
  original-IL preparation stays reproducible on the Mac. Such a kit remains
  private and is not yet the intended game-free public launcher.

Acceptance requires an actual owned-file import, the build 13 mod/gameplay/
audio/resume/save checks, a fresh launch without reimport, and an update in the
same LC1 guest that retains content, both mods and the saved counter. Exercise
cancelled/invalid input without losing a working library. Keep native logging
and Export diagnostics available throughout import failures and startup.

## Full owner-file launcher

Move the actual NETCoreifier, Everest game/FNA patching, HookGen and legacy
relink operations into an in-process preparation stage under the device's
custom Mono runtime. The current preparation tool runs these on host CoreCLR;
it has not yet passed as an iOS Mono importer. Keep cache keys for original
assembly identities plus the Everest/runtime/platform-patch tuple, and retain
original owner inputs independently of generated assemblies.

Only after that path works should the public app omit all proprietary original
and patched game assemblies as well as assets. Preserve third-party notices;
FMOD redistribution remains an unresolved separate project requirement.
The first asset-only size reduction does not settle it.

## Strawberry Jam and later updates

Import original SJ and dependency ZIPs into persistent app storage when the
real helper/LuaCutscenes tests are ready. Keep large unchanged packages across
small app updates; obtain only changed archives when a mod set changes. A mod
ZIP may require many helper modules, so downloading SJ alone is not proof of
a complete runnable set. The pinned 52-archive set is over 1 GB; the current
handoff limit still applies to files uploaded for the owner. Direct owner
downloads/imports can avoid bundling those archives into every development IPA.

Order: physical build 13 acceptance → persistent content/small IPA → actual
LuaCutscenes/helper coverage → SJ Beginner lobby/Bing. A small Lua test can
progress independently once the runtime is accepted, but there is no reason
to postpone the transfer-size reduction until full SJ compatibility.
