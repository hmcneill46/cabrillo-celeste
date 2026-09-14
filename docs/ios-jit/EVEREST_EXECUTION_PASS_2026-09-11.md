# Build 13 physical Everest acceptance

11 September 2026. **Bounded real Everest, map/code ZIP loading, hooks, Lua,
saves and background/resume pass on the target iPhone.** The owner reports all
visible checks passed. See [the evidence](EVEREST_EXECUTION_PASS_2026-09-11_EVIDENCE.json).

The iCloud Results export matches the exact delivered IPA BuildInfo, native
binary, all packaged framework/Everest assemblies, both imported ZIPs, session
script and 140 frozen build inputs. Its untouched SHA256 is
`58c932839fc7ea41ca17c6c80ab2e7df51a9e8797656af1b57131fd7046a0f29`.
Raw export, validator, structured events and console tail are preserved under
`.build/ios-jit/device-evidence/2026-09-11/build-13-pass/`. No debugger attachment
or direct phone collection was needed.

The owner used ordinary Everest menus, played Prologue, then entered the mod
room (`area=11; room=test`). This is valid: the actual loader registered both
modules, used the code mod's EverestModuleAssemblyContext, created/rendered its
custom entity and executed both generated hook kinds. The logs record:

- 11,174 native callbacks, 11,176 sampled rendered frames and 7,004 level frames.
- 50 normal hooks and 50 IL hooks, including 11 jumps after resume.
- 196 touch presses and releases; GPU readback and all nine game checks pass.
- 34.628 seconds background, returning to the same process with audio and hooks.
- Real Everest NLua calling managed C# and returning 42 on ARM64.
- The floating-point probe reproducing mixed-width 0 and corrected 15.000001.
- Native FMOD 1.10.09, XML settings/slot-0 readback and genuine YAML mod save
  readback: prior 0, written 50, read back 50.
- Fifteen worker starts/ends, zero remaining native worker pools, hook cleanup,
  clean managed worker/main detach, PASS UI and delayed foreground liveness.
  Export occurred 17.441 seconds after the result.

All 15,891 JIT completions belong to prepared code allocations. There are zero
JIT failures, unowned completions, managed errors or rejected patches; 43 hook
patches complete. Code reservations are 22,102,016 of 67,108,864 bytes across
179 allocations. Peak sampled physical footprint is 1,469,171,736 bytes. This
is a bounded test, not a sustained benchmark or an SJ memory estimate.

**Fresh-process mod-save reload is not present in this export.** It contains
one session with a cold prior value of zero. Same-process disk readback passes;
do not infer a second process from the owner's general “all pass” report. Carry
the reload check into build 14's update/import test, where the saved value 50
also checks retention of the existing guest's data.

Proceed with [persistent content import and the small IPA](CONTENT_IMPORT_NEXT.md)
in an independent source/staging lane, retaining build 13's exact sources,
symbols and delivery snapshot. Keep the same guest identifier for the update.
Arbitrary mods, full on-device original-IL preparation, LuaCutscenes and
Strawberry Jam remain unaccepted. The AOT workspace stays untouched; no commit
or push was made.
