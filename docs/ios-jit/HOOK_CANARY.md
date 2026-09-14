# Build 7 — actual MonoMod hooks and resumed managed execution

**Physical follow-up:** [build 7 selected the wrong native protocol header and
stopped before debugger attachment; build 8 corrects it](BUILD_7_PROTOCOL_AND_BUILD_8.md).
The two 4 MiB regions described below were the intended geometry; build 7
actually requested 64 KiB per region. Preserve this initial report as history
and use the linked correction for the current test.

11 September 2026. **Build 7 is ready for a physical G2 test.** The actual pinned
Mono host regression, protected-alias regression, unsigned ARM64 package and
simulator launcher checks pass. ARM64 hook execution on the phone remains
unverified until the owner's build 7 logs are reviewed.

This follows the [accepted build 6 managed JIT result](MANAGED_EXECUTION_PASS_2026-09-11.md).
The next uncertainty is whether the actual hook machinery needed by Everest
works through iOS 26's prepared RX/RW memory, including execution after a real
background interval. Testing that now gives much more useful failure evidence
than combining the hook port with the entire game and mod ecosystem at once.

The implementation is [hook-canary](../../experiments/ios-jit/hook-canary/README.md).
Its [physical instructions](../../experiments/ios-jit/hook-canary/INSTALL.md) and
[build evidence](HOOK_CANARY_EVIDENCE.json) are the development handoff.

## Exact build and preserved foundation

| Component | Identity |
| --- | --- |
| Device build | `hook-canary-20260911-07`, version 0.3.0 (7) |
| App | Celeste Hook Canary; same guest bundle ID `io.github.hmcneill46.celeste.everest.jit.canary` |
| Runtime | Mono 8.0.28, `46295af5828b062bbbf93a9cef50fd8cb9fbcb09`; AOT and interpreter disabled |
| MonoMod | `dfc30a1506d37fb88a2c2be004f525205f46a24c`; Core 1.3.1, RuntimeDetour 25.3.1, Utils 25.0.9 |
| Iced source | `c50f29b7bc305696895c075f3fc7719751426b12` |
| Other managed dependencies | Cecil 0.11.6, Backports 1.1.2, ILHelpers 1.1.0 |
| Managed closure | 168 original iOS framework DLLs plus 10 MonoMod/Cecil DLLs |
| External fixture | `HookCanary-v0.3.0.dll`, 22,016 bytes, compiled after IPA packaging |
| Compiler | Xcode 26.6 / 17F113, iPhoneOS SDK 26.5, arm64, minimum iOS 26.0 |
| Build-only SDKs | SDK 9.0.300 for MonoMod's newer MSBuild requirements; SDK 8.0.422 for fixture IL |

The runtime archive and component archives, framework IL, runtime configuration,
7-file runtime patch and debugger script are hash-identical to build 6. The
8 MiB allocation budget is unchanged. The worker detach correction is reused.
No G1 source or delivered kit was changed. The active AOT checkout, original
game inputs and AOT build scripts were not modified. HEAD remains
`b65bedd20016dc3482d7702d7f0a9707bc2b1479`; there was no commit, push or GitHub write.

## What changed in MonoMod

The canary keeps the pinned library's ordinary Hook/ILHook implementations,
chain management, IL cloning and architecture emitter. It installs an explicit
`AppleJitSystem` before the first default platform lookup. This routes code
writes through a small native bridge and retains the standard Mono detour
factory. The backend is designed for this pinned Mono embedding setup.

Three upstream compatibility problems were addressed in the isolated clone:

1. `PlatformTriple.SetPlatformTriple` has reversed initialization guards at
   this revision. The guards now reject an already initialized singleton while
   permitting its first explicit installation.
2. The Mono DynamicMethod adapter looks only for legacy `mhandle`; the matching
   .NET 8 CoreLib uses `_mhandle`. The adapter checks the newer field first.
3. Legacy Darwin/uname detection cannot distinguish iOS correctly and sees an
   iPhone model string instead of an ARM64 machine name. The net8 build uses
   CoreLib's Apple OS checks and runtime process architecture.

A conditional build property restricts this experiment to net8.0 and omits
unneeded desktop native helpers. The six existing-file changes and added
backend are pinned and hashed. Source references:
[platform installation](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.Core/Platforms/PlatformTriple.cs),
[Mono adapter](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.Core/Platforms/Runtimes/MonoRuntime.cs),
[platform detection](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.Utils/PlatformDetection.cs).

The native bridge verifies a Mono method's actual code extent or an explicitly
owned hook allocation before any write. Device code must lie inside prepared
memory, have ARM64 alignment, and expose distinct exact-RX and exact-RW aliases.
It backs up from RX, writes through RW, flushes caches and compares the result.
Reserved page padding alone does not authorize a patch. Mixed protection
mappings are rejected conservatively by its readable-memory query.

The unchanged upstream ARM64 detour uses a 16-byte sequence: load an absolute
destination into x9, branch through x9, and store the 64-bit destination beside
the instructions. If the actual method is too small, this bridge rejects the
write rather than extending into a neighbor. Original calls use MonoMod's
managed IL-cloning path. [Pinned ARM64 emitter](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.Core/Platforms/Architectures/Arm64Arch.cs).

## Test flow and evidence

The app keeps the successful slot-1 → slot-2 StikDebug route. It verifies fresh
PID/nonce preparation, native execution and debugger detach before starting
Mono. The external fixture is imported independently of the IPA.

```mermaid
flowchart LR
    A[Import new test DLL] --> B[Enable JIT through slot 2]
    B --> C[Native checks and G1 fixtures]
    C --> D[Real Hook and ILHook tests]
    D --> E[Keep two hooks installed]
    E --> F[Home Screen for at least 20 seconds]
    F --> G[Execute retained hooks and create new hooks]
    G --> H[Export diagnostics]
```

The first hook phase performs 32 assertions: method layout and DynamicMethod
handle checks; original calls with changed arguments; undo, reapply and dispose;
configured ordering independent of creation order; removal and reinsertion in
chains; IL replacement combined with ordinary hooks; instance calls; a 32-byte
struct return and floating-point struct arguments/returns; managed exception
propagation through original calls; GC while a hook is held; and 64 calls from
a managed worker. A Hook and an ILHook remain rooted across native-worker detach.

After a real background/foreground interval, the native launcher attaches a
worker to the existing domain. Ten more assertions execute the retained hooks,
run GC, remove them and verify the restored originals, create a new DynamicMethod,
and install/remove fresh Hook and ILHook instances. It detaches cleanly again.
The resume path does not rerun arena initialization or native rewrite tests.
The complete run emits 42 assertions and two phase-completion markers.

The fixture follows the real continuation, configured ordering and disposal
semantics described by [MonoMod's RuntimeDetour usage guide](https://monomod.dev/docs/RuntimeDetour/Usage.html).
It only calls the original continuation within the active hook invocation.

| Local verification | Captured result | Boundary |
| --- | --- | --- |
| Real pinned macOS Mono | All 8 G1 stages, 42 hook assertions plus 2 completion markers, 108 actual code patches, both worker detachments | x64 Mono execution; no physical background interval |
| JIT profiler in that run | 2,986 completion events, 1,302,301 compiled bytes; new DynamicMethods in both phases, no JIT failures | Host measurements; not a phone memory/performance estimate |
| Actual device bridge with host aliases | 5 successful writes, 11 rejected writes; ASan and UBSan pass | Real RX/RW mappings; narrow mocked Mono metadata; no ARM64 execution |
| iOS simulator 26.5 | Import, disabled run/resume gates before JIT, export, 800 persisted/rendered burst events, prior console/session recovery | UI-only x64 build; share-sheet interaction not automated |
| Final IPA | ARM64 executable, no signature/profile/embedded dSYM, exact 178-DLL closure, fixture absent from payload | Packaging proof |
| External fixture | Deterministic IL hash matches the final real-Mono host test and compilation occurred after IPA packaging | Phone execution pending |

Local receipts and logs are copied beside the unsigned IPA. The 70 source files
identified by its receipt are preserved under
`.build/ios-jit/device-evidence/2026-09-11/build-7-ready/source-snapshot/`.
The external dSYM matches executable UUID `06BA762E-0B3F-3797-9040-9A8DCBE7247A`.

## Findings to carry forward

The pinned public Hook API explicitly rejects generic source methods and methods
on generic declaring types, including closed types. An initial fixture attempted
one and received the upstream ArgumentException. The final test verifies that
restriction and separately confirms generic execution. The library's policy was
not bypassed to manufacture compatibility. [Pinned Hook.CheckSupported](https://github.com/MonoMod/MonoMod/blob/dfc30a1506d37fb88a2c2be004f525205f46a24c/src/MonoMod.RuntimeDetour/Hook.cs#L707).

This is a bounded hook canary, not full Everest acceptance. Hook mutations are
serialized; the separate managed thread calls a stable installed hook and is
joined before removal. Installing a 16-byte patch while unrelated threads
execute that target remains unverified. The fixture uses non-inlined targets;
late hooking of already-inlined game calls and the adapter's lack of Mono
recompilation notifications need deliberate treatment in the game integration.

The native allocation ledger is capped, executable reservations last until
process exit, and there is no growth, unload or runtime restart. The iOS path
has no host RWX fallback or interpreter. Invariant globalization and the existing
native import table remain canary limits. The full game's native libraries,
FNA/SDL lifecycle and content loader still need integration.

If the exact build passes on the phone, the recommended next build is **G3:
Celeste's game loop through this managed JIT host**, retaining the existing
native graphics/audio/input implementation in the separate JIT lane. Establish
launch, a playable baseline and pause/resume before enabling Everest and a small
real mod. Keep the managed game/FNA/Everest/mods in one runtime with IL and metadata
retained. Preserve the fully AOT vanilla and static-AOT/SJ products independently.

## Physical handoff

The complete six-file phone kit is **10,904,418 bytes**, under the owner's 50 MB
iCloud limit. It is staged at:

`iCloud Drive/Celeste JIT Tests/0.3.0-build-7/`

Use [the phone guide](../../experiments/ios-jit/hook-canary/INSTALL.md) and save
its diagnostic export into that folder's `Results` subfolder. Export remains
available after a crash and includes previous sessions. The same guest bundle
identity preserves the future direct USB collector path; no phone installation,
JIT enablement or debugger attachment was performed by the host this turn.

Local unsigned IPA:
`artifacts/ios-jit/hook-canary-20260911-07/CelesteJITHooks-unsigned.ipa`

- IPA SHA-256: `59edb0bd96ab6f870e16c5657c87298e5cbdb25916307bfc40663f9095512fe0`
- DLL SHA-256: `c4256d9f5f6400fe5b23a7b1590c4b343c280a90d882fbce3efb37999dc28157`
- Matching script template SHA-256: `79d53b7c77fd2cfdb6045e1b699c2b8e0eca3822d9cfb98a03556b35d674b72b`

The delivered template is reference-only; the app generates the runnable script
for its actual current PID and mappings. Delivery and cloud-upload observations
are recorded in the evidence JSON, separately from actual phone download.


**Delivery confirmation:** all six files and the Results directory report
uploaded with no iCloud error as of **2026-09-11 09:44:02 UTC**. Their locally
copied bytes match the kit's SHA-256 manifest. A transient account-access error
cleared without changing account settings. Actual phone download is unobserved.
The owner reported that iCloud appeared signed in. Read-only discovery also
found the paired phone over the local network; iCloud remained the handoff route.
