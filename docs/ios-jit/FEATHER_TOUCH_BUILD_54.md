# Build54 /0.26.0 — optional feather touch steering

2–3 October2026. Owner-requested local development in `launcher-feather-touch` on
`codex/game-input-compatibility`. No commit, push or public release is requested.
Build53's original game input compatibility is retained.

## Phone startup failure — 3 October

The owner reports Celeste did not start. The 2,417,490-byte Results export
(SHA256 `e18e57478734e79fdb40d3cd18d047a4d31fbd148ca1999ec55dc3fd379e6331`)
matches the final54 BuildInfo exactly. Its session passes all26 native JIT checks
and confirms Shortcut readiness. Both attempts verify all1,216 saved asset files, then reject
preparation because no ZIP is staged. Neither reaches game-code readiness or
feather execution. Retained history shows52 previously reused its prepared game.

This exposes a53/54 regression: native startup always supplies the expected
staging pathname, even after its ZIP is consumed. GameCodeStore incorrectly uses
nonempty-path alone to select a ZIP. The old host warm test supplied an empty
string, so it missed the native contract. Build55's separate lane restores the
file-existence check and adds the actual missing-path case. Preserve54 and this
failed evidence; the original host/simulator passes below remain scoped as such.

## Behavior

Settings → Cabrillo extras → **Feather follows finger** defaults off. It is stored
per installation in `cabrillo.featherTouch` and sampled when starting Celeste.
It is built into Cabrillo's existing game adapter, so no optional mod ZIP or
Everest menu setup is required. The native switch is locked during a game session.

While a living player is in the original feather state, a fresh touch inside
the game viewport and away from jump/dash/grab/pause/journal controls claims
steering. Dragging supplies a continuous, normalized direction toward the finger;
it does not snap to the ordinary joystick's eight directions. Lift to supply zero.
The joystick is hidden only during touch-controlled feather flight. Outside
flight, or when disabled, the original touch movement and feather bindings apply.
Keyboard/controller source arbitration remains active; an idle connected pad
cannot suppress touch. The new real-game fixture exercises keyboard takeover.

Celeste still decides flight speed, acceleration, turn rate, collisions, duration,
animations and audio. Inspection and execution of the owner's original game show
neutral steering targets91, held forward steering can approach190, and partial
analogue input does not implement a proportional speed slider. No new speed
curve, movement shortcut or `Player` method patch is added.

This targets the normal Celeste feather state. Mods with entirely different
movement or non-affine screen effects can require a separate integration.

A small deadzone around Madeline supplies the same zero input as release. This
avoids rapidly reversing heading when Madeline reaches the finger. It enters
neutral at16 native display points and resumes steering beyond22, preventing
boundary jitter. The faint circle marks the16-point region. Coasting still moves
the player; this is not dragging, teleporting or stopping in midair.

## Input and display details

- Captured fingers retain ownership until release. A second finger cannot steal
  the target or automatically take over after release. Action-button touches
  cannot become steering by sliding off their button.
- A pre-held joystick finger does not suddenly become a target on entering a
  feather. Start a fresh touch. Pause, death, transition, player replacement and
  input-source changes end steering; retained fingers cannot turn into buttons.
- Missing/cancelled touches, viewport/layout invalidation and the existing native
  suspend path clear steering. Fresh presses can reuse a cancelled SDL finger ID.
- Native points map through backbuffer pixels, the actual letterboxed viewport,
  Engine.ScreenMatrix and Everest's WorldToScreen transform, inverted from a
  64-pixel affine basis. This keeps both directions on the rendered camera, even
  when Motion Smoothing offsets CameraToScreen but leaves ScreenToCamera alone. It
  includes camera transformation, zoom/focus, screen padding and Mirror Mode.
- Input is polled at the existing MInput.Update hook, including with Motion
  Smoothing's extra render callbacks. Only Input.Feather.Value is overridden,
  after ordinary polling, and only while the optional touch mode is active.
  Zero is explicit, so an old joystick node cannot leave a direction latched.
- The loop uses fixed-size gesture storage and a cached setter delegate. No
  per-frame reflection, async task, file access or game-code preparation is added.

## Reproduction and distribution

Use `tools/build_release54.py` and your own FMOD SDK for a fresh public-source
build. Local iteration can use the explicit verified native/FMOD receipts from
`.build/release51-local`; these are unchanged dependencies, not fresh native
runtime compilation. The managed payload builds from public sources without
original game inputs. The optional NuGet cache accepts only release-pinned public
archives, extracts them anew and records them with the usual provenance.

The original game ZIP is a private runtime/test input. The IPA contains neither
original/prepared Celeste code nor original game assets. FMOD runtime distribution
permission and the separate developer SDK restriction remain as documented in
[RELEASING](../RELEASING.md). Public workflows still select52. Keep shortcut49.

## Verification and physical acceptance

Fresh host checks and package evidence are recorded in the accompanying ledger.
An earlier prototype reproduces mismatched camera conversion with Motion
Smoothing; the final transform uses the same rendered camera in both directions.
The tests execute the original StarFlyUpdate method and exercise the complete
SDL → FNA → TouchPort → MInput path with the option off and on. They cover screen
mapping, fresh presses, dragging, release, missing fingers, original joystick
fallback, keyboard takeover and touch recovery. Separate gesture cases cover
multitouch, action ownership, resets, cancelled-ID reuse and deadzone hysteresis.
The host fixture removes FNA’s inactive-app sleep for local checks; no physical
performance claim is based on its callback rates. The actual production Settings
view is tested on iPhone and iPad simulators for default, persistence, disabling
and the session lock.

The final managed receipt is `.build/feather54-managed-e/receipt.json`. Tests of
that exact payload pass:

| Check | Result |
| --- | --- |
| Gesture policy | 37 controls, including cancellation and hysteresis |
| Original-game input integration | 37 checks per run, option off and on |
| Cold and cached host runs | Gameplay, hair, desktop save transfers, save/resume and normal Quit |
| Original Motion Smoothing 1.8.0 | Fast and Fancy at both 60 and 120 requested callbacks; original fixed physics step retained |
| Native Settings UI | iPhone and iPad simulator; default, relaunch persistence and session lock |
| Python build/release controls | 59 pass |

Receipts are `.build/feather54-host-e/receipt.json`,
`.build/feather54-motion-e60/receipt.json`,
`.build/feather54-motion-e120/receipt.json` and
`.build/feather54-ui-b/receipt.json`. The motion fixture totals update counts
across death/room reload, which can replace its probe entity; it still checks
every observed fixed physics step. Test instrumentation is absent from the IPA.

Of 199 managed assemblies, 191 match53 byte for byte. The game adapter changes;
seven public MonoMod/NLua dependencies are freshly rebuilt from the same pinned
sources. Bootstrap, the content manifest and the original-game compatibility code
remain exact53. The preparation recipe changes only its rebuilt tool hashes, so
the first run prepares a new cache from the retained original files. All16 native
dependency archives and both signed49 Shortcuts are unchanged. Earlier
nine-input/full-Strawberry-Jam evidence belongs to53; the new
54 runs use the Steam Windows FNA input. None of those results is relabelled as a
new physical-device pass.

Host/simulator checks are not physical acceptance or measured sustained120Hz.
The owner should replace Cabrillo while keeping its data container, enable the
option, try a feather room, lift/re-touch, pause/resume and return to normal
movement, then use normal Quit and export diagnostics. After a fresh app process,
turn it off to compare. All earlier save-manager, lifecycle, iPad and display gates
remain separate. No phone is modified as part of this local build.

## Package and delivery

The unsigned IPA is `Cabrillo-0.26.0-build-54-unsigned.ipa`, 18,787,093 bytes,
SHA256 `b298b217e20a4e6585c19fe365c077c6215434fe462ef69cf64cc2efa88dc437`.
The build and independent release-package auditors pass, with a matching dSYM,
199 managed assemblies and no bundled original/prepared game code or assets.
All272 captured app inputs are frozen under `artifacts/cabrillo-build54-final`.
All15 retained earlier source manifests match. New implementation must use55.

The eight-file kit has exact local readback and confirmed upload in iCloud Drive
→ Celeste JIT Tests → `0.26.0-build-54`. Initial transient iCloud errors cleared.
Only the superseded38 cloud IPA was retired after matching its
retained local original and package receipt. Every Results folder and accepted
fallback is preserved. Local cloud total is996,231,844 bytes, below the1GB budget.
The [evidence ledger](FEATHER_TOUCH_BUILD_54_EVIDENCE.json) links private receipts
by path and checksum without publishing raw logs or original game data.
