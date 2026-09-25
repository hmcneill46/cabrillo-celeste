# Build37 — Everest stable1.6580

25 September 2026. Version0.20.0, `launcher-everest6580-20260925-37`.
The owner requested the latest Everest while the build36 Motion Smoothing fix
was being delivered. The latest stable release checked through GitHub's release
API was [1.6580.0, released19 September](https://github.com/EverestAPI/Everest/releases/tag/stable-1.6580.0),
commit `082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75`. This was22 commits and22 changed
files after the pinned1.6531 source. Stable is the selected update channel.

## Changes and preservation

The actual Everest source and registered runtime identity become1.6580.0;
this is not a metadata-only version bump. The new release includes map-loading
allocation reductions, mapper/API additions, and mod-loading/cursor fixes.

A separate ignored source snapshot applies the exact upstream change to the
previously pinned embedded source. Each changed upstream file was verified
byte-for-byte against the new commit. The native lifecycle, optional-integration
policy and cooperative loading continuations remain. Native and managed runtime
expectations are generated together from the new RuntimeIdentity.json.

Four managed assemblies are rebuilt: Celeste.dll, Celeste.Mod.mm.dll,
MMHOOK_Celeste.dll and CelesteJITEverest.dll. The other197 assemblies and all16
native archives are exact build36 dependencies, including the restored Mono
visibility rule. The35 touch hook remains at MInput.Update. The34 repair changes
only its four named methods in the newly prepared game;17,323 other method
bodies are unchanged by that repair, ten intended double-precision sites remain,
and the bounded numeric audit reports no remaining recognized mismatch.

The temporary Everest/FNA preparation adds three inert patch attributes and
updates two dialogue resources. Existing FNA methods, fields, types, references
and shader resources are unchanged. The exact shipped FNA with its external
frame loop/readback fixes is retained; the new Celeste/Everest assemblies carry
the new dialogue/patch metadata. This exception is explicit in the semantic
audit and rejects any other change. Native iOS15/JIT/high-refresh support, save
transactions, unknown files, disabled mods and fresh-process gates remain.

## Verification

- 119 production Swift backup/save-transfer checks pass under the new runtime
  identity, including recovery and rollback controls.
- Real Mono/Metal gameplay passes the actual1.6580 version/module assertions,
  active-tagged-only freeze updates and paused-scene control, plus the repaired
  backward IL cursor search. Existing dust and mirror-enumeration controls pass.
- Native backup/export/import followed by real Everest verifies slot transfer
  with four mod sidecars, save/readback, touch, resume and normal Quit. The actual
  hair solver moves correctly; the lava fixture has40 surface bubbles.
- Original Motion Smoothing1.8.0 passes Fast/Fancy60/120 with the corrected native
  metadata source. Gameplay remains a fixed1/60-second step; host wall timing
  is not a physical iPhone frame-pacing measurement.

- The original vanilla Celeste1.4.0.0 serializer passes a save round trip through
  the native import/transfer path and new Everest, preserving mod sidecars. This
  is evidence for the tested format/version, not every Celeste port or mod.

The four host receipts are pinned in `EverestValidation.json`; their statuses
and hashes are also recorded in [the evidence ledger](EVEREST_6580_BUILD_37_EVIDENCE.json).

## Package and delivery

Final package: `artifacts/cabrillo-build37-final`. Independent package/symbol
verification passes for 68 compiled sources, 201 managed assemblies and all
16 preserved native archives. The unsigned IPA is 24,121,997 bytes:

- SHA256: `893a9f3fe146e4319751bb19c8b12f2431c7b4abb0c5be8a8f4dcef538cd37e6`
- Executable/dSYM UUID: `F04DFD22-0A17-3910-B5B7-BE9D6BF9D481`
- Managed receipt: `.build/everest-managed37-b/receipt.json`, SHA256
  `277fbf915027ea3e791facdb35266a9e87c8be12ff9b5fabb905c7d2cecc558d`
- Native overlay receipt: `.build/visibility-runtime36-a/receipt.json`, SHA256
  `3e30564ab34bbaaa3d7a33375522f26dfd0a5cddaef8aba19297759a80b335ca`

All six kit files are byte-verified and confirmed uploaded to
`iCloud Drive/Celeste JIT Tests/0.20.0-build-37`. Total retained kit storage is
897,775,166 bytes, below the1GB limit; every earlier Results folder remains.
The delivery and frozen-source manifests are in the final artifact directory.
All 220 captured implementation inputs are frozen. New implementation needs38.

USB transfer was hash-verified, TrollStore installation returned success, and
Cabrillo opened on the iPad mini4/iOS15.8.8. Its new native log confirms build37,
Everest1.6580.0, the exact managed receipt/runtime identity, an existing profile
and the imported-content pointer. No game was running before installation.
This is install/native-launch evidence; new JIT checks and managed gameplay
have not yet been observed on this version. Raw logs remain ignored/private.

## Phone evidence — later25 September

Export `CelesteJIT-c2f1df9c-f202-4f85-aa92-e715b0eb827c.diagnostics.json` is
3,451,426 bytes, SHA256
`999d4ad11dfdb16c9b1043a048a8449d7b659b336b3a5e8237de10e8f9a21489`.
The cloud original and byte-verified private copy are preserved. It contains a
new launcher-only37 export session, two earlier37 attempts, and one complete36
run. All four embedded BuildInfo objects exactly match their delivered IPAs.
No retained session is marked truncated or has invalid lines.

**The two initial37 runs fail.** The owner confirms the app closed or restarted by
itself. Both phone37 runs pass26 native JIT checks through standalone StikDebug,
catalogue quiescence with zero active requests, actual Everest1.6580 registration,
and all57 selected/built-in identities. MotionSmoothing1.8.0 and the full newly
installed StrawberryJam2021 1.0.13 dependency set are active (54 archives total).
Both reveal on their first drawn/read-back callback, with zero recorded JIT,
unowned-code, managed-error or patch-rejection counts through the last samples.

The first attempt ends during GameLoader after its first frames. The second
reaches the main menu and file selection, requests Celeste/2-OldSite, and ends
just after the LevelLoader worker finishes. Neither records a room, successful
managed gameplay or normal Quit. An absent exception does not establish a clean
exit: the owner explicitly reports the unexpected closure.

The iOS unified log, collected over the paired Wi-Fi connection, confirms both
processes were killed by jetsam with `per-process-limit` (PIDs3496/3932). The
second process has an explicit3376MiB limit (3,540,058,112 bytes); its last app
sample is3,529,428,720 bytes. This is an OS memory-limit termination, not a new
recorded managed exception. No debugger was attached for collection. The raw
archive and filtered records stay private; the ledger pins the filtered evidence.

This identifies the termination mechanism, not why earlier builds worked. The
accepted32 run reached3,996,585,976 bytes on the same phone. The owner also reports
failure with Strawberry Jam alone and success before the iOS15-support builds.
The installed LiveContainer signature and current profiles omit Increased Memory
Limit, while retained profiles for the earlier signing identity grant it. The
exact same host release has now been re-signed with the permission and installed
over Wi-Fi; the installed permission and all14 unchanged save/settings files are
verified. New iOS logs confirm a6144MiB ceiling after the repair, up from3376MiB.
[The memory review](BUILD_37_MEMORY_REVIEW.md) records the repair and
matched32/37 host comparison. The owner now confirms Strawberry Jam works, and
a new exact37 phone journal verifies SJ room/touch gameplay with a4.05GB peak
and zero recorded runtime errors. It ends during background/pause rather than
normal Quit, so full lifecycle/save acceptance remains separate.

Two isolated host runs load all54 exact SHA256-matched archives, reach Old Site
room10, and pass touch, resume, save and Quit with both Motion Smoothing renderers.
Sampled host peaks are3.04GB (Fast, cold cache) and2.72GB (Fancy, warm cache).
These differ in cache state and are not renderer performance comparisons. They
do not reproduce the phone's constrained-process termination. The exact host
receipt is recorded in the ledger. A further run uses the copied phone saves and
settings with Motion Smoothing disabled and passes. Matched cold-profile SJ
Beginner Lobby tests of32/37 also pass;37 uses slightly less peak memory on the
host (3.35GB versus3.46GB). Host checks do not close the phone gate.

Cabrillo requests120 callbacks/sec, but the two retained loading windows measure
57.4 and58.6 callbacks/sec. These are loading samples, not sustained gameplay or
GPU presentation measurements. Do not mark120Hz performance as accepted.

The original export closes36's base-game/Motion Smoothing runtime gate: actual rooms,
four resumes, save readback, stage8 normal Quit and a delayed native heartbeat,
with zero runtime errors. See [its review](VISIBILITY_BUILD_36.md#phone-evidence--later25-september).
Keep32 as the broader accepted phone fallback. The combined native backup/restore/
transfer gate is still pending. All37 implementation remains frozen; any new
Cabrillo implementation uses identity38. This host signing repair does not change
the delivered37 package. No new GitHub publication is authorized.
