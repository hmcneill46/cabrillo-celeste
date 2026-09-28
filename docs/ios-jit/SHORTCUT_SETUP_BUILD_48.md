# Build48 — create a Home Screen shortcut from Cabrillo

## Later28 September: installed, export verified, import field fails

The owner installed48 and used its in-app export. USB collection verifies the48
native identity, a LiveContainer shortcut export and two copy-link actions. The
owner reports that typing in Configure This Shortcut disappears almost immediately.
A USB screenshot shows Apple's URL-list editor. The real iOS26.5 simulator import
of the exact signed48 file reproduces the defect: typed text is replaced by the
old parameter value. This answers the earlier setup request with a failure before
Home/JIT. No screen recording is needed to identify it.

The native export itself is working; full48 setup/Home routing is not accepted.
Read [the49 repair](SHORTCUT_IMPORT_BUILD_49.md). Its plain-text import question
retains typed/pasted text and the real Apple runner delivers the exact configured
URL to an isolated simulator fixture. That remains separate from phone acceptance.
All233 frozen48 inputs and its original delivery remain untouched. The historical
pre-staging statements below describe the earlier state, not current installation.


28 September2026. Version0.23.0, lane `launcher-shortcut-setup`.
**Packaged and verified; new phone setup/import/launch acceptance is pending.**
The47/46 phone-tested pair remains available. No GitHub or public IPA publication
is authorized. See the [evidence ledger](SHORTCUT_SETUP_BUILD_48_EVIDENCE.json).

## Result and signing boundary

Settings → Home Screen shortcut → **Add Home Screen shortcut** shows Cabrillo’s
installation and current JIT provider. The button exports the correct signed file
through the iOS Files picker. For LiveContainer it also copies an exact Home launch
link; the owner pastes that into the shortcut’s import question. Apple still
requires importing the file and choosing Add to Home Screen. The UI and diagnostics
never mark file export as proof of shortcut installation.

Two templates are signed during development with `shortcuts sign --mode anyone`.
They are bundled with the app and verified against their build manifest before
export. Cabrillo does not attempt on-device signing, install a profile, modify a
signed workflow, read the user’s clipboard or write to their shortcut library.
The user explicitly requests the clipboard write by pressing the labeled button.
The signed file contains no PID, user folder, pairing data or debugger script.
Apple’s import question supplies the Home URL; native JIT uses each fresh request.
No runtime template download or Cabrillo signing service is needed.

Sources: Apple’s [CLI signing documentation](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac),
[import questions](https://support.apple.com/guide/shortcuts/apdf330fd3a0/ios) and
[Home Screen steps](https://support.apple.com/guide/shortcuts/apd735880972/ios).
The [LiveContainer guide](https://livecontainer.github.io/docs/guides/add-to-home-screen)
and pinned3.8.10 source confirm the explicit launch URL and optional data-container
selection. The host-only exploratory Apple question-object check used a Comment
parameter, not the real URL action or import UI; it is not a phone acceptance result.

## Routing and current settings

- Standalone Cabrillo uses `cabrillo://launch`.
- A LiveContainer guest generates `livecontainer-launch` with its actual host
  scheme, bundle folder, current data folder and base64 Home URL. This replaces
  the46 generic forwarding route that depends on the active guest. Names are
  validated as single components and encoded as query values. A switch from another
  running guest can still need LiveContainer’s own confirmation.
- The native coordinator reads **Enable with** at launch. Switching between
  supported StikDebug installations does not require a new shortcut. Moving
  Cabrillo between hosts/data containers does require a new Home link/import.
- LC Cabrillo retains bounded, exact shared StikDebug discovery. Standalone
  Cabrillo cannot inspect LC’s sandbox: it can now retain an owner-supplied helper
  launch link copied from StikDebug’s LC menu. That route is validated and targets
  LC2 explicitly. The link’s structure is checked; helper identity and the full
  standalone/LC2 handoff need physical confirmation.
- Cabrillo in LC2 with StikDebug in the same LC2 host is rejected before network
  preparation. Choose standalone StikDebug or run Cabrillo in LC1.
- Export/setup actions retain busy/game/profile/recovery guards. Helper changes
  are blocked after a JIT request. Unsupported/manual providers receive setup
  guidance rather than a claimed automatic JIT shortcut.

The typed URL output bindings, explicit text comparisons and natural completion
from46 remain. The47 native reducer stays byte-for-byte identical: actual JIT
execution, known detach and foreground are required; network receipts and durable
Travel recovery remain separate. **Test installed shortcut** now actually runs
Shortcuts. The unrelated duplicate Home Screen controls inside a failed mod
installation report are removed from this new lane; Settings remains their home.

## Validation and package

- 132 retained launch/recovery controls, including original43 missing-callback
  failure reproduction;50 new route/helper/file integrity controls.
- 36 generated shortcut branches and12 rejected broken URL connections. The
  customized Home parameter still drives the explicitly connected typed URL.
- 7 production-view UI tests each on iPhone17ProMax and iPad11-inch simulators:
  export action, optional helper entry, large text, rotation and retained status/
  recovery/preset behavior. An initial test used a whole-window swipe that sent
  the simulator Home after rotation; gestures were scoped to the form. Helper
  entry also gained an explicit keyboard dismissal. The final14 tests pass.
- Xcode26.6/17F113, iPhoneOS26.5 SDK, arm64/iOS15 minimum compile and link pass.
  Package audit verifies199 managed assemblies, zero bundled game assemblies or
  game assets, fresh executable/dSYM identity and exact signed shortcut bytes.
- All199 managed assemblies and16 dependency archives match47. The reducer matches47.
  All captured35–48 source manifests remain exact. These checks do not establish
  native document-picker, Shortcuts import, physical Home routing or gameplay.

IPA: `Cabrillo-0.23.0-build-48-unsigned.ipa`,18,758,159bytes.
SHA256: `5e0a7fefddea8ab2346dc997df0677375dd1513448f9fd68ae3921a35179fdb4`.
Executable/dSYM UUID: `61b8805445643ef7b9e6795f946199fc`.
All233 inputs are frozen in `artifacts/cabrillo-build48-final`; any new
implementation needs49. Exact signed input bytes are in the frozen archive.

## Delivery and next phone check

All six kit files are confirmed uploaded in `Celeste JIT Tests/0.23.0-build-48`.
The initial transient account-access errors cleared. All six files are also staged
with exact USB readback at **On My iPhone → LiveContainer → Cabrillo-build48**.
The installed app was verified as47 before staging; no installation or app launch
was performed. Results starts empty. An owner request for installation and the new
in-app import/Home launch test is pending. See the ledger for private receipt hashes.

Only the superseded33 cloud IPA was retired after matching its exact local copy
and original receipt (`a66a44bd1e477fadb4df8d9127912fca2412babf87b3d3603b9f67461f5de79d`).
Its Results, local installer and original source remain. Cloud total is976,287,829
bytes; accepted32 and working43/47 installers remain.

The focused owner check is48 installation → its in-app export → successful signed
import and Home link question → Add to Home Screen → cold Automatic launch with
native ready/automatic return. After a normal game Quit, separately test another
LC guest being selected, then the Cabrillo icon selecting the same data container.
Preserve independent Export diagnostics in48/Results. Do not repeat earlier47
passes solely to collect another export. Keep alternate restore presets,
fully-out-of-Wi-Fi operation, cancellation, game/Quit, save-manager, iPad38 and
sustained120Hz acceptance distinct. Do not stop an active game to install/test.

The [setup guide](../HOME_SCREEN_SHORTCUT.md) includes standalone/LC choices and
remaining first-use prompts. The new setup has no universal unattended guarantee
through locked devices, missing pairing/DDI, helper confirmations or OS termination.
FMOD redistribution and authorized CI SDK access remain public-release gates.
