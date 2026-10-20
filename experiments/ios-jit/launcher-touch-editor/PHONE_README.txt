Cabrillo 0.27.0 / build56 — SwiftUI touch controls

Replace the app in its existing slot and KEEP its data container and shortcut49.
Finish an active game with normal Quit first. Use fresh JIT when relaunching.
Your retained original game files may need one automatic preparation rebuild.

Settings → Controls → Customize touch controls:
- Drag, resize, circles/rectangles, duplicates and extra buttons.
- Four split Jump/Dash orientations, sliding and Mirror.
- Fixed/floating joystick, opacity and haptics.
- Hold/Toggle/Inverse Grab, separately for touch/controller/keyboard.
- Files/iCloud layout export and import preview (including Morro D3 v2).

Rotate landscape for a full-screen, actual-size editor. Buttons can use the whole
display, edge to edge. The 16:9 guide marks the game image; drag the toolbar
handle or hide it if it gets in the way. Details returns to the full editor.

Pause → Touch controls opens the same SwiftUI editor during a game.
Save applies the draft; Cancel keeps your saved layout.

Optional Behavior → Tap / Swipe preset:
Touch/hold to jump, swipe once to dash in that direction, then lift before the
next gesture. Move with the other thumb; Mirror swaps sides. A swipe starts with
a jump, so use buttons for precise dashes without jumping. In menus tap/release
confirms and swipe goes back. Feather follows finger takes priority in flight.

Test a normal Quit and fresh-process return. Export diagnostics to Results.
The experimental mode's physical feel still needs your device feedback.
