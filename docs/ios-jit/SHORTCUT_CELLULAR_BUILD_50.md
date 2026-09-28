# Build50: check the cellular VPN route before Airplane Mode

## Problem and change

The owner imports revision49 successfully, then reports the same Home
launch timeout with Wi-Fi disabled in Control Centre and in Settings. USB retrieves
both actual journals, each recording app49. Automatic correctly chooses Travel. Preparation returns,
LocalDevVPN opens and returns, but Remote Pairing at10.7.0.1:49152 remains unreachable.
The25-second connect deadline expires before isolation or any JIT request. Both
runs receive the restoration receipt and clear their recovery record. The phone
screenshot shows4G and the reported error. All125 saves and preferences are unchanged.

Earlier code requires the developer-service reply **before** switching to Airplane
Mode. [StikJIT's cellular instructions](https://github.com/StikDebug/StikJIT/blob/5d732f94b871031704ef6f580a313e8d99d80ec1/INTEGRATION.md)
connect LocalDevVPN, then enable Airplane Mode before returning to the developer
client. This creates an ordering dependency if the service is unavailable with
cellular still active. Earlier47 cellular-start successes occurred near saved
Wi-Fi that preparation could reconnect; they did not establish wholly unassociated
Wi-Fi behavior. An attempted controlled early-isolation phone experiment could not
start because CoreDevice timed out. No radio mutation/intervention was dispatched;
it is not physical evidence for the fix.

Build50 changes Travel's connect gate to a **selected tunnel route**. A UDP socket
selects its local route/source for10.7.0.1 without sending a datagram. The source
must match an active point-to-point utun IPv4 interface; cellular, Wi-Fi, loopback,
link-local, removed and unrelated-interface sources fail. The interface address is
not hard-coded, so both current and earlier LocalDevVPN configurations can work.
This observes a tunnel route, not ownership by a particular VPN or service readiness.

Only that Travel connect phase can proceed on route readiness. The matching
isolation receipt is still required, followed by the complete bounded Remote
Pairing hello **in Airplane Mode**. Only then can StikDebug receive a fresh JIT
request. The Wi-Fi path still requires the real service hello. Native execution,
debugger detach and restoration receipts remain mandatory. A wrong or lost route
cannot grant JIT. Timeouts identify whether the VPN route or developer service
failed. Fresh connect tokens also reject asynchronous probe results from an older
launch; no timeout is extended and no fixed success delay is introduced.

## Validation and limits

- 132 retained native launch controls,50 installation controls and53 cellular route/
 ordering controls pass. The new scenario leaves the developer service unavailable
 until isolation; the exact49 reducer fails it and50 advances through every gate.
- 36 generated shortcut branches and15 broken typed-URL controls pass. The exact43
 missing-JIT-callback failure control remains reproduced. Cancellation, missing
 offline service, failure to restore, restart recovery, native failure and attached
 debugger gates remain exercised.
- Route controls reject unrelated/down interfaces, wrong address families and
 non-tunnel routes. The actual Mac route returns `local_route_not_tunnel` within
 its bounded check. This host result is separate from iPhone route acceptance.
- Xcode26.6/17F113 builds arm64 with minimumiOS15. Package checks verify no bundled
 game assemblies/assets,199 unchanged managed DLLs,16 unchanged dependency archives,
 unchanged SwiftUI and exact Apple-signed revision49 templates. Existing49 Apple
 import/execution tests are retained; they were not rerun for this native change.
- All16 frozen35–50 manifests still match. The scoped physical50 cellular-launch pass is recorded below.
 The connected phone's125 saved files (683,136bytes) and launcher preferences are
 unchanged against the pre-test28 September snapshot.

## Package and delivery

- Version: **0.23.2 / build50**, lane `launcher-shortcut-cellular`.
- IPA: `Cabrillo-0.23.2-build-50-unsigned.ipa`; 18,759,543bytes.
- SHA256: `e22ca126d8cb5eb829d027267504d0b9c2600efbf3ebf4c88fd762b080ae87ff`.
- Executable/dSYM UUID: `e5dc790840513f77b0406a1fb0405649`.
- All243 inputs are frozen in `artifacts/cabrillo-build50-final`;
  new implementation requires51. See the [ledger](SHORTCUT_CELLULAR_BUILD_50_EVIDENCE.json).

All six kit files are confirmed uploaded at `Celeste JIT Tests/0.23.2-build-50`.
All six also have exact USB readback at On My iPhone → LiveContainer → Cabrillo-build50.
The installed app before staging is49; copying the kit is not installation.
Only48's superseded cloud IPA was removed after its exact local original, package
receipt and bytes were verified. All Results, all local originals and accepted32/
working43/47 installers remain. Cloud logical total is995,088,905bytes.

## Physical cellular-launch acceptance —28 September

The owner replaced49 with50, kept shortcut49 and ran the requested Automatic test
starting with Wi-Fi off, cellular on and LocalDevVPN disconnected. The owner reports
that it passed. USB verifies installed50's exact BuildInfo and both signed49 assets.
The actual journal records this complete sequence:

1. Automatic selects Travel with no Wi-Fi address.
2. The route initially fails, LocalDevVPN opens and returns, then the route passes.
3. Shortcuts confirms isolation; the Remote Pairing hello succeeds afterward.
4. All26 native JIT checks pass with debugger detach known, and Cabrillo returns.
5. The both-on restore preset receives its matching success receipt; recovery is
   cleared and Home Screen launch finishes ready.

From Home launch to ready: **31.262seconds**. Journal SHA256:
`6b5b49d5792519fb88352c06a6369a6367c2c95f8132571253834dac753cd31a`.
All125 save files/683,136bytes and launcher preferences still match the original
28 September snapshot. No game is started or stopped by the Mac. This closes the
reported cellular-start failure for the observed app50/shortcut49 configuration.

## Independent exported diagnostics —28 September

The owner generated Export diagnostics after the successful run. The actual
960,314-byte app-generated file was retrieved over USB while the iCloud copy was
not yet visible, preserved in50/Results, and then verified uploaded with identical
bytes. SHA256:
`9fdaaac4ca669c11ccad121acd6f26cf33015dbaa38eca9e1db2b4af9933efa4`.
Its build metadata matches installed50. All98 current events are retained without
storage errors or evictions; the first95 exactly match the accepted USB journal.
The export confirms26 native checks, JIT ready, restoration and no pending recovery.

Three historical sessions accompany it: a50 native-only opening and both49 failed
cellular attempts. Both49 histories match the collected failure journals followed
by later app background/foreground events. Those older failures do not change the
accepted50 result. No game was started in the exported50 session, so this supplies
independent evidence for the same shortcut run without adding a gameplay/Quit pass.
All Results remain preserved; cloud logical total is996,049,219bytes after export.

Keep app50 and shortcut49; no reimport or repeat launch is needed for this export.
Entirely out-of-range Wi-Fi, alternate presets, another current guest, other
providers, cancellation and game/Quit remain separate gates. Native saves, iPad38
and sustained120Hz retain their earlier distinct status.

The package and original six-file kit remain unchanged; their pending-acceptance
wording records delivery time. New implementation requires51. No second debugger,
GitHub write or public IPA publication occurred; FMOD redistribution remains gated.
