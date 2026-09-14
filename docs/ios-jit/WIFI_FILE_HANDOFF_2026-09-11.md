# iPhone file handoff over the existing Apple Wi-Fi tunnel

Build 12 uncovered a working alternative to USB and iCloud: Apple's existing
CoreDevice/RemoteXPC tunnel can carry the House Arrest document service. This
uses the owner's paired iPhone 15 Pro Max (iPhone16,2), without attaching a
debugger, changing pairing or starting a privileged replacement tunnel.

**Completed:** all nine build 12 files, **883,114,836 bytes**, are verified
on the phone at **2026-09-11 18:43:26 UTC**, under
`Files → On My iPhone → LocalSend → Celeste JIT Tests → 0.5.0-build-12`.
No IPA installation/launch or physical gameplay test was performed by the host.

The initial observations were different for three interfaces:

- `devicectl list devices` showed the paired phone with a disconnected network
  tunnel. A bounded live `device info details` request connected successfully
  and confirmed the intended iPhone16,2 / iOS 26.5.
- `usbmux list --network --simple` returned an empty list. This did not mean
  the phone was unreachable through Apple's developer tunnel.
- CoreDevice `device info files --domain-type appDataContainer` still failed
  for LocalSend. This did not mean its Files-sharing Documents were unavailable.

The task-local **pymobiledevice3 11.12.4** provides
`remote.native_tunnel.establish_native_rsd(serial=target_udid)`. It borrows
Apple's native tunnel assertion and returns a connected service-discovery
object. Verify both `rsd.udid` and `rsd.product_type` against the intended phone
before requesting any app service. Do not select the first network device.

The phone advertises `com.apple.mobile.house_arrest.shim.remote`.
`HouseArrestService.create(rsd, 'org.localsend.localsendApp', documents_only=True)`
successfully vends LocalSend's document tree. As with USB, its AFC root contains
`/Documents`; the test directory is `/Documents/Celeste JIT Tests/`.

## Transfer behavior

The build 12 transfer helper is preserved privately at
`.build/ios-jit/device-transfer/2026-09-11/copy-build12-wifi.py`.
Its input kit and receipt pin every filename, size and SHA-256. It creates only
the new version folder and `Results`, then writes each new file with an
`.uploading` suffix. Files stream in 4 MiB blocks with operation timeouts.
The helper reads every byte back from the phone, checks the checksum and size,
then renames the completed file to its final filename. Existing different final
files and unexpected partial uploads cause a failure, rather than replacement.

The helper never installs or launches the IPA, modifies another app's data,
reads unrelated files or enables JIT. Small files go first; the large IPA is
not presented as complete until readback succeeds. A transfer interruption leaves
an explicit partial filename and a diagnostic receipt for review.

The authoritative completion record is
`artifacts/ios-jit/celeste-canary-20260911-12/phone-wifi-handoff.json`.
Only `COPIED_TO_IPHONE_OVER_WIFI_AND_READ_BACK_VERIFIED` means the whole kit is
on the phone. Per-file success or a working tunnel is not full delivery.
The [build 12 evidence](CELESTE_BASELINE_BUILD_12_EVIDENCE.json) records the final
handoff state separately from iCloud and pending gameplay. The iCloud upload
eventually confirmed at **18:42:57 UTC**; it is also available as a backup.

## Future diagnostics collection

This establishes remote document transport for LocalSend. It suggests the same
transport can be added to the existing direct diagnostic collector, but a new
LiveContainer guest must still be discovered and verified by its game bundle ID
and current data-container UUID. Do not reuse a graphics/hook guest UUID or claim
that build 12 game diagnostics were fetched before that guest has been installed
and tested. Keep Export diagnostics for explicit LocalSend/iCloud handoffs.

Preserve target identifiers, discovery data and pairing material only in the
ignored private transfer directory. Retain only routing information needed for
the selected phone; discovery can include unrelated paired devices and keys.
Do not copy raw discovery or pairing records into public reports or test kits.
