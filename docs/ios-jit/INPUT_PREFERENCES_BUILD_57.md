# Build57: live input preferences and controller integration

Date: 3 October 2026. Version: **0.28.0 / build57**. Branch:
`codex/game-input-compatibility`. New implementation is isolated in
`experiments/ios-jit/launcher-input-preferences`; build56 remains frozen.
No new GitHub write or public Release is authorised. Public workflows select52.

## Behaviour

The SwiftUI editor's Behavior page now includes the shared **Feather follows
finger** preference, **Toggle behaviour**, and **Controller prompts**. Use
Pause → Touch controls… → Details → Behavior during play. Save applies changes
in the running game, Cancel retains saved preferences, and a fresh feather touch
is required after editing. The original neutral circle and physics are retained.

Grab buttons now supply raw input to original Celeste. The custom GrabCheck
replacement and parallel hardware/touch toggle calculations are removed.
`Settings.Instance.GrabMode`, `Input.UpdateGrab`, `Input.GrabCheck` and the game's
bindings perform Hold, Inverse and Toggle. Per-source preferences automatically
select that internal setting. Changes made through Celeste Options are saved
for the previous active source before applying a newly observed source, avoiding
a menu edit being assigned to the wrong input method. Touch, keyboard and
controller preferences are independent; idle controllers do not steal focus.
The touch Grab drawing uses the game's effective state too.

Default uses original ResetGrab and clears on source changes. **Until untoggled**
preserves the original latch across ResetGrab calls, including death and new maps.
Each source retains its own latch when switching away and back. Changing a source's
mode, changing toggle behaviour, or ending the game clears the appropriate state.
It does not persist a held grab into a new process.

Automatic controller symbols use the exact SDL handle selected by FNA and
Celeste's player index. Pinned Everest's GUID lookup recognises old DualShock
IDs but omits DualSense. SDL's controller type supplies the missing PS5 family;
manual choices include Xbox, PlayStation, Nintendo Switch and Stadia. Keyboard
and touch focus still work. Explicit mod prompt overrides take precedence.

Original game light colours continue through FNA and SDL, with their original
colour transformation. Cabrillo replays the latest active-controller colour on
late attachment, reconnect, selected-controller change and foreground return.
It logs identity and light support without claiming unsupported hardware works.
The reported physical DualSense colour issue is not yet reproduced or accepted
on the owner's controller; the new replay path addresses late-connect/reset cases.

Older schema1 layouts decode with defaults for the new optional fields. The
existing feather preference remains canonical. Native editor dismissal is deferred
until its confirmation dialog closes, and actual dismissal clears input isolation.
This addresses an iPad discard/reopen problem caught by the added UI test.
Full-display placement, landscape actual-size editing and the16:9 guide remain.

## Verification

The final evidence ledger records exact receipts and package hashes. Checks cover:

- 59 Swift migration/serialization controls and 2,743 managed input/geometry controls.
- Six actual Apple UI tests across iPhone and iPad simulators: save/cancel,
  persistence, native presentation/reopening, full-display drag and resize.
- Three complete original-game runs: cold import, saved-game launch with a missing
  staging ZIP, and old-layout original-code cache rebuild. Each includes 56 new
  input-preference checks plus 17 touch-editor, 37 feather gesture and 37 feather
  integration checks, hair, desktop save transfer, resume and normal Quit.
- A separate real-game lifecycle run: original Player death/respawn under both
  toggle modes and persistent grab across loading another map and returning.
- Original Motion Smoothing1.8.0 at60/120 callbacks, Fast and Fancy. These are host
  integration checks, not sustained physical120Hz measurements.
- 59 Python release/boundary controls and independent package/source audits.

Controller input, disconnect/reconnect and LED RGB callbacks use the real pinned
SDL virtual backend. This SDL virtual bus intentionally hides VID/PID, so the
fixture supplies PS5 type at the native query boundary for its test controller
only. Physical Apple GameController detection/LED behaviour is a distinct device
gate. The old Mac test library lacked AttachVirtualEx; it is replaced only in the
host fixture with a fresh public SDL build. The iOS dependency archives are unchanged.

The initial Motion Smoothing trials exposed draw-timed assumptions in the new
host fixture. Tracing showed a pressed grab with its latch unchanged: the mod's
original UpdateEveryNTicks hook deliberately rejects grab updates between game
ticks. The final fixture runs grab contracts inside an accepted original input
update, preserving that hook, and advances VirtualButton's normal lifecycle for
each synthetic edge. Touch gestures wait on actual game updates, including dash
startup. These test-only changes leave the managed application payload unchanged.
Failed trial logs are retained separately from the final passes.

## Build and distribution boundary

Final managed input: `.build/input57-managed-c/receipt.json`. 191 of199 managed
assemblies match56; the adapter changes and seven pinned public MonoMod/NLua
assemblies rebuild. Bootstrap, original-game preparation, FNA and support module
remain exact56. The16 native dependency archives and signed49 Shortcut resources
are unchanged. Native/FMOD receipts remain `.build/release51-local/{native,fmod}`.
`tools/build_release57.py` is the separate fresh public-source builder requiring
a developer-owned FMOD SDK. No original/prepared Celeste code or assets, FMOD SDK
components, pairing/signing material or private test fixtures enter the IPA.

## Device gate

55 and56 Results were empty at review. No phone has been changed. Keep the existing
data container and shortcut49; allow a prepared-code cache rebuild. Confirm live
feather/grab/prompt preferences, input switching, persistent/default death behaviour,
actual DualSense colours, normal Quit and a fresh-process return. Export diagnostics
into57 Results. Earlier physical save-manager/iPad/sustained120Hz gates remain separate.

## Final package and delivery

[The evidence ledger](INPUT_PREFERENCES_BUILD_57_EVIDENCE.json) links the exact
host, simulator, package and upload receipts. The unsigned IPA is19,039,518 bytes,
SHA256 `7b8abb06247baa0ac1e1fa49535a50c34c5e8534dbd50ab3e5ad1368503fdf4b`.
The matching dSYM and291 frozen app/build inputs are retained in
`artifacts/cabrillo-build57-final`; all18 prior source manifests still match.
Use58 for new implementation.

All nine kit files have exact local readback and confirmed upload to iCloud →
Celeste JIT Tests → 0.28.0-build-57. Initial transient iCloud errors cleared.
Only the superseded37 cloud installer was retired after verifying the exact
retained local copy and its package receipt. All Results and accepted fallbacks
remain. Cloud total is993,871,336 bytes. No phone or GitHub release was changed.
