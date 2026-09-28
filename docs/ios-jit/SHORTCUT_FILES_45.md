# Preserve complete typed URLs — shortcut revision45

26 September2026. Shortcut-only correction for installed app43 /0.22.3. No45 IPA
is produced; app/game files remain unchanged. Eleven source/dependency inputs are
frozen in `artifacts/cabrillo-shortcut45-final`; next implementation identity46.
No GitHub write or public IPA distribution is authorized.

## Phone result: failed before opening Cabrillo

The scoped, read-only synced shortcut check now verifies one named Cabrillo with
all 45 revision45 actions. The owner reports an immediate invalid-URL error below
the final LiveContainer URL. Running that same imported shortcut through the Mac's
actual `shortcuts run Cabrillo` command reproduces the identical error and exits1.
No Cabrillo/JIT handoff occurs in this test.

Both Open URL actions have no `WFInput`. The generated-branch interpreter wrongly
assumed that an adjacent URL action would supply it automatically. The earlier
Apple content-conversion checks remain valid, but did not execute this action
pair and could not catch that wiring error. [Revision46](SHORTCUT_FILES_46.md)
adds explicit typed-output references and checks that reject missing connections.
All 11 revision45 implementation inputs and its delivered files remain frozen.

## Reproduced cause

The owner imported44; all48 actions were verified before the cold test. App43
session `aa99d420-4008-41e4-a9dc-81a0acefca4e`, PID21828, passes the VPN hello in19ms
and creates an11,083-character JIT URL. The phone executes Replace Text, opens the
helper, waits and executes the second Open URL. LiveContainer then throws from
`LCHandleControlAppURL +732`: `initWithBase64EncodedString:options:` receives nil.
The owner sees the Home Screen and an error in the helper. No JIT or game runs.
Nothing and the whole44 workflow finish; no native success callback is collected.

The corresponding pinned3.8.10 source/binary decodes each `open-url` query item
without a nil-value guard. Apple text-to-URL detection reproduces exactly that
missing value: an otherwise valid long URL ends at `&open-url`, losing the equals
sign and encoded script. This explains43's cold helper opening without a request
and44's exception once the guest is running. Cabrillo's direct native request
preserves the original NSURL, matching the already-passed manual warm test.

The regression fixture uses **Apple's actual WFContentItem conversion** and the
frozen app43 native URL builders. Original plain-text cases lose long direct and
LC-wrapped script values; explicit NSURL/WFURLContentItem cases preserve every
byte. Short native success/cancel/error callback links remain exact in both paths.
An initial experiment called the lower-level generation API and returned no items;
the final fixture uses the normal content-conversion callback. Those empty
experimental results are not passes.

## Change and validation

Each generated opening consists of a **URL** action followed immediately by
**Open URL**. The intended automatic input connection is missing, as the later
phone result above demonstrates. The URL field uses text token serialization for
a dictionary variable. Both the Home Screen route and fresh JIT route have the
same missing Open URL input.

45 removes44's provisional helper-only opening and extra startup allowance. It
sends the full original request once to the explicitly selected helper. Natural
completion, protocol `cabrillo-39`, radio ordering/presets, native JIT/detach gates
and recovery stay unchanged.

-36 generated branch cases pass for both host variants and radio choices; every
  Open URL must directly consume a preceding URL action, and JIT opens once.
-37 isolated Apple WorkflowKit controls pass:36 comparisons including12 original
  missing-parameter controls, plus natural completion without output.
-18 Apple URL content-conversion checks pass:12 direct/LC URL cases including
  four original long-string truncation controls, plus six short callback controls.
  The typed cases preserve the actual native builders' links, including encoded
  guest identity, selected data container, fresh PID and inline script.
- No URL is opened, script executed, radio changed or personal shortcut library
  written by these fixtures. They do not execute ActionKit's URL/Open URL actions;
  their parameter structure follows pinned Cherri definitions. Actual phone
  delivery/return is still required. Controls: `.build/shortcut45-controls-a`.
- All35–45 frozen-input comparisons pass. The unchanged app43 runtime remains
 199 managed assemblies and16 native archives. No new game/runtime build occurs.

## Preserved delivery and failed physical gate

The Apple-signed default file is25,255 bytes, SHA256
`6f3a50934232bcc4a4793d3031c7f81869a4d878d4bdd6392f66b869a15b65e8`.
Standalone is25,209 bytes, SHA256
`297a3412857ce5eb43a5cef9084fb0953c8b46f69c7b7648bca85e185d748de2`.

All six kit files, including the additive delivery note, are confirmed uploaded at
`iCloud Drive/Celeste JIT Tests/shortcut-45`. USB disconnected before transfer;
**no45 phone-folder staging occurred**. CoreDevice lists the paired phone but its
tunnel is unavailable. Use the iCloud copy. The additive delivery note corrects the
planned USB path in the preserved original guide. The original five files stay exact.
Every previous Results folder and artifact remains intact.

The owner completed import; all45 actions are verified under exactly **Cabrillo**.
Automatic fails before Cabrillo opens, as recorded above. Preserve45 and use46
for the next fresh test. The older scoped manual43 warm JIT/menu/save/Quit pass
is separate from this shortcut gate.

```sh
python3 tools/check_shortcut_files45.py --work .build/new45-controls
python3 tools/build_shortcut_files45.py --output .build/new45-signed --sign
```

Use fresh paths. Integration references: [Cherri URL action serialization](https://github.com/electrikmilk/cherri/blob/d96eee9c7768649d441df0166b68a7e3c742690c/actions_std.go),
[LiveContainer query decoding](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/TweakLoader/UIKit%2BGuestHooks.m).
