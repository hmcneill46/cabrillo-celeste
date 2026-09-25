# Private Cabrillo build34 notices

This kit contains the owner's prepared Celeste IL and native FMOD SDK
libraries for their physical test. It is not a public redistribution package.
FMOD's exact license is included as FMOD-LICENSE.txt in the app. Permission for
public FMOD redistribution remains unresolved; desktop libraries are not iOS
binaries. No permission has been inferred from other ports.

Everest is pinned to d72e94f4b9e62b91cbdea674587ed39d53de9550 (1.6531.0),
NLua to b3524288712743fb2394dcf615d14d0dac3276e2 and KeraLua 1.4.7 to
20113b5267f18fdf9f153ba4acaed2c6c8d1d3e1. Their MIT notices are in licenses/.
Lua 5.4.8 is built from the official checksum-verified source; its MIT notice
is included. The iOS build reports external-process execution unsupported.

The .NET/Mono 8.0.28 distribution's LICENSE.TXT and THIRD-PARTY-NOTICES.TXT are
copied from the runtime pack. Native compression and Apple cryptography use
that same pack. MonoMod, Cecil, Iced, FNA, SDL2, FNA3D/MojoShader, FAudio,
Theorafile and their dependencies retain the copied notices in licenses/.
Their source/archive hashes and the native callback adaptation are in receipts.

This lane retains FNA's GetRenderTargetsNoAllocEXT API to the existing managed FNA
assembly, following FNA-XNA/FNA commit
76b1aef1fd0fa913ac53726fab9d230291c15327, src/Graphics/GraphicsDevice.cs.
FNA is copyright Ethan Lee and the MonoGame Team and is distributed under
the Microsoft Public License; see licenses/FNA-LICENSE. This extension uses
the existing managed render-target state and adds no native entry point.

Everest-managed dependencies include YamlDotNet, Newtonsoft.Json, DotNetZip,
Jdenticon, MAB.DotIgnore and .NET compatibility libraries. Exact package versions,
NuGet license metadata and available license texts are in licenses/. DotNetZip's
upstream license also contains its bundled component notices. Discord's managed
binding is present as an Everest reference; native Discord and startup downloads
are disabled in this embedded host. Steamworks.NET is a managed reference only;
no desktop Steam library is included or required by this private target.

Touch artwork attribution is in TOUCH_ARTWORK_NOTICE.md in the app. The diagnostic
canary code is authored here; they contain no copied game content.
Proprietary inputs, runtime binaries and generated game IL remain ignored local
artifacts. See the source receipt and license files before any future release.

The native installer reads the community index and dependency graph through
Everest's official HTTPS pointer files. Original archive downloads retain their
embedded author/license information. Historical SJReleaseManifest.json records
the original test corpus and the three app-managed compatibility releases; the
normal launcher uses general identity-based dependency/update planning.
Downloads and this private test do not grant redistribution rights.

Native discovery uses the public Celeste catalogue also used by Olympus, with
GameBanana's public profile API for page details. The consulted Olympus browser
is pinned to 568cc5fc846836d480e41f928a3db7c06e87798d. Creator names, descriptions
and screenshots belong to their respective authors. They are retrieved when
browsing and are not bundled in this IPA. GameBanana links and author credit
remain visible. The browser adds no third-party library dependency.

The bundled CJITCodeCanary is authored in this checkout and contains no game
assets. Separate local compatibility caches adjust optional CelesteNet type
loading in exact GravityHelper and CollabUtils2 releases. Original archives
and upstream caches remain unchanged. Original FemtoHelper IL is retained;
the scoped Mono beforefieldinit policy is recorded in the runtime patch.
The original full dependency graph and selected SJ gameplay are physically
accepted through build24; all-map compatibility and actual CelesteNet networking
are not established. Public original-game-IL import and FMOD permission
are separate release gates.

Inherited native launcher dependencies: ZIPFoundation 0.9.20 (MIT), and the CYaml
libyaml parser vendored by Yams 6.2.2 (MIT). Exact Git commits are pinned in
`native-dependencies.json`; source and archive hashes are in the native receipt.
See `licenses/ZIPFoundation-LICENSE` and `licenses/Yams-LICENSE` and `licenses/libyaml-LICENSE`. Only the C YAML
parser is linked, not the Yams Swift decoder. Apple SwiftUI/UIKit/CryptoKit are
platform frameworks. The tiny CJITLauncherExample ZIP is authored in this repo.

Build24 local FNA/FNA3D changes: retained Metal backbuffer descriptor, deferred
clear/MSAA preservation, and bounded managed readback with a finally-released
pin. Original project licenses and notices are retained. These are local changes,
not an upstream release.

The Swift xxHash64 implementation follows the published seed-zero XXH64
algorithm (https://github.com/Cyan4973/xxHash/blob/v0.8.3/doc/xxhash_spec.md).
The specification is copyright Yann Collet; its notices are preserved in the
private reference snapshot. No xxHash library binary is linked. Published xxHash
checks are download integrity checks, not publisher signatures; receipts also
record local SHA256. Python xxhash and PyYAML are host test tools only.

Download fallback follows Everest ModUpdaterHelper.GetAllMirrorUrls at commit
4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00 (MIT). Original third-party mod
ZIPs are fetched separately from public community servers, with their published
licenses retained. No Spring Collab or helper archives are bundled in the IPA.

Build26 changes three Mono CoreLib reflection methods and adds a private native
flag-access binding, based on .NET runtime v8.0.28 (MIT). Attribute queries read
method flags without resolving absent signature types. All unrelated methods,
fields, resources and references are structurally checked; the original runtime
packs and native Mono archives remain unchanged. This is a local correction,
not an upstream runtime release. Exact input/output identities are in BuildInfo.

Cabrillo build34 retains the accepted build32 managed payload except Celeste.dll.
Its local IL preparation removes ten accidental float/double conversions in
player hair, seeker and bird-tutorial calculations, preserves the ten intended
movement precision sites, and makes three LavaRect precision boundaries explicit.
All other 200 managed assemblies and all native runtime libraries are unchanged.
The new profile backup and save transfer interface is original Cabrillo code.
Original game IL and FMOD distribution permissions remain separate release gates.

## Build36 native visibility restoration

The Mono8.0.28 metadata member-access correction already present in the accepted
pre35 runtime is restored after its omission from the iOS15 rebuild. It honors
explicit IgnoresAccessChecksTo assembly grants for protected members. Only one
native archive member changes; the unchanged license and source provenance above
continue to apply. No original mod, game or SDK content is added to the IPA.

## Build37 Everest source upgrade

Everest is built from stable1.6580.0, commit
082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75, with the documented embedded lifecycle
and cooperative loading adaptations. MonoMod and all native dependency pins
remain unchanged. Build34's four-method precision repair is reapplied to this
new prepared game assembly; the original game and mod content remain unbundled.
