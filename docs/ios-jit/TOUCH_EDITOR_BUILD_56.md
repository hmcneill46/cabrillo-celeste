# Build56 /0.27.0 — SwiftUI touch controls

3 October2026. Owner-requested local work in `launcher-touch-editor`, on
`codex/game-input-compatibility`. Public workflows still select52. No new commit,
push, workflow run or public Release was requested. Build55's original-storage
repair is retained; its Results folder was empty at this review, so no physical55
acceptance is inferred from the owner's next feature request.

## User behavior

**Settings → Controls → Customize touch controls** opens the SwiftUI editor.
**Pause → Touch controls…** opens it during a game, including live grab changes.
There is no additional mod ZIP to install. Save applies a draft; Cancel leaves
the stored layout alone. iPhone and iPad keep separate layouts.

The editor supports fixed/floating movement, editable acquisition regions,
circle/rectangle action buttons, four split Jump/Dash orientations, swapped
halves, sliding, duplicates, up to24 controls, opacity, action/direction haptics,
visibility, per-source grab modes, Crouch Dash and Quick Restart. It includes
move/resize, precise sliders, Undo, Mirror, per-control/full Reset, Files export
and import preview. Morro D3 v2 layout documents can be converted.

The owner clarified that controls must cover the **entire display, edge to edge**,
including space outside the game image. Coordinates therefore use full display
bounds. Safe-area insets guide the default placements but never restrict edits.
Portrait retains the detailed editor. Rotating landscape shows controls at actual
size with a centered16:9 game-image guide, draggable resize corners and a compact
movable/hideable toolbar. Details returns to the complete editor without requiring
rotation during gameplay. Camera cutouts and system gestures can still obscure
or intercept the physical edges.

The **Tap / Swipe** preset is optional and experimental. Contact holds Jump;
a swipe beyond the adjustable point threshold triggers one eight-way Dash,
independently of the movement joystick. Lifting releases Jump and permits the
next gesture. The gesture begins with Jump; use the button/split presets for
a dash without an initial jump. Menus confirm on tap release; a swipe cancels
without first confirming. Grab/Pause/Journal retain buttons. Feather follows
finger has priority in flight. Celeste retains its own physics and timing.

See [the user guide](../TOUCH_CONTROLS.md) for the Morro comparison and usage.
Morro was inspected at `cc02b0cc697bd620c0dc864d4af3c60d79a95e85`;
its MIT attribution is retained. Its device results remain separate evidence.

## Runtime and storage

SwiftUI owns the editor and file flows. SDL/FNA still own the gameplay overlay
and input polling at MInput.Update, including render-only Motion Smoothing ticks.
The configuration is loaded when its revision or display metrics change. Bounded
finger ownership prevents a contact from acquiring a new unrelated action after
starting outside it; duplicate actions are combined. Split boundaries use a small
point hysteresis. Source, pause, player/scene and lifecycle changes clear transient
input. The native editor isolates game input while it is open.

The swipe's separate aim lasts through the ordinary button buffer and dash-start
freeze, using scaled game time. It does not change MoveX/MoveY or any Player
physics method. Crouch Dash and Quick Restart feed original game inputs: the
original Crouch Dash Mode and Quick Restart confirmation still apply. Hardware
grab defaults to the original game setting; explicit Hold/Toggle/Inverse modes
use Cabrillo's separate source state.

The full-display JSON schema1 is validated by Swift and managed code. Stored
profiles live in dedicated launcher preference keys; game saves are untouched.
Imports preview before becoming a draft, and saved replacement requires Save.

## Verification

Final managed payload: `.build/touch56-managed-d/receipt.json`.

| Check | Result |
| --- | --- |
| Swift profiles/imports/defaults/edges | 45 checks pass |
| Managed input policy and cross-language geometry | 2,740 checks pass |
| Actual Apple UI tests | Two each on iPhone and iPad simulators pass |
| Full real-game host runs | First import, cached missing-ZIP start, legacy rebuild pass |
| New real-game input checks | 17 per run pass |
| Feather regression | 37 gesture and37 real-game checks per host run pass |
| Original Motion Smoothing1.8.0 | 60/120 callbacks, Fast/Fancy, all four pass |
| Python build/release controls | 59 pass |
| Independent package/dSYM and frozen-source checks | Pass |

UI checks cover rotation, full-display bounds, the16:9 guide, actual-size dragging,
resizing and moving to the screen edge, draft duplicate/undo, presets, Save/Cancel,
persistence, the pre-game session lock and native modal presentation. Their final
screenshots were visually inspected. The simulator fixture has its own bundle and
preferences and is not packaged. The checked production SwiftUI also compiles for
the real arm64 iOS15 target with Xcode26.6.

The real-game tests observe held Jump, leftward movement with an upward swipe
dash, original Crouch Dash, Quick Restart confirmation, native editor input
isolation, live touch Inverse Grab and return through the ordinary pause menu.
They also retain hair, desktop save transfers, save/resume and normal Quit. The
legacy cache rebuild preserves every retained original byte. The Motion Smoothing
runs use the same final managed payload and original mod ZIP; they verify fixed60
physics steps, not sustained physical120Hz output.

Early UI controls exposed competing row actions and drag recognizers; the final
SwiftUI controls give row buttons separate actions and use a stable canvas gesture.
Early host probes sampled transient dash state too late or began during an opening
cutscene. The final fixtures observe original Player updates and wait for ordinary
play before sending the gesture. These earlier probes are retained privately and
are not counted as final passes.

Final receipts:

- `.build/touch56-policy-e/receipt.json`
- `.build/touch56-ui-h/receipt.json`
- `.build/touch56-host-i/receipt.json`
- `.build/touch56-motion-c/receipt.json`

191 of199 managed DLLs match55. The game adapter changes and seven pinned public
MonoMod/NLua dependencies rebuild. Bootstrap, preparation, original-input support
and the feather implementation remain unchanged. All16 native dependency archives
and both signed49 Shortcuts remain exact. Rebuilt preparation-tool hashes can
require one new cache generation from retained originals.

These are host/simulator checks. Physical56 startup, native presentation over the
SDL game, thumb comfort, accidental swipes, multi-touch/haptics and sustained120Hz
remain device gates. Earlier granular save-manager and iPad gates are not closed.
No physical phone or iPad was modified in this work.

## Build and package

Use `tools/build_release56.py` for the separate fresh public-source build with a
developer-owned FMOD SDK. Local iteration used explicit verified51 native/FMOD
receipts and freshly compiled56 managed/app sources. The FMOD runtime permission
and separate developer SDK restriction remain as described in
[RELEASING](../RELEASING.md). No original/prepared game code, original assets,
SDK archives or signing material is in the IPA or public source candidates.

The unsigned IPA and matching dSYM are retained in
`artifacts/cabrillo-build56-final`. IPA:19,020,874 bytes, SHA256
`b20ed0a6aafc40bf957f2be64411db80a71591dfd88f6206214037e6fffd9b96`.
All285 captured inputs are frozen, with an exact source archive. All17 checked
prior manifests still match. Use57 for new implementation.

## Device handoff

The nine-file kit has exact local readback and confirmed upload in
**iCloud → Celeste JIT Tests → 0.27.0-build-56**. Initial transient upload errors
cleared. The evidence ledger records the confirmation; the cloud total is
998,928,055 bytes. Only the
superseded53 cloud IPA is retired after verifying its exact retained local copy
and package receipt. Every Results folder, local53 artifact and accepted fallback
is preserved, within the owner's1GB cloud budget.

Keep the existing data container and imported shortcut49. Finish an active game
with normal Quit before updating, use fresh JIT, and allow one automatic cache
rebuild if needed. Check the editor in portrait and landscape, split/duplicate
buttons, live grab changes and experimental swipe direction. Also test another
fresh-process start, normal Quit and Export diagnostics to56/Results.
