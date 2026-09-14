# Actual Everest JIT integration canary

Build 13 uses genuine pinned Everest 1.6458.0 and original owned Celeste IL.
The previous `celeste-canary` remains the immutable build 12 baseline. Read
`docs/ios-jit/EVEREST_BUILD_13.md` for evidence, fixes, limits and next gates.

Build in this JIT checkout only, with the private SDK/native stages described
in the root AGENTS.md. Source preparation, dependency build, original-IL
preparation, adapter and mod compilation are separate scripts here. The native
builder uses Xcode 26.6 by per-command DEVELOPER_DIR and rejects delivered kits.

Sequence: `prepare_sources.py`, `build_dependencies.py`, `prepare_game.py`,
`build_lua.py`, `build_managed.py`, `build_mods.py`, host checks, `build.py`
and `build.py --simulator`, simulator/protocol/package checks. Preserve all
receipts and use a new version for a delivered kit correction. There is no
dependency on writable AOT worktrees or modern .NET Apple managed bindings.

The ordinary canary mod has no launcher/native reference. Everest reads and
relinks its ZIP, owns its AssemblyLoadContext, registers its entity, runs both
generated hook kinds and saves its YAML sidecar using normal UserIO. The small
map is originally authored by build_mods.py and refers to installed assets.

Adaptations are recorded separately: embedded paths/lifecycle, static native
imports, accepted touch policy through Everest input nodes, FNA text-input
query, exact generated-assembly resolution, and explicit floating operand
widths for Everest's precision patch. Managed JIT remains mandatory.

The native shell imports only the exact supplied canary ZIPs. A public launcher
still needs owner game-file import, on-device preparation/cache, arbitrary
profile selection/dependency validation, save management and broader testing.
