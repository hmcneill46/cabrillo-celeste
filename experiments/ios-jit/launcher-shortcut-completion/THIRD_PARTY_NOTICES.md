# Cabrillo build38 notices

This app contains no original or prepared Celeste game assembly, generated Celeste
hook assembly, or original game assets. The user supplies their original Celeste
FNA 1.4.0.0 ZIP. Cabrillo prepares their copy in its private Documents storage.
The stripped metadata references supplied by Everest are build-only and are not
included in the app.

The native FMOD Engine 1.10.09 / build97915 iOS libraries are an explicit,
user-supplied proprietary SDK input. The SDK is never copied into Git. Its license
is included at `licenses/FMOD-LICENSE.TXT`. Public IPA redistribution is blocked
pending Firelight's permission for this launcher and an authorized way to supply
the SDK to release builds. This private test package does not assert that permission.

Everest stable1.6580.0 is built from commit
082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75 with the documented Apple embedding
and cooperative loading patches. Its MIT source, public MonoMod/Cecil/NLua
submodules, public NuGet packages, and the .NET8.0.28 runtime are rebuilt or
retrieved from the pinned sources in `release/owned-game-dependencies.json`.
All resolved NuGet package archives are pinned in `release/owned-game-nuget.json`.
Public SDK/runtime packs are declared binary dependencies; source provenance
is not a claim that every dependency is original Cabrillo code.

FNA uses the Microsoft Public License. SDL2, FNA3D/MojoShader, FAudio, Theorafile,
Lua5.4.8, MonoMod, Cecil, Iced, NLua, KeraLua and their bundled dependencies retain
their respective license and attribution texts in `licenses/`. FNA's local
changes include stable touch slots, externally driven frames, static Apple
imports, render-target compatibility and bounded backbuffer reads. Native
FNA3D changes provide the existing callback and Metal backbuffer support.
The native runtime retains the assembly-scoped visibility, JIT memory,
beforefieldinit and arithmetic adaptations recorded in the source patches.

Everest's managed dependencies include YamlDotNet, Newtonsoft.Json, DotNetZip,
Jdenticon and MAB.DotIgnore. Publicly supplied Steamworks.NET and Discord managed
bindings are included as references; native Steam/Discord libraries are absent.
Dependency license expressions, source URLs and available license texts are
included with the package. FMOD audio is separate from those bindings.

The native launcher includes ZIPFoundation0.9.20 and libyaml from Yams6.2.2,
both MIT licensed. Touch artwork attribution is in `TOUCH_ARTWORK_NOTICE.md`;
Google Material Symbols use Apache2.0 and Daniel Tacho's punch icon uses CC BY3.0.
The internal CJITCodeCanary module is authored in this repository and contains
no copied game content. The app icon is generated from project-owned geometry.

Mod ZIPs, catalogue images and descriptions are obtained from their authors'
services at the user's request and retain their original identities and notices.
No third-party mod ZIP is bundled. The optional compatibility adaptations and
physics repairs are described in the build38 report; the original user files
remain unchanged. Gameplay acceptance is scoped to recorded tests, not every
map, device or network mod.
