# Build37: Everest stable 1.6580

Version0.20.0, `launcher-everest6580-20260925-37`.

This lane upgrades the pinned Everest source from1.6531.0 to stable1.6580.0,
commit082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75. It retains build36's corrected
native runtime, build35's touch/input timing and iOS15/JIT routes, and build34's
precision repairs and save recovery boundaries. Native and managed runtime
identity expectations are generated from RuntimeIdentity.json together.

The source input is a separate ignored, hash-locked copy. The22-file upstream
change was applied to the previously pinned embedded source; every upstream
changed file matches the actual new commit. Existing embedding and cooperative
loading adaptations remain. Only four managed assemblies are replaced; the
native archives and FNA binary remain exact. The FNA audit permits only the
reviewed three patch attributes and two Everest dialogue updates in its temporary
preparation output, preserving every existing graphics method/field/type.

Use tools/build_everest6580_managed.py, tools/build_everest6580.py and
tools/verify_everest6580.py. See [the report](../../../docs/ios-jit/EVEREST_6580_BUILD_37.md).
Sources are frozen after final packaging; physical acceptance is separate.
