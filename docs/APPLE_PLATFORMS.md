# Cabrillo: Apple platform direction

14 September 2026. Product name: **Cabrillo — Celeste Mod Loader for Apple Platforms**.
The AOT sibling is **Morro**. Repository separation does not change the current
runtime or imply a new platform has passed physical testing.

| Platform | Evidence and next work |
| --- | --- |
| iPhone/iOS | Primary product. Physical build27 accepted on iPhone15ProMax/iOS26.5; browser28 awaiting acceptance. |
| iPad/iPadOS | Intended next family. Existing build28 declares UIDeviceFamily1 and2. Test actual tablet JIT, sidebar/grid layouts, narrow/resizable windows, safe areas, controllers, keyboards/pointers, touch editing and memory budgets. |
| macOS | Current x64 Mono/FNA/Metal integration tests provide useful groundwork. A native product launcher, Apple-silicon runtime, packaging, imported data and controller handling still need implementation and acceptance. |
| tvOS | Worth a separate feasibility investigation after iPad. Controller-first UI, Files/import/download alternatives, storage lifecycle and a viable device JIT/install route must be proven. Morro's AOT tvOS progress is not a JIT proof. |
| visionOS | Exploratory. Start by evaluating a comfortable flat game window and controller input. Native graphics/runtime and installation/JIT are independent gates; compatible iPad presentation is not evidence that this custom JIT host runs. |
| watchOS | Outside scope: screen/input/runtime constraints do not fit this launcher and game. |

Keep shared game/runtime services independent of the native window/presentation
layer. Do not add platform conditionals to arbitrary user mods. Native services
own files, launch, downloads, JIT and lifecycle; the versioned support module owns
game-side Quit/input integration. Device-specific geometry and touch settings
must remain versioned and separate from saves.

Apple recommends adapting game menus and safe areas to each device's inputs and
orientations, and documents keyboard/mouse support on iPad. This informs the
tablet acceptance checklist; it does not establish Cabrillo's JIT compatibility.
Sources: [Designing for games](https://developer.apple.com/design/human-interface-guidelines/designing-for-games),
[Bring keyboard and mouse gaming to iPad](https://developer.apple.com/videos/play/wwdc2020/10617/).

Apple describes both compatible iPad presentation and native visionOS conversion;
graphics and interaction choices differ. A future Cabrillo assessment must also
prove this runtime's execution and installation route independently.
[Bring your iOS or iPadOS game to visionOS](https://developer.apple.com/videos/play/wwdc2024/10093/).

The immediate order remains phone28 acceptance and real loading progress. iPad
requirements should shape new native screens now, without delaying the current
backend work or claiming untested devices are supported.
