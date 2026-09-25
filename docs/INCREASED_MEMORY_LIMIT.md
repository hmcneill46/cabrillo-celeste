# Strawberry Jam and Increased Memory Limit

For Strawberry Jam and other large mod packs, we recommend enabling **Increased
Memory Limit** on supported devices with enough RAM. iOS can otherwise close the
game when it reaches its per-app allowance, even if the device has more RAM.

This permission lets iOS grant a larger allowance on supported models. The amount
depends on the device and system conditions; it does not add physical RAM or make
every mod pack fit. JIT still needs to be enabled separately. See
[Apple's entitlement documentation](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.kernel.increased-memory-limit).

## Choose the app that runs the game

| How you run Cabrillo | Where the memory permission belongs |
| --- | --- |
| Inside LiveContainer | The LiveContainer instance that runs Cabrillo. If you use LiveContainer2 for the game, select that instance. |
| Installed directly through a signing tool | Cabrillo's own signed app and its matching provisioning profile. |

For LiveContainer, changing only the Cabrillo guest does not grant the host this
permission. LiveContainer documents that guest entitlements do not apply to its
host process. Select the instance running the game, rather than an instance used
only for StikDebug. [LiveContainer limitations](https://github.com/LiveContainer/LiveContainer#limitations).

## GetMoreRam with SideStore or AltStore

[GetMoreRam's nightly release](https://github.com/hugeBlack/GetMoreRam/releases/tag/nightly)
provides an alternative to enabling the capability through Xcode. Follow its
[upstream instructions](https://github.com/hugeBlack/GetMoreRam#how-to-use):

1. Sideload GetMoreRam.
2. In its settings, sign in with the Apple account used to sign the target app.
3. Open **App IDs**, tap **Refresh**, and select the app identified above.
4. Choose **Add Increased Memory Limit**.
5. Re-sign and reinstall the target app through SideStore or AltStore, keeping
   its existing App ID and data. Update the existing installation; deleting
   LiveContainer also deletes the guest apps and data stored inside it.
6. Check that the resulting installation includes **Increased Memory Limit**.
   Then reopen Cabrillo and make a fresh JIT request before playing.

Changing the registered App ID alone does not update an installed signature.
The signed app must request `com.apple.developer.kernel.increased-memory-limit`
and its provisioning profile must permit it. LiveContainer's upstream package
already requests it; a standalone Cabrillo installation also needs its signing
tool to include it. Recheck the permission after changing signing accounts,
certificates or installation methods if the same problem returns.

TrollStore and jailbreak installations use different signing arrangements; the
SideStore/AltStore procedure above is not a required step for those routes.

## What we verified

On the tested iPhone 15 Pro Max, iOS initially killed build37 at a3376MiB process
limit. Restoring the host's permission raised that limit to6144MiB, and the owner
then confirmed Strawberry Jam worked. Its new phone log verifies SJ room/touch
gameplay above the old ceiling. This is one device's result, not a promised
allowance or minimum-RAM specification for other devices. The repair used Xcode;
the GetMoreRam steps above follow its documentation.

If the game still closes unexpectedly, export Cabrillo diagnostics and keep the
device's crash or memory-termination report for investigation. Other causes can
produce similar symptoms. [Technical investigation](ios-jit/BUILD_37_MEMORY_REVIEW.md).
