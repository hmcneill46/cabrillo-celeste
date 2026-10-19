# Copy-based Files imports — build54

19 October2026. Version0.24.3/build54 continues the failed build53 Files-picker
repair. Game and mod importers request a temporary copy through Apple's public
document-picker API, matching the existing save/backup importer policy. Original
bundle ID, existing signing profile, staging validation and JIT remain intact.
Local source/UI/production compile checks pass; a54 IPA/phone pass is not yet claimed.

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
| Complete54 IPA / phone game import |Pending separate hosted build and physical test. |

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

The owner's existing approval covers pushing the tested Files-picker repair and
running the unsigned test workflow;54 continues that same repair after53 fails.
No version tag or public Release is authorized. An unsigned54 package must pass
the full fresh source build, package checks and exact-source attestations before
delivery. Original-ID Feather game/mod import remains a physical test afterward.
Keep the working installation and its saves. No new Arctic Sign profile or
bundle-ID change is part of this repair. See the accompanying evidence ledger
for completed checks and their precise scope.
