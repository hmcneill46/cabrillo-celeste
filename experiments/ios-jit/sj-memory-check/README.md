# Build 18: page-sized VM range validation

Build 17 received StikDebug's success reply and detach but stopped at the old
4,096-entry VM inspection limit, halfway through its first 128 MiB arena.
All seven mod ZIPs were correct; no native code or managed runtime ran.

This native-only correction uses the number of OS pages intersected by the
requested range as the traversal bound. The production wrapper uses
getpagesize(); host tests can supply explicit page geometry. Complete coverage
and uniform RX/RW protection remain mandatory. No uninspected tail is accepted.
The app records page size and entry limit in its range diagnostics.

The exact build17 managed assemblies, seven ZIPs, game identity and script,
and accepted build16 Mono archives are reused. No content or mod imports are
required. The runtime/managed/mod builder scripts here verify existing inputs
without rewriting them. Main build command: `python3 build.py`; `--simulator`
builds the launcher test. Test outputs use `.build/ios-jit/sj-memory-check*`.

The VM regression replays the actual recorded prefix with the original
checker, then covers 8,192-page regions, late faults, partial pages, geometry,
malformed callbacks and a real 8,192-entry Darwin map with ASan/UBSan.
The full GravityHelper host test checks that shared native hook range queries
still work; physical ARM64 gravity acceptance remains pending.

See [the phone guide](PHONE_README.txt) and
[the report](../../../docs/ios-jit/BUILD_17_VM_LIMIT_AND_BUILD_18.md).
