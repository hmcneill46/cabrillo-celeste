# Remote Pairing endpoint correction — build41 /0.22.2

26 September2026. Local development and private phone testing; no GitHub write or
public IPA publication is authorized.

## Physical finding

The owner installed40. Direct collection verifies its identity, existing data
container, JIT-off setting and125 unchanged save/profile files. A remotely started
Automatic shortcut resolves the actual LC host, opens LocalDevVPN and returns to
Cabrillo, then times out before creating a JIT request. The build39 availability
defect is fixed;40's probe incorrectly expects the legacy lockdown service at
10.7.0.1:62078.

StikDebug's current source and its integration library use Remote Pairing at
**10.7.0.1:49152**. A hello sent from the Mac to the positively identified phone's
advertised network address receives the actual Remote Pairing envelope: protocol24,
minimum8, with incoming tunnel connections allowed. This verifies the protocol on
the physical phone, not the phone's VPN loopback path or JIT. A USB control-service
hello also succeeds; a direct USB port connection closes and is not a pass.

No pairing setup/verification, keys, encrypted tunnel or debugger is used by these
hello checks. The native launcher closes immediately after the unauthenticated
reply; StikDebug retains all privileged preparation and attachment work.

## Implementation and checks

Build41 in `launcher-shortcut-tunnel` preserves40's routing correction and replaces
the probe with the correct framed JSON hello. It requires the Remote Pairing
magic, bounded reply length, device-origin sequence0, a protocol range containing19
and permission to receive tunnel connections. Invalid shapes, reflected replies,
unsupported protocols, truncation and closed/silent peers fail. Socket work stays
off the main thread with the original1.5-second total budget and16KiB reply limit.
Diagnostic events report the failure category without retaining device metadata.

-91 native host checks pass, including14 protocol/socket cases with fragmented
  replies and timeout controls.36 generated shortcut branches pass. Receipt:
  `.build/shortcut41-controls-a/receipt.json`.
- All199 managed assemblies,16 native dependency archives, owned-game recipe,
  content manifest, JIT script, Swift UI and installed shortcut remain exact40.
  The shortcut still uses the39 callback protocol; no re-import is needed.
- Fresh Xcode26.6 build, unsigned/game-free package audit and matching new dSYM
  pass. IPA18,695,000 bytes; SHA256
  `9a35a4c1554aceca3a0bb2d9e78ea58bf97000453d421111ad0fa66dd15ef74d`;
  UUID `1dda044b59453b6d9c2790f5e9d0bb4f`.
- All210 inputs are frozen in `artifacts/cabrillo-build41-final`. Retained35–40
  manifests still match. Further implementation needs **build42**.
- No original/prepared game code or original assets enter the IPA. FMOD remains
  the distribution gate; release configuration and remote workflows are unchanged.

## Delivery and physical result

The six-file kit is copied directly to
`On My iPhone/LiveContainer/Cabrillo-build41`; complete IPA readback matches.
After collecting40's failed state with no JIT request, its unused process was
closed and LiveContainer's normal installer opened. The owner selected replacement;
direct readback verifies41, the same data container, JIT off, Fix File Picker on,
and125 unchanged save/profile files.

All six iCloud kit files at `Celeste JIT Tests/0.22.2-build-41` are confirmed uploaded.
To retain room for Results, only the superseded
broken39 cloud IPA was removed after verifying its exact retained local artifact.
All39 Results and other kit files remain. Total logical cloud bytes at placement:
981,235,391. The broader32 fallback and every local build remain preserved.

The real phone now passes the Remote Pairing VPN-loopback check in about53ms and
creates a fresh PID-specific request. The installed39 shortcut then fails before
opening StikDebug: iOS reports `ConditionalAction Code=1`, action index4, and its
editor shows the missing comparison value. A generic dictionary-value variable
needs explicit text coercion for a string comparison. The native coordinator
accepts the error callback, preserves networking, waits through its safe detach
deadline and reports failure. JIT is not granted and no game is started.

[Shortcut revision42](SHORTCUT_FILES_42.md) repairs those comparisons while keeping
the exact41 app. Its isolated Apple-engine tests reproduce the original error;
the earlier Python branch interpreter did not detect this platform schema issue.
Next: replace the shortcut, retry Automatic, then Travel in a fresh process,
restored radio preset and actual game/Quit. Preserve the
independent diagnostics export alongside direct collection. Raw phone logs and
helper-version observations remain under `.private/device-evidence/2026-09-26`.

## Sources and reproduction

- [Pinned StikDebug endpoint](https://github.com/StikDebug/StikDebug/blob/5e3e1bc91efb0dbec784be5a81e377d3ed355a40/StikDebug/Device/JITEnableContext.swift).
- [StikJIT integration endpoint](https://github.com/StikDebug/StikJIT/blob/5d732f94b871031704ef6f580a313e8d99d80ec1/INTEGRATION.md).
- [Pinned idevice handshake](https://github.com/jkcoxson/idevice/blob/d32c8189c51c2789496b0768039419c3705498c3/idevice/src/remote_pairing/mod.rs)
  and [framing](https://github.com/jkcoxson/idevice/blob/d32c8189c51c2789496b0768039419c3705498c3/idevice/src/remote_pairing/socket.rs).

```sh
python3 tools/check_shortcut_tunnel.py --work .build/new-tunnel-controls
python3 tools/build_shortcut_tunnel.py \
  --managed .build/owned-public-managed38-e/receipt.json \
  --native .build/owned-public-native38-e/receipt.json \
  --fmod .build/owned-fmod38-c/receipt.json \
  --work .build/new-tunnel-native --output artifacts/new-tunnel-package
```
