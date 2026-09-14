# Everest runtime upgrade assessment — 13 September 2026

The next implementation should bring the embedded Everest runtime from 1.6458.0
to **stable 1.6531.0**, pinned to `d72e94f4b9e62b91cbdea674587ed39d53de9550`.
Build26 now supplies the accepted fresh Spring dependency/gameplay baseline.
The official release API identifies 6531 as the latest stable release, published
5 September 2026. This version meets the recorded minimums for
ExtendedVariantMode 0.51.0 and MaxHelpingHand 1.40.10; satisfying those minimums is
not yet proof that these versions execute correctly on iOS.
[Official release](https://github.com/EverestAPI/Everest/releases/tag/stable-1.6531.0).

This is a source/integration assessment, not a compiled or delivered build27.
The captured primary responses and hashes are recorded in
[the assessment evidence](EVEREST_RUNTIME_UPGRADE_ASSESSMENT_EVIDENCE.json).

## Scope of the upstream change

The exact comparison from accepted commit
`4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00` contains nine commits and five changed
files. Two are TAS-check infrastructure; the three runtime source changes are:

| File | Change | Relevant verification |
| --- | --- | --- |
| `Everest.Content.cs` | Intern repeated asset-extension strings | Full asset/mod load, memory observations |
| `ModUpdaterHelper.cs` | Return an enumerable directly, removing an enumerator wrapper | Mirror URL enumeration; preserve native installer transport and integrity checks |
| `Patches/Dust.cs` | Guard Dust.Burst/BurstFG when the scene is not a Level | Actual game patching; normal Level particles and scene-transition/dream-block reload controls |

There are no project/package/submodule, FNA, MonoMod or runtime-target changes in
this comparison. The five accepted local embedded-Everest adaptations are in
different files. This makes an isolated source rebuild a reasonable bounded next
step, while actual compilation/patching and gameplay remain required gates.
[Pinned source comparison](https://github.com/EverestAPI/Everest/compare/4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00...d72e94f4b9e62b91cbdea674587ed39d53de9550).

## Integration work required

Create an independent build27 source/staging lane, for example
`experiments/ios-jit/launcher-runtime` and `.build/ios-jit/launcher-runtime*`.
Copy verified inputs or use them read-only. The old preparation/dependency
builders write directly into `.build/ios-jit/everest-source`, `everest-game` and
`everest-dependencies`; do not invoke them unchanged. Isolate source checkout,
managed outputs, NuGet/CLI caches, original-IL preparation and generated hooks.
Keep the AOT checkout and accepted26/24 source, package and renderer untouched.

Reapply the accepted embedded source behavior: native session ownership, no
desktop runtime updater, no background desktop mod updater, no native Discord
integration, no file-watcher hot loading, safe missing entry assembly handling,
and worker-scheduler disposal. Regenerate the patched game and hook assembly
from the original licensed input with the actual new Everest source. Preserve
the subsequent accepted game/platform transformations, support-module ABI,
MonoMod fixes and build26 CoreLib reflection binding. Record each input/output
identity. Changing a displayed version or resolver constant alone is insufficient.

Keep accepted Mono 8 archives, JIT arena geometry, StikDebug protocol, native
renderer and FNA fixes unchanged unless a concrete failing test requires an
independent correction. Their source dependencies did not change upstream.

Use one verified runtime-identity source for native preflight, dependency planning,
update checks and diagnostics, and verify it against actual managed registration.
Build26 currently repeats Everest/EverestCore1.6458.0 in
`ModLibrary.preflight` and `DependencyPlanner.builtins`, while the embedded source
patch separately sets Everest's VersionString. The next implementation must keep
all of them aligned with the bytes actually shipped.

The update cache needs a runtime/policy fingerprint. `ModUpdates.CheckCache`
currently keys freshness by schema, time and installed-library revision. Its
cached `canUpdate`/reason values are replayed directly by
`DependencyInstaller.checkUpdates` when the library and index hashes match.
An IPA upgrade can leave those keys unchanged while changing compatibility.
Re-evaluate cached candidates against current built-ins and pins, or invalidate
the derived availability record when runtime/policy changes. Preserve verified
ZIP hashes and downloaded index data; a runtime change should not require
rehashing every large archive or downloading everything again. Cover upgrades
and downgrades, offline mode, automatic checks disabled and automatic backoff.
The final plan/apply gate must still validate the current runtime independently.

Retain existing compatible installed helpers. The two historical candidates
remain fallback metadata, separate from the three app-managed compatibility
pins. After the runtime upgrade, prefer compatible current candidates when
resolving missing dependencies and offer the two newer versions as reviewed
updates. Do not silently update user mods, remove old archives, alter profiles,
or make the desktop Everest installer available inside the launcher.

## Gates before the next phone handoff

1. Bind the new managed version/source/assemblies and native built-ins to one
   receipt; validate actual patch output and retained compatibility surfaces.
2. Pass the real Mono reflection, hooks, input/support, FNA/Metal readback,
   pending-save/Quit and fresh-process controls using isolated outputs.
3. Boot the original fresh Spring graph with current ExtendedVariantMode and
   MaxHelpingHand, verify actual registered versions, then play a real Spring
   route. Replay updated Paint and the full SJ fixture without editing originals.
4. Cover current/old-runtime cache transitions, genuine too-new requirements,
   disabled updates, compatible installed versions, earlier-candidate selection,
   actual old→new reports and recovery/cancellation behavior.
5. Deliver the next small unsigned IPA through the existing versioned iCloud
   process, preserving the accepted26 fallback. Phone testing should update
   existing data, verify the two reviewed old→new updates, play, background/resume,
   Quit, reopen and export both sessions. Existing game imports remain reusable;
   every new process still needs its fresh JIT request.

Only after that acceptance should broader catalogue installation become the main
feature. The native loading screen, full-profile save/settings manager and touch
editor remain planned. The original-IL public-package and FMOD permission gates
remain separate. No source/runtime build or remote write was performed for this
assessment.
