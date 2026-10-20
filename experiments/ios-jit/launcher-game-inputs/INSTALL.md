# Installing build53 for testing

Replace Cabrillo in its existing installation/data container, preserving saves.
Keep the existing revision49 shortcut and JIT provider setup. Import one clean
Celeste FNA1.4.0.0 ZIP from itch.io, Steam or Epic and use a fresh JIT-enabled app
process. See `docs/CELESTE_INPUTS.md` for exact covered downloads and ZIP layouts.

A prior standard import can be prepared again from retained originals without
selecting a ZIP. The first build53 launch uses a new preparation recipe; later
launches verify and reuse that cache. Edition-specific caches do not share code.

Check base-game input/audio, save, suspend/resume and normal main-menu Quit, then
export diagnostics. Try another edition only after closing the completed app
process. Keep device evidence distinct from the automated Mac integration tests.
