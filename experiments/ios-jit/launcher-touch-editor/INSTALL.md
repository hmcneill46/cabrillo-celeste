# Installing build56 for testing

Finish any active game using normal Quit. Replace Cabrillo in its existing
LiveContainer slot, preserving its data container and imported shortcut49.
Use a fresh JIT launch. The first start may rebuild the prepared cache from the
retained original game files. A second fresh-process start should reuse it.

Open Settings → Controls → Customize touch controls. Rotate landscape and check
the actual-size layout, 16:9 guide, drag/resize and placement at the display edges.
Move or hide the toolbar; Details returns to the complete editor.
Check Save/Cancel, a split
region, duplicate Jump, rectangular Grab and left/right Mirror. Then test in-game
Pause → Touch controls, changing Hold/Toggle/Inverse. Add Crouch Dash and Quick
Restart and check normal game behavior. Keep Crouch Dash Mode at Press for a
single-button crouch dash, or use its normal modifier behavior in Hold mode.

Try the optional Tap / Swipe preset: hold to jump, swipe once to dash, lift to
release, and repeat. Movement and dash aim should be independent. In menus, tap
and release confirms; swipe goes back. With Feather follows finger enabled,
feather steering takes priority over the gesture region.

Check normal Quit, relaunch and layout persistence. Export diagnostics to this
build's Results folder. Local host/simulator checks do not establish device feel,
physical multi-touch/haptics, native live presentation or sustained120Hz output.
