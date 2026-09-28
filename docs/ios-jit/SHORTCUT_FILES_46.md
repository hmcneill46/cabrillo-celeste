# Explicit URL connections — shortcut revision46

26 September2026. Shortcut-only correction for installed app43 /0.22.3.
The app, its data container and runtime remain the existing versions. No46 IPA is
produced. No GitHub write or public IPA distribution is authorized.

## Phone result: JIT/game start works; app43 completion status fails

The owner imported46; the latest scoped read-only synced check verifies a single
Cabrillo containing all45 exact46 actions. The owner reports automatic return,
green JIT status without tapping Enable, and a successful Celeste start.
A Wi-Fi screenshot independently shows the green native-pass status and enabled
Run Celeste alongside a contradictory Home Screen launch timeout.

The Home Screen indicator first kept spinning, then reported JIT was unconfirmed.
App43 requires an additional Shortcuts callback after actual native success and
debugger detach. A focused host regression reproduces that false timeout when
the callback is absent. Separate [app47](SHORTCUT_COMPLETION_BUILD_47.md) removes
that extra completion requirement while retaining native execution/detach checks
and token-matched networking receipts. Keep the exact46 shortcut for47.

Raw evidence is in `.private/device-evidence/2026-09-26/shortcut46`. Network
screenshots work, but both CoreDevice and native AFC log transfers timed out.
No fresh journal, level-input or normal-Quit acceptance is claimed from this run.
The independent export and Travel/recovery remain pending.

## Observed failure and change

The owner's exact imported45 shortcut fails immediately, below its final
LiveContainer URL, before Cabrillo opens. A read-only check of the synced shortcut
verifies all45 actions and no duplicate Cabrillo. The same imported shortcut run
with Apple's Mac `shortcuts run Cabrillo` command exits1 with:

> Make sure to pass a valid URL to the Open URL action.

Revision45 left the `WFInput` of both Open URL actions unset. Its branch interpreter
incorrectly supplied the previous action's output automatically. Revision46 binds
each Open URL input explicitly to its preceding URL action using an ActionOutput
attachment with that action's UUID. This keeps the value typed as a URL; converting
it back to plain text would reintroduce the long-query truncation reproduced in45.

The Home Screen and dynamic JIT routes both use the corrected connection. Each
variant still has45 actions. Conditions, radio stages/presets, native callback
protocol `cabrillo-39`, natural completion and the single fresh JIT request remain
unchanged. The app still verifies actual native JIT and debugger detach.

The action/input relationship is consistent with [Apple's URL-action guidance](https://support.apple.com/guide/shortcuts/use-another-apps-url-scheme-apd68802640c/ios)
and the explicit `WFInput` parameter in the pinned
[Cherri Open URL definition](https://github.com/electrikmilk/cherri/blob/d96eee9c7768649d441df0166b68a7e3c742690c/actions/web.cherri).

## Validation and its limits

- 36 generated branches pass for both host variants and all radio presets.
- 12 broken connections are rejected: missing input, text interpolation and a
  reference to dictionary output at each opening in both variants. The interpreter
  now resolves only the explicit input; it no longer assumes adjacency supplies it.
- 37 retained Apple WorkflowKit condition/completion controls pass, including12
  original missing-parameter failures.
- 18 retained Apple content-conversion controls pass, including four original
  long-link truncation failures. The native app43 URL builders supply these cases.
- The original45 failure is separately reproduced by the installed Apple Shortcuts
  runner. The owner subsequently confirms the positive46 phone handoff/JIT and
  game start, with the app43 completion defect described above. The fixtures
  themselves do not establish that physical result.

An isolated attempt to submit an in-memory workflow to Apple's background runner
was rejected for a required entitlement; that path was stopped. No entitlements
were changed, no platform restriction was bypassed, and no personal shortcut
database was written. The unavailable phone network tunnel also prevented a new
screenshot; the owner's precise report and local reproduction establish the error.

```sh
python3 tools/check_shortcut_files46.py --work .build/shortcut46-controls-new
python3 tools/build_shortcut_files46.py --output .build/shortcut46-signed-new --sign
```

The checker reuses the exact frozen45 Apple fixtures and six frozen app43 URL
source/header files. Together with the two46 tools and BuildInfo, all11 inputs
are frozen in `artifacts/cabrillo-shortcut46-final`. Further implementation needs47.
Delivery hashes and status are in [the evidence ledger](SHORTCUT_FILES_46_EVIDENCE.json).

## Owner test

Use `iCloud Drive/Celeste JIT Tests/shortcut-46/Cabrillo.shortcut`; keep app43.
Replace the old shortcut, retaining exactly the name Cabrillo. Close both
LiveContainer apps, then run Cabrillo once from Shortcuts with Wi-Fi on and
Automatic selected. Allow any Open prompts. Leave the native Enable button alone
during this test so the automatic route can be distinguished from the accepted
manual route. Report the last screen or error; success requires returning to
Cabrillo with its native JIT status green.

After Automatic passes, continue Travel/recovery and normal game/Quit. Keep an
independent diagnostics export in `shortcut-46/Results`. The older save-manager,
iPad38 and sustained120Hz gates remain separate. No earlier Results is removed.
