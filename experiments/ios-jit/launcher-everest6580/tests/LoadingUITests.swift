import XCTest
final class LoadingUITests: XCTestCase {
    let app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.loading.preview")
    override func setUp() { continueAfterFailure=false;XCUIDevice.shared.orientation = .portrait }
    override func tearDown() { app.terminate();XCUIDevice.shared.orientation = .portrait }
    private func capture(_ name:String) {
        let attachment=XCTAttachment(screenshot:XCUIScreen.main.screenshot());attachment.name=name;attachment.lifetime = .keepAlways;add(attachment)
    }
    private func visible(_ name:String) {
        let item=app.staticTexts[name]
        XCTAssertTrue(item.exists,name);XCTAssertTrue(app.frame.contains(item.frame),name+" must fit without scrolling")
    }
    func testPassiveDetailsAcrossRotation() {
        app.launch();XCTAssertTrue(app.staticTexts["loading.stage"].waitForExistence(timeout:15))
        for name in ["loading.stage","loading.detail","loading.counts","loading.extraCounts","loading.elapsed"] { visible(name) }
        XCTAssertEqual(app.buttons.count,0);XCTAssertEqual(app.scrollViews.count,0);capture("passive-portrait")
        let old=app.staticTexts["loading.counts"].label;sleep(2);XCTAssertNotEqual(old,app.staticTexts["loading.counts"].label)
        XCUIDevice.shared.orientation = .landscapeLeft;sleep(2)
        for name in ["loading.stage","loading.detail","loading.counts","loading.extraCounts","loading.elapsed"] { visible(name) }
        XCTAssertEqual(app.buttons.count,0);XCTAssertEqual(app.scrollViews.count,0);capture("passive-landscape")
        print("PASS_PASSIVE_LOADING_DETAILS_AND_ROTATION")
    }
    func testIndeterminateWithLargerTextAndReducedMotion() {
        app.launchArguments=["--indeterminate","--large-type"];app.launch()
        XCTAssertTrue(app.staticTexts["loading.stage"].waitForExistence(timeout:15));capture("larger-text-portrait")
        XCTAssertEqual(app.staticTexts["preview.track"].label,"Activity checks passed")
        XCUIDevice.shared.orientation = .landscapeLeft;sleep(2)
        for name in ["loading.stage","loading.detail","loading.counts","loading.extraCounts","loading.elapsed"] { visible(name) }
        XCTAssertEqual(app.buttons.count,0);XCTAssertEqual(app.scrollViews.count,0);capture("larger-text-landscape")
        print("PASS_LOADING_INDETERMINATE_LARGER_TEXT")
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
    func testFirstFrameHandoffGuardsAndTouches() {
        app.launchArguments=["--window-cover"];app.launch()
        XCTAssertTrue(app.staticTexts["preview.focus"].waitForExistence(timeout:15));sleep(1)
        XCTAssertEqual(app.staticTexts["preview.focus"].label,"Game keeps focus; guards passed")
        app.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        XCTAssertTrue(app.staticTexts["loading.stage"].exists)
        XCTAssertTrue(app.staticTexts["preview.gameReady"].waitForExistence(timeout:20))
        XCTAssertTrue(app.staticTexts["preview.gameReady"].isHittable)
        XCTAssertTrue(app.staticTexts["preview.gameReady"].label.contains("touches=0"))
        XCTAssertFalse(app.staticTexts["loading.stage"].exists);capture("first-frame-handoff")
        print("PASS_FIRST_FRAME_WINDOW_GUARDS_FOCUS_AND_TOUCHES")
    }
    func testBackgroundDefersPresentation() {
        app.launchArguments=["--window-cover","--background-gate"];app.launch()
        XCTAssertTrue(app.staticTexts["preview.focus"].waitForExistence(timeout:15));sleep(1)
        XCTAssertEqual(app.staticTexts["preview.focus"].label,"Game keeps focus; guards passed")
        XCUIDevice.shared.press(.home);sleep(2);app.activate()
        XCTAssertTrue(app.staticTexts["preview.gameReady"].waitForExistence(timeout:10))
        XCTAssertTrue(app.staticTexts["preview.gameReady"].label.contains("background=true"))
        print("PASS_FIRST_FRAME_BACKGROUND_DEFERRAL")
    }
}
