# Build37 Strawberry Jam exits and LiveContainer memory permission

25 September 2026. The owner's report that Strawberry Jam worked before the
iOS15-support builds was significant: the phone's permitted process size had
changed. This investigation restores the missing host permission while retaining
the exact delivered Cabrillo build37. The owner now confirms Strawberry Jam works,
and a new phone journal verifies actual SJ room/touch gameplay after the repair.
For installation guidance, see [Increased Memory Limit and GetMoreRam](../INCREASED_MEMORY_LIMIT.md).

## Confirmed failure and changed host configuration

The two failing37 processes in the exported diagnostics were killed by iOS
jetsam with `per-process-limit`. The second had a3376MiB limit
(3,540,058,112 bytes) and its final app sample was3,529,428,720 bytes. The earlier
accepted32 Strawberry Jam run reached3,996,585,976 bytes on the same iPhone15ProMax
and iOS26.5. These records establish a lower effective ceiling, rather than
merely a large mod pack. See [the37 review and ledger](EVEREST_6580_BUILD_37.md#phone-evidence--later25-september).

The installed LiveContainer3.8.10 signature and its current provisioning profiles
omitted `com.apple.developer.kernel.increased-memory-limit`. Retained profiles
for the earlier signing identity grant it, including a profile created at
23:53:09UTC on24 September. Current-identity profiles created at00:02–00:08UTC
on25 September omit it. This does not identify which user action changed signing,
or establish the exact profile used by the15 September build32 session.
It does identify a concrete hosting difference consistent with the OS ceiling.

Apple documents this entitlement as requesting a higher per-process memory
limit on supported devices; it is not unlimited memory. LiveContainer requests
it in its own upstream entitlements. A guest IPA's entitlements do not add
permissions to its hosting process, so rebuilding Cabrillo with the same flag
would not repair this installed host.

Primary references:

- [Apple: Increased Memory Limit](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.kernel.increased-memory-limit)
- [Apple: interpreting jetsam reports](https://developer.apple.com/documentation/xcode/identifying-high-memory-use-with-jetsam-event-reports)
- [LiveContainer's pinned upstream entitlements](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/entitlements.xml)
- [LiveContainer limitations](https://github.com/LiveContainer/LiveContainer/blob/4dbe0f9a626de801184a42c0be8d2cb105058e3d/README.md)

Raw signing profiles, account/device identifiers, system logs and saves remain
ignored/private. The public37 ledger contains only the scoped review and hashes.

## Controlled runtime comparisons

The full current phone set of54 mod archives was reproduced with exact archive
hashes. Build37 passes Old Site room10, touch, resume, save and normal Quit with
both Motion Smoothing renderers on the Mac. A further run uses copied phone saves
and settings, with Motion Smoothing disabled as in the owner's latest settings;
it also passes. A forced full managed collection at the menu saves less than1MB
in that run, so adding a forced collection is not a supported repair.

A separate matched comparison uses the same53 compatible original Strawberry
Jam1.0.12/dependency archives, copied phone saves,60 callbacks/sec and cold profile
caches for both32 and37. Both enter the actual SJ Beginner Lobby and pass touch,
resume, save and normal Quit. The current CommunalHelper1.25.7 requires Everest
1.6580, so the exact current mod set cannot legitimately serve as a32 control.

| Matched host run | Build32 | Build37 |
| --- | ---: | ---: |
| Peak process footprint | 3,457,781,760 bytes | 3,349,229,568 bytes |
| Whole test duration | 245.23 seconds | 243.66 seconds |
| Managed bytes at level readiness | 1,150,979,656 | 1,096,208,520 |

There is no increased peak in this matched host comparison. It is not an iOS
memory benchmark or proof that every native platform path behaves identically.
The source audit also retains all nine accepted Mono runtime patches and the
accepted renderer source. The iOS15 rebuild changes native object bytes; do not
describe it as byte-identical to32. Build35's separate visibility omission was
already corrected by36 and physically verified in the retained phone session.

## Applied signing repair

Xcode26.6 used the already configured signing account to enable Increased Memory
Limit for the current LiveContainer App ID and generate a matching profile. A
private provisioning-only stub obtained that profile; **the stub was not installed**.
The new profile was created at03:34:25UTC on25 September and expires at03:34:25UTC
on2 October. Normal signing renewal still applies.

The repair uses the exact official LiveContainer3.8.10 release already on the
phone, `Release (main/4dbe0f9)`, with main binary UUID
`10A2F666-F59A-316B-9DD8-F0EE0498649B`. The official downloaded archive has SHA256
`bec41bc21d75a0f2e85a0aa589ce5772e24e410deb017486758a3bc0503c8de7`.
All15 Mach-O code/data section sets and254 ordinary resources are unchanged.
The main app keeps its existing bundle identity, team, app groups and explicit
keychain groups; its only added entitlement is Increased Memory Limit. The
four extensions use their existing matching profiles. Deep strict signature
and profile/entitlement compatibility checks pass.

The in-place install over paired Wi-Fi succeeded. A fresh installation-service
query verifies the added permission on the actual installed host, with the
same version, release, app identity and shared group containers. iOS assigned a
different application data-container path during installation; all14 Cabrillo
save/settings files were copied before and after and have exactly matching hashes.
The same Cabrillo guest data path remains accessible. The old process had reached
only native JIT checks and was backgrounded; no game was running when replaced.
The repaired host launches successfully without a debugger attached. The newly
collected iOS runningboard log records process4581 with active and inactive limits
of6144MiB (6,442,450,944 bytes), replacing3376MiB. This directly verifies that the
signing repair changes the effective OS ceiling, beyond merely adding a plist key.

Private repair receipts are in `.private/livecontainer-memory-provision38`.
That historical work-directory suffix does **not** allocate Cabrillo build38.
No delivered Cabrillo implementation, IPA, build metadata or source lock changed.

## Post-repair phone gameplay — later25 September

The owner confirms the repair worked. The retained session journal
`bd1717f8-d16b-4628-93ea-fb44fdb0348d`, collected read-only over paired Wi-Fi,
matches the delivered37 BuildInfo exactly. It runs from10:04:49 to10:15:21UTC
and verifies26 native checks,14 graphics checks, zero active catalogue requests,
all57 selected/built-in identities, Everest1.6580 and StrawberryJam2021 1.0.13.

It reaches Old Site room10, SJ Prologue rooms00/01, the Beginner Lobby, and
NotYourBadeline rooms a_01, a_02 and a_03. Original SJ On/IL hooks execute. The
final input sample records31,629 callbacks and501 paired touch presses/releases.
Peak physical footprint is4,049,129,488 bytes, above the former3,540,058,112-byte
ceiling. All sampled JIT-failure, unowned-code, managed-error and patch-rejection
counters remain zero. This closes the scoped Strawberry Jam loading/gameplay
regression after the host memory permission repair.

The journal ends with normal background/pause events in a level. It does not
record normal Quit/native return or the full save readback gate, and does not
establish another unexpected exit. A later launcher-only session contains a new
JIT request. The independent iCloud diagnostics export has not yet arrived;
preserve that export separately when available. The public37 ledger pins the
private journal hash and review. Do not repeat the successful SJ test merely
because that export is absent, or convert this scoped result into every37 gate.
Do not revert to32 with incompatible current mod dependencies.

Retain the repaired host permission when signing/refreshing LiveContainer. If the
same limit returns, inspect the actual installed signature and process budget
again. GetMoreRam is now documented as an alternative to the Xcode method used
for this repair; its own workflow was not the tested installation route.
No new GitHub write was requested. The full native save-manager gate and
sustained120Hz performance acceptance remain separate outstanding work.
