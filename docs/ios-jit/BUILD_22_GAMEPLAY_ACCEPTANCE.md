# Build22 phone gameplay and save evidence

Reviewed 12 September 2026. **The recorded gameplay and save readback pass.
Final shutdown and a subsequent game/save reload remain unverified.**

The owner reports the test passed, and later could not remember whether
“SESSION SAVED” appeared before closing the app. There is no need to infer a
crash from the missing completion marker. Keep build19 as the previously
accepted complete-shutdown fallback until the next lifecycle test.

## Exact evidence

- Input: `0.11.2-build-22/Results/CelesteJIT-6b626dd9-ba01-4afc-a019-f3c5b65e663a.diagnostics.json`
  in the established iCloud test folder.
- Private preserved copy: `.build/ios-jit/device-evidence/2026-09-12/build-22-results/`.
- Export: 4,152,214 bytes; SHA256
  `05b9b03285f37cba12c94ee787f04be3de9c88168b2cf375103a10bfe69d79ae`.
- Played session: `34e1038b-adc2-45e5-84b5-b82b0b060a3f`, PID2394.
  The current export session is a separate fresh process that only opened the
  launcher and exported logs. Two other historical sessions are failed build21
  runs; their failures must not be assigned to build22.
- Every recorded build field matches the delivered `launcher-reflection-20260912-22`
  receipt, including adapter, MonoMod.Utils, FNA and script hashes.
- IPA SHA256: `b9a89008136a1dbf0e409c5fd22095df876a1430992a5110348a6cf5f88dd17e`.
- Hardware: iPhone16,2, iOS26.5. LiveContainer/StikDebug version text remains
  the earlier owner-entered values; this is not a new installed-version query.

Reproduce the checks with
`python3 experiments/ios-jit/product-audit/validate_build22.py`.
The sanitized results are in [the evidence receipt](BUILD_22_GAMEPLAY_EVIDENCE.json).
The delivered app, source snapshot and cloud kit are unchanged.

## What passes

There are 26 native checks and 13 graphics/save/resume checks, with no recorded
JIT failures, managed exceptions, rejected patches or frame failures. All 56
enabled ZIPs and 58 selected/built-in metadata identities match. Normal mode
is active, with no regression map shortcuts.

The session runs for **1,427.946 seconds (23 minutes 48 seconds)** from game
startup returning to the owner tapping Finish: 82,199 native frame callbacks,
218 recorded player jumps and 21 room transitions. The sequence includes the
Beginner lobby, area44 `intro → a-00 → a-01 → a-02`, another map, and several
gym rooms. Area44's sequence is consistent with the prescribed Paint retest
and pinned content; the phone currently logs numeric area IDs rather than SIDs.
Add SID/mode to future room events instead of depending on this inference.

Three suspend/resume cycles pass. The longest recorded background interval is
27.55 seconds. Earlier resumes have subsequent jumps; the last interval does
not have a recorded jump afterward, so the exact “jump after the long pause”
step is not established.

The ordinary save worker completes. Settings write/readback passes; slot 1
write/readback passes with 162,410 bytes and 37 deaths. The mod canary reads
prior counter 102, then writes and reads back320. This demonstrates persistence
of prior mod data and current in-process readback; it does not demonstrate a
new game process reopening the just-saved320 or the same checkpoint.

The last sampled runtime before teardown uses 235,503,616 of 536,870,912 code
bytes (about 224.6 / 512 MiB). Peak sampled physical footprint is 4,062,040,080 bytes
(about 3.78 GiB). These are bounded-session observations, not an indefinite-play
budget guarantee or proof of the memory requirement of every mod.

## Shutdown needs a clearer test

Finish is explicitly logged as the stop reason. Save verification succeeds,
then the journal continues for about 9.5 seconds while hook/JIT counters grow.
It ends before `game_checks_pass`, main-thread detach, `graphics_bridge_pass`
or the result screen. No shutdown exception is recorded.

The source provides a plausible explanation for continued work: game disposal
runs Everest's detour undo callbacks, which can rebuild hook chains and compile
additional methods. The export cannot establish whether this was still normal
teardown, a stall, an owner close, or a subsequent termination. Do not classify
it as a confirmed shutdown crash, timeout, or clean completion.

The next lifecycle build should log entry/completion and elapsed time for save,
external-loop end, content release, game disposal, platform shutdown and native
return, then test the normal Quit command. Keep save success separate from
complete shutdown. A physical acceptance test must wait for a visible native
completion state, export in that process, then restart and reopen the saved
slot. Do not force-kill after a fixed teardown time or claim a successful save
merely because a quit request was received.

The independent native backbuffer-read issue described in
[the build22 engineering report](LITERAL_FIELDS_BUILD_22.md) remains open.
It did not cause a recorded failure in this phone run.

The next product design is in
[the native launcher roadmap](NATIVE_LAUNCHER_ROADMAP_2026-09-12.md).
