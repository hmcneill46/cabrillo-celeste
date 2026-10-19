# Copy-based Files imports — build54

19 October2026. Version0.24.3/build54 continues the failed build53 Files-picker
repair. Game and mod importers request a temporary copy through Apple's public
document-picker API, matching the existing save/backup importer policy. Original
bundle ID, existing signing profile, staging validation and JIT remain intact.
Local source/UI/production compile checks and complete unsigned54 package/local
verification pass. The original-ID Feather game ZIP selection/staging phone gate now passes;
physical mod import and broader gameplay/JIT gates remain separate.

## Phone evidence that changes the diagnosis

The owner reports unchanged game-ZIP selection failure after installing53.
USB collection verifies the exact0.24.2/build53 metadata, original bundle ID and
all254 captured input hashes from hosted source `e63f1e0`. The iPhone15ProMax
runs iOS27.0.1. Its game-picker preparation records a valid entitlement, a needed
adaptation, available runtime and installed hook. No game selection callback
arrives. Entitlement lookup and hook registration are therefore working; they
do not establish a real host remap or successful document-service access.

At our request the owner selects the same game ZIP through Saves → Import backup
from Files. This already uses `asCopy:YES`. It dismisses and calls Cabrillo's
delegate twice; backup validation correctly rejects the ZIP with “Choose a
Cabrillo profile backup with a supported manifest.” No restore/rollback action
appears. A further game-picker attempt still ends in cancellation. These are
separate selectors with different filters and purposes, so they support the
copy-path repair without isolating a single API argument experimentally.

Read-only collections and a comparison receipt remain ignored under
`.private/picker-failure-2026-10-19`. No extra debugger, profile replacement,
installation, app-data rewrite or device setting change is performed by Codex.

The earlier53 simulator tests established real picker interaction with a valid
simulator host and synthetic method rewriting. They did not establish Files
service acceptance of an actual mismatched phone signature. A subsequent
production/no-seam simulator probe confirms that both open/copy pickers invoke
the host setter three times using the bundle ID on iOS26.5; both select normally.
That is separate from the observed iOS27 phone failure.

## Narrow repair

`launcher-copy-picker` overlays a new main on the same frozen50 base. Only the
game and mod picker arguments change from `asCopy:NO` to `asCopy:YES`, with added
redacted mode diagnostics. The compatibility module is byte-identical to53.
Save/backup/connection imports and exports retain their existing copy settings;
types, multiple-selection policy, scoped access, archive staging, cancellation,
saves and runtime/JIT behavior retain their existing implementation. No global
file-access override or security-scope bypass is added.

The system supplies a temporary app-local selection to the existing importer,
which validates and stages its permanent copy. The original remains untouched.
Temporary and staged copies can coexist, increasing peak storage use. The
existing free-space check occurs after the system copy and still reserves the
staged ZIP, extracted content and margin. Large selections can take time inside
the system picker before its delegate runs. No arbitrary returned URL is deleted.

This choice follows the [LiveContainer maintainer's copy-mode workaround](https://github.com/LiveContainer/LiveContainer/issues/234#issuecomment-2510905293)
and [report that the host hook alone can still fail with mismatched IDs](https://github.com/LiveContainer/LiveContainer/issues/566#issuecomment-2954467260).
MeloNX also combines its [standalone signing adaptation](https://github.com/nurtrino/MeloNX/blob/f925129209afd55927a0201d82285b8fa4b7ba30/src/MeloNX/MeloNX/Common/AppEnvironment.swift#L52)
with [copy-based file imports](https://github.com/nurtrino/MeloNX/blob/f925129209afd55927a0201d82285b8fa4b7ba30/src/MeloNX/MeloNX/Common/FileImporter.swift#L57).
[Apple's document-picker guide](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/DocumentPickerProgrammingGuide/AccessingDocuments/AccessingDocuments.html)
describes the temporary-copy and storage semantics. The implementation is an
original change to Cabrillo's own picker initializers, without copied GPL code.

## Validation and delivery gate

Completed local checks:

| Check | Result and scope |
| --- | --- |
| Python source/build controls |76 pass, including9 new54 source-selection/preserved-input rejection controls. |
| Production arm64/iOS15 compilation |42 Swift,6 CYaml C and2 Objective-C sources compile with the actual generated bridge; test seam absent; all82 captured inputs remain exact. |
| Actual iOS26.5 picker UI |Two tests pass, each2 real selections and1 cancellation, repeat, exact staged bytes/hash and unchanged synthetic source. |
| Copy semantics |54 returns Import mode and distinct app-local temporary Inbox URLs;53 comparison returns Open mode and original URL. |
| Frozen53 preservation |All254 hosted53 input hashes remain exact; compatibility module byte-identical. |
| Independent review |No blocking findings; public SDK/dependency/Shortcut pins, original bundle ID and JIT remain exact. |
| Complete54 IPA |PASS source build, package audit and independent local kit/attestation verification. |
| Phone game import |PASS owner confirmation and USB journal: original ID, exact54 source, copy-mode selection and875,540,825 bytes staged on iOS27.0.1. |
| Physical mod import / new gameplay or JIT acceptance |Not claimed by this game-import test. |

The54 fixture has no entitlement injection and verifies the actual mode and
returned URL for each selection. Its initializer arguments are checked against
both production main files before compilation. The simulator53 control passes;
it is not a reproduction of the phone failure. Receipts/source hashes are in
`COPY_PICKER_BUILD_54_EVIDENCE.json`.

Preserve all254 captured53 app inputs and its immutable kit. New54 source,
recipe selection, actual copy-picker UI and production compilation are checked
separately. Test fixtures must compile without the entitlement override seam
and record real picker modes, delegate calls, copied/staged bytes and source
preservation. Simulator open mode is a comparison control, not a reproduction
of the phone's provisioning failure.

The owner's initial approval covered pushing the tested Files-picker repair and
running the unsigned trial after53 fails. Following the confirmed54 phone pass,
the owner explicitly requests a public Release with change notes. This authorizes
v0.24.3 publication through the existing tagged workflow. The54 package must pass
the full fresh source build, package checks and exact-source attestations before
delivery. The game-import phone gate passes below; physical mod import remains separate.
Keep the working installation and its saves. No new Arctic Sign profile or
bundle-ID change is part of this repair. See the accompanying evidence ledger
for completed checks and their precise scope.

## Unsigned hosted54 kit

[Trial39276928342](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39276928342)
produces the54 kit at `4a094527a96e62fbf63518c088a1dd48d19407e5`, with public
Release publishing disabled. The separate Ubuntu verification passes and trial publishing is skipped. The [five-file artifact](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39276928342/artifacts/12199896629)
requires GitHub sign-in and has14-day retention. A separate download into
`artifacts/cabrillo-build54-hosted` passes the strict allowlist/checksums, all253
captured source hashes, all151 unchanged53 dependency hashes, exact49 Shortcut
resources, original bundle ID and copy-import BuildInfo. Production symbols
are present; no entitlement test-seam symbol/string appears. All five local
attestations verify the exact commit/ref/workflow, GitHub-hosted runner and
run39276928342/attempt1.

IPA bytes:18,764,021. SHA256:
`254a126168837708bbb7d136da0c3e426a3522feb375c0d19bb26d5fbcf89762`.
Package audit reports199 managed assemblies, no original/prepared game assemblies
or assets, and no distribution blockers. Keep the253 captured54 app inputs and
kit frozen; use55 for new app implementation. No tag, public Release, cloud kit
replacement or automatic phone installation occurs during the trial.

## Confirmed54 phone game import

The owner confirms that Import game ZIP finishes and reports ready under Feather
with the same Development profile and original identifier. Read-only USB verifies
installed0.24.3/build54 and all253 source hashes against the tested hosted kit.
The iOS27.0.1 journal records copy mode, a game selection callback and completed
staging of875,540,825bytes. Journal SHA256:
`92ff72a8361d24ea7efd4dcd3b999d08aecc09e6b1a0468bd02ca3654e042985`.
This closes the reported picker/staging defect. It adds no physical mod-import,
JIT or gameplay gate. The original collection/receipt stays ignored in
`.private/picker-failure-2026-10-19`.

The owner then authorizes the public v0.24.3 Release and change notes. Keep all253
tested app inputs exact; only documentation and generated release-note prose
change for publication. The tagged workflow rebuilds, audits, attests, verifies
and publishes the five-file kit. A tagged build remains separate from an actual
device run of that freshly compiled IPA; no bit-reproducibility claim is made.
