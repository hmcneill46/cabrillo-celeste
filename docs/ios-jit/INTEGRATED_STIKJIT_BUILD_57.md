# Built-in StikJIT — build57 /0.26.0

20 October2026. Local implementation trial requested by the owner after the
published0.25.1/build56 download repair. All274 captured56 app inputs remain
frozen. This source lane is `launcher-integrated-jit`; it retains the exact
Everest1.6642.0/runtime/dependency pins, copy imports, bundle ID and save paths.
The source is pushed as hmcneill46 in draft
[PR7](https://github.com/hmcneill46/cabrillo-celeste/pull/7). The unsigned hosted
trial and independently downloaded kit pass as recorded below. No57 version tag,
public Release or physical helper/JIT acceptance is claimed.

## Verified unsigned test IPA

[Download the five-file build57 test kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39406495715/artifacts/12257984521)
(GitHub sign-in required; expires3 November2026 at10:37:38 UTC). Extract
`Cabrillo-0.26.0-unsigned.ipa` and sign it in Feather with the Development profile,
preserving the embedded helper extension and framework. Keep the existing bundle
ID. In Cabrillo, select Built-in StikJIT if a previous provider remains selected,
import a valid pairing plist under Settings → Built-in StikJIT, connect
LocalDevVPN and press Run Celeste. No iLoader changes or recognition are needed.

[Run39406495715](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39406495715),
attempt1, passes at source `0f08fc64083d539fdba9f1b78fd79bb41e516048` on
`codex/actions-release`. Fresh public managed/native compilation, official FMOD
SDK acquisition, package audits, all five attestations and separate Ubuntu
checksum/attestation verification pass; Release publication is skipped.

The retained `artifacts/cabrillo-build57-hosted` kit independently verifies
all299 captured app source hashes, all274 frozen56 inputs and all151 prior
dependency hashes, with only the separately disclosed StikJIT mixed archive and
idevice binary added (153 total). Actual199 DLLs pass434 metadata checks, exactly
matching the hosted audit; NLua's full RSA signature and two tamper controls pass.
Fourteen guarded native/managed version comparisons pass156 assertions. Structural
IPA checks independently confirm the six exact unsigned helper/framework files,
host iOS15/helper iOS17.4 isolation, licences and scripts. All five attestations
bind the exact bytes to the source, workflow, ref and hosted run.

IPA bytes:21,038,013. SHA256:
`c45c0f5067c95ce4422e8def19c6595e078f03f8d52b1061d6d7754428a5a76f`.
All299 captured57 inputs and this kit are frozen; use58 for new implementation.
Documentation-only delivery updates preserve those inputs. Feather installation,
actual helper registration, real DDI/JIT and gameplay remain device gates.

## User flow

Built-in StikJIT is the recommended default for new standalone installations on
iOS17.4 or later. Explicitly saved existing choices stay selected. StikDebug in
LiveContainer2, standalone StikDebug, manual/already-enabled and the older
TrollStore route retain their behavior. LiveContainer cannot create the required
helper extension; its existing default and providers remain available. A saved
unsupported built-in selection is explained rather than silently rerouted.

Connect LocalDevVPN or a compatible tunnel exposing the device Remote Pairing
service at10.7.0.1:49152. Play checks that actual service, with an expiring result;
it does not infer JIT readiness from a network interface. After importing game
files and resolving the mod library, press Run Celeste. Cabrillo starts its
embedded helper, prepares the developer image if needed, shows the current
operation and enables JIT for this process. The game starts only after the
matching helper result, existing native JIT checks, known debugger detach and
foreground/profile/content/library gates all pass. Preparing the developer image
from Settings is optional; Run performs preparation itself.

The app must preserve get-task-allow, the helper extension and its framework
when signed. Developer Mode and a valid pairing file are required. Feather's
current recursive signing uses the selected provision for nested bundles; source
review does not establish whether a specific signed installation registers and
launches the helper. An actual device test remains necessary. No new profile is
automatically requested and no privileged App Group entitlement is used.

## Pairing files and iLoader

Settings → Built-in StikJIT → Import pairing file accepts a copied plist from
iLoader or another compatible pairing tool. It validates Remote Pairing public
and private32-byte fields plus an identifier, preserves combined Lockdown fields
and unknown keys, limits the input to1MiB and replaces the protected file
atomically. Original selected files are retained.

Cabrillo also detects `Documents/pairingFile.plist`, the usual tool placement
location, and adopts it into `Documents/StikJIT/pairingFile.plist`. Changed tool
bytes are detected even when a tool preserves the timestamp. An unchanged older
tool file cannot overwrite a later manual import. Both credential files are
excluded from backups; pairing changes invalidate displayed readiness. No
pairing content, filename, private identifier or raw helper log enters exported
diagnostics or the IPA. The helper receives bytes over the extension request
and deletes its protected temporary plist after the operation.

Current official iLoader source9f5bddb2051e3391fa2ed3bef6f59d7978f332f6 uses a
hardcoded CFBundleDisplayName list in `src-tauri/src/pairing.rs`; app metadata
cannot make a new app appear in that list. The owner explicitly requests that iLoader must not be changed or receive any
submission. The proposed patch is removed from Cabrillo’s public source.
Cabrillo does not appear in that fixed iLoader list automatically; export its
pairing file and import it in Cabrillo instead. Manual import and generic
Documents file discovery work independently of iLoader recognition.

## Process and protocol boundaries

StikJIT is pinned to official32287268fa5824f9edce4cb359f5833ce0cf7b00, with
archive SHA256ed38ff2e296b1de00b7b664f8ff10b2e10c843375b9422e5cef7fb1d6b42e3d0.
Its Swift implementation is compiled for an iOS17.4 helper and is never linked
into the iOS15 host. A process attaching its own debugger would deadlock. The
classic `com.apple.ar.viewer` helper runs the blocking API on one serial queue;
the host discovers its actual post-signing identifier and uses a private
NSExtension request, without an App Group. Progress contains only fixed stages
and a random notification token. Only a matching operation-specific response
can complete the helper request.

The exact existing Cabrillo mailbox script is passed through customBase64. It
uses the same get_pid/send_command/log bindings supplied by StikJIT and prepares
the same two256MiB arenas. It remains mandatory on iOS26+, independently of
TXM detection. The user toggle can force this same script on earlier supported
systems; it never selects a different allocator or script. Native memory checks
and both detach gates are retained. A framework success message alone does not
establish JIT.

Failed or uncertain enablement requires a fresh Cabrillo process; no silent
provider fallback, repeated debugger attachment or game launch occurs. The
watchdog reports failure once, retains a possibly active helper until its real
terminal response and never claims that a timeout detached or cancelled it.
Late success cannot override the terminal host failure. Existing Home Screen
shortcut49 remains for the external providers; built-in JIT uses Play → Run.
Pending shortcut recovery stays visible.

## Build and distribution boundaries

`tools/build_release57.py` uses the existing fresh public managed/native/FMOD
recipe and additionally runs `tools/build_stikjit57.py`. The upstream StikJIT
archive contains a prebuilt idevice FFI static library (57,017,464bytes; SHA256
4db23fe1d342927b9480bb9a8577f219994365621dc28aa0018e23ea1990ecc8). It is
disclosed as a binary input; upstream does not disclose its exact source revision.
The archive is classified as mixed source/binary rather than fully source-built.
MPL-2.0, the idevice MIT notice, upstream script notices, exact source URL and
hashes are included. No endorsement is claimed.

The framework and helper are unsigned. Their runtime bundles contain exactly
six approved files; compiler modules, dSYMs, static SDK archives and credentials
are excluded. Their17.4 load commands, framework install name, helper run path,
host isolation and package identity are audited. All original151 dependency
hashes remain unchanged; StikJIT and its idevice binary are separately added.
Full IPA creation requires the existing developer-owned FMOD SDK or authorized
GitHub workflow. No historical app/runtime capsule is substituted.

## Validation

All final local checks pass; exact receipts and hashes are in the
[57 evidence ledger](INTEGRATED_STIKJIT_BUILD_57_EVIDENCE.json).

| Check | Result and scope |
| --- | --- |
| Python source/package/release controls |115 tests pass, including source selection, immutable56 inputs and helper/package rejection cases. |
| New native launch/coordinator |131 production provider/reducer controls plus55 protected-pairing/IPC-result/watchdog controls pass. These use synthetic pairing and a stubbed service boundary. |
| Actual device-target host compilation |43 Swift sources including the real vendors,6 CYaml C and5 selected Objective-C files compile for arm64/iOS15 with the actual generated bridge; other selected native sources remain hash-checked. No whole app/runtime link or IPA is claimed. |
| Actual framework/helper compilation |All11 upstream Swift files plus Cabrillo’s helper Swift and Objective-C entry compile/link for arm64/iOS17.4. Exactly6 unsigned runtime files pass platform, identity, dynamic-library/run-path and source/binary disclosure checks. |
| Actual simulator extension IPC |The production coordinator launches the production helper in a separate process;3 Darwin progress stages and the validated prepare response arrive, and the temporary synthetic pairing file is removed. StikJIT is a no-JIT fixture stub; no real DDI, pairing or JIT is performed. The test-created simulator is deleted. |
| Actual simulator UI |14 Apple UI tests pass across iPhone17Pro and iPadPro11M5 on iOS26.5, with66 PNG captures. Ready/pressed/disabled/used/progress/failure, larger text, landscape, pairing actions, TXM unknown, service expiry and legacy controls are covered. Both simulators are shut down. |
| Retained saves/shortcuts |119 profile checks,185 native shortcut checks,36 generated branches and15 bad-URL controls pass. |
| iLoader boundary |Read-only source review confirms the fixed app list. The owner rules out iLoader changes or submissions; manual import and Documents file discovery remain supported. |

Read-only visual review reproduces the original invisible pink glyph and confirms
the fixed icon/title share a visible foreground and remain centered in normal,
held-press, disabled and larger-text captures on both device families. Earlier
partial/interrupted fixture runs stay retained separately; only the final-c UI
receipt is a full presentation pass.

Independent source review also closes the asynchronous mod-verification entry
race: internal launch rechecks foreground and profile readiness immediately before
managed entry. Terminal native/trace verification failure now latches a restart
error instead of later being presented as still waiting for JIT. Native tests
and both existing debugger-detach checks remain authoritative.

Full fresh managed/native/FMOD packaging and independent downloaded-kit
verification now pass as recorded above. Signed installation, actual helper
registration under the owner’s Feather setup, real pairing/DDI/JIT, gameplay and
saves/normal Quit remain pending for57. Hosted, native or simulator success does
not close those physical gates. The existing restricted GitHub build environment
accepts the established `codex/actions-release` trial branch, main and version
tags; no environment access expansion is needed for a source trial. After the local checks, the owner explicitly authorizes “Push/build Cabrillo
only”: commit/push as hmcneill46, open a Cabrillo PR and run the existing unsigned
trial workflow. No57 version tag or public Release is authorized. The owner
explicitly reiterates that nothing should be changed or submitted to iLoader.
