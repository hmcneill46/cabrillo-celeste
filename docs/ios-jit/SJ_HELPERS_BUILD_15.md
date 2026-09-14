# Build 15: real LuaCutscenes and MaxHelpingHand

12 September 2026. Build 15 implements the next bounded Strawberry Jam
compatibility test, using the original LuaCutscenes 0.2.13 and MaxHelpingHand
1.40.9 ZIPs. A small authored room exercises the actual helpers. Host gameplay
passes. The later phone run exhausted the code budget before the title; see
[the diagnosis and build 16 correction](BUILD_15_CAPACITY_AND_BUILD_16.md). See the adjacent
[SJ_HELPERS_BUILD_15_EVIDENCE.json](SJ_HELPERS_BUILD_15_EVIDENCE.json) for final
artifact identities, checks, frozen inputs and handoff state.

## What the phone test establishes

Update the existing build 14 guest, preserving its data. The two old canary
ZIPs should already be present. Import three new ZIPs: LuaCutscenes,
MaxHelpingHand and CJITSJHelpers. Stored game content should verify with
`reused=True`; no new Celeste download or build 13 extraction is necessary.
The previous export saved the canary counter at 12. The owner intentionally
deleted an older save, so do not restore it or mistake that deletion for loss.

The room `CJITSJHelpers/RuntimeRoom` has a real LuaCutscenes trigger and
MaxHelpingHand `MultiNodeMovingPlatform`. Lua uses the helper's own `walk` and
`wait` functions, calls managed C# through NLua, yields while the game runs,
and resumes the same coroutine after a native lifecycle signal. The monitor
requires one begin/wait/resume/end, no skip, a measured walk and post-resume
frames. Native code only reports the lifecycle; it does not complete Lua's
checkpoints. The platform must travel at least 64 pixels, have actual player
contact and carry an idle player at least 16 pixels. Visible LUA and PLATFORM
checks make the requested interaction concrete.

Existing canary checks remain required: real On/IL Player.Jump hooks, matching
counts, a new hooked jump after resume, real XML/YAML save/readback, FMOD,
rendering and clean worker/main-thread shutdown. The phone guide asks for
30 seconds on Home, return, more jumps, Finish and a delayed export. Host
suspend/resume calls are not evidence of physical iOS background survival.

## Compatibility changes

Three failures were reproduced before packaging:

1. **Optional dependency type discovery.** Mono 8's RuntimeModule.GetTypes can
   throw the first individual loader exception instead of returning the partial
   types through ReflectionTypeLoadException. Everest's GetTypesSafe only
   handles the latter. Re-querying types can expose failed RuntimeType objects;
   a subsequent Lua namespace scan crashed natively. A narrow GetTypesSafe hook
   handles loader exceptions only for EverestModuleAssemblyContext, reads its
   already-retained relinked Cecil metadata and retains loadable types. Calling
   IsAssignableFrom first forces Mono to report a failed parent as a managed
   error before namespace inspection. Actual MaxHelpingHand loads 443 types
   and skips four types tied to absent optional BounceHelper, FrostTempleHelper
   or FlaglinesAndSuch. No substitute dependencies or global assembly resolver
   are introduced. The existing exact-identity generated-DMD resolver remains.
   Primary implementation references: [Mono InternalGetTypes](https://github.com/dotnet/runtime/blob/v8.0.28/src/mono/mono/metadata/icall.c)
   and [Everest GetTypesSafe](https://github.com/EverestAPI/Everest/blob/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00/Celeste.Mod.mm/Mod/Everest/Extensions.cs).

2. **Generated hooks accessing protected members.** MaxHelpingHand's
   StaticMoverWithLiftSpeed hook clones Platform.MoveStaticMovers, which reads
   the protected staticMovers field. The generated Cecil assembly already has
   an exact IgnoresAccessChecksTo("Celeste") grant. Mono honors that grant for
   private/internal members but its family/family-and-assembly paths omit it.
   A small can_access_member correction honors the existing assembly grant
   before evaluating those visibility cases. Type-visibility behavior is
   unchanged. The actual-source builder recompiles only metadata/class.c into
   copied host/iOS archives; all other 259 archive members must remain identical.
   Fifteen cases on each of the original and patched runtimes verify private,
   internal, protected, family-or-assembly and family-and-assembly members, with
   correct, absent and wrong-assembly grants. The original control reproduces
   the two denied protected cases; the patch permits them while all ten negative
   cases still deny access. [Pinned Mono member-access implementation](https://github.com/dotnet/runtime/blob/v8.0.28/src/mono/mono/metadata/class.c).

3. **Obsolete MonoMod native-layout write.** The pinned SetMonoCorlibInternal
   routine writes a guessed byte inside MonoAssembly. Mono 8 has removed the
   corlib_internal field, so that write is not a valid compatibility mechanism.
   The isolated MonoMod.Utils copy replaces only that method's body with return;
   DMD's explicit access-check attribute is retained. The input DLL is pinned
   and the expected original byte-store instruction is checked before patching.
   [MonoMod routine](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.Utils/Extensions.cs),
   [Mono 8 assembly layout](https://github.com/dotnet/runtime/blob/v8.0.28/src/mono/mono/metadata/metadata-internals.h).

These changes are confined to `experiments/ios-jit/sj-helpers/` and ignored
`.build/ios-jit/sj-*` outputs. Original helper archives, accepted game/FNA IL,
original runtime source/archives, build 13/14 inputs and the separate AOT
checkout remain intact. The helper DLLs load through normal Everest relinking
and module contexts; neither helper is recompiled from decompiled source.

## GravityHelper investigation

GravityHelper 1.2.28 was also downloaded and matched to the locked SJ graph.
It still fails after the discovery/member-access corrections: compiling
GravityHelperModule.Load reports an invalid instance field type in its optional
CelesteNetModSupport integration. That method unconditionally references
CelesteNetModSupport; ForceLoadType constructs it before TryLoad tests whether
the optional module is installed. Mono's eager type loading encounters the
missing CelesteNet types first. This is a separate compatibility issue, not an
owner setup error and not proof that the gravity mechanics fail on iOS.

The attempted three-helper source, exact archive identity and failing host log
are retained in `.build/ios-jit/sj-helper-gravity-investigation/`. GravityHelper
is explicitly deferred in helper-pins.json and excluded from the delivered kit.
Do not add fake CelesteNet classes or silently remove required gameplay to
claim it passes. Next investigate a narrow optional-integration relinking fix
or a compatible upstream fix, with positive/negative tests and the original ZIP
preserved. Then restore the gravity trigger/ceiling-platform room from the
investigation snapshot. [GravityHelper upstream](https://github.com/swoolcock/GravityHelper).

## Capacity and verification

The selected real helpers create far more dynamic hooks than the earlier
canary. Host runs allocated roughly 52 MB of code in around 900 chunks, with
about 960 executable patches. The earlier device code budget was 64 MiB.
Build 15 reserves **two 64 MiB regions, 128 MiB total** to leave headroom for
ARM64 code and allocation differences. This is a bounded diagnostic budget,
not an iPhone memory/performance measurement or a final arbitrary-mod policy.
There is still no late growth or managed-runtime restart in the same process.

The packaged ARM64 constants, native-generated simulator request and exact
script template are checked together: 8,192 mocked page acknowledgements,
checked mailbox completion/detach, wrong PID and stale nonce rejection, plus
rejection of historical build 7/8/12/14 geometries. The old script is not valid
for build 15. The native launcher supplies the new current-session script.

Real host tests use pinned Mono 8.0.28 x64 cooperative GC with AOT/interpreter
disabled, original helper DLLs, actual FNA/Metal and FMOD/Lua, Metal API
Validation and NSZombieEnabled. Separate fresh processes reuse verified content
and reload the mod counter. Final exact-input host/package/simulator receipts
are referenced in the evidence file; earlier exploratory failures are retained
and are not counted as passes. The simulator covers native archive staging,
five-mod import/JIT gating, same-bundle update, 800-event persistence, export
and prior-console recovery. Physical file-picker behavior uses the owner's
proven LiveContainer Fix File Picker setting.

The unchanged content store/native-copy/paired-renderer files are compared with
accepted build 14; their prior detailed regression suites are inherited rather
than being represented as newly executed. Exact package checks ensure no
Content assets, Apple managed bindings, signature, provisioning profile or
dSYM is inside the IPA; matching symbols remain beside it. All static native
imports from game/FNA/KeraLua resolve, and both original helper DLLs declare
zero native imports.

## Delivery and next decision

Version 0.8.0 (15), same bundle
`io.github.hmcneill46.celeste.everest.jit.everest`, same
`Documents/Profiles/everest-jit-canary`, same persistent content identity.
Local kit: `artifacts/ios-jit/sj-helpers-20260911-15/`.
Phone folder: `iCloud Drive/Celeste JIT Tests/0.8.0-build-15/`.
Follow [the phone guide](../../experiments/ios-jit/sj-helpers/PHONE_README.txt).
Export Results even after a crash; keep all earlier Results and original saves.
The template is included for reference and current-session manual export
remains available. Local iCloud placement is distinct from confirmed phone
download; see the delivery receipt for what has actually been observed.

If the phone passes, review exact identities, cached content, retained ZIPs and
save counter, actual Lua checkpoints/platform contacts, code capacity, resume
and delayed liveness. Then tackle GravityHelper and other required helpers,
followed by SJ Beginner lobby/Bing. Full SJ remains untested; its locked archive
set exceeds the owner's 1 GB cloud handoff limit and must not be split to evade
that limit. A user-downloaded campaign is a later import-flow test.

The app is small because game Content remains in the guest's persistent data.
It still contains private prepared game IL and linked iOS FMOD; it is not yet
the public owner-IL-preparation launcher. No commits, pushes or public uploads
were made. Useful helper references are the
[LuaCutscenes API/examples](https://maddie480.ovh/lua-cutscenes-documentation/modules/example_talker.html)
and [Max/MaddieHelpingHand source](https://github.com/maddie480/MaddieHelpingHand),
with exact tested historical ZIP hashes recorded in helper-pins.json.
