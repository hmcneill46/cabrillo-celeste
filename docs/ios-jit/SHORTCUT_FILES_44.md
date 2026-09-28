# Helper startup and natural shortcut completion — revision44

26 September2026. Shortcut-only update for installed app43. Both Apple-signed
import variants are packaged; no44 IPA is produced. No GitHub/public IPA write is
authorized. Four source inputs are frozen in `artifacts/cabrillo-shortcut44-final`;
further implementation requires45.

## Physical result: superseded by45

The verified48-action phone test passes the19ms VPN hello, Replace Text and the
helper-only opening. The second Open URL crashes in LiveContainer's guest handler
while decoding a nil `open-url` value. The owner sees Home Screen and the error.
Mailbox stays1/untraced. Nothing and the workflow finish, but no native callback
is collected. No JIT/game pass occurred. Private evidence is `automatic-b` under
`.private/device-evidence/2026-09-26/shortcut44`.

[Revision45](SHORTCUT_FILES_45.md) reproduces the cause with Apple's actual content
conversion: long plain-text links are cut at the query key, whereas typed URLs
retain every byte. The provisional startup separation did not address that cause.
Keep44 frozen; use45 for further testing. The following change/validation record
is retained as historical evidence.

## Evidence and change

The first actual43 phone run opens the correct cold StikDebug guest but executes
no JIT request. Shortcuts also stalls at Stop and Output before a later error
callback. The owner then tapped Cabrillo's native button with StikDebug already
running. The same PID/request returns from StikDebug, passes26 native checks while
detached, and starts Celeste through its title menu. This isolates a working direct
warm route; it is not a successful Home Screen shortcut test. See [the43 review](SHORTCUT_GUESTS_BUILD_43.md).

For a LiveContainer2 guest URL,44 first removes only app43's final `open-url` query
item and opens the same helper/data container without a JIT request. After a
two-second startup allowance, it opens the original URL unchanged, exactly once.
Standalone StikDebug retains its direct request. This avoids including the request
in the first cold guest opening. The allowance is not a readiness observation;
native JIT/detach checks and the existing timeout still decide success. Slow starts
and first-use/switch confirmations remain physical test cases.

The44 generator replaces stage-ending Stop and Output actions with nested
If/Otherwise branches and natural workflow completion. A final Nothing action
clears intermediate output. App43 already embeds the expected receipt in its
x-success URL, including inside LiveContainer's routed URL; native validation does
not need a returned output value. Existing protocol `cabrillo-39`, fresh script,
radio order, restoration presets and native JIT/detach gates remain unchanged.

LiveContainer's pinned source handles a cold scene URL differently from its warm
guest control route. Combined with the owner's warm pass, that supports separating
guest startup from request delivery. It does not prove every cause of43's cold
failure. Phone44 must demonstrate that both request delivery and return now work.

## Local controls

-42 generated branch/routing cases pass across both host variants, radio presets,
  explicit/default data containers and encoded folder names. The first opening
  has no `open-url`; exactly one opening preserves the original JIT URL.
-43 isolated Apple WorkflowKit controls pass:42 comparison cases including14
  original missing-parameter controls, plus natural completion with no output.
  Only If, Comment and Nothing actions run in that engine fixture; no radios,
  networking, external URLs or personal shortcut library writes are performed.
- Two Foundation ICU regex controls independently verify removal of the final
  request item while preserving encoded guest/data identity. Replace Text's
  parameter names are checked against pinned Cherri source. The isolated engine
  cannot load that ActionKit action, so these are not Shortcuts action executions.
- The first checker invocation accidentally omitted the comparison cases and
  failed its required37-case assertion after the one completion case passed.
  The corrected completion-only draft passed in controls-b. Controls-c then
  passed all43 WorkflowKit cases but could not find the two Replace Text actions;
  controls-d explicitly separates Foundation checks from WorkflowKit execution.
  The final receipt is `.build/shortcut44-controls-d/receipt.json`. Failed fixtures
  are retained and are not counted as complete passes.
- A separate host-only legacy Exit experiment cannot resolve that action from
  WorkflowKit alone. This is not evidence about its availability on iOS.

These checks do not execute the full iOS shortcut or establish successful
x-success delivery. Phone44 callback, cold/warm shortcut JIT, Travel/recovery and
game/Quit remain pending. No installed43 implementation input has been edited;
35–44 frozen-input comparisons pass.

## Delivery

The five-file kit is fully read back over USB at
`On My iPhone/LiveContainer/Cabrillo-shortcut44`. App43 and its data-container
identity are verified; no app replacement or save-file write occurred. Both
signed files and the guide are also confirmed uploaded at
`iCloud Drive/Celeste JIT Tests/shortcut-44`. Existing Results are preserved;
logical cloud contents are981,405,236 bytes.

- Default signed file25,557 bytes; SHA256
  `eea778517274313d068ba461a3f0273d1f8bc0df1e4e5724d7e72a89f45aeb82`.
- Standalone signed file25,532 bytes; SHA256
  `c1c8f293542c1a3d807d8982e3ac274bdd4304beefbc9eb71166d83675e31188`.

The owner imported44 as **Cabrillo**. Scoped read-only inspection of the synced
Mac shortcut records verifies all48 actions in that single named shortcut. The
previous game completed normal Quit. The subsequent cold Automatic run failed as recorded above. Use45 for the next
test; Travel/recovery and complete shortcut acceptance remain pending.
Private transfer evidence: `.private/device-evidence/2026-09-26/shortcut44`.

```sh
python3 tools/check_shortcut_files44.py --work .build/new44-controls
python3 tools/build_shortcut_files44.py --output .build/new44-signed --sign
```

Use fresh paths. Preserve every earlier package and Results folder.

Integration sources: [LiveContainer guest URL handling](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/TweakLoader/UIKit%2BGuestHooks.m)
and [Cherri text action definitions](https://github.com/electrikmilk/cherri/blob/d96eee9c7768649d441df0166b68a7e3c742690c/actions/text.cherri).
