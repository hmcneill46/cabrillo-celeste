# Build 14 physical test

Follow [the phone instructions](PHONE_README.txt), copied as README-FIRST.txt
in the private handoff. Install the unsigned IPA over the existing build 13
Everest guest in LiveContainer 1, retaining its data container. StikDebug stays
in LiveContainer 2. Launch with JIT OFF and script blank.

The intended first input is the owner's original **Celeste Windows (FNA)
1.4.0.0**, `celeste-win-opengl.zip`, from [the official itch.io page](https://maddymakesgamesinc.itch.io/celeste).
All 1,216 Content files in the locally supplied archive match the trusted
manifest. Select the ZIP directly. Linux is an intended additional input, but
its actual archive has not been verified here; do not claim it is accepted.
No build 13 IPA or separately prepared asset pack is required. A single wrapped
Content folder or exact build 13 IPA is structurally accepted if every trusted
content byte matches, as covered by importer tests.

The physical gates are first import, retained build 13 mods/save counter,
Everest map/hooks/Lua/audio/touch/resume, then a same-guest update of build 14
and a fresh run using the saved content and counter. Export both sessions.
Keep Export diagnostics available on import rejection, cancellation and crash.

This is a private asset-only split. The IPA still includes prepared game IL
and iOS FMOD. It is not the public game-free launcher. No commits or public
publishing are authorized.
