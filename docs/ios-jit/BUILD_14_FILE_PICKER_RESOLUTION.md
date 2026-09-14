# Build 14 file picker: LiveContainer setting resolves selection

11 September 2026. **The owner confirms enabling LiveContainer's Fix File
Picker resolves the stalled selection.** The subsequent export also
[passes original-ZIP import and Everest gameplay](CONTENT_IMPORT_PASS_2026-09-11.md).
No replacement IPA was needed for this issue. The remaining text records the
initial picker diagnosis and instructions before that successful run.

The owner could see the locally downloaded original Celeste ZIP but neither
selecting it nor tapping Open dismissed the picker. Their export matches the
exact delivered build 14 BuildInfo. Both existing mod ZIPs are retained. Its
current session has ten events, no content staging/progress/error event, and
no JIT execution. It also contains previous sessions, so older successful game
logs must not be mistaken for a build 14 import pass. The build 14 logging did
not record picker delegate entry; the export alone cannot establish whether a
delegate callback or security-scoped access stalled.

The owner then enabled **Fix File Picker** in the guest's LiveContainer settings
and explicitly confirmed it fixed the issue. This is LiveContainer's documented
compatibility setting, not evidence of a bad ZIP, insufficient JIT, or a game
runtime failure. The supplied FNA archive does not need to be renamed, unzipped
or downloaded again.

Setup: close the Celeste guest, long-press its card in **LiveContainer 1 →
Settings → Fixes → Fix File Picker**, enable it, then reopen. Keep Launch with
JIT OFF and the JIT script field blank; StikDebug remains in LiveContainer 2.
Use the current Fixes-section option. There is also a distinct legacy file-picker
option, which changes copy/inbox behavior; the observed resolution does not
require changing that option or the global LiveContainer bundle identity.

References: [official app settings](https://livecontainer.github.io/docs/guides/app-settings),
[LiveContainer picker hooks](https://github.com/LiveContainer/LiveContainer/blob/main/TweakLoader/DocumentPicker.m).
The current hook adjusts the document service's host identifier using the host
application entitlement. The legacy hook separately forces import-copy and
multiple-selection behavior. These explain the relevant compatibility paths;
the exact on-device hook configuration was not captured in build 14's export.

Build 14's remaining gates are unchanged: finish original-ZIP import, play the
Everest test map with audio/touch/hooks, background/resume, save and export. Then
update the same guest with the same small IPA, launch fresh without reimporting,
and confirm game content, both mods and the saved counter survive. Put exports
in `iCloud Drive/Celeste JIT Tests/0.7.0-build-14/Results`.

An additive `FILE-PICKER-FIX.txt` is in that iCloud folder. The delivered IPA,
original instructions, hashes, symbols and source snapshot remain unchanged.
Exploratory `experiments/ios-jit/content-picker/` and build-15 simulator outputs
were prepared while investigating; they are **draft, not delivered or accepted**.
They must not supersede the active build 14 phone test. No commits or publishing
were made. Preserve the new diagnostics and resolution evidence privately at
`.build/ios-jit/device-evidence/2026-09-11/build-14-picker-failure/`.

The exploratory UI harness built and ran, but actual-picker automation could
not tap its accessibility element. Its folder-button test passed; do not claim
a complete picker regression pass or use this draft as a verified release.
