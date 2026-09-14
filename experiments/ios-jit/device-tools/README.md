# Direct USB diagnostics

`pull_diagnostics.py` retrieves the canary's automatically persisted JSONL
events and full native console directly from LiveContainer 1. The owner does
not need to tap Export, move files, restart the app or enable JIT for collection.
Keep **Export diagnostics** in the app for iCloud/share and disconnected tests.

The verified service is House Arrest `VendDocuments` / AFC using
`pymobiledevice3==11.12.4`. CoreDevice `appDataContainer` failure does not imply
this normal file-sharing path is unavailable. Use the existing isolated
`.build/ios-jit/device-transfer-tools/bin/python`; no global install is needed.

The phone must be connected over USB and accessible to this paired Mac. If iOS
requires unlocking or trust, resolve that before retrying. The collector uses
a private inventory to identify one target device and verifies its product
type after connection. It reads only the specified guest's Diagnostics folder.

```sh
.build/ios-jit/device-transfer-tools/bin/python \
  experiments/ios-jit/device-tools/pull_diagnostics.py \
  --device-inventory .build/ios-jit/device-transfer/2026-09-11/usbmux-build6.json \
  --pairing-cache .build/ios-jit/device-transfer/2026-09-11/private-pairing-cache \
  --host-bundle-id '<installed LiveContainer 1 bundle ID>' \
  --guest-data-id '<verified canary data-container UUID>' \
  --output .build/ios-jit/device-evidence/<date>/<new-snapshot>
```

Resolve current host/guest identifiers from the private
`.build/ios-jit/device-evidence/2026-09-11/build-6-pass/direct-usb-retrieval.json`
receipt. The owner's current canary path begins
`LiveContainer/Data/Application/3C268B63-02B6-…/Documents/Diagnostics`.
Do not assume that UUID remains valid after reinstalling or changing containers.
The host ID is the installed, signed LiveContainer identifier, not the guest ID.

By default the collector selects the most recently modified session; pass
`--session <launch-uuid>` when a recovery launch follows a crash. Earlier session
filenames can be listed within this same known Diagnostics folder. Do not copy
all LiveContainer guests or inspect unrelated app contents.

Each log is read twice with size checks, then saved in a new local directory
alongside a SHA-256 receipt. A changing file stops collection and requests a
retry when the app is idle. The session and console are separate stable reads,
not an atomic filesystem snapshot. An incomplete final JSONL record after a
crash is retained verbatim and counted separately; it is not accepted as an
event. The tool does not attach a debugger, launch an app or write to the phone.

The raw log includes launch/build/device identity and execution/lifecycle
events; its console is not limited to the export bundle's 128 KiB tail. Owner-
entered environment preferences remain in the optional exported bundle and
are not collected by this script. Raw logs and pairing/inventory data stay in
ignored private paths. The collector itself contains no device UDID or secret.

See [the physical result](../../../docs/ios-jit/MANAGED_EXECUTION_PASS_2026-09-11.md)
for the successful build 6 collection and its comparison with the owner's export.
