# Individual saves and numerical repairs — build34

17 September 2026. **Local validation passes and the kit is confirmed uploaded;
combined phone acceptance is pending.**
Build32 remains the accepted fallback. The owner deferred build33 testing to include
individual save transfers, then requested investigation of hair physics and related
bugs. Build34 includes the whole-profile backup feature and one combined phone guide.
The [evidence ledger](SAVE_TRANSFERS_BUILD_34_EVIDENCE.json) records exact receipts.

## Save management

Slots1–3 always appear, including empty gaps. Existing extra Everest slots remain
visible. Long press or use the accessible ellipsis button for:

- Export save + mod data as a ZIP of the original numbered files.
- Export the main `.celeste` file for vanilla Celeste.
- Replace/import from Files, with incoming and current progress shown before confirmation.
- Duplicate into the first unused slot, with review and cancellation.
- Save details: name, play time, deaths, date, game version and filenames.

**Import another save** chooses the first unused index. Empty rows do not create
placeholder game saves. New games use Everest's own empty slot; its pinned file
selector expands by default, while `MaxSaveSlots` may impose a custom limit.
350 sparse occupied slots plus empty slots1–2 were checked. Newly allocated indices
stay below50,000; this is not a guarantee of unlimited capacity in every mod.

ZIP exports contain `N.celeste` and all `N-mod*.celeste` files at their root, plus
`cabrillo-save.json` and desktop instructions. Plain one-slot desktop ZIPs, an
optional enclosing `Saves/` folder and multiple selected files are accepted too.
Internal file contents remain unchanged; only numeric filename prefixes change
when targeting another slot. Opaque mod data is preserved without executing mods.
Data stored by mods outside these standard slot filenames needs a whole-profile
or separate backup.

A standalone main-file import offers **Keep this slot's existing mod files**, on
by default for returning the same climb from vanilla. Turning it off, or importing
a complete slot ZIP, replaces the target's standard slot files, removing stale
sidecars. A ZIP containing only the main file is still a complete replacement.
Other slots, settings, archives, caches, disabled choices and unknown files remain
unchanged. No mod installation, automatic syncing or progress merging is performed.

## Desktop compatibility and recovery

The real, unmodified Celeste1.4.0.0 serializer successfully reads an exported save,
writes changed time/deaths, and native import retains its bytes and existing mod
files. The actual Everest game then loads the result and a renamed duplicate,
plays, saves and Quits normally. This verifies current desktop-format transfer;
it does not establish every historical version, console container or custom mod
format. Use compatible game/mod versions and keep an export before replacing.
Vanilla exposes `0.celeste`, `1.celeste`, `2.celeste` as slots1–3. Copying changes
file dates, so compare actual progress as well as timestamps.

Import copies into private staging, bounds and validates all inputs, then shows a
review. The main save must be UTF-8 SaveData XML without DTD/entities. Limits are
32MiB main XML,128MiB per sidecar,512MiB total and4,096 files. Path traversal,
case/Unicode ambiguity, noncanonical numbers, links, unrelated files, wrong-slot
data, malformed XML, CRC/hash failures and stale or tampered reviews are rejected.

Commit uses build33's durable whole-profile journal and retained rollback. Staged
files and directories are synchronized before renaming. Recovery selects a complete
old or new profile before mod scans/startup. Both forms of import share this path;
one review is active at a time. Profile operations remain unavailable while active
or after playing. Relaunch after any import/restore/rollback attempt before Play.
A retained profile requires an explicit rollback/discard decision before another
replacement. Diagnostics remain independent of these operations.

## Hair and related bugs

The historical platform patch selected every `Player*` method containing any double
conversion. That test was too broad: it widened just one operand in ten originally
float-only multiplications. The affected sites are hair attraction (one),
`PlayerSeeker.Update` (six), and the bird dash tutorial coroutine (three).

The actual macOS Mono8 game reproduces the hair fault. Under a controlled probe,
the first hair segment travels zero before repair and **1.7500038** after repair.
Removing the accidental conversions restores the hair method's normalized IL to
the original vanilla method exactly. Seeker/tutorial repairs use the same checked
instruction pattern; other Everest changes in those methods are preserved.
Ten legitimate double-precision movement sites remain unchanged.

The adjacent assembly audit found a lava surface-bubble calculation with a float
constant left in widened double arithmetic, plus two float setter boundaries.
The repair widens the missing constant and restores the original float setter
arguments. A256×128 rectangle with step4 produces **40 surface bubbles**, previously
4. Width, height and163 underlying bubbles are unchanged. The setter cleanup does
not imply a previously observed size defect; Mono8 already handled those setters.

Only four game method bodies change;17,300 others retain their normalized IL.
The conservative straight-line expression audit reports eleven mixed arithmetic
sites and two float-boundary findings before repair, zero recognized findings
afterward. Unknown control-flow joins are not guessed. This is a targeted check
for this class of bug, not an exhaustive correctness or visual-gameplay audit.
Seeker/tutorial visual behavior and physical iPhone hair behavior remain unaccepted.

The original loading patch and all delivered sources remain frozen. A separate
checked repair derives `Celeste.dll` from the exact accepted managed receipt.
The native build pins that derived receipt and every resource. Of201 managed DLLs,
only `Celeste.dll` changes from32/33; FNA, adapter, content and200 other DLLs match.
All16 native runtime/renderer archives also match. The verifier's inherited
four-rebuilt/197-preserved fields compare against28, not against32.

## Validation and limits

| Check | Result |
| --- | --- |
| Native storage/transfer/recovery |119 checks pass, including eight whole-profile and four slot-specific forced process exits |
| iPhone and iPad simulators |8 UI tests each; long press, menus, details, empty slots, reviews, rollback, large text and rotation |
| Real macOS game, exact final managed payload |Native roundtrip, mod sidecars, renamed slots, hair/lava probes, gameplay, save/resume contracts and normal Quit pass |
| Original vanilla serializer roundtrip |Original1.4.0.0 read/write, native reimport and real Everest load/save/Quit pass |
| Numerical repair controls |6 checks pass, including scope, unchanged movement precision and rejection of changed provenance/repeated repair |
| Final arm64 package and symbols |Pass; all8 deliberately altered package controls rejected |
| Preservation |Build31/32/33 source hashes, entire33 lane, final test inputs, managed pins and actual32/33/34 IPA contents checked |

The vanilla roundtrip used the corrected precursor payload; its four repaired
method bodies match the final payload, whose fresh MVID differs. A separate full
game check uses the exact payload shipped in34. Simulator fixtures use production
Swift storage/views; Files presentation is a fixture. Real document-picker,
LiveContainer/JIT and physical visuals therefore remain phone checks. Screenshots
were inspected; both simulators returned to their original shutdown state.
Exploratory failed harness runs are retained alongside the final passing receipts.

No game binaries, private profiles, decompiled game code or raw logs enter Git.
Build33/34 publication has not been authorized. Loading through32 remains published
at `16ff42ca62438ccfa1c3ea14e76a6606da1bc820`. Public IPA permission remains separate.

## Identity and delivery

| Item | Value |
| --- | --- |
| Version / build |0.18.0 (34), `launcher-save-transfers-20260917-34` |
| IPA |`artifacts/cabrillo-build34/Cabrillo-0.18.0-build-34-unsigned.ipa` |
| Bytes / SHA-256 |24,056,162 / `02440e406dd9e940465684e9ac32824966303d0067e0dbe650fac73891f786e7` |
| Executable/dSYM UUID |`FD136517-5EE7-3169-B275-3CE4BB0011F0` |
| Derived managed receipt SHA-256 |`80bb0a19d7f63944aa6fe23379338c747db776cae51744c73482a390425b13aa` |
| Compilation |66 source inputs,139 source hashes; Xcode26.6 / iOS26.5 SDK |
| iCloud folder |`Celeste JIT Tests/0.18.0-build-34` |

All six kit files match their local originals and iCloud confirms their upload.
Delivery status is recorded in
`artifacts/cabrillo-build34/delivery.json`; phone download/execution are unconfirmed.
The shared cloud folder totals794,488,191 bytes after placement, below1GB, with
all earlier builds and Results retained. Follow
[the combined phone guide](../../experiments/ios-jit/launcher-save-transfers/PHONE_README.txt)
instead of a separate33 suite. Keep accepted32. Next unused identity is35; any new
implementation requires another build and fresh evidence.

Desktop format references: [Everest save locations](https://github.com/EverestAPI/Resources/wiki/FAQ#how-can-i-backup-my-savedata),
[pinned slot discovery](https://github.com/EverestAPI/Everest/blob/d72e94f4b9e62b91cbdea674587ed39d53de9550/Celeste.Mod.mm/Patches/OuiFileSelect.cs),
[pinned slot assignment](https://github.com/EverestAPI/Everest/blob/d72e94f4b9e62b91cbdea674587ed39d53de9550/Celeste.Mod.mm/Patches/UserIO.cs).


## Retained device evidence reviewed25 September

A build35 export retains a complete build34 gameplay/save/Quit session with
3,533 callbacks, shutdown stage8 and zero JIT/unowned/managed errors or patch
rejections. This adds real build34 gameplay evidence. It contains no native
backup/restore or per-slot transfer UI actions, so that combined gate remains
open. The standalone34 Results folder is still empty. See the evidence ledger
for the source export hash and retained session identity.
