# Private build 19 notices

This kit contains the owner's prepared Celeste IL and native FMOD SDK
libraries for their physical test. It is not a public redistribution package.
FMOD's exact license is included as FMOD-LICENSE.txt in the app. Permission for
public FMOD redistribution remains unresolved; desktop libraries are not iOS
binaries. No permission has been inferred from other ports.

Everest is pinned to 4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00 (1.6458.0),
NLua to b3524288712743fb2394dcf615d14d0dac3276e2 and KeraLua 1.4.7 to
20113b5267f18fdf9f153ba4acaed2c6c8d1d3e1. Their MIT notices are in licenses/.
Lua 5.4.8 is built from the official checksum-verified source; its MIT notice
is included. The iOS build reports external-process execution unsupported.

The .NET/Mono 8.0.28 distribution's LICENSE.TXT and THIRD-PARTY-NOTICES.TXT are
copied from the runtime pack. Native compression and Apple cryptography use
that same pack. MonoMod, Cecil, Iced, FNA, SDL2, FNA3D/MojoShader, FAudio,
Theorafile and their dependencies retain the copied notices in licenses/.
Their source/archive hashes and the native callback adaptation are in receipts.

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

The app's explicit download button retrieves the 52 original pinned release
archives from their recorded upstream URLs, including Strawberry Jam 1.0.12,
its assets/audio and helpers. Exact versions, ZIP/DLL hashes, source URLs and
available archive-license metadata are in SJReleaseManifest.json. Those ZIPs
are not bundled in the IPA or uploaded in the iCloud kit. Keep original ZIPs
and embedded notices intact; these private tests grant no redistribution rights.

The bundled CJITCodeCanary is authored in this checkout and contains no game
assets. Separate local compatibility caches adjust optional CelesteNet type
loading in exact GravityHelper and CollabUtils2 releases. Original archives
and upstream caches remain unchanged. Original FemtoHelper IL is retained;
the scoped Mono beforefieldinit policy is recorded in the runtime patch.
Full SJ iPhone compatibility and actual CelesteNet networking remain untested
until separately accepted. Public original-game-IL import and FMOD permission
are separate release gates.
