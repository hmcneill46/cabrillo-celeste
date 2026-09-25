# Cabrillo documentation

- [Fresh-chat development handoff](../HANDOFF.md)
- [Strawberry Jam: Increased Memory Limit and GetMoreRam setup](INCREASED_MEMORY_LIMIT.md)
- [Repository separation and verification](CABRILLO_MIGRATION.md)
- [Building, local private inputs and exact reproduction](BUILDING.md)
- [Public CI, gated IPA releases and build provenance](RELEASING.md)
- [Build37 memory investigation and host signing repair](ios-jit/BUILD_37_MEMORY_REVIEW.md) — restored LiveContainer permission; owner confirms Strawberry Jam works afterward.
- [Build37 Everest stable1.6580 upgrade](ios-jit/EVEREST_6580_BUILD_37.md).
- [Build36 Motion Smoothing startup correction](ios-jit/VISIBILITY_BUILD_36.md) — scoped phone gameplay/save/Quit passed.
- [Build35 iOS15 / JIT / refresh](ios-jit/PLATFORMS_BUILD_35.md) — scoped iPad base-game gate passed.
- [Build34 saves and numerical repairs](ios-jit/SAVE_TRANSFERS_BUILD_34.md) — individual desktop transfers, whole-profile recovery and hair/seeker/tutorial/lava fixes; combined phone gate pending.
- [Build33 whole-profile backups](ios-jit/PROFILE_BACKUPS_BUILD_33.md) — preserved unaccepted build; the owner deferred testing to34.
- [Build32 physical acceptance](ios-jit/BUILD_32_ACCEPTANCE.md)
- [Build32 first-frame presentation and original phone gate](ios-jit/FIRST_FRAME_BUILD_32.md)
- [Build31 phone review and loading feedback](ios-jit/BUILD_31_LOADING_REVIEW.md)
- [Build31 responsive loading implementation](ios-jit/RESPONSIVE_LOADING_BUILD_31.md)
- [Build29 independent startup preparation and managed next steps](ios-jit/STARTUP_PREPARATION_BUILD_29.md)
- [Apple platform direction](APPLE_PLATFORMS.md)
- [File-by-file purpose and hash inventory](MIGRATION_FILE_INVENTORY.json)
- [Current product roadmap](ios-jit/NATIVE_LAUNCHER_ROADMAP_2026-09-12.md)
- [Build28 physical acceptance: browser, installs and gameplay/Quit](ios-jit/BUILD_28_CATALOGUE_ACCEPTANCE.md)
- [Build28 original browser implementation and delivery](ios-jit/NATIVE_CATALOGUE_BUILD_28.md)
- [Build27 physical acceptance](ios-jit/BUILD_27_RUNTIME_ACCEPTANCE.md)
- [Original JIT feasibility audit](ios-jit/FEASIBILITY_AUDIT.md)
- [Reuse, distribution and FMOD boundaries](ios-jit/IOS_REUSE_AND_DISTRIBUTION_2026-09-11.md)
- [Historical development instructions](history/LEGACY_AGENTS_BUILD28.md)

All prior JIT reports/evidence ledgers remain under `ios-jit`. Their dated
observations, absolute paths and old active-work labels are historical. Current
instructions are in the repository-root `AGENTS.md`; current build outputs and
private inputs are wholly inside Cabrillo. Large past device logs, SDK working
copies and retired installers remain in the preserved legacy archive and are
not current build inputs.
