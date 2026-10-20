# Cabrillo 0.29.1 / build59 notices

This app contains no original or prepared Celeste game assembly, generated Celeste
hook assembly, or original game assets. The user supplies their original Celeste
FNA 1.4.0.0 ZIP. Cabrillo prepares their copy in its private Documents storage.
The stripped metadata references supplied by Everest are build-only and are not
included in the app.

## FMOD runtime distribution permission

The app links the proprietary FMOD Engine 1.10.09 / build97915 iOS runtime.
Firelight Technologies permits distribution of these runtime libraries inside
a built application, as recorded in Cabrillo's docs/RELEASING.md. This permission
does not make FMOD open source or grant permission to redistribute its SDK.
Developers must obtain their own FMOD SDK from https://www.fmod.com.
SDK components are not redistributed. The SDK stays outside Git and public build
artifacts; the app includes its applicable licence at `licenses/FMOD-LICENSE.TXT`.
Players downloading a built app do not need an FMOD account.

## Public runtime dependencies

Everest stable 1.6642.0 is built from commit
5abd7876821223c20711c1844a5187321d6e904c with the documented Apple embedding
and cooperative loading patches. Its MIT source, public MonoMod/Cecil/NLua
submodules, public NuGet packages, and the .NET8.0.28 runtime are rebuilt or
retrieved from the pinned sources in `release/everest55-dependencies.json`.
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
No third-party mod ZIP is bundled. Store compatibility, precision repairs and
optional touch controls operate on the user's separately imported game. Their
original files remain unchanged. Gameplay acceptance is scoped to recorded tests,
not every map, device or network mod.

## Morro game input investigation

Store acquisition guidance and input compatibility research reference Morro at
cc02b0cc697bd620c0dc864d4af3c60d79a95e85 (MIT, copyright 2024 rooot).
The full licence is included as licenses/MORRO-LICENSE. Cabrillo uses its own
on-device IL preparation; no Morro generated game is bundled.

## Morro touch controls reference

The touch editor, D3 v2 layout importer and control ownership behavior reference
Morro commit cc02b0cc697bd620c0dc864d4af3c60d79a95e85. Its MIT notice is retained
in licenses/MORRO-LICENSE. Cabrillo implements its own SwiftUI editor, portable
configuration and SDL/virtual-input adapter, including the optional swipe mode.
The existing touch artwork keeps the original attribution above.

## Built-in StikJIT

StikJIT is MPL-2.0, pinned to commit32287268fa5824f9edce4cb359f5833ce0cf7b00.
The unmodified covered Swift sources and scripts are available at
https://github.com/StikDebug/StikJIT/tree/32287268fa5824f9edce4cb359f5833ce0cf7b00
and the exact source archive and hashes are recorded in licenses/StikJIT/UPSTREAM.json.
MPL-2.0 and the idevice MIT notice are included in licenses/StikJIT.
StikJIT is compiled for Cabrillo's isolated helper using the pinned Xcode compiler.
Its upstream repository includes a prebuilt idevice FFI static library. That
explicit binary input is hash-pinned and disclosed; it is not rebuilt from source
by Cabrillo. Upstream does not disclose that binary's exact source revision.
Bundled universal.js and legacy.js retain their upstream notices.
Cabrillo uses its own fixed, per-process mailbox script.

This integration is independent and does not imply StikDebug/StikJIT endorsement.
