import XCTest
final class LoadingUITests: XCTestCase {
    let app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.loading.preview")
    override func setUp() { continueAfterFailure=false;XCUIDevice.shared.orientation = .portrait }
    override func tearDown() { app.terminate();XCUIDevice.shared.orientation = .portrait }
    private func capture(_ name:String) {
        let attachment=XCTAttachment(screenshot:XCUIScreen.main.screenshot());attachment.name=name;attachment.lifetime = .keepAlways;add(attachment)
    }
    func testLoadingRemainsInteractiveAcrossRotation() {
        app.launch();XCTAssertTrue(app.staticTexts["loading.stage"].waitForExistence(timeout:15))
        XCTAssertTrue(app.staticTexts["loading.elapsed"].exists);capture("loading-portrait")
        app.buttons["loading.details"].firstMatch.tap()
        XCTAssertTrue(app.staticTexts["preview.expanded"].waitForExistence(timeout:3));capture("loading-details-portrait")
        XCUIDevice.shared.orientation = .landscapeLeft
        sleep(2);capture("loading-landscape")
        XCTAssertTrue(app.staticTexts["loading.stage"].exists)
        app.buttons["loading.details"].firstMatch.tap()
        XCTAssertFalse(app.staticTexts["preview.expanded"].exists)
        let old=app.staticTexts["loading.elapsed"].label
        sleep(2);XCTAssertNotEqual(old,app.staticTexts["loading.elapsed"].label)
        capture("loading-landscape-collapsed")
        print("PASS_LOADING_PRESENTATION_ROTATION_AND_LIVE_DETAILS")
    }
    func testFailureKeepsExportAvailable() {
        app.launchArguments=["--failure"];app.launch()
        XCTAssertTrue(app.staticTexts["loading.failure"].waitForExistence(timeout:15));capture("loading-error-portrait")
        app.buttons["loading.export"].tap();XCTAssertTrue(app.alerts["Fixture action received"].waitForExistence(timeout:3));app.alerts.buttons["OK"].tap()
        XCUIDevice.shared.orientation = .landscapeLeft;sleep(2);app.swipeUp();capture("loading-error-landscape")
        XCTAssertTrue(app.buttons["loading.export"].isHittable)
        print("PASS_LOADING_FAILURE_EXPORT_PRESENTATION")
    }
    func testFilePreparationCancellation() {
        app.launchArguments=["--files"];app.launch()
        XCTAssertTrue(app.buttons["loading.cancelFiles"].waitForExistence(timeout:15));app.buttons["loading.cancelFiles"].tap()
        XCTAssertTrue(app.alerts["Fixture action received"].waitForExistence(timeout:3))
        print("PASS_LOADING_FILE_CANCEL_PRESENTATION")
    }
    func testCoverDoesNotStealGameFocus() {
        app.launchArguments=["--window-cover"];app.launch()
        XCTAssertTrue(app.staticTexts["preview.focus"].waitForExistence(timeout:15))
        XCTAssertEqual(app.staticTexts["preview.focus"].label,"Game keeps focus")
        app.buttons["loading.details"].firstMatch.tap()
        XCTAssertTrue(app.staticTexts["preview.expanded"].waitForExistence(timeout:3))
        sleep(2);XCTAssertEqual(app.staticTexts["preview.focus"].label,"Game keeps focus")
        app.buttons["preview.handoff"].tap()
        XCTAssertTrue(app.staticTexts["preview.gameReady"].waitForExistence(timeout:3))
        XCTAssertTrue(app.staticTexts["preview.gameReady"].isHittable)
        print("PASS_NATIVE_LOADING_WINDOW_FOCUS_AND_HANDOFF")
    }
}
