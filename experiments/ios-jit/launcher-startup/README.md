# Build 29: startup preparation

Local preparation for responsive loading, while build 28's phone evidence is
pending. Identity: **Cabrillo 0.15.1 (29)**,
`launcher-startup-20260915-29`. This is not a responsive loading implementation
or a new phone handoff.

`src` and `native` derive from the frozen build 28 lane. Changes are the Cabrillo
Play title and four passive startup timings, with distinct milestone retention.
The native bridge still performs the same work on the same threads. The accepted
201 managed assemblies, native runtime/renderer and JIT protocol are reused.
Bundle/executable identity and `GameLibrary` / `Profiles/sj-first-play` persist.

## Build

Run from the Cabrillo root:

```sh
python3 tools/build_development.py --check-inputs
python3 tools/build_development.py \
  --work .build/my-startup-preparation \
  --output artifacts/my-startup-preparation
python3 tools/verify_development_build.py artifacts/my-startup-preparation
python3 -m unittest discover -s tools/tests -v
python3 tools/check_development_package.py artifacts/my-startup-preparation \
  --output .build/my-startup-package-controls
```

To compile the native retention regression on the host, choose a fresh test
directory and run:

```sh
mkdir .build/my-startup-retention
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer xcrun clang \
  -fobjc-arc -O2 -Wall -Wextra -Werror -Wno-deprecated-declarations \
  -framework Foundation -Iexperiments/ios-jit/launcher-startup/src \
  experiments/ios-jit/launcher-startup/tests/StartupRetentionTests.m \
  experiments/ios-jit/launcher-startup/src/CJEventStore.m \
  -o .build/my-startup-retention/test
.build/my-startup-retention/test .build/my-startup-retention/result
```

Work/output directories must be new and inside `.build` / `artifacts` respectively.
The recipe pins Xcode 26.6 / 17F113, iPhoneOS SDK 26.5 and the local private
capsule. It compiles current native/Swift/vendor source, creates fresh symbol
tables, assets, BuildInfo and a native receipt, links once and keeps that UUID.
Its freshly generated dSYM stays outside the unsigned IPA. It never invokes the
historical builders, replays ZIP timestamps or restores a previous UUID.

`Dependencies.json` identifies reused libraries, headers, shared/vendor source
and the capsule manifest by hash. Active runtime/policy resources come from this
lane; original game manifests, managed assemblies and licensed inputs remain
explicit private dependencies. There is no managed compiler mode: changing game,
adapter, Everest or FNA source requires a separately ported managed recipe and
new pinned outputs. The native build must not be presented as such a rebuild.

`BuildIdentity.json` and `Info.plist` are this lane's version authority. A later
implementation requires another version/build identity and fresh evidence.
Preserve the emitted build 29 preparation artifacts.

## Measurements

`startup_phase_begin` and `startup_phase_end` carry `phase`, a shared monotonic
`started_uptime`, actual `thread_id` and `main_thread`. End events add duration,
`same_thread` and an outcome. Four phases are measured:

- `catalogue_quiescence`: native cancellation/drain; `returned` only describes
  callback return. The separate nested `catalogue_quiesced` payload is the gate.
- `runtime_prepare`: allocator, Mono initialization and adapter lookup on the
  worker; `ready` or `failed`.
- `content_prepare`: attached worker verification/import; `ready`, `cancelled`,
  `not_ready` or `failed`.
- `managed_start`: the existing main-thread Start call; `returned` is not proof
  of a first frame, gameplay or complete native window handoff.

Each begin/end pair is a retained milestone keyed by its phase, still subject
to the existing global bounds. An interrupted call can have only a begin event.
No timer produces synthetic progress or kills a slow operation. Normal existing
graphics/first-frame/save/Quit diagnostics remain authoritative.

See [the preparation report](../../../docs/ios-jit/STARTUP_PREPARATION_BUILD_29.md)
for current validation, exact thread boundaries and the managed implementation
sequence after phone 28 acceptance.
