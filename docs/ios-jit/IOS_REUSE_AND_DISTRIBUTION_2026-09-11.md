# Reuse of the iOS port and eventual distribution

Owner steering on 11 September 2026 confirms the intended direction: reuse the
working vanilla iOS experience where it fits, and aim for a reusable sideloaded
launcher whose users import their own Celeste installation and mod ZIPs. Preserve
the independent fully AOT product and its ongoing Everest/Strawberry Jam work.

## Runtime and product boundaries

The accepted vanilla app uses the .NET Apple Mono full-AOT route, full trimming
and LLVM. It is not a NativeAOT application. Its existing compiled managed game
cannot simply be loaded into our pinned Mono 8 JIT runtime or become the target
of arbitrary Everest hooks. Initially the hookable game, Everest and mods share
one JIT runtime; UIKit, SDL, FNA3D/Metal and FMOD remain precompiled native code.
Selective managed AOT can be investigated later in that same compatible runtime,
with retained IL/metadata and proven hook/inlining behavior. Performance is not
yet measured on the real JIT game.

Reuse priorities are the existing safe-area presentation, input policies,
touch layouts/artwork, controller behavior, audio/lifecycle policy and the save
manager's interaction and backup design. Apple managed bindings in the .NET 10
app cannot be copied into this binding-free Mono 8 host: bridge their native
services explicitly. Keep input bound once, reset touch ownership on inactivity,
and preserve the native-callback Metal lifetime contract accepted in build 11.
A bounded first game test is not full feature parity with the vanilla app.

The vanilla save manager's strict schema, four-file allowlist and generated
serializers are inappropriate as the complete storage contract for arbitrary
Everest modules. Reuse backup, preview and import/export behavior, but scope saves
by game/mod profile and retain complete Everest/module files and sidecars.
Keep unrecognized mod data opaque rather than deleting fields or rejecting it as
an invalid vanilla save. The first JIT game canary uses a separate container and
profile, and exercises the normal Settings/SaveData XML serializer under JIT.
It never reads/writes the AOT app's actual saves.

## Intended user flow

1. Install the reusable unsigned launcher IPA using the supported sideload path.
2. Import a supported owned Celeste installation. Validate the version, retain
   untouched originals, and derive/cache the platform/Everest assembly locally.
3. Import mod ZIPs, resolve dependencies and select a profile.
4. Use the fresh process-bound JIT handshake, then run the selected profile.
5. Keep content, saves and profiles across launcher updates; keep diagnostic export.

No Xcode build should be required for end users. The importer must still be
implemented and tested: the current canary's privately generated game fixture
is not the final on-device original-IL patch pipeline. A distributable launcher
must exclude Celeste's original/recompiled game code and assets, as well as any
third-party component without appropriate redistribution rights. The runtime and
native dependencies consume some space; the launcher should be small relative
to the game, not assumed to be only a few kilobytes. Separate data lowers update
size, and caching native builds should lower development iteration cost. JIT
itself is not required to import assets, and does not guarantee faster builds.

## FMOD release decision

Preferred route: obtain written clarification/permission from Firelight for the
specific free, unofficial iOS Celeste compatibility/mod-loader application and
its intended distribution. Clarify runtime version/platform, compiled IPA
redistribution, attribution, and whether the proposed free/noncommercial use is
covered. Do not assume another project's permission extends to this app.

The currently supplied SDK is FMOD 1.10.09 for iOS, distributed as static
archives linked when building our private IPA. Windows/macOS/Linux FMOD binaries
from an owned Celeste installation are not iOS native binaries. Asking users to
import those desktop files cannot satisfy the iOS runtime dependency. A later
user-supplied audio runtime route would require a separately proven native
packaging/loading/signing solution; importing an SDK `.a` file into a running
app is not the equivalent of loading a managed DLL. Do not promise that this
fallback removes user build requirements until it has been demonstrated.

PortMaster is a useful distribution precedent: its Celeste README describes
installing port files, adding an owned game to `gamedata`, then performing first
run preparation. It also references FNA patches and texture compression work.
The public sources inspected here do **not** verify the precise FMOD permission
claimed by the owner; retain that as unverified until primary permission evidence
is supplied. No contact/email has been sent on the owner's behalf.

Potential enquiry text for the owner:

> I am developing a free, unofficial Celeste compatibility and Everest mod-loader
> app for sideloading on iOS. Users would supply their own legally obtained Celeste
> installation; the public app would contain no Celeste game code or assets. The
> app needs an iOS FMOD runtime (our current private prototype uses 1.10.09). May
> I redistribute that runtime linked into the IPA, and what licensing,
> registration and attribution requirements would apply? Please also advise if
> this should be treated as a game port or a compatibility tool.

Sources inspected on 11 September 2026:

- [FMOD licensing](https://www.fmod.com/licensing): a licence grants permission
  to distribute the FMOD engine; requirements depend on the project/use.
- [PortMaster Celeste README](https://github.com/PortsMaster/PortMaster-New/blob/main/ports/celeste/README.md):
  owner-supplied game data and first-run preparation.
- [PortMaster permission overview](https://portmaster.games/developer-details.html):
  says packages contain required permission/licence files, but is not a grant to
  this app or evidence of the exact FMOD agreement.
- [Everest installation](https://everestapi.github.io/): installs alongside an
  existing Celeste installation and accepts mod ZIPs.
