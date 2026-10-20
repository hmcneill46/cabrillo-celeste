# Changelog

## 0.26.0 · unreleased development

- Add recommended Built-in StikJIT for new standalone iOS17.4+ setups, keeping saved JIT provider choices and every existing method.
- Let Run Celeste prepare and enable JIT with progress, then launch only after helper completion, native checks and verified debugger detach.
- Show expiring Remote Pairing service readiness separately from developer-image preparation and actual JIT readiness.
- Add protected pairing-file import and detection of files placed in Documents by compatible tools, without requiring changes to iLoader.
- Keep the play triangle visible and center it with the Run Celeste label in enabled, pressed and disabled states.

Built-in JIT requires a compatible signed helper, debugging permission, Developer
Mode, pairing and LocalDevVPN or a compatible tunnel. LiveContainer keeps its
existing providers. Cabrillo does not require iLoader recognition; manual pairing import works
independently. The [verified unsigned test kit](https://github.com/hmcneill46/cabrillo-celeste/actions/runs/39406495715/artifacts/12257984521)
is available with GitHub sign-in until3 November. Physical helper/JIT acceptance
and a public Release remain pending. See [the build57 report](docs/ios-jit/INTEGRATED_STIKJIT_BUILD_57.md).

## 0.25.1 · 20 October 2026

- Update Everest from stable1.6580.0 to1.6642.0, including TeleportTrigger and separate menu-search binding support.
- Recover moved mod downloads through bounded official current/archive listings, retaining the exact reviewed version and integrity checks.
- Repair the removed FemtoHelper1.15.22 link used by Strawberry Jam without changing the tested archive.
- Read Everest MirrorName metadata for backup downloads and validate each archive before accepting a source.
- Keep stable Everest1.6642.0 consistent across the actual payload, launcher and dependency resolver; align optional API alias handling with upstream.

## 0.25.0 · development (included in0.25.1)

Updates Everest from1.6580.0 to stable1.6642.0, including updated GameBanana mirror
handling, the TeleportTrigger API and a separate menu-search binding. Existing
Feather ZIP imports, bundle ID, profiles, saves, JIT routes and Shortcut49 are
retained. The first launch prepares the newer Everest from retained originals;
later launches reuse the new verified cache. Device gameplay/JIT acceptance is
tracked separately in the build55 report.

## 0.24.3 · 19 October 2026

Fixes the game ZIP picker stall seen after signing Cabrillo with Feather using a
Development profile whose app identifier differs from Cabrillo's bundle ID.
Automatic document-service host adaptation and temporary copies for game and mod
imports require no new profile, bundle ID change or setting. Original files stay
unchanged. Large ZIPs can take time to copy and need extra temporary storage.

The build54 trial's game ZIP picker and staging pass on iPhone 15 Pro Max / iOS 27.0.1 with the
original bundle ID and the same Development profile; the staged archive is
875,540,825 bytes. This release adds no physical gameplay, JIT or mod-import test
result. Existing Shortcut49 and runtime dependency pins are retained.

The unsigned IPA requires iOS 15 or later, JIT and your own original Celeste FNA
1.4.0.0 game ZIP. It contains no Celeste game code/assets or FMOD SDK. FMOD runtime
code is included with Firelight permission. Release provenance and attestations
identify the source, dependencies and workflow for each download.
