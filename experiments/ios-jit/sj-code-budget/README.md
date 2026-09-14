# Build 16: Mono code allocation

Independent correction for build 15's physical 128 MiB code-arena exhaustion.
Ordinary Mono code managers use a 64 KiB minimum instead of 16 OS pages;
page/granule alignment, larger requests and ARM64 branch-binding space remain.
The private runtime builder replaces only mono-codeman.c.o in copies of the
build 15 member-access-fixed archives. Host tests additionally model 16 KiB
pages/granules and ARM64 binding space; they still execute x64 code.

Keep build 15 source/staging/artifacts intact. New outputs use
`.build/ios-jit/sj-budget*` and `artifacts/ios-jit/sj-code-budget-20260912-16`.
Original mod ZIPs, content identity, guest/profile identity and helper tests
are unchanged. Update the existing guest without importing anything.

See [the phone guide](PHONE_README.txt) and
[the report](../../../docs/ios-jit/BUILD_15_CAPACITY_AND_BUILD_16.md).
