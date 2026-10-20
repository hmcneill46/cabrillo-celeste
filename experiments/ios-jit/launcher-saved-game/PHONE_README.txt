Cabrillo 0.26.1 / build55 — saved-game startup repair

This fixes the startup rejection seen in54 after the temporary import ZIP was
removed. Your retained originals can prepare the game without another import.

Replace the existing Cabrillo app, keeping its data container and shortcut49.
Start normally and allow the first cache rebuild to finish. Please also check
a second fresh-process launch, then use normal Quit and export diagnostics.
In Settings → Cabrillo extras, turn on “Feather follows finger”, then start
Celeste with JIT as usual. The toggle starts off and remembers your choice.

When flying with a feather, touch away from the buttons and drag to steer.
Lift to coast. A small faint circle around Madeline also gives neutral input
when your finger is inside it, to avoid jitter as she reaches the target.
The original game controls all speeds and turning; it does not stop in midair.
Jump/dash/grab/pause remain separate; ordinary movement uses the usual joystick.
Start a fresh touch after entering flight, resuming or switching input devices.

Please try feather steering, lifting, pause/resume and returning to ordinary
movement, then normal Quit. After restarting you can turn the option off to
compare. Keep your existing Motion Smoothing choice; there is no extra mod to import.
Put an Export diagnostics in this build's Results and report how the control feels.
The game-file compatibility improvements from53 are included.
