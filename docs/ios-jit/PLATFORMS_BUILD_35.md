# Build35 — iOS15, JIT routes and Motion Smoothing

25 September2026. Version0.19.0, `launcher-platforms-20260925-35`.
See [the evidence ledger](PLATFORMS_BUILD_35_EVIDENCE.json). Build32 remains the
accepted phone fallback. Build33/34 Results were still empty on25 September.
The owner's issue1/iPad request takes priority over the planned touch editor.

## Outcome and package

Build35 is installed through TrollStore on the owner's iPad mini4 (`iPad5,1`),
iOS15.8.8, with Dopamine active. The native launcher and real Celeste gameplay
run. It passes26 native JIT checks, content verification, first-frame handoff,
Metal readback, touch movement/jumping and a brief resign/foreground cycle (zero recorded background seconds). The owner confirmed correct visuals/audio and normal return. Save readback,
shutdown stage8 and the delayed native heartbeat also pass (7,020 callbacks,
17,428 completed JIT methods, zero JIT/unowned/managed errors or patch rejections). This does
not establish the issue reporter's exact iOS15.3.1 crash cause: no crash log was
attached to [issue1](https://github.com/hmcneill46/cabrillo-celeste/issues/1).

The previous package and seven native archives required iOS26. The new app and
all selected arm64 archive objects require iOS15 or earlier. Recompilation uses
Xcode26.6/SDK26.5; this is not a minimum-version edit to existing machine code.
Newer systems keep the modern SwiftUI presentations;15 gets navigation, empty
states, rows, sheets and orientation calls that exist on that OS.

- IPA:24,113,498 bytes; SHA256 `6227fb1d8197442dcdd5dc4471c3b46f237f4d7b6fb59809dccb0c423a7dd662`.
- Executable/dSYM UUID:`B6E76E0B-C4D8-377A-BAEE-E65CFBA3F9A3`.
- Local artifacts:`artifacts/cabrillo-build35-final`.
- Six phone-kit files are confirmed uploaded with matching bytes to
  `iCloud Drive/Celeste JIT Tests/0.19.0-build-35`. Phone download/execution is confirmed; see the failure review below.
- The complete cloud folder is842,391,221 bytes at delivery. All previous kits and
  Results remain. An initial transient iCloud error cleared before verification.
- The owner's875,540,825-byte game ZIP was transferred over USB, SHA256 checked
  on both ends and moved into this app's ContentImport folder. Actual content
  verification covered1,158,665,183 bytes and took28.151s on this first iPad run.

## JIT activation and memory preparation

JIT is still required below26. On older systems, enabling that permission is
usually enough for the app to allocate executable memory itself. iOS26 on the
accepted A17 phone additionally needs its debugger-prepared arenas. Opening a
URL alone never marks JIT ready: process permission, debugger detach, mapped
protections, writable aliases and generated-code execution must pass.

Settings offers the available routes:

| Installation | Activation |
| --- | --- |
| Cabrillo in LiveContainer | Existing StikDebug-in-LC2 PID route; standalone StikDebug is also selectable |
| Standalone Cabrillo, iOS17.4+ | Direct StikDebug URL, real PID and standalone bundle ID |
| Standalone iOS15/16 with TrollStore | TrollStore URL, or Open with JIT followed by Check JIT |
| JIT already enabled by a jailbreak/another tool | Check this process; no helper is opened |

The owner's iPad already had `CS_DEBUGGED` and was detached at native launch.
Check JIT then allocated two256MiB virtual arenas with separate RX/RW mappings.
It samples32 pages across each arena plus the endpoints and performs cache,
argument, branch, thread and rewrite checks; unlike the unchanged script path,
it does not touch every page and commit512MiB at startup. Logs explicitly name
sampled-page coverage. Runtime allocations remain demand driven and bounded.
The game reserved about15MiB of JIT code during this initial run. Total physical
footprint was around1.1GiB, so large mod packs remain a separate memory/performance gate.

StikDebug's own minimum is17.4. TrollStore's URL scheme must be enabled in its
settings. We do not add dynamic-codesigning or other special private JIT
entitlements to the shared unsigned IPA. TrollStore supplied get-task-allow
when signing the installed copy. No debugger was attached by this Mac.

References: [StikDebug](https://github.com/StikDebug/StikDebug),
[StikJIT integration](https://github.com/StikDebug/StikJIT/blob/main/INTEGRATION.md),
[LiveContainer JIT guide](https://livecontainer.github.io/docs/guides/jit-support),
[TrollStore activation code](https://github.com/opa334/TrollStore/blob/main/RootHelper/jit.m),
[TrollStore2.0.12 URL support](https://github.com/opa334/TrollStore/releases/tag/2.0.12).
The iOS26 path retains the tested script policy; older26 hardware with a different
memory policy and other jailbreak configurations are not yet accepted.

## Motion Smoothing and touch repair

[Motion Smoothing](https://gamebanana.com/mods/514173) is an existing Everest mod;
it is not bundled or silently enabled. The tested original1.8.0 ZIP has SHA256
`fb021011aa505e5670cf08ade375e7f80b58eb40c5045f9da15556a9bff888d2`.
Its EverestCore minimum1.4673.0 is met by the pinned1.6531.0 runtime.
Its [source](https://github.com/FancyFurret/celeste-motion-smoothing) explains
camera subpixel smoothing at60Hz and additional rendered frames above60Hz.

Cabrillo previously capped CADisplayLink at60. The optional Allow up to120Hz
setting now requests the screen's rate, capped at120, and opts into high refresh
on ProMotion iPhones.60Hz remains the default. The mod chooses its render FPS;
Cabrillo does not alter Celeste's physics step or force a game-speed setting.
The guide explains60 FPS on60Hz hardware and120 FPS/Interval on120Hz hardware.
The actual rate can still fall with workload, system policy or Low Power Mode.

The real-game120 FPS test uncovered an input bug: the adapter polled touch in
its Game.Update override, before Motion Smoothing's Engine.Update hook skipped
alternate ticks. That could clear a press before an actual input/gameplay update.
The new adapter hooks MInput.Update and polls immediately before virtual input
is consumed. Both render-only frames and the mod's fixed gameplay updates now
retain the correct tap edge. The hook is disposed during normal shutdown.

The initial120 FPS run rendered but produced zero Player.Jump calls. With the
fix, the same scripted holds/releases produce jumps and complete resume/save/Quit.
All four cases pass on the actual Mono8.0.28/Metal host runtime: Fast60, Fast120,
Fancy60, Fancy120. The120 runs observe roughly260 gameplay updates for520 draws;
each gameplay update is1/60 second.60 FPS also keeps that fixed step. These
host results establish compatibility and the input repair, not physical iPhone
120Hz acceptance, sustained frame pacing, battery use or A8 mod performance.

## Phone Motion Smoothing failure — later on 25 September

Two owner exports show successful JIT setup and zero-active catalogue quiescence,
then `MethodAccessException` on the first managed Frame, at both 120 and 60Hz.
The generated Engine.Update method cannot call protected Engine.OnSceneTransition
or FNA Game.Update. The owner also reports startup succeeds with the mod disabled
and Cabrillo's 120Hz option enabled. That last control is a visual owner report.

The iOS15 runtime rebuild omitted the accepted assembly-scoped member visibility
patch in Mono class.c. The older host archive retained it, so the earlier host
PASS did not exercise the broken iOS metadata implementation. Build36 restores
the exact patch, adds a broken-source host reproduction at both rates, and pins
positive and denied-access controls. See [build36](VISIBILITY_BUILD_36.md).
Build35 remains frozen; its iPad base-game pass does not imply mod acceptance.

## Exact dependencies and preservation

- Managed receipt:`.build/platform-managed35-b/receipt.json`, SHA256
  `e03d75eb1377a81a71d596c7e47567b431e2c67103eb2af1346f5bc315943fcc`.
  It derives from the exact build34 precision receipt. Only CelesteJITEverest.dll
  changes among201 assemblies; repaired Celeste.dll and the other199 remain exact.
- Native receipt:`.build/platform-native35-c/receipt.json`, pinned in NativePayload.json.
  Mono plus four components, FNA3D and Lua are rebuilt; nine archives remain exact.
- Explicit imported source manifest:`.private/platform-inputs35/manifest.json`,
  SHA256 `6f57a25d28981cd827f920324737f06ec8ff0a51ef2f3f5efe007aeffa9f027b`.
  Import validated accepted archive/source hashes and recorded every copied file.
  Builds run in the sandbox denying legacy checkouts and private-capsule writes.
  No original or sibling checkout was built into or changed.
- The derived Mono retains16KiB code-budget and Femto before-field-init policy.
  FNA3D retains the accepted callback pool/first-frame changes; Lua retains
  the CJIT_IOS external-process restriction.
- Build34 backup/restore transactions, all unknown files, exact mod identities,
  fresh-process gates and hair/lava fixes remain. Catalogue quiescence has zero
  active requests before the actual iPad managed startup. First reveal is callback1.
- The earlier unfinished35 packaging attempt was interrupted before IPA creation
  after the touch fault was found. Its logs remain; only the final package was
  installed or delivered. Sources listed in its frozen manifest are immutable.

## Reproduction and remaining physical checks

Use `tools/build_platform_runtime.py` with the explicit source manifest to rebuild
native inputs; `tools/build_platform_adapter.py` derives the adapter from34.
`tools/build_platforms.py --managed .build/platform-managed35-b/receipt.json`
and `tools/verify_platforms.py` check the exact pins, every arm64 archive OS floor,
package bytes and matching dSYM. Every changed build needs a fresh identity.
Host regression: `tools/check_motion_smoothing.py`; JIT route cases:
`experiments/ios-jit/launcher-platforms/tests/PlatformOptionsTests.m`.

The iPad base-game gate is accepted, including normal save/Quit and the owner's
visual/audio review. A USB screenshot also confirms the iOS15 Settings view
after native return. This is not broad iPad mod or backup/restore acceptance.
The phone still needs the combined backup/save-transfer/precision checks plus
JIT-route and optional60/120Hz Motion Smoothing checks in README-FIRST.txt.
Standalone StikDebug and LC→standalone helper routing are implemented and URL
checked; physical route acceptance is separate. Build33/34 acceptance is not
inferred from35 startup. The full touch editor stays behind the saves gate.
No GitHub write or publication was performed for this work.
