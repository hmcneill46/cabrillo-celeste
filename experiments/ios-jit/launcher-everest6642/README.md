# Build55 runtime identity overlay

This overlay selects Everest stable1.6642.0 at
`5abd7876821223c20711c1844a5187321d6e904c` for Cabrillo0.25.0/build55.
The native and managed expectations are generated from the same JSON using the
frozen build50 generator. Celeste1.4.0.0, CelesteIOS1.0.0 and compatibility
policy1 stay unchanged. The build55 recipe must select both generated files and
bundle this RuntimeIdentity.json alongside the rebuilt Everest payload.

The owned-game recipe hashes its preparation components, including
Celeste.Mod.mm.dll. Updating Everest therefore creates a new prepared-game
generation automatically. Verified original game files remain reusable, and old
published generations are retained. No cache schema change or deletion is needed;
the first launch prepares the new generation and later launches reuse it.

Build54's copy-based Files imports, signing compatibility, JIT gates, signed49
Shortcuts and other runtime/native pins remain separate retained inputs. This
identity overlay alone is not a completed build or a gameplay/device test.
