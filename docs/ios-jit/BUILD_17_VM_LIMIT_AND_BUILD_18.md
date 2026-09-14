# Build 17 VM inspection limit and build 18 correction

12 September 2026. The build 17 setup was correct. StikDebug reported successful
preparation and detached, but the app stopped cleanly at an obsolete VM-range
inspection limit before any generated code or managed runtime ran. Build 18
corrects that checker and repeats the same GravityHelper phone test.

## Exact device finding

The exported session `36d9afb8-1675-4276-b1d0-fdd444a9230e` matches the delivered
build 17 IPA, 200 packaged managed assemblies, script, 155 frozen source inputs
and 16 native libraries. The original five ZIPs were retained; the two new
GravityHelper/CJITGravityProbe ZIPs imported with matching hashes, leaving all
seven ready. The installed game-content pointer is present. Content hashing
and save reload did not run in this session, so it adds no gameplay acceptance.

The current process used the correct LC2 route and matching 128 MiB-per-region
script. The mailbox reached status 2, script version 1, error 0; process tracing
was clear. The checks for debugger detach and valid mailbox response passed.
The next check, `prepared_region_is_rx`, failed with `too_many_entries`.

The recorded 4,096 entries are contiguous 16 KiB mappings, all with current RX
protection. They cover 67,108,864 of the requested 134,217,728 bytes. The old
`CJInspectVMRange` hard-coded a 4,096-entry traversal limit; increasing the
arena from 64 MiB to 128 MiB exposed that assumption. I missed this bound in
build 17's arena-size change. The checker never queried the remaining half
or the second arena. The app made no alias mapping or code-execution attempt
and exported diagnostics successfully. StikDebug's success reply alone does
not independently prove those uninspected mappings or native execution.

Private raw export, exact-input validator, per-session events and consoles:
`.build/ios-jit/device-evidence/2026-09-12/build-17-results/`.
Raw SHA256 `a699f36af72a86f6ac0af24a9846d264021660c1f38f384201b2aaa2a52f96da`,
54,074,829 bytes. Older build 16 passes and build 15's known allocation failure
are historical sessions in this export, not additional build 17 failures.

## Correction

The isolated source lane is `experiments/ios-jit/sj-memory-check/`. It owns its
VMRange source/header copies, leaving delivered sources unchanged. The native
builder explicitly compiles the local checker and verifies that main resolves
the local header rather than the old shared probe header.

The traversal limit is now the number of OS pages intersected by the requested
range: `floor((end - 1) / pageSize) - floor(start / pageSize) + 1`. This includes
partial boundary pages and avoids rounding-addition overflow. The production
API reads `getpagesize()`; an explicit-page-size entry point supports host
regressions. A 128 MiB range on a 16 KiB-page device allows 8,192 entries.
Larger ranges derive a suitable bound without another fixed-count edit.

Every mapping must still advance without overflow or gaps. Full byte coverage
and identical current RX/RW protection remain mandatory; no tail is skipped
or accepted from the prefix alone. Invalid page sizes and ranges fail before
querying. Malformed sub-page callbacks retain a finite traversal bound. The
native diagnostic adds the page size and computed entry limit.

Build 18 reuses all build 17 managed DLLs, seven ZIPs and script bytes, plus
the accepted build 16 Mono archives. The code geometry stays two 128 MiB
regions, 256 MiB total. No game/mod reimport, runtime rewrite or save migration
is required. The runtime/managed/mod builder scripts in this native-only lane
are read-only verifiers of those preserved inputs.

## Verification

- The original checker reproduces the exact 4,096-entry/64 MiB cutoff from
  the phone's recorded prefix. The corrected checker refuses to accept that
  prefix when the unobserved tail is unavailable.
- Eighteen corrected-checker cases pass with ASan/UBSan: all 8,192 fragmented
  16 KiB pages, old-limit boundaries, larger ranges, 4/16/64 KiB geometry,
  partial pages, large single mappings, late RW/RWX fragments, holes, missing
  tail, query errors, zero-size/nonadvancing/overflowing entries, invalid
  bounds and finite handling of malformed callbacks.
- The same production wrapper and Darwin adapter traverse 8,192 real macOS
  VM entries. Alternating maximum protections force fragmentation while all
  current permissions remain read-only. This executes no generated code.
- The full pinned-Mono GravityHelper/Lua/Max host game runs with the new native
  checker, unchanged adapter and original ZIPs. Gravity inversion, inverted
  ceiling-platform contact, return to normal gravity, retained Lua resume,
  FMOD, On/IL hooks and clean detach pass. The copied independent profile
  reloads mod counter 6 and writes/reads 9; accepted profiles are untouched.
- Capacity replay remains 235,569,152 / 268,435,456 bytes including extra
  chunks and native reserve. Package checks match all 200 managed DLLs,
  seven ZIPs, runtime libraries and script to build 17. Native imports resolve;
  the unsigned IPA excludes Content assets, signatures and embedded dSYMs.
- Simulator update/import readiness/export/recovery and the exact native/script
  protocol are checked on final bytes. Physical ARM64 native execution and
  GravityHelper gameplay remain pending; host/simulator tests cannot establish
  those results.

## Physical retest

Build ID `sj-memory-check-20260912-18`, version 0.9.1 (18). Local kit:
`artifacts/ios-jit/sj-memory-check-20260912-18/`.
Phone folder: `iCloud Drive/Celeste JIT Tests/0.9.1-build-18/`.
Follow the [phone guide](../../experiments/ios-jit/sj-memory-check/PHONE_README.txt).

Close the previous process and update the existing LC1 guest, keeping its data,
Launch with JIT OFF, stored script blank and Fix File Picker ON. All seven ZIPs
should already be ready; import nothing. StikDebug remains in LC2. Enable the
new process's fresh script, return after detach and run Celeste once native
checks pass. Play the same Gravity map: Lua walk, red gravity zone, underside
of the ceiling platform, exit to normal gravity, Home 30 seconds, return and
jump, all three helper passes, Finish, ten-second wait and Export to build 18
Results. After a crash, reopen and export before another JIT request.

Inspect complete native VM coverage/alias/execution checks first, then actual
code usage, GravityHelper/Lua/platform behavior, retained saves and detached
resume. Full Strawberry Jam remains a later gate after helper integration.
The exact [evidence ledger](BUILD_17_VM_LIMIT_AND_BUILD_18_EVIDENCE.json) records
validation, artifacts, snapshot and cloud status. No commits, pushes or public
publication are authorized; the separate AOT checkout stays read-only.

Artifact: 22,780,024 bytes, IPA SHA256
`8ae85ea014c6f301ed7a065eb8a506e3b726301fc14ed5c0e0a1209548dd1272`;
executable/dSYM `UUID: E1A7F78F-0879-3C6A-8E3E-B223641BF855`. Script template SHA256
`6b8ab9a65b976441c5d96991f3e26ad1f0c8b5b41d7be1b8db29416486c1f191` (unchanged from build 17).

All 13 kit files (24,566,084 bytes total) have verified local readback and
confirmed iCloud upload. Phone download and physical execution remain pending.
The superseded build 17 cloud installer was removed after its exact local
copy was checked. Build 16 and all Results folders remain available.
