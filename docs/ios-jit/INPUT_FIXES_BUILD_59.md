# Build59: touch resize bounds and controller resume

The local repairs pass the source compilation, focused regression and iPhone/iPad
UI checks described below. No new IPA or physical controller result is claimed.

20 October 2026. Local **0.29.1 / build59** implementation:
`experiments/ios-jit/launcher-input-fixes59`.

The owner requested fixing both defects reported after rebasing to
`3f5c6bb61f7d47d8569e7e457272348bd5ebf236`, with regression testing. This authorizes
local changes and tests. After reviewing those results, the owner explicitly
authorizes committing/pushing as hmcneill46 and building an unsigned test IPA.
The existing hosted workflow now selects59 with publication disabled. No version
tag, public Release, iLoader submission or device mutation is authorized. The 345
captured58 inputs and 299 captured57 inputs remain byte-identical;59 explicitly
pins both complete maps and retains the 153 dependency hashes and Everest 1.6642.0.

## Owner-approved hosted trial

After the completed local validation, the owner explicitly requests committing
and pushing the fixes as `hmcneill46` and building a test IPA. The trial uses
`codex/actions-release` and the existing workflow with `publish=false`. The
workflow now compiles and tests59; all 159 repository/Python controls pass after
that selection change. Strict sealed-kit controls reject old build identities,
changed IPA bytes and unexpected helper files. The original application and
helper sources remain exactly those tested locally. Hosted build and independent
artifact verification are pending. No version tag or public Release is authorized.

## Repairs

**Touch resizing:** build58 applied a 32-point minimum after limiting the requested size
to the remaining screen space. A valid small control against the right/bottom
edge could therefore extend beyond the canvas and disable Save.59 limits the
minimum to the control's existing size and applies the available-space limit
last. It also preserves the schema's normalized minimum and accepted edge
rounding tolerance. Small imported controls remain editable. Circle bounds scale uniformly,
preserving their proportions and fitting both edges, including imported
non-square bounds. A boundary rounding correction keeps scaled dimensions at
the schema minimum. Move, selection, history, Undo, validation and storage paths
remain unchanged. The Foundation policy is called directly by the production
SwiftUI draft's resize gesture.

**Controller light replay:** build58 inferred resume only from a game update that saw
the engine inactive. Native lifecycle handling pauses updates before suspend
and restarts them after resume, so both SDL focus events can be processed before
the next update. Build59 marks suspend/resume explicitly through the existing managed
Entry methods. The next active update replays the last game-requested colour to
the same selected FNA controller. Replay waits for an active foreground and a
connected controller, remains pending through disconnects, and clears after one
attempt. Repeated Resume calls are harmless; Dispose clears the lifecycle and
colour state for a new game session. Controller selection, button input, prompt
mapping and the original light hook remain in place.

## Verification

The machine-readable [evidence ledger](INPUT_FIXES_BUILD_59_EVIDENCE.json)
records receipt hashes, counts and scope for the completed local validation
phase, before the later owner-approved GitHub trial. Its no-GitHub-write and
workflow58 fields describe that earlier phase. Tests use synthetic layouts,
controlled lifecycle/SDL fixtures, public source dependencies and owned Apple
simulators. No original game, pairing credential or private SDK is required.

- The actual production resize policy passes 779,994 assertions across 201,978
  geometry cases, 150 schema encode/decode tolerance cases and 600 wide/fractional
  schema round trips. An independent check passes 560 schema round trips and
  confirms 350 exact prior results in the phone/tablet size range. Three
  exact build58 draft negative controls reproduce invalid
  right, bottom and circular-edge resizing, with Undo recovery.
- The actual controller source is compiled against controlled SDL/engine/hook
  fixtures, covering native paused resume, sampled focus changes, delayed active
  state, no colour, no device, reconnect/player changes, repeated transitions,
  disposal/new session and retained prompt mappings.58 reproduces the missed
  replay, while59 replays once after native resume.
- All 20 actual build59 adapter C# inputs and the support module compile against newly
  generated stripped metadata/hooks and exact public build58 dependencies. The public
  IPA is hash-checked and its GitHub attestation verified for the exact tag,
  source and hosted workflow. BuildReference uses the pinned official Everest
  stripped references and removes all method implementations. The adapter and
  game are never executed. This is an integration compilation audit, **not a
  fresh dependency build or a usable59 managed payload/IPA**. The shipping59
  recipe retains fresh dependency compilation.
- Production iOS 15 host compilation, isolated iOS 17.4 helper compilation,
  iPhone/iPad gesture checks and retained policy/import/JIT/save/shortcut checks
  are recorded separately in the ledger. Source hashes are checked before and
  after each successful check; interrupted or source-drift attempts are retained
  separately and do not count as passes.

The completed regression checks include 152 repository/build Python tests,
59 Swift and 2,743 managed touch-policy checks, 186 native JIT/pairing controls,
12 picker scenarios, 321 dependency controls, 14 retained game-input controls,
119 save/transfer checks, 185 native shortcut controls, 36 shortcut branches and
15 invalid-URL controls. The iOS 15 compile builds 25 launcher and 21 vendor Swift
sources, six CYaml sources and 15 Objective-C host sources. The iOS 17.4 helper
and pinned framework compile independently. The actual build59 native retained-input
function also passes 51 assertions against exact public build58 package metadata;
this is metadata compatibility coverage, not a build59 package test.

The UI suite passes 14 distinct positive cases: three normal editor tests,
four-edge resize/Move/Undo/Save in one test, and three combined launcher/JIT
settings tests on each device family. Four fresh successful runs cover all seven
cases per family and retain 28 screenshots. Two build58 negative-control tests reproduce
all eight invalid edge cases. The result guard requires the complete expected
test set, successful xcresult and log records, and matching source/fixture
hashes before and after execution. Its 27 adversarial tests reject missing,
partial, skipped, failed, misnamed and mismatched results.
Representative final phone/tablet edge, circle and same-draft Move/Undo captures
were visually inspected; Save remains enabled. The retained settings captures
also show the combined touch and JIT settings.

Earlier candidate UI results are retained as historical evidence and excluded
from the final-source count. A final iPad landscapeLeft attempt was interrupted
after repeated animation-idle waits; its passing individual cases are also
excluded. The successful tablet editor retry uses landscapeRight through an
ignored generated fixture, with the actual compiled fixture hashed before and
after the run. Phone editor and both combined launcher suites use landscapeLeft;
the suites also exercise portrait transitions. Final-source tablet editor
landscapeLeft completion is not claimed. All test-owned simulators are deleted.
Earlier
recovery of a stuck test
simulator required restarting the per-user simulator service after verifying
all 14 unrelated devices were shut down; their states remain unchanged. Some
earlier attachments contain simulator backboardd crash reports; no Cabrillo
crash is inferred from those system reports. The exact cause of the stall is
unproven. Baseline58 also exposes invalid gestures with no Undo entry in two
iPad cases; the report does not assign a cause to that observation.

## Running the local checks

Use Xcode26.6 /17F113 (SDK26.5); this Mac's developer directory is
`/Applications/Xcode.app/Contents/Developer`. Every work directory must be fresh.

```sh
python3 tools/check_touch_resize59.py --work .build/input59-resize
python3 tools/check_controller_resume59.py --help
python3 tools/check_input_fixes59_compile.py --work .build/input59-host
python3 tools/check_input_fixes59_native.py --work .build/input59-native
python3 tools/check_input_fixes59_policy.py --sdk /path/to/pinned/sdk8 --work .build/input59-policy
python3 tools/check_input_fixes59_ui.py --help
python3 tools/check_input_fixes59_managed_compile.py --help
python3 -m unittest discover -s tools/tests
```

The full fresh build is `tools/build_release59.py`, using the same explicitly
licensed FMOD SDK/public-source requirements as58. The local adapter audit may
never be supplied to that builder as a substitute for its fresh managed receipt.

## Limits

There is no new59 IPA, hosted workflow, phone installation or physical controller
LED result. This Mac lacks the licensed FMOD SDK and complete toolchain required
for a fresh IPA. The local compile checks omit the SDL/Mono-dependent graphics
implementation and final app linking; the helper is compiled but not registered
or run on a phone. Real controller LED, helper/DDI/JIT, gameplay, saves/lifecycle
and sustained 120Hz acceptance retain their previous scope. Prior build58 real-game
results are preserved history, not new59 execution evidence.
