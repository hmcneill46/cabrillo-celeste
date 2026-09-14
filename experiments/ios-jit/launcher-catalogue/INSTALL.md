# Build28 installation

Use [PHONE_README.txt](PHONE_README.txt) for the complete physical test.
The versioned handoff is `iCloud Drive/Celeste JIT Tests/0.15.0-build-28`.
Update the existing app in LiveContainer1, preserving all imported data.
The IPA is unsigned. Native browsing and installation do not require JIT;
Celeste needs a fresh inline StikDebug request through LiveContainer2.

The [implementation record](../../../docs/ios-jit/NATIVE_CATALOGUE_BUILD_28.md)
and artifact delivery receipt distinguish local placement, confirmed iCloud
upload and matching phone execution. Host compilation is not phone acceptance.
