# Touch controls

Build57 includes **Settings → Controls → Customize touch controls**. During a game,
open **Pause → Touch controls…** to use the same SwiftUI editor, including grab
and input preferences. In landscape, choose **Details → Behavior** for these
options. Save applies them immediately; Cancel keeps the saved settings.

## Arrange the screen

- Select a control on the landscape preview or in the list. Drag it to move;
  drag its corner to resize. The sliders also provide precise positions/sizes.
- Choose circles or rectangles, change the action, or adjust opacity. A wide
  rectangular Grab button can serve as a shoulder region.
- Duplicate buttons for another finger or position. Add Jump, Dash, Grab, Pause,
  Journal, Crouch Dash, Quick Restart or another split region. Up to24 controls
  fit in a layout, including the movement and gesture regions.
- Split Jump/Dash supports both diagonals, left/right and top/bottom. Swap the
  halves and choose whether a held finger can slide between actions.
- Mirror swaps the sides. Undo reverses edits; Reset restores this device's
  defaults. Controls use the **whole screen, edge to edge**, including the space
  outside the game image. Each button's drawn shape is its hit region; the movement
  nub uses the usual joystick dead zone.

Portrait has the detailed editor. Turn the device landscape for a full-screen,
actual-size layout: move buttons and drag their resize corners while holding the
device as you would during play. A **16:9 game-image outline** shows where Celeste
sits on either display shape. Drag the compact toolbar by its handle if it covers
a control, or hide it. Details returns to the complete editor; Save applies the
layout. During gameplay the same full-screen editor opens from Pause, with Details
available without leaving landscape.

Buttons are allowed beyond safe-area insets. Camera cutouts and system gestures
can still obscure or intercept those edges; the default layout avoids them.

Buttons take priority over broad movement/gesture regions. Overlapping explicit
buttons use their order in the list; the editor warns about overlaps. Very small
controls also produce a warning. The editor requires movement, Jump/Dash (or
gesture mode), and a visible Pause button. Opacity zero hides a control's drawing
without removing its hit region; disable it to remove its input.

## Behavior

**Fixed movement** uses the displayed joystick center. **Floating movement**
starts at the first contact inside its region. Both keep the existing eight
directions, dead zone and direction hysteresis.

### Grab modes

**Hold**, **Toggle** and **Inverse** use Celeste's internal Grab Mode and original
input logic. Inverse grabs until the button is held. Touch, controller and keyboard
remember separate choices, and switching input methods selects the corresponding
Celeste setting automatically. Changing Grab Mode in Celeste's ordinary Options
updates the preference for the input method currently in use. An idle connected
controller does not take over from touch. Controller/keyboard inherit the existing
Celeste setting on their first run, unless you have already chosen a mode here.

**Toggle behaviour** offers:

- **Default · reset with Celeste:** normal game resets clear toggled grab,
  including after death. Switching input methods also clears it.
- **Until untoggled:** a toggled grab stays on across death and map changes.
  Each input method keeps its own toggle when switching away and back. Press Grab
  again to release. Changing that method's grab mode, changing Toggle behaviour,
  or quitting the game clears it. It is not restored across app launches.

All Grab buttons, including duplicates and shoulder regions, feed the same
original input. The Grab icon reflects the game's effective state.

### Controller prompts and light colours

**Button symbols** offers Automatic, Xbox, PlayStation, Nintendo Switch and Stadia.
Automatic uses the type of the SDL controller selected by Celeste, including
DualSense. A manual choice changes symbols, while bindings stay the same.
Keyboard and touch prompts still follow their own input methods. An explicit
prompt override from a mod takes precedence.

Celeste's original colour requests still go through FNA and SDL to controllers
with a light bar. Cabrillo remembers the latest requested colour and reapplies
it after a late connection, changing the selected controller, or returning to the
foreground. A prompt override does not change these colours. Virtual-controller
checks cover this path; physical DualSense colours remain a device test.

### Feather follows finger

The experimental **Feather follows finger** switch is now also in Behavior and
can be changed during play. It shares the existing **Cabrillo extras** preference.
Save applies it without restarting the game; begin a fresh touch after closing
the editor. The original speeds, turning and neutral zone are unchanged.

Visibility can follow the active input source, stay on, or turn off touch controls.
Action haptics and direction-change haptics are separate options; hardware support
varies. Overall and individual opacity can be adjusted independently.

Crouch Dash and Quick Restart feed the original Celeste inputs. Celeste's own
Crouch Dash Mode still applies: in Hold mode it is a modifier for Dash. Quick
Restart uses the game's normal confirmation behavior.

## Experimental tap and swipe

Choose the **Tap / Swipe** preset in Behavior, then adjust the gesture region.
The movement joystick remains separate; Mirror supports the opposite hand.

During gameplay, contact immediately holds Jump. Crossing the swipe distance
triggers one Dash in one of eight directions. Dash aim is separate from joystick
movement. Lift before the next swipe. Lifting releases Jump. Celeste retains its
ordinary jump height, dash speed, acceleration, timers and physics.

A swipe starts with a jump. For precise dashes that must not also jump, use the
button or split presets. The swipe threshold is adjustable in screen points.
Grab, Pause and Journal remain buttons. In menus, releasing a tap confirms;
swiping goes back without confirming first. If **Feather follows finger** is on,
its flight gesture takes priority over the action region. Pause, death, scene and
input-source changes clear held gestures and require a new contact.

This mode is experimental. Local checks verify the input contract; physical
comfort, accidental swipes and precise platforming need device testing.

## Keep and share layouts

Export the draft to Files/iCloud. Import opens a preview and then a draft; it does
not replace the saved layout until Save. iPhone and iPad retain separate layouts.
Cabrillo's JSON schema1 preserves its controls and behavior. Morro's current
`.celestetouch` D3 version2 documents can also be imported and converted to the
full display; their separate phone/tablet layouts are selected automatically.
Cabrillo exports its own format because Morro's D3 format does not describe the
experimental gesture region or larger control count.

## Morro comparison

Reviewed against [Morro source at cc02b0c](https://github.com/hmcneill46/morro-celeste/tree/cc02b0cc697bd620c0dc864d4af3c60d79a95e85).

| Morro capability | Cabrillo build57 |
| --- | --- |
| Fixed/floating movement, acquisition region | Both, editable region |
| Separate/split actions, four orientations, swapped halves, sliding | All supported |
| Circle/rectangle controls, shoulder Grab | Every action button; wide rectangular Grab |
| Duplicates and four extra actions | Up to24 total controls; all seven action kinds |
| Hold/Invert/Toggle by input source | Separate touch/controller/keyboard choices |
| In-game changes | SwiftUI editor from Pause, including feather/grab/prompts |
| Controller prompt choice and automatic family | Automatic plus four manual families, including DualSense recognition |
| Visibility, global/per-control opacity, action/direction haptics | All supported |
| Move, resize, mirror, undo, reset, delete | Draft editor with explicit Save/Cancel |
| Layout import/export and preview | Files/iCloud; Cabrillo and Morro D3 v2 imports |

Morro's MIT attribution is retained. Its device acceptance is separate from
Cabrillo's testing.
