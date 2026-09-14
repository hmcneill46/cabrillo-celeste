# Native probe provenance

The new Objective-C/C probe, JavaScript mailbox client, build tools, tests,
documentation and geometric icon are original source additions in this
MIT-licensed repository. The repository's existing MIT notice is included as
`REPOSITORY_LICENSE.txt` in the delivery and app resources.

The app links Apple's system UIKit, Foundation and system libraries. It embeds
no StikDebug, LiveContainer, MeloNX, Mono, .NET, Everest, MonoMod, Celeste or FMOD
implementation or assets. Xcode-generated asset catalogs are built from the
original geometric icon source. No game installation is needed for this test.

References, retained outside product source under ignored research directories:

| Reference | Pinned revision | Use |
| --- | --- | --- |
| StikDebug (AGPL-3.0) | `94bc9e8cf3b41f32f125f046abf33d913f4e1b2d` | Inspected external script API, URL handler and callback lifecycle; no implementation copied/linked |
| StikJIT (MPL-2.0) | `3623e725876f76aecb0520582ad6194bacb15d39` | Published executable-page/debugserver protocol and expected JS globals; independent narrow client |
| LiveContainer (AGPL-3.0) | `3afa9eb9a53625e9b8bd8b932e5785fd716ad5ae` | Inspected guest lifecycle and base64 `open-url` envelope; no implementation copied/linked |
| MeloNX (GPL-3.0) | `6a1c15962e61f681feedd5cb5fa02d37d53679cd` | Research reference for dual memory mappings; native probe calls Apple's VM APIs directly |

Debugger commands and OS API/ABI interoperability are implemented directly.
The probe script deliberately does not copy upstream `universal.js` or its
breakpoint loop. Users provide their existing LiveContainer/StikDebug
installations separately; this delivery does not redistribute those apps.
