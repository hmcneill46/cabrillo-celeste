# Build36 — restore Motion Smoothing startup

25 September 2026. Version 0.19.1, `launcher-visibility-20260925-36`.
See [the ledger](VISIBILITY_BUILD_36_EVIDENCE.json) and
[build35's phone failure](PLATFORMS_BUILD_35.md#phone-motion-smoothing-failure--later-on-25-september).

## Cause and correction

Two build35 iPhone15ProMax/iOS26.5 exports pass the 26 JIT checks and catalogue
quiescence, then fail on the first managed frame. Motion Smoothing's generated
Engine.Update cannot call protected Engine.OnSceneTransition or FNA Game.Update.
The failure occurs with Cabrillo targeting either60 or120Hz. The owner reports
startup succeeds with the mod disabled and120Hz enabled; that control is an owner
observation, not inferred from the two failed-session exports.

The iOS15 native rebuild omitted an accepted Mono metadata correction from
`sj-helpers/build_runtime.py`. The older host archive retained it, so build35's
host PASS missed the device regression. The correction honors an explicit
IgnoresAccessChecksTo assembly grant for protected members. Absent and incorrect
grants still reject non-public member access.

Build36 restores the exact accepted `class.c` content, SHA256
`c7630e2d48e3b2b3231b53777ff8667a52a798cec72f6f9e7d9e978a1e1841b0`.
Only `class.c.o` changes in Mono; its other259 archive members, fifteen other
native archives and all201 managed assemblies remain byte-identical to35.
Thus the35 touch polling repair,34 precision repairs and all save/backup features
remain. Minimum iOS15 and first-frame reveal are unchanged. Build35 is preserved.

## Validation

- A host runtime using build35's original metadata source reproduces the exact
  OnSceneTransition MethodAccessException at60 and120 with original Motion
  Smoothing1.8.0. The corrected source passes Fast/Fancy60/120 gameplay, touch,
  resume, save and normal Quit.
- Both metadata sources run36 field/method cases: exact, missing and incorrect
  assembly grants, including private/internal/protected/private-protected/public
  access. The broken control has the expected limited behavior; the restored
  rule passes all granted accesses and retains all denied controls (72 cases).
- All nine accepted Mono source patches were compared with the earlier source
  receipts using read-only access. No other omission was found in that set.
- `RuntimeValidation.json` pins those receipts; the package validator rejects
  changed test sources, receipts, compilation dependencies or unrelated archive
  members. iOS15 deployment floors and fresh matching executable/dSYM pass.

Host execution does not establish physical120Hz pacing or broad mod compatibility.
The iPad build35 base-game pass remains scoped to that build. The owner reports build36 launches and plays normally on the phone with the
requested mod/120Hz setup. Its Results folder was still empty when checked;
frame timing and runtime-error review remain pending. The installed iPad36 has
passed its native JIT checks; managed gameplay was not yet collected.

## Package and delivery

- IPA:24,114,019 bytes, SHA256
  `efbbfb12bf1e6095d0dfa31227913cf90f3349944bf7e9b3e31d539668064e22`.
- Executable/dSYM UUID:`A9DCB11B-22F0-37A2-A664-F377ADD16B9D`.
- Artifacts:`artifacts/cabrillo-build36-final`; frozen source manifest included.
- Native correction receipt:`.build/visibility-runtime36-a/receipt.json`.
- Exact35 managed receipt:`.build/platform-managed35-b/receipt.json`.
- Six files confirmed uploaded to `Celeste JIT Tests/0.19.1-build-36`; byte hashes
  match. Whole cloud test folder873,639,006 bytes at delivery, under1GB. Every
  older Results folder remains.
- Installed over USB through TrollStore and opened on the owner's iPad (both
  commands exit0). Existing app data and the imported game are preserved.

Use `tools/build_visibility_runtime.py`, `tools/build_visibility.py` and
`tools/verify_visibility.py` for this lane. Never alter a packaged build identity
or restore historical UUIDs. Next identity37 is reserved for the separately
requested Everest stable upgrade. No commit, push or GitHub write was performed.

## Phone evidence — later25 September

The owner's build37 export also retains a complete build36 session. Its full
BuildInfo matches the delivered36 IPA. On iPhone15ProMax/iOS26.5, standalone
StikDebug activation passes26 native checks, with catalogue requests quiesced.
Everest1.6531 and original MotionSmoothing1.8.0 load with the canary (two selected
archives; five built-in/selected identities). The first callback reveals the game.

Old Site, Prologue and Summit rooms run; the owner had already reported normal
visual gameplay. Four background/resume cycles total67.49 seconds. Normal Quit
verifies slot1, completes shutdown stage8 and detaches the managed thread after
18,982 callbacks. The native foreground heartbeat arrives5.17 seconds later.
JIT failures, unowned code, managed errors and patch rejections are all zero.
This passes the scoped base-game/Motion Smoothing startup/gameplay/save/resume/
Quit gate. It also provides physical evidence for the standalone StikDebug route
while Cabrillo is hosted by LiveContainer.

The requested native rate is120Hz. An early window reaches118.66 callbacks/sec,
but later windows mostly measure about60; sustained120FPS is not established.
The export does not include the mod's in-game FPS/renderer settings, so no cause
for that rate is assigned. No new touch-input claim is made from this run's
controller use. The native save-manager/backup/restore gate remains pending.

Source export:3,451,426 bytes, SHA256
`999d4ad11dfdb16c9b1043a048a8449d7b659b336b3a5e8237de10e8f9a21489`.
It is preserved in build37 Results and a private evidence copy. The earlier
empty-Results observation is superseded;36's own Results can remain empty.
