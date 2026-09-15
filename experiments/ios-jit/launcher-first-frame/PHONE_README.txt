CABRILLO 0.16.2 / BUILD32 — EARLIER GAME PRESENTATION

Build31's two successful phone runs showed Celeste drawing behind the native
loading screen for another 17.7 seconds, until the title menu. This build shows
the game immediately after its first successful draw and existing GPU readback.
Celeste's own opening fade/loading screen can now be visible before the menu.
It is still loading at that point; audio does not by itself mean loading is done.

Startup details are always visible, with no expandable panel or scrolling during
game startup. The bar counts real archive/folder work when available and shows
an activity segment for uncounted phases. Large individual mod operations can
still pause the text/counts. Error Export and file-preparation cancellation remain.
The game/runtime/mod-loading bytes are unchanged from your tested build31.

FOCUSED CHECK (no repeat browser suite or separate export after each step)
1. Update the existing LiveContainer slot1 entry with the build32 IPA. Preserve
   its data container, game files, mods and saves. StikDebug stays in slot2.
   Launch with JIT OFF, saved script blank, Fix File Picker ON. Close the old
   process; use the app's fresh PID-specific inline request and detach before Run.
2. Run your existing large mod set. Check that the stage, current mod, bar and
   counts fit in landscape. The loading display should have nothing to expand
   or scroll, and touching it should not trigger anything in the covered game.
3. Watch the transition: Celeste's own fade/intro/loading view should take over
   before the title menu, with no prolonged audio playing behind Cabrillo.
   A brief initial black fade is part of the game. Report a lasting blank screen,
   lost input, a native screen covering audible game activity or anything odd.
4. Briefly background and return during loading if convenient. Once the menu
   arrives, check movement/jump/audio and the saved room, then normal main-menu
   Quit. Wait five seconds on the returned native launcher.
5. Export diagnostics ONCE to this build's Results folder and report the visual
   result. If you also try a fresh-process warm run, one export after both is fine.

If a failure occurs, use Export diagnostics on the error screen. If stuck, close
and reopen the app, then export before another run; prior journals are retained.
Keep build28 as the accepted fallback, build31 and all Results folders.

Files > iCloud Drive > Celeste JIT Tests > 0.16.2-build-32 > Results
This is a private phone test; build32 physical acceptance is pending.
