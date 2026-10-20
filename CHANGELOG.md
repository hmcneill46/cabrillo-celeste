# Changelog

## 0.25.1 — development

- Recover moved mod downloads through bounded official current/archive listings, retaining the exact reviewed version and integrity checks.
- Repair the removed FemtoHelper1.15.22 link used by Strawberry Jam without changing the tested archive.
- Read Everest MirrorName metadata for backup downloads and validate each archive before accepting a source.
- Keep stable Everest1.6642.0 consistent across the actual payload, launcher and dependency resolver; align optional API alias handling with upstream.

## 0.25.0 · development

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
