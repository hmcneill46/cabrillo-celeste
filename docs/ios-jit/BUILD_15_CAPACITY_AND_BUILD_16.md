# Build 15 startup crash and build 16 code allocation fix

12 September 2026. The owner followed the build 15 setup successfully. The
crash is a native JIT code-budget exhaustion while MaxHelpingHand loads its
BloomRenderer hook, before the title screen. Build 16 corrects Mono's allocation
policy; the later physical test now passes (see follow-up below). Exact final artifacts and
checks are recorded in [the evidence](BUILD_15_CAPACITY_AND_BUILD_16_EVIDENCE.json).

## Follow-up: build 16 physically accepted

The later [build 16 export](SJ_HELPERS_PASS_BUILD_16.md) now passes all native,
helper, save and resume checks. Actual code usage is 58,408,960 / 134,217,728
bytes with no runtime errors; cached content and all five ZIPs survived the
update and the mod counter reloads at 15 then writes/reads 23. The pending
language below records the original handoff. Continue with
[build 17 GravityHelper](GRAVITY_HELPER_BUILD_17.md).

## Physical evidence and retained data

The recovery export was retrieved from `0.8.0-build-15/Results`, copied unchanged
and checked against the delivered IPA, all 200 managed assemblies, script
identity, 148 frozen source files and 16 native libraries. Private raw evidence,
validator, console tail and allocation trace are in
`.build/ios-jit/device-evidence/2026-09-12/build-15-crash/`.

The failed session passes all 26 native JIT checks, returns detached from
StikDebug, verifies all five expected ZIPs, and reuses the installed game
content: 1,158,665,183 bytes verified in 2.107 seconds, same content generation.
The two existing canary ZIPs were present before new imports. This accepts
fresh-process content reuse and build 14 → 15 content/mod retention on the
phone. Build 15 never reached a save slot, so it adds no save-reload acceptance.
The export also contains an older incomplete build 14 run with a missing
post-resume jump; that is a different session and is not this startup failure.

There are 561 successful executable reservations. The next 262,144-byte
request fails after 134,037,504 of 134,217,728 bytes are reserved; only 180,224
bytes remain in aggregate. Of those successful reservations, 508 are 256 KiB.
The log then records `jit_code_budget_exhausted`. The native stack enters
`mono_valloc` and `new_codechunk`; the managed stack is the generated
BloomRenderer.Apply IL hook in MaxHelpingHand's CustomSeekerBarrier.Load.
The explicit allocator guard aborts before Mono can use a null thunk pointer.
This is exhaustion of the app's prepared code arena, not evidence of general
phone RAM exhaustion or a user import/JIT mistake.

Build 15's capacity estimate used a desktop run of about 52 MB. Mono's old
minimum is 16 OS pages: 64 KiB on this Intel Mac, 256 KiB on the 16 KiB-page
phone. Numerous generated hook assemblies each own code managers. The prior
estimate did not account adequately for this difference; the earlier build 8
investigation had already exposed it. Future capacity decisions must use
explicit device page/granule sizing and account for branch-binding space.

## Narrow runtime correction

`experiments/ios-jit/sj-code-budget/build_runtime.py` starts from the exact
build 15 visibility-fixed runtime archives. It copies the accepted alias-patched
Mono 8.0.28 `mono-codeman.c`, changes the ordinary chunk minimum to
`max(64 KiB, OS page size, allocation granule)`, and replaces only
`mono-codeman.c.o` in isolated host/iOS archives. All other 259 archive members,
including the earlier protected-member access correction, remain identical.
The original Mono source and accepted build 15 stages are not edited.

Larger method requests still round to the allocation granule. Dynamic chunks,
ARM64 branch-binding room, existing read/write alias handling and the terminal
budget guard retain their previous logic. Reducing the minimum does not mean
all methods or chunks are constrained to 64 KiB. The overall two 64 MiB arenas
remain unchanged at 128 MiB, with no unsafe reclamation or runtime restart.
The inherited MonoTypeDiscovery, exact DMD resolver and MonoMod native-layout
fix remain. Original helper ZIPs, prepared game and FNA are unchanged; the
adapter's assembly file version advances to 0.8.1.16.

The host archive additionally compiles the actual code manager with test-only
16 KiB page/granule overrides and a binding-space divisor of four. Only host
harnesses supply the override functions. The iOS archive uses its real page
APIs and ARM64 policy; symbol inspection confirms the host overrides are absent.
Host execution remains x64 and does not prove iPhone instruction execution.

## Verification

- Exact physical allocation trace replay through the actual C allocator with
  16 KiB-aligned read-only/writable shared mappings reproduces the same failed
  request and reserved-byte count.
- The complete original/patched `new_codechunk` function is extracted verbatim
  into allocation-stub harnesses. Four runs each pass 6,744 property checks:
  4/16/64 KiB pages and granules, x64/ARM64-style alignment and binding space,
  ordinary/dynamic and malloc/mmap paths, small/boundary/large methods, usable
  code space, and failed allocation. ASan/UBSan are enabled. The original
  control produces the phone's 256 KiB minimum; the correction produces 64 KiB.
- Thirty real-Mono member-access cases retain the build 15 positive and
  negative visibility behavior, with original-runtime controls.
- The full actual-Mono LuaCutscenes/MaxHelpingHand scene runs with the new host
  sizing, FNA/Metal, FMOD, real NLua coroutine, On/IL hooks, platform contact,
  saves and lifecycle callbacks. Cold and fresh cached processes are recorded
  separately. Host lifecycle callbacks do not prove iOS background survival.
- Actual host chunk sizes are replayed through the same 16 KiB alias allocator.
  Every created chunk is counted, including any recycled address. The stress
  trace contains two complete runs plus an additional 16 MiB reserve for the
  maximum 256 native hook allocations at their maximum 64 KiB size. It must
  fit the unchanged 128 MiB pool, with no recycling, and terminal exhaustion
  must still emit the diagnostic and stop before Mono uses null.
- Package/native-import closure, simulator staging/update/export/recovery and
  exact native/script geometry are checked against final artifact bytes. The
  template geometry is unchanged from build 15; a new process still always
  needs its own fresh PID/nonce script.

Final cold/cached host runs save 0 → 3 → 6. The cached run records 932 code
chunks: 54,589,024 raw bytes and 56,213,504 bytes after 16 KiB rounding. The
stress replay uses 129,204,224 of 134,217,728 bytes. The cold run also fits the
same stress criterion at 132,448,256 bytes. Final game execution records no
JIT failures, managed errors or rejected patches. The IPA is 22,777,560 bytes;
SHA256 `3fe02d4b0e56681c4b6aa21dbbf18c2b5644b272353392e3889a931744d1cbe6`.

These checks are a stronger capacity model, not a prediction of exact ARM64
code size, final performance, full Strawberry Jam compatibility, or iOS memory
pressure behavior. The next physical run must establish those bounded helper
checks and reveal actual device allocations after the correction.

## Phone handoff and next decision

Version 0.8.1 (16), build ID `sj-code-budget-20260912-16`, same bundle
`io.github.hmcneill46.celeste.everest.jit.everest`, same
`Documents/Profiles/everest-jit-canary` and installed content identity.
Local kit: `artifacts/ios-jit/sj-code-budget-20260912-16/`.
Phone folder: `iCloud Drive/Celeste JIT Tests/0.8.1-build-16/`.
See [the phone guide](../../experiments/ios-jit/sj-code-budget/PHONE_README.txt).

Update the existing guest, keep its data, and import nothing. All five ZIPs
should already be ready; identical recovery copies are supplied. Keep LC1
Launch with JIT OFF, script blank and Fix File Picker ON; StikDebug stays in
LC2. Enable the fresh process, run the helper map, wait for Lua's walk, ride
the platform, jump, Home for 30 seconds, return and jump again, require both
helper passes, Finish, wait ten seconds and export to build 16 Results. If it
crashes, reopen and export first before another JIT attempt.

Inspect actual code chunks, native/managed errors, Lua checkpoints, platform
contacts/carry, save reload and delayed liveness before accepting the build.
Then resume the separate GravityHelper optional CelesteNet integration fix,
followed by other required helpers and SJ Beginner lobby/Bing. The current
private IPA still includes prepared game IL and linked iOS FMOD; public
owner-IL preparation and redistribution remain separate work. The AOT checkout
is read-only, and no commit, push or publication is authorized.
