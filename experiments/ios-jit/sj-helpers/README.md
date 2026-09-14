# LuaCutscenes and MaxHelpingHand integration

Build 15 starts from accepted build 14 in an independent source/staging lane.
The small IPA retains the same guest bundle, content library and complete
Everest profile. The original LuaCutscenes 0.2.13 and MaxHelpingHand 1.40.9 ZIPs
run through Everest's normal dependency, relinking and module context pipeline.
An authored room measures Lua-driven walking, a retained Lua coroutine across
resume and a real moving platform carrying the player. Original On/IL and
XML/YAML save checks remain required.

GravityHelper 1.2.28 was investigated but deferred: its optional CelesteNet
support type fails while Mono compiles GravityHelperModule.Load. Preserve the
private reproduction at `.build/ios-jit/sj-helper-gravity-investigation/`.
Do not mistake this two-helper test for full Strawberry Jam compatibility.

Build in order: `fetch_helpers.py`, `build_runtime.py`, `build_managed.py`,
`build_mods.py`, then `build.py` (or `build.py --simulator`). All staging uses
`.build/ios-jit/sj-*`; deliverables use `artifacts/ios-jit/sj-helpers-20260911-15`.
Use Xcode 26.6. Do not mutate the accepted runtime or earlier sources/outputs.

Two runtime compatibility changes are isolated here: honor an existing
IgnoresAccessChecksTo assembly grant for protected members; remove MonoMod's
obsolete native MonoAssembly byte write. The first recompiles one metadata
object into copied host/iOS archives and verifies the other 259 members match.
The second patches only a copied MonoMod.Utils assembly. Type discovery also
filters failed optional-base types before Everest's Lua cache examines them.
The original game/FNA/other managed dependencies remain unchanged.

Verification includes original-runtime controls and absent/wrong-assembly
negative tests for the visibility grant, real pinned-Mono gameplay, native
package/import closure, same-bundle simulator update/export and actual compiled
request/template regression. Keep all evidence, external symbols and a frozen
source/input snapshot before delivery. A delivered build ID is immutable.

See [INSTALL.md](INSTALL.md) and [the build report](../../../docs/ios-jit/SJ_HELPERS_BUILD_15.md).
The device code budget is 128 MiB (two 64 MiB arenas), increased after the
focused host run allocated about 52 MB of native code. The existing content importer and
Export diagnostics remain available. This private app still contains prepared
game IL and linked iOS FMOD; public owner-IL preparation is a separate gate.
