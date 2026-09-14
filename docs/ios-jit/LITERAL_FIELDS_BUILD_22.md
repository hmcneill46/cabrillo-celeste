# Build21 session stop and build22 constant-field fix

Build21 stopped loading **Paint by mosscairn**, intro room, after the original
EeveeHelper attempted to enumerate entity fields using MonoMod DynamicData.
MonoMod generated `ldsfld`/`stsfld` instructions for `Celeste.Decal.Root`, which
is a literal string constant. Mono rejects those instructions because a literal
has no stored field value. Everest caught the exception twice; the native host
then stopped its frame loop because the JIT profiler reported two failures.
The app stayed alive and exported diagnostics. There is no intended timer and
no evidence of a setup mistake, expired JIT permission or exhausted code arena.

## Phone evidence

The [validated export](BUILD_21_SESSION_STOP_EVIDENCE.json) matches the exact
0.11.1 (21) IPA, adapter and FNA hashes. Its raw JSON is preserved privately in
`.build/ios-jit/device-evidence/2026-09-12/build-21-results/`, with an executable
validator. SHA256: `6aae3e3e444709d3cfb2a4abbad3fd3cc2e9737238541c65289ffd0ea587fa34`.

- All 26 native and six graphics checks passed; debugger detached.
- 54 ZIPs were enabled, with all 56 expected metadata identities verified.
- Failure occurred after 6,702 callbacks, about 124 seconds after game start.
- Code allocation was 180 MiB of 512 MiB; 332 MiB remained. This is code-arena
  usage, not total process memory. Footprint at stop was about 3.80 GB.
- The previous missing FNA render-target method error is absent.
- The propagated-managed-exception counter stayed zero because Everest handled
  the error internally. Build21's native error-summary field was consequently
  empty, even though the console retained the full cause and stack.
- Finish/save shutdown did not complete. This export does not establish clean
  saves, normal map progression or fresh-process save reload.

## Fix and scope

Isolated source: `experiments/ios-jit/launcher-reflection/`, version **0.11.2 (22)**,
build ID `launcher-reflection-20260912-22`. Build21's source, delivered files and
snapshot remain immutable. The AOT checkout and original owner files are untouched.

The build-time MonoMod patch adds one internal emission helper and changes the
two static field emission call sites inside `CreateFieldInvoker`'s existing
closure. Literal reads emit the metadata constant using the correct IL opcode;
literal writes throw `FieldAccessException`. Existing type validation, result
boxes, caches, instance-field access and ordinary static fields remain in place.
This fixes the shared reflection operation rather than changing a map/helper ZIP.
The accepted Mono 8 corlib-structure correction is retained. Against the pinned
raw DLL, 2,384 other methods and all 578 fields remain unchanged, as do assembly
identity, dependencies and embedded resources. No new runtime DLL is added.

The native host now retains the first JIT method failure as a bounded fallback
summary, while a propagated managed exception takes precedence. It continues to
stop on JIT failures; no failure counter or allocator safeguard is bypassed.

The accepted FNA extension, Mono archives, native renderer, original game IL and
mod ZIPs are unchanged. Profile paths, selection, saves and content remain in use.
The additional direct Paint command and graphics test are desktop-only regression
paths; the phone uses normal Celeste menus and entrances.

## Validation and limits

[Build22 evidence](LITERAL_FIELDS_BUILD_22_EVIDENCE.json) records the final input
hashes and test receipts. The literal regression uses the accepted Mono 8 runtime
with AOT/interpreter disabled. The original build21 DLL reproduces the exact
`MissingFieldException` for the actual Celeste constant. The patched DLL passes
137 checks across its real field, string/empty/null, boolean/character, signed and
unsigned numeric, floating-point and enum constants, both fast-invoker APIs,
DynamicData lookup/enumeration, rejected writes, repeated reads, and ordinary
instance/static/readonly/decimal/method/boxed-struct controls, with zero JIT failures.
The patch repeats deterministically and rejects wrong/already-patched inputs.

The exact new adapter/MonoMod DLLs pass real Mono/Metal Paint intro loading,
its original EeveeHelper gates, retained-texture GPU readback, the full original
Lua intro through ordinary confirm input, movement/jumps, jumps after resume,
clean Finish, whole-profile save/readback, and a fresh-process repeat. The reload
uses the existing slot and reads the previous canary sidecar counter before
writing its next value. This test starts a fresh map session; it does not prove
resuming the exact saved room/checkpoint through normal menus.

The final baseline harness with the old build21 MonoMod DLL reproduces the exact
Paint failure and verifies the native JIT summary. Full SJ lobby/Bing plus 33
Frost/FNA controls, normal example enabled/disabled, native catalogue, bounded
logging, real SwiftUI/picker interactions, simulator import/update/recovery,
package and fresh-request protocol checks all pass. No test fixture DLL is bundled.
An initial desktop-only display-backbuffer read crashed inside native FNA3D.
Further source inspection shows `METAL_ReadBackbuffer` builds a local texture
descriptor without assigning its native texture handle before passing it to
`METAL_GetTextureData2D`. This is a separate known backend issue, not the phone's
MonoMod failure. The final Paint test reads the retained gameplay texture and
passes. General `GetBackBufferData` compatibility is not established. Investigate
and test that API in an isolated renderer follow-up before broader product work.
Intermediate test logs are preserved privately and are not acceptance receipts.
This paragraph corrects the preliminary frame-lifetime inference in the frozen
pre-handoff report; the code/package hashes and passing test results are unchanged.

The final unsigned IPA is 23116505 bytes (about 23.1 MB), SHA256
`b9a89008136a1dbf0e409c5fd22095df876a1430992a5110348a6cf5f88dd17e`. Its executable/dSYM identity is `UUID: EB66D6A0-13F1-3231-885C-02A5AC681617`.

Physical build22 acceptance remains pending. Host testing does not establish
all-map compatibility or physical ARM64 execution of this fix.

## Physical retest

All eight kit files (23,133,578 bytes total) have confirmed iCloud upload.
Phone download and physical execution are not yet observed.

Use `iCloud Drive/Celeste JIT Tests/0.11.2-build-22`. The kit contains the unsigned
IPA, matching script template, phone instructions, identities and checksums.
Update LC1 while retaining its data; leave StikDebug in LC2. Keep Launch with JIT
OFF, saved script blank and Fix File Picker ON. Use a fresh inline request for
every new process. No game or SJ reimport is needed.

Test the normal Beginner-lobby entrance to Paint, its intro and subsequent play,
then background for 30 seconds, resume, Finish and export. In a fresh process,
verify the saved progress and export separately. Put exports in this version's
Results folder. Keep an incomplete SpringCollab import disabled for this test.
After a failure, export before retrying. Build19 remains the accepted fallback.

## References and subsequent work

The pinned [MonoMod field emitter](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.Utils/FastReflectionHelper.cs)
uses stored-field instructions for every static field. Its
[DynamicData cache](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.Utils/DynamicData.cs)
creates fast invokers under a fallback guard, but the failed read occurs later
when the cached delegate is invoked. This explains why the cache's reflection
fallback does not rescue this phone session. The correction is local and tested;
no upstream fix or public compatibility claim is implied.

Subsequent phone review: [recorded gameplay and save readback pass](BUILD_22_GAMEPLAY_ACCEPTANCE.md),
including longer normal room progression; final shutdown and subsequent game
reload are not established by that export. The owner has now reactivated and
expanded the product requests. See [the native launcher roadmap](NATIVE_LAUNCHER_ROADMAP_2026-09-12.md)
for a general mod catalogue, dependency plans, loading progress, native files and
controls, plus a required iOS support module for Quit and input prompts. Public
original-IL preparation and FMOD permission remain release gates. No commits,
pushes or public distribution were performed.

Build21’s superseded cloud IPA was removed only after its exact local hash was
verified. Build19’s cloud fallback and every Results folder are preserved.
The frozen source snapshot inherits verified build21; see the delivery receipt
for its hash and the handoff addendum for the later backbuffer diagnosis.
