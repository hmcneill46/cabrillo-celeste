# Signing-aware Files picker — build53

19 October2026. Version0.24.2/build53 adds automatic document-picker compatibility
for standalone sideloading profiles whose explicit application ID differs from
Cabrillo's bundle ID. The source is committed/pushed and the complete unsigned53
IPA passes hosted build/audits and independent download checks. A phone run with
the unchanged bundle ID remains pending.

## Confirmed problem

The owner installed published52 through Feather using their Development profile
and kept `io.github.hmcneill46.celeste.everest.jit.everest`. The picker displayed
the local game ZIP normally, but a tap did not select, dismiss or import it;
there was no Open button. The private profile audit found a different explicit
application ID. The owner confirms that signing with the matching Identifier
restores selection, then requests automatic support without that change or a
replacement profile.

[Feather's matching upstream report](https://github.com/claration/feather/issues/610#issuecomment-4182946719)
identifies this document-service application-ID mismatch. The current Feather
source has no built-in Fix File Picker switch. This failure occurs before game
staging or JIT. Replacing ZIP filters or forcing an extra system copy would not
correct the host identity.

## Implementation

`experiments/ios-jit/launcher-signing-picker` overlays only a new `src/main.m`
and `CJDocumentPickerCompatibility` module on the frozen50 launcher used by52.
`release/app53/Dependencies.json` locks all168 base files and selects the two
changed/added Objective-C compilation inputs explicitly. The build rejects a
missing repair, an altered base or a different source lane.

Before constructing an import or export picker, the app reads its own signed
`application-identifier` through optional Security SPI. It removes exactly the
App-ID prefix before the first dot, validates the remaining identifier and
compares it with its own bundle ID. App-ID prefixes need not equal Team IDs.
Missing, non-string, malformed and wildcard values leave Apple's normal path.

For a valid mismatch, the adapter replaces only Documents UI host requests
equal to Cabrillo's original bundle ID with the host from its own entitlement.
It chains the previous `DOCConfiguration.setHostIdentifier:` implementation,
preserves inherited superclass methods and unrelated requests, and installs
once. Optional runtime lookup checks the method ABI. Unavailable private APIs
retain the original behavior and produce a redacted status. LiveContainer is
left to its established host-aware picker handling.

This is a small original implementation informed by the public behavior in
[LiveContainer's document-picker adaptation](https://github.com/LiveContainer/LiveContainer/blob/9108ae624ea001f7d7696d48407f890b48fa2653/TweakLoader/DocumentPicker.m#L103).
It does not copy the LiveContainer implementation or add a dylib dependency.
It uses a private iOS document-service API, so future OS changes can make the
compatibility path unavailable. This distribution remains for sideloading.

Cabrillo's public bundle ID, URL schemes, data paths, signed entitlements,
memory permissions and JIT protocol remain unchanged. The existing coordinated
security-scoped archive read, validation, cancellation and retained saves remain
the import path. Picker preparation, selection, cancellation and blocked-callback
events improve diagnosis without recording signing identifiers or credentials.

## Validation and limits

Final local results:

| Check | Result and scope |
| --- | --- |
| Python build/release controls |67 pass, including new53 source-selection rejection cases and a changed download-page rejection before environment credentials are read. |
| Compatibility policy/runtime |12 host scenarios pass, including malformed inputs, absent APIs, retry, prior hooks, inherited methods and LiveContainer bypass. |
| Production device compilation |Actual launcher Swift/vendor sources and53 main/helper compile for arm64/iOS15 with the real generated Swift bridge; production test seam absent. |
| Actual Apple Files UI |Two iOS26.5 simulator tests pass ZIP tap/delegate/staging, exact bytes/hash, unchanged source, cancel and repeat. |
| First picker |Compatibility installs with zero earlier picker constructions; actual Apple host setter maps the synthetic request correctly. |
| Retained native regression |119 profile checks and185 shortcut checks pass, plus36 workflow branches and15 broken-URL controls. |
| Complete53 IPA |PASS hosted source build, package audit, five attestations and independent downloaded-kit checks. |
| Physical Feather signing |Unchanged-ID phone validation remains pending. |

The checks exercise policy and runtime method chaining, actual production iOS
compilation, and real Apple picker interaction separately. The simulator fixture
uses a synthetic identity only inside its test build to exercise the actual
Apple configuration setter while keeping the real picker host valid. It reads
no personal profile or key and contains only a synthetic ZIP. The production
object is checked to exclude the test-environment entry point.

Actual picker tests select a ZIP by tapping its Files item, receive the real
delegate callback and stage it through the unchanged production importer. They
check exact bytes/SHA256, preservation of the source, cancellation and a second
selection. Calling the import delegate directly is not a picker test. Simulator
tests do not reproduce physical provisioning enforcement or establish a phone
pass; the owner-confirmed Identifier workaround is also separate from testing53.

Reproduce the focused checks using fresh work directories:

```sh
python3 -m unittest discover -s tools/tests -v
python3 tools/check_document_picker_compatibility.py --work .build/picker-policy
python3 tools/check_signing_picker_compile.py --work .build/picker-compile
python3 tools/check_signing_picker_ui.py --work .build/picker-ui --device <simulator-UDID>
```

Use Xcode26.6/17F113. Set `DEVELOPER_DIR` explicitly if the installed path differs
from the historical name. Native profile/shortcut regression checks and public
inventory validation are retained. Final local results and sanitized receipt
hashes are in [the evidence ledger](SIGNING_PICKER_BUILD_53_EVIDENCE.json).

## Build and phone gate

`release/public53.json`, `tools/build_release53.py` and `compile_release53.py`
are the active source recipe. They preserve the public dependency pins, exact
signed49 Shortcut assets, licensed FMOD input checks, payload audit and fresh
UUID/dSYM/package verification used by52. Published52 and its source/builders
are not rewritten. The new source is not a published53 Release.

The current Mac has Xcode26.6 but lacks Mono6.14.1/sn, CMake and the licensed
FMOD1.10.09 SDK required for a complete source IPA. Native arm64 compilation
does not require those runtime link inputs. A complete build must use the
explicit developer SDK recipe or an owner-authorized hosted workflow; do not
extract development inputs from the old IPA or use a legacy checkout.

Install the completed53 trial through Feather with the original Cabrillo
Identifier and the existing Development profile. Test local game/mod imports,
cancel/reopen, backup/save import/export and existing JIT/game behavior. Preserve
both current installations and their data: the temporary matching-ID workaround
has a different app container and does not automatically migrate to the original
ID. Record that physical result separately. After the local checks, the owner
explicitly authorizes committing/pushing this fix and running the existing
hosted workflow for an unsigned test IPA. No tag or public Release is authorized;
the local results above are separate from the hosted package and phone gates. Keep game
content, SDK components and signing credentials outside source/build outputs.

## Hosted trial preparation

Commit `1f2de6de055e200886a144baf617207fca7d30de` is pushed to the trusted
`codex/actions-release` branch. [The first trial](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39266218357)
passes source and native controls, including the new production picker compile.
SDK acquisition stops before sign-in because FMOD's public download-page asset
changed. Independent inspection of the official public JavaScript confirms the
login bundle is byte-identical and the current catalogue/download-link requests
still match the helper. The previous download chunk body is unavailable, so no
claim is made about the precise changed lines.

Only the reviewed `download.chunk.js` SHA256 pin changes to
`85fe802e316372e1a243b0785d62be6ce6c69edbb83e12a7a0508b282536137f`.
The credential-free probe passes the expected HTTP401 sign-in boundary. SDK
version/archive/library pins, origin/redirect restrictions and credential handling
remain unchanged. A new synthetic regression rejects a changed second asset
before reading environment credentials. The retry passes the complete
source/package and independent attestation gates below.

## Completed unsigned hosted trial

[Retry39267829175](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39267829175)
passes all jobs at `e63f1e0a8030daa3f0f4228ca6992c428e4f1811`, with publishing
skipped. The [five-file test kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39267829175/artifacts/12194283151)
is downloaded separately to `artifacts/cabrillo-build53-hosted`; Actions access
requires GitHub sign-in and retention is14 days. Checksums, all five exact-source
hosted-workflow attestations, original bundle ID, automatic-picker BuildInfo,
all254 captured source hashes and151 unchanged52 dependency hashes verify.
The final arm64 executable contains the production picker adapter and no test
environment symbol. Both signed49 Shortcut assets remain exact.

IPA size:18,763,886bytes. SHA256:
`cbf396e7a7b1aec7bbf0a25c19cf3cfe59ef80d26e1f47df1481ed3b7791ad55`.
Package audit reports199 managed assemblies, zero bundled game assemblies/assets
and no distribution blockers. These are build/package checks, separate from a
phone pass. Keep the immutable kit and all254 app inputs; use54 for new app
implementation. No0.24.2 tag/Release, iCloud replacement, phone install or device
mutation occurs in this delivery. The current signing/import phone test remains
the next owner action.
