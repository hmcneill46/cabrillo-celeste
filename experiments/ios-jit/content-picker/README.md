# Exploratory picker changes — not delivered

The owner resolved build 14 selection by enabling LiveContainer's **Fix File
Picker** setting. Build 14 remains the active physical test. No replacement
IPA is needed and no build 15 device IPA was delivered.

This isolated draft was created while investigating: import-copy mode, picker
callback/security-scope/coordinator logs, and a manual GameImport-folder route.
The managed adapter is inherited unchanged from build 14; do not rebuild or
overwrite `.build/ios-jit/content-managed` from this draft.

Native Foundation staging/cancel tests pass. The exploratory XCUITest runner
built and ran: the folder button test passed, but the actual picker test failed
to tap its filename accessibility element after it changed/disappeared. There
is **no passing real-picker UI regression**. Its logs/results are private under
`.build/ios-jit/picker-ui-tests/`. The simulator app also predates subsequent
harness/document edits and is not a frozen deliverable. Rebuild and complete
validation before any future handoff. The copied package/protocol scripts need
review for the final scope before use.

Read `docs/ios-jit/BUILD_14_FILE_PICKER_RESOLUTION.md` and the root AGENTS.md.
Keep the existing build 14 source/artifact/symbols/receipts unchanged.
