# Build 14 physical original-game import and Everest pass

11 September 2026. **The small build 14 app imports the original itch.io FNA
ZIP and passes bounded Celeste + Everest gameplay on the target iPhone.** The
owner reports all checks passed, and that the previous save survived before
they deliberately deleted it. See [the evidence](CONTENT_IMPORT_PASS_2026-09-11_EVIDENCE.json).

The iCloud Results export contains one successful build 14 import/game session.
Its build metadata matches the delivered 0.7.0 (14) IPA. The local validator
checks the exact IPA, executable, 200 framework/Everest assemblies, script
template, content manifest, two canary ZIPs and all 137 frozen build inputs.
The untouched export is 54,964,114 bytes, SHA256
`b5999f5fb6b0ea75e4decba4850df444070e5f0c42d0e1b9046783a8a53f6687`.
Raw export, validator, validation result and extracted sessions/console tails
are preserved privately at
`.build/ios-jit/device-evidence/2026-09-11/build-14-pass/`.

## What the phone verified

- The chosen `celeste-win-opengl.zip` is exactly the supplied original owner
  archive: 875,540,825 bytes, SHA256
  `d1072fe39c086ed1cde0b0887f68ee8032b101822ddf55e6ee806b5e736896c3`.
  It was selected after enabling the guest's LiveContainer **Fix File Picker**
  setting. No replacement IPA or repacked game archive was needed.
- The managed import worker verified/extracted all 1,216 Content files,
  totaling 1,158,665,183 bytes, into the persistent game library in **4.638
  seconds**. This measures the managed import phase, not download, Files copy,
  JIT preparation or total launch time. It completed off the main thread,
  detached cleanly and released the app-owned staged ZIP.
- Both existing canary ZIPs were already verified before game import, with
  no mod-import events in this process. Existing settings also loaded. This
  supports retention across the build 13-to-14 transition.
- Actual Everest 1.6458.0 registered both canary modules, loaded the code ZIP
  in its normal assembly context and rendered the custom entity in the test
  room. Twelve normal hooks and twelve IL hooks executed, four after resume.
- All 26 native and nine game/graphics assertions passed. The run recorded
  6,406 frame callbacks, 3,715 level frames, 2,315 movement frames and 167
  balanced touch presses/releases. Real NLua called managed C# and returned
  42; native FMOD 1.10.09 initialized and audio remained active after resume.
- The same process returned after 36.571 seconds in the background. Settings,
  slot-0 XML and the canary's YAML mod sidecar passed disk readback. The mod
  counter was prior 0, written 12, read back 12.
- All eleven game workers finished, native worker pools reached zero, hooks
  were removed and managed threads detached. PASS and delayed foreground
  liveness are present; the export was made 20.881 seconds after PASS.

All 15,208 JIT completions belong to prepared allocations. There are zero JIT
failures, unowned completions, managed errors or rejected patches; 43 hook
patches completed. Code reservations reached 21,495,808 of 67,108,864 bytes.
Peak sampled physical footprint was 1,337,624,504 bytes. This bounded canary
does not establish sustained performance or Strawberry Jam memory capacity.

## Save observation and remaining retention check

The owner explicitly reports the old save **survived and was then deliberately
deleted**. Record that as an owner-observed successful retention followed by
intentional deletion, not as an importer or update failure. The logs do not
independently record that deletion or prove the former build 13 counter of 50
was reloaded. The current 0 → 12 round trip is valid new save evidence; do not
restore an intentionally deleted save or interpret zero as data loss.

The sole successful build 14 session has `content_library_ready: reused=False`.
Its previous-session section contains two earlier build 14 startup/picker
sessions and two build 13 sessions; none supplies a cached build 14 run.
**Fresh-process cached-content reuse and a post-import same-guest app update
remain unverified on the phone.** Host reuse and simulator update tests already
pass, and existing phone mods/settings survived this transition, so development
can continue while this final retention check is folded into the next phone
handoff. Do not mark the entire physical update matrix complete.

For that check, update the existing guest while preserving its data, launch
fresh, import nothing, enable the current process's JIT via LiveContainer 2
and run. Require `reused=True`, both old mods retained and a nonzero previous
canary counter (12 after this run, unless subsequently changed/deleted), then
save/readback and export. A fresh launch of build 14 alone can verify reuse;
the next actual IPA update additionally verifies container retention. Keep
**Fix File Picker ON**, Launch with JIT OFF and the script field blank.

## Development handoff

Use the accepted `experiments/ios-jit/content-import/` as the next stage's
baseline, preserving its delivered IPA, sources, symbols and snapshot. Keep
the independent `content-picker/` build-15 simulator experiment marked draft;
it was not delivered or accepted and is not needed for this resolved issue.

The next development stage is actual LuaCutscenes script/coroutine execution
and real Strawberry Jam helper compatibility through Everest, followed by the
Beginner lobby and Bing. A Lua-to-C# arithmetic callback alone does not validate
LuaCutscenes. Verify the original locked mod ZIPs and preserve normal loader,
dependency, hook and save behavior; do not substitute the AOT implementations.
Include the retained-content check above in the next small IPA test.

The private 22.8 MB IPA still contains prepared game IL and linked iOS FMOD.
On-device original-IL preparation and public distribution remain separate work.
No new IPA was required for this results review. No accepted source, AOT file,
original game input or delivered artifact was changed; no commit or publication
was made.
