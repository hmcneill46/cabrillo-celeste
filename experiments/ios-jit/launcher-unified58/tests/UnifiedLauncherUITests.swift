import XCTest

final class ProfileUITests: XCTestCase {
    let app = XCUIApplication(bundleIdentifier: "io.github.hmcneill46.cabrillo.unified58.preview")
    override func setUp() { continueAfterFailure = false; XCUIDevice.shared.orientation = .portrait }
    override func tearDown() { app.terminate(); XCUIDevice.shared.orientation = .portrait }
    private func launch(_ state: String) {
        app.launchArguments = ["--state=" + state]; app.launch()
        XCTAssertTrue(app.navigationBars["Cabrillo"].waitForExistence(timeout: 15))
    }
    private func reveal(_ item: XCUIElement) {
        for _ in 0..<16 {
            if item.exists && item.isHittable && app.frame.contains(item.frame) { return }
            if let list = app.collectionViews.allElementsBoundByIndex.last { list.swipeUp() } else { app.swipeUp() }
        }
        XCTAssertTrue(item.exists); XCTAssertTrue(item.isHittable)
    }
    private func capture(_ name: String) {
        let image = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        image.name = name; image.lifetime = .keepAlways; add(image)
    }

    func testTouchSettingsAndIntegratedJITCoexist() {
        launch("integratedService")
        XCTAssertTrue(app.buttons["How to get your game files"].exists)
        let status = app.staticTexts["integrated.jitStatus"]; reveal(status)
        XCTAssertFalse(status.label.contains("verified"))
        let run = app.buttons["launcher.run"]; reveal(run); XCTAssertTrue(run.isEnabled)
        app.buttons["Settings"].firstMatch.tap()
        let controls = app.buttons["touch.open"]
        XCTAssertTrue(controls.waitForExistence(timeout: 5)); XCTAssertTrue(controls.isEnabled); controls.tap()
        XCTAssertTrue(app.buttons["Behavior"].waitForExistence(timeout: 5)); app.buttons["Behavior"].tap()
        let feather = app.switches["touch.featherTouch"]; reveal(feather)
        XCTAssertEqual(feather.value as? String, "0")
        feather.coordinate(withNormalizedOffset: CGVector(dx: 0.92, dy: 0.5)).tap()
        capture("merged-live-touch-preferences")
        app.buttons["touch.save"].tap()
        XCTAssertTrue(controls.waitForExistence(timeout: 5))
        let extra = app.switches["cabrillo.featherTouch"]; reveal(extra)
        XCTAssertEqual(extra.value as? String, "1")
        let pairing = app.buttons["integrated.importPairing"]; reveal(pairing); pairing.tap()
        XCTAssertTrue(app.alerts["Fixture action"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.alerts.staticTexts["integrated.importPairing"].exists)
        app.alerts.buttons["OK"].tap()
        capture("merged-integrated-jit-settings")
        print("PASS_UNIFIED_TOUCH_SAVE_FEATHER_AND_INTEGRATED_PAIRING_ACTION")
    }

    func testIntegratedBusyLocksEditorAndExternalProviderKeepsIt() {
        launch("integratedProgress")
        app.buttons["Settings"].firstMatch.tap()
        XCTAssertTrue(app.buttons["touch.open"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["touch.open"].isEnabled)
        app.terminate()
        launch("ready")
        app.buttons["Settings"].firstMatch.tap()
        XCTAssertTrue(app.buttons["touch.open"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["touch.open"].isEnabled); app.buttons["touch.open"].tap()
        XCTAssertTrue(app.buttons["touch.save"].waitForExistence(timeout: 5))
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(app.otherElements["touch.fullScreen"].firstMatch.waitForExistence(timeout: 10))
        let canvas = app.otherElements["touch.canvas"].firstMatch.frame
        let screen = app.windows.firstMatch.frame
        XCTAssertEqual(canvas.width, screen.width, accuracy: 2)
        XCTAssertEqual(canvas.height, screen.height, accuracy: 2)
        capture("merged-external-provider-full-display-editor")
        print("PASS_UNIFIED_JIT_BUSY_LOCK_AND_EXTERNAL_FULL_DISPLAY_EDITOR")
    }

    func testLayoutCopyPickerCancellationKeepsDraft() {
        launch("integratedService")
        app.buttons["Settings"].firstMatch.tap(); app.buttons["touch.open"].tap()
        XCTAssertTrue(app.buttons["touch.mirror"].waitForExistence(timeout: 5))
        app.buttons["touch.mirror"].tap(); XCTAssertTrue(app.buttons["touch.undo"].isEnabled)
        let importer = app.buttons["touch.import"]; reveal(importer); importer.tap()
        // The editor has its own Cancel behind Files. Require the picker action,
        // then wait for the real dismissal before interacting with the draft.
        let cancel = app.buttons.matching(NSPredicate(format: "label == %@ AND identifier != %@", "Cancel", "touch.cancel")).firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout: 10))
        expectation(for: NSPredicate(format: "hittable == true"), evaluatedWith: cancel)
        waitForExpectations(timeout: 10); cancel.tap()
        expectation(for: NSPredicate(format: "hittable == true"), evaluatedWith: app.buttons["touch.cancel"])
        waitForExpectations(timeout: 10)
        XCTAssertTrue(app.buttons["touch.save"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["touch.undo"].isEnabled)
        app.buttons["touch.cancel"].tap()
        XCTAssertTrue(app.buttons["Discard changes"].waitForExistence(timeout: 5)); app.buttons["Discard changes"].tap()
        XCTAssertTrue(app.buttons["touch.open"].waitForExistence(timeout: 5))
        print("PASS_UNIFIED_LAYOUT_COPY_PICKER_CANCEL_RETAINS_DRAFT")
    }
}
