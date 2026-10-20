import XCTest

final class ProfileUITests: XCTestCase {
    func testFeatherPreference() {
        let app = XCUIApplication(bundleIdentifier: "io.github.hmcneill46.cabrillo.backups.preview")
        func settings(_ args: [String]) -> XCUIElement {
            app.launchArguments = args; app.launch()
            app.buttons["Settings"].firstMatch.tap()
            let toggle = app.switches["cabrillo.featherTouch"]
            XCTAssertTrue(toggle.waitForExistence(timeout: 10))
            return toggle
        }
        var toggle = settings([])
        XCTAssertEqual(toggle.value as? String, "0")
        toggle.coordinate(withNormalizedOffset: CGVector(dx: 0.92, dy: 0.5)).tap(); XCTAssertEqual(toggle.value as? String, "1")
        let shot = XCTAttachment(screenshot: app.screenshot()); shot.lifetime = .keepAlways; add(shot)
        app.terminate(); toggle = settings(["--preserve"])
        XCTAssertEqual(toggle.value as? String, "1")
        toggle.coordinate(withNormalizedOffset: CGVector(dx: 0.92, dy: 0.5)).tap(); XCTAssertEqual(toggle.value as? String, "0")
        app.terminate(); toggle = settings(["--preserve"])
        XCTAssertEqual(toggle.value as? String, "0")
        app.terminate(); toggle = settings(["--preserve", "--used"])
        XCTAssertFalse(toggle.isEnabled)
        print("PASS_FEATHER_NATIVE_TOGGLE_DEFAULT_PERSISTENCE_AND_LOCK")
        app.terminate()
    }
}
