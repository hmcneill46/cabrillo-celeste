# Build56 — dependency downloads

Cabrillo0.25.1 retains the exact stable Everest1.6642.0 managed/native runtime
identities and the original-ID Feather copy-import repair. This overlay replaces
native `DependencyPlan.swift`, `DependencyInstaller.swift`, `ModLibrary.swift` and the two
bundled download metadata documents. The production main/helper remain build54.

FemtoHelper1.15.22 now uses GameBanana file1838255. Its11,103,153-byte archive and
SHA256 `5a845805bae30490ed7c9da84410fbe672628b8fe927a830f5f2eb148eb88419`
are identical to the retained tested release; no helper compatibility policy is
relaxed. The original file1776026 is unavailable.

Native candidates preserve Everest's `MirrorName` and use a validated basename
on fixed community mirror hosts. Missing metadata retains the legacy canonical
GameBanana file-ID fallback; malformed explicit metadata uses the original URL
only. After failed transport, bounded official page/archive discovery can locate
a moved copy; every attempt must match the original reviewed archive identity.
Required API aliases and optional dependency names follow upstream Everest.
All size, content-hash, actual ZIP metadata, runtime dependency, staging,
cache and atomic commit checks remain mandatory.

Use `tools/build_release56.py` with your own approved FMOD SDK. Current evidence
and physical-test scope belong in
[`DEPENDENCY_DOWNLOADS_BUILD_56.md`](../../../docs/ios-jit/DEPENDENCY_DOWNLOADS_BUILD_56.md).
The overlay contains public source and tests only; mod ZIPs, game files and build
outputs remain ignored. All261 captured55 app inputs remain immutable.
