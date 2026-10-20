# Build55 /0.26.1 — saved-game startup repair

3 October2026. Local owner-requested diagnosis and repair in
`launcher-saved-game`, on `codex/game-input-compatibility`. No commit, push,
workflow run or public release is requested. Public workflows still select52.

## Phone evidence

The owner's54 export matches the final54 BuildInfo exactly. Its session passes
all26 native JIT checks, completes the Home Screen launch and reports no storage
error. Both game-start attempts verify all1,216 saved asset files (1,158,665,183
bytes), then reject game-code preparation before loading Celeste. Feather input
does not run. The retained52 history records successful prepared-code reuse and
game startup.

The exact export is2,417,490 bytes, SHA256
`e18e57478734e79fdb40d3cd18d047a4d31fbd148ca1999ec55dc3fd379e6331`.
It stays in54/Results and in the ignored private evidence directory. See the
[54 report](FEATHER_TOUCH_BUILD_54.md) and the accompanying55 evidence ledger.

## Cause and repair

Native startup always sets `CJIT_CONTENT_ARCHIVE` to the expected
`ContentImport/game-input.zip` pathname. A successful import removes that
temporary ZIP. ContentStore already treats the absent file as a request to use
the saved assets. The53/54 GameCodeStore instead interprets any nonempty path as
a selected ZIP and rejects the missing file. Its host warm tests passed an empty
string, which did not reproduce the native caller's contract.

The production repair is one condition in GameCodeStore: a new import requires
both a nonempty path and an existing file. Otherwise it selects the saved source,
verifies every original code file against the trusted recipe, and reuses or
rebuilds the prepared cache. It retains the previous default source for pre-53
installations without a selected-source pointer. A present but invalid ZIP still
fails; damaged or absent originals still require import. No game-file validation
is removed, and saves/profile data are outside this operation.

The feather adapter, all native code, SwiftUI, input transformations and original
game adaptations stay exact54. The seven public MonoMod/NLua libraries rebuild
from the same pins. Bootstrap changes for this repair; the preparation recipe
tracks the actual rebuilt tool hashes. The first successful55 launch can rebuild
its cache from retained originals. Keep the existing data container and shortcut49.

## Verification

`probe_saved_game.py --original54-control` compiles the frozen54 preparation
source with the new regression fixture and reproduces the exact missing-path
rejection after first proving the cache works with a null path. Its expected
native assertion is the test runner's failing-result contract, not a new app crash.

The repaired store checks native-style missing paths for all nine supported
original archives/four input combinations, cache repair, pre-53 selection,
invalid replacements, corruption, cancellation and interrupted preparation.
`check_saved_game_host.py` exercises the public55 payload with a real standard
original: first import, cached startup using the absent native ZIP path, and a
pre-53 storage contract with retained originals but no current cache or selection
pointer. Each run checks gameplay, feather off/on, hair, desktop saves, resume
and normal Quit. Test instrumentation is not bundled.

The final managed receipt is `.build/saved55-managed-a/receipt.json`. Results:

| Check | Result |
| --- | --- |
| Original54 source control | Reproduces the phone's missing-ZIP rejection |
| Store recovery/validation | 22 controls pass |
| Nine original game packages | 97 checks pass, including absent native ZIP paths |
| Full real-game runs | First import, cached missing-ZIP start and legacy rebuild all pass |
| Feather input | 37 gesture and37 original-game checks per run, off/on |
| Python build/release controls | 59 pass |
| Bootstrap method comparison | Only GameCodeStore.Prepare changes among372 method bodies |

The full runs also pass hair, desktop save transfers, save/resume and normal Quit.
The legacy rebuild preserves every original file byte. Its cache rebuild takes
14.787 seconds on this host; the cached path in the separate warm run
takes0.159 seconds. These are observations from the Mac fixture, not phone timing
promises. Receipts are `.build/saved55-store-a/receipt.json`,
`.build/saved55-host-a/receipt.json` and
`.build/saved55-original-control-b/receipt.json`. The initial control harness
needed a log-decoding correction for mixed Mono/native output; its private run is
retained and is not counted as a passing control.

191 of199 managed DLLs match54 exactly. Bootstrap changes and seven pinned public
dependencies rebuild. The actual feather game adapter is byte-identical to54;
all native/SwiftUI source files and16 native dependencies remain unchanged.
Earlier54 Motion Smoothing and simulator UI results retain their original scope;
they are not relabelled as new55 runs.

The accompanying ledger records receipt hashes and package identity.
Host results are separate from phone acceptance, sustained120Hz display
evidence and earlier save-manager/iPad gates. No phone is modified by this repair.

## Reproduction

Use `tools/build_release55.py` for fresh public dependencies and an explicit
developer-owned FMOD SDK. Local iteration uses `build_saved_game_managed.py` and
`compile_release55.py`, with explicit verified native/FMOD receipts. A public
NuGet archive cache may be passed only if every archive matches its release pin;
sources are compiled and packages extracted afresh. Game code/assets and SDK
components remain excluded from Git and the IPA. FMOD's built-runtime permission
and developer SDK restriction remain as documented in [RELEASING](../RELEASING.md).

## Package and delivery

The unsigned `Cabrillo-0.26.1-build-55-unsigned.ipa` is18,787,140 bytes,
SHA256 `e257b92175657c1d1374700c58bd93036795d499407c3a2c5bb43f42d42b3645`.
Both package auditors pass, with199 managed assemblies, no original/prepared game
code or assets, and a matching dSYM. All273 captured app inputs are frozen in
`artifacts/cabrillo-build55-final`; use56 for new implementation. All16 checked
earlier source manifests still match.

The eight-file kit has exact local readback and confirmed upload in iCloud Drive
→ Celeste JIT Tests → `0.26.1-build-55`. The superseded54 cloud IPA was retired
after exact retained-local-copy and
receipt verification. Its Results export, all Results folders, local54 artifacts
and accepted fallbacks remain. Local cloud total is998,666,002 bytes.
The [evidence ledger](SAVED_GAME_BUILD_55_EVIDENCE.json) records exact receipts.
