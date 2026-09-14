# After build 12: real Everest, then Strawberry Jam

**Implementation update:** [build 13 physically passes real Everest map/code
ZIPs](EVEREST_EXECUTION_PASS_2026-09-11.md), and [build 14 physically passes
original-game content import with the small IPA](CONTENT_IMPORT_PASS_2026-09-11.md).
The next development stage is actual LuaCutscenes script/coroutine and SJ helper
coverage, then Beginner lobby/Bing; include fresh cached-content/save retention
in the next same-guest phone update. The planning snapshot below predates both
implementations; its statements about missing Everest/runtime work are historical.

11 September 2026. The [physical game baseline passes](CELESTE_EXECUTION_PASS_2026-09-11.md).
We are ready to begin the real Everest/SJ integration. The current app has no
Everest loader, so importing Strawberry Jam into build 12 cannot work.
This document records the next implementation and acceptance sequence; no
Everest build or new physical test kit is claimed by this planning update.

## Next implementation

Create an independent `experiments/ios-jit/everest-canary/` stage with private
`.build/ios-jit/everest-*` staging and a new versioned artifact folder. Keep the
accepted build 12 source and renderer/runtime inputs reproducible. Reuse its
native lifecycle, controls, logging and platform services deliberately; keep
the managed game, Everest and mod DLLs in the custom Mono 8 JIT runtime.

Start with **Everest 1.6458.0**, commit
`4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00`, already pinned by this project's
audit. This is a reproducibility choice, not a claim that it is the latest
release. Its pinned MonoMod commit, `dfc30a1506d37fb88a2c2be004f525205f46a24c`,
matches the source underlying the working iOS hook backend. Preserve that
backend when assembling the actual Everest dependency set.

1. **Prepare real patched game IL.** Use an isolated copy of the validated
   owner-original Celeste input. Run the conversion, Everest game/FNA patches,
   HookGen generation and legacy hook relinking, recording original/patch/output
   hashes. Apply the iOS lifetime/input/audio integration explicitly. Build 12's
   reconstructed game is useful reference, but is not the final import format.
   Upstream's [MiniInstaller](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/MiniInstaller/Program.cs)
   performs these preparation steps and explicitly rejects running under Mono.
   First run a controlled preparation tool on the Mac's private CoreCLR SDK;
   port the preparation operations into an in-process mobile importer later.
   Do not run the unmodified desktop installer against owner originals.
2. **Boot genuine Everest through the retained game lifetime.** Preserve its
   module registration, content mount, relinker, dependency resolution and
   generated `On.*`/`IL.*` surface. Adapt desktop startup, splash subprocesses,
   updater/relaunch and Discord integration to the existing iOS launcher.
   Patch ordering must preserve both Everest's FNA changes and the accepted
   UIKit/Metal callback contract. A desktop FNA binary is not an interchangeable
   replacement for the current paired native/managed renderer.
3. **Supply the remaining runtime capabilities.** Exercise the pinned
   [assembly contexts](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Module/EverestModuleAssemblyContext.cs)
   under this Mono runtime, including stream loading, dependency resolution,
   relinked legacy DLLs and shared assembly identity. Restrict the first app to
   one selected mod set per process; do not promise collectible-context unloading
   or hot reload. Desktop native DLL folders need an explicit iOS policy.
4. **Include Lua in the compatibility work.** [Everest startup](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Everest/Everest.cs#L454)
   calls Lua initialization before loading ordinary mods, and its [Lua loader](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Everest/Everest.LuaLoader.cs)
   constructs NLua when its boot resource is present. Build the appropriate
   native Lua library for iOS and connect the pinned managed bindings; test
   Lua-to-managed callbacks and a real cutscene. A native Lua interpreter is
   compatible with keeping Celeste/Everest/mod C# on JIT. Hiding Lua failures
   or substituting AOT cutscene shims would not establish SJ compatibility.
5. **Load normal mod ZIPs.** Use a small original test map and an independently
   built code-mod ZIP through Everest's actual loader. The code mod should use
   the generated hook API and persist a module save sidecar. Log package hashes,
   resolved versions, relinking, module load/initialize failures and live hooks.
   Finish with a fresh-process save/settings reload, as build 12 only established
   same-session XML round trips.

The read-only audit clone's MonoMod, NLua and Everest-libs submodules are not
initialized. Materialize pinned dependencies in the new staging lane, not in
the reference clone or AOT workspace. The other exact pins are NLua
`b3524288712743fb2394dcf615d14d0dac3276e2` and Everest-libs
`591f7c12fcb4e8fda9ef5ef1b331b5ed40d3fb1f`. Compiling this dependency set is
still work to perform; no host Everest execution result exists yet.

## Strawberry Jam target

Reuse the existing [dependency graph](../../apple-everest/strawberry-jam-dependency-graph-stage25kc.json)
as an input lock and discovery aid. It records **StrawberryJam2021 1.0.12**, with
**52 archive nodes**, including the root, assets, three audio packages and
helpers, and 106 required package edges. LuaCutscenes 0.2.13 is among the pinned
helpers. Built-in Celeste/Everest requirements are separate runtime edges.
These are recorded versions, not a freshly downloaded closure or JIT passes.
No matching SJ archive was found in the supplied Required Files directory or
this JIT checkout's `.build` cache during this follow-up.

Fetch and verify the locked original ZIPs/DLLs before loading them. Some packages
represent multiple modules or small forwarding metadata, so do not equate
archive count with helper DLL count. Validate actual manifests and identities
rather than copying the AOT audit's compatibility classifications into JIT.
The AOT work supplies useful knowledge of maps and dependencies; its selected
semantic substitutes are not the runtime implementation of these original mods.

The first SJ gameplay target is **the Beginner lobby and Bing**, with the real
dependency closure loaded. This gives a familiar comparison with the separate
AOT work. Require lobby entry, map entry, movement, helper behavior, deaths/
respawn, audio, completion/return, save/relaunch and background/resume. Then
expand across maps that exercise additional helpers, rendering and Lua paths.
Neither one successful map nor a successful title screen validates all SJ maps.

Measure code reservations, total footprint, GC pressure, loading time and frame
gaps during actual Everest/SJ runs. Build 12 used 9.50 MiB of its 32 MiB code
budget and peaked at 1.13 GiB sampled footprint. Those measurements cannot size
SJ in advance. Any larger executable arenas need preparation at process start
with matching native protocol/script tests; late expansion is not implemented.

## Test and delivery contract

The next useful phone kit should test **Celeste + real Everest + one small map
and code-mod ZIP**, retaining build 12's audio/touch/save/resume checks. Include
Lua coverage as its backend becomes available, and gate SJ gameplay on it.
Host and package checks precede physical testing; a smaller focused IPA is
appropriate only if an identified runtime failure needs isolation.

Preserve imported game content and original ZIPs in persistent guest Documents,
with prepared IL/cache and separate profile save roots. Stream/hash large
imports and record selected package sets. Build 12 bundles content inside its
app, so an update must explicitly migrate or import it before reducing the IPA;
do not assume an old LiveContainer app bundle survives replacement. The first
private Everest test can use host-prepared IL while on-device preparation is
implemented. The final product still targets owner file import without Xcode.

The graph's recorded ZIP sizes total **1,237,284,560 bytes** (about 1.24 GB),
before the base game or app. A complete SJ handoff therefore exceeds the owner's
current 1 GB total allowance. Do not copy that full kit into iCloud under the
existing permission or split it into batches to bypass the limit. Prefer
owner-downloaded original mods through a working importer, or resolve a larger
transfer when a concrete SJ kit exists. The small-map Everest stage need not
include SJ. FMOD/public distribution permission remains unresolved.

Deliver genuinely unsigned IPAs, matching scripts, all required external test
files, versioned instructions and checksums. Preserve the LC1/LC2 setup and
Export diagnostics. Use the verified Wi-Fi/USB LocalSend handoff or iCloud and
confirm the actual transfer. No further owner file, baseline repeat or device
test is needed to begin this development work.
