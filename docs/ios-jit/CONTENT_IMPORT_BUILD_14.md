# Build 14: small IPA and persistent original-game content

11 September 2026. **Original-ZIP import and bounded Everest gameplay now pass
on the phone.** See [physical acceptance](CONTENT_IMPORT_PASS_2026-09-11.md).
Fresh-process cached reuse and the post-import app update remain pending.
**Picker setup update:** [the owner confirmed Fix File Picker in the guest's
LiveContainer settings resolves selection](BUILD_14_FILE_PICKER_RESOLUTION.md).
The original build 14 IPA was used for the subsequent successful import/run.

Build 13 is [physically accepted](EVEREST_EXECUTION_PASS_2026-09-11.md), including
real Everest mod ZIPs, On/IL hooks, custom entity, ARM64 Lua callback, mod saves
and resume. Build 14 keeps that runtime/game path and moves the large assets
out of the IPA. It remains a private development kit.

## Result and intended input

The unsigned IPA is **22,774,779 bytes (22.8 MB)**, compared with build 13's
890,087,879 bytes: approximately 97.4% smaller. It bundles **zero Content files**.

Use **Celeste Windows (FNA), version 1.4.0.0**, `celeste-win-opengl.zip`, from the
owner's [official itch.io purchase](https://maddymakesgamesinc.itch.io/celeste).
The already supplied Mac copy of that original archive has exactly the trusted
1,216 Content files, totaling 1,158,665,183 bytes, with all SHA-256 values matching
and no extra Content files. This is a normal store ZIP, not a generated asset
pack. The phone picks it directly without manual extraction. The owner has
been asked to download this edition, which also makes the first test reproducible.

The owner clarified that reusing build 13 is unnecessary and that normal store
files should be the product route. No build 13 IPA is required. An exact Content
subtree from that IPA remains structurally compatible, but is only an optional
private fallback. The Linux archive and direct folder-picker import have not
been validated/implemented in this build; do not advertise their acceptance.
A single wrapped Content folder inside a ZIP is supported when every trusted
file matches. Unknown or modified Content is rejected with a diagnostic reason.

## Storage and execution

- Bundle/version: `io.github.hmcneill46.celeste.everest.jit.everest`, 0.7.0 (14).
  Update the existing LiveContainer 1 guest and retain its data container.
- Existing `Documents/Profiles/everest-jit-canary` preserves the two mod ZIPs,
  game/settings saves and complete Everest module sidecars.
- Foundation's coordinated, security-scoped picker stages an archive into
  `Documents/ContentImport/game-input.zip` before JIT. It streams 128 KiB chunks,
  hashes the copy, checks available space and exposes progress/cancellation.
  The owner's original Files source is never modified or deleted.
- After the current PID/nonce StikDebug script prepares memory, a separately
  attached Mono worker validates/extracts assets before constructing Celeste.
  No renderer or second game process starts during import. Expected invalid
  input and cancellation allow retry using the already prepared runtime.
- Content lives under
  `Documents/GameLibrary/v1/<content-hash>/<generation>/Content`. All files must
  match trusted paths, lengths and SHA-256 values. A generation is selected by
  atomic `active.json` only after full verification; pointers contain relative
  generation identities so a moved app data-container path is supported.
- Bound archive length, central-directory allocation, entry count and expanded
  bytes. Reject missing/extra Content, traversal, duplicate/case-colliding paths,
  symlinks, split/ZIP64 archives and mismatched content. Unrelated desktop binary
  entries are not extracted or loaded.
- A fresh launch verifies the persisted library rather than importing again.
  Cancellation/failure preserves the active generation. Marked unfinished
  extraction directories are recovered on the next attempt; cleanup does not
  follow links or touch saves. Corrupt installed content needs a verified import.
  Superseded corrupt generations are retained for now, so repairs can consume
  additional space; a user-facing library manager is later work.
- Successful preparation deletes only the app-owned staged ZIP. The source
  download stays in Files. The initial import conservatively needs about 3 GB
  free; persistent assets occupy about 1.16 GB.

Source: `experiments/ios-jit/content-import/`. Stages use `.build/ios-jit/content-*`.
Only the adapter is rebuilt; accepted prepared Everest/FNA/game dependencies,
Mono 8.0.28, the paired Metal backend, Lua 5.4.8 and FMOD stay unchanged. Xcode
26.6 (17F113), iOS SDK 26.5, ARM64, two 32 MiB JIT arenas. The AOT checkout and
accepted build 13 source are untouched. Nothing was committed or published.

## Evidence and limits

| Check | Result |
| --- | --- |
| Original owner FNA ZIP versus trusted content catalog | All 1,216 files match, no extras |
| ContentStore tests on CoreCLR 8.0.28 | 39 checks, including invalid input, insufficient space, cancellation, interrupted-stage recovery, cache corruption/repair and link handling |
| Actual native Foundation staging | Streaming/progress, cancellation preserving prior archive and source, missing source, symlink rejection pass |
| Pinned Mono 8.0.28 cold import + real game | Import 1,158,665,183 bytes in 5.262 seconds on this Mac; Everest map, movement/hooks, NLua callback, FMOD, saves, resume and clean detach pass |
| Fresh pinned-Mono process | No input archive; hashes/reuses the installed content in 2.000 seconds on this Mac; mod save 3 → 6; full game test passes |
| Same Mono runtime after expected import failures | Cancel result 3, invalid input result 2, followed by successful import preparation/gameplay; clean worker detachment |
| iOS 26.5 simulator | Actual 4 MiB native staging, same-bundle update retains archive, ZIP import, JIT gating, 800-event log burst, export and previous-session recovery pass |
| Request/script integration | Exact binary geometry and actual simulator-generated request, 4,096 mocked page acknowledgements, detach and stale/old-geometry rejection pass |
| Exact unsigned device package | No Content, signature, provisioning or embedded dSYM; all 1,294 game/FNA/FMOD and 126 Lua static imports resolve; all declared inputs match |

The simulator update changed its data-container UUID. The test now re-resolves
that path and confirms retained data rather than continuing to read the obsolete
path. The production library already derives the current Documents location and
uses relative generation pointers. This is simulator evidence, not LiveContainer
update acceptance.

Host times are not iPhone performance predictions. The subsequent phone export
verifies original-ZIP selection/staging, ARM64 import in 4.638 seconds and
post-import gameplay. Both mods/settings were retained; the owner saw the old
save survive and then deliberately deleted it. The new mod save passes 0 → 12.
Device cancellation under lifecycle, fresh cached reuse and a post-import
LiveContainer update still need evidence; see the physical acceptance report.

## Physical handoff

Private kit: `artifacts/ios-jit/content-import-20260911-14/`.
iCloud location: `Celeste JIT Tests/0.7.0-build-14/`.
The nine-file kit totals 22,874,884 bytes. Local iCloud copies were hash-verified.
Apple reports a mixture of completed uploads and an account error for the IPA;
the owner subsequently downloaded, installed and successfully ran build 14.
That physical result resolves delivery despite the stale metadata. Inspect the mutable local
`handoff-status.json` for delivery updates. The superseded 890 MB build 13 cloud
installer was removed only after both copies matched its accepted SHA-256;
its exact local IPA/symbols and iCloud Results are retained.

Follow the included `README-FIRST.txt`; [source instructions](../../experiments/ios-jit/content-import/PHONE_README.txt).

1. Update the existing build 13 guest. Confirm its two mod ZIPs are still ready;
   if missing, export and stop before reimporting anything.
2. Import the original FNA ZIP, enable fresh-session JIT via LC2, then Run.
   Test the map, saved counter, controls/audio, 30-second background/resume,
   Finish/PASS and delayed liveness. Export `first-import.json` into Results.
3. Close the process and install the same small build 14 IPA as another update
   of the same guest. Reopen without importing any files; run fresh-session JIT
   and the test again. Export `after-update.json`. This covers both fresh process
   and actual guest update retention.
4. After a crash, reopen and export before requesting JIT. Retain Export as the
   fallback even when direct diagnostics collection is available.

The app sends the current PID/nonce script automatically. The kit's `.js` is a
reference template; a manual fallback must use Export session script in the
running app. The kit contains the unchanged two small canary ZIPs for recovery,
not Strawberry Jam. Default handoff remains iCloud; local placement, cloud upload
metadata and actual phone download are recorded separately.

## Public launcher and SJ follow-up

This private IPA **still contains original/prepared Celeste IL and linked iOS
FMOD**. Asset import alone does not make it a game-free public release. The next
public-packaging gate is running original-IL conversion, Everest patching,
HookGen and preparation-cache management on the phone; FMOD permission remains
unresolved. Do not require users to supply desktop FMOD expecting it to be an
iOS library. Normal original-game ZIP import is the intended product flow.

With physical content/gameplay accepted, develop real LuaCutscenes and the
relevant SJ helper tests, then Beginner lobby/Bing. Include cached reuse/update
retention in the next phone kit. Persistent assets/mod ZIPs will let later
small app updates avoid resending large unchanged packages. Full arbitrary-mod
import, profiles, save management and a public release remain subsequent work.
