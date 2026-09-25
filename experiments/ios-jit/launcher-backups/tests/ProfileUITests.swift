import XCTest
final class ProfileUITests: XCTestCase {
    let app = XCUIApplication(bundleIdentifier: "io.github.hmcneill46.cabrillo.backups.preview")
    override func setUp() { continueAfterFailure = false; XCUIDevice.shared.orientation = .portrait }
    override func tearDown() { app.terminate(); XCUIDevice.shared.orientation = .portrait }
    func capture(_ name: String) { let a = XCTAttachment(screenshot: XCUIScreen.main.screenshot()); a.name = name; a.lifetime = .keepAlways; add(a) }
    func scrollUp() { app.collectionViews.firstMatch.swipeUp(velocity: .slow) }
    func scrollDown() { app.collectionViews.firstMatch.swipeDown(velocity: .slow) }
    func button(_ id: String) -> XCUIElement {
        let element = app.buttons[id]
        for _ in 0..<10 { if element.exists && element.isHittable { return element }; scrollUp() }
        XCTFail("Button not reachable: " + id); return element
    }
    func top() { for _ in 0..<5 { scrollDown() } }
    func waitMessage(_ text: String) {
        top()
        let pred = NSPredicate(format: "label CONTAINS %@", text)
        expectation(for: pred, evaluatedWith: app.staticTexts["profile.message"]); waitForExpectations(timeout: 15)
    }
    func testCreateReviewCancelExport() {
        app.launch(); XCTAssertTrue(app.buttons["profile.create"].waitForExistence(timeout: 15)); capture("saves-portrait")
        button("profile.create").tap(); waitMessage("Backup verified")
        button("profile.export.0").tap(); XCTAssertTrue(app.alerts["Export requested"].waitForExistence(timeout: 3)); app.alerts.buttons["OK"].tap()
        button("profile.review.0").tap(); waitMessage("Review the backup")
        button("profile.cancel").tap(); waitMessage("cancelled")
        XCTAssertFalse(app.buttons["profile.restore"].exists); capture("backup-retained")
    }
    func testRestoreRelaunchRollback() {
        app.launch(); XCTAssertTrue(app.buttons["profile.create"].waitForExistence(timeout: 15))
        button("profile.create").tap(); waitMessage("Backup verified")
        button("profile.review.0").tap(); waitMessage("Review the backup")
        button("profile.restore").tap(); XCTAssertTrue(app.alerts["Replace profile"].waitForExistence(timeout: 3)); capture("restore-confirmation")
        app.alerts.buttons["profile.confirm"].firstMatch.tap(); waitMessage("Backup restored")
        top(); XCTAssertTrue(app.staticTexts["profile.restart"].exists); XCTAssertFalse(app.buttons["profile.create"].isEnabled); capture("restore-relaunch-required")
        app.terminate(); app.launchArguments = ["--preserve"]; app.launch()
        XCTAssertTrue(app.buttons["profile.create"].waitForExistence(timeout: 15))
        button("profile.rollback").tap(); app.alerts.buttons["profile.confirm"].firstMatch.tap(); waitMessage("Previous profile restored")
        top(); XCTAssertFalse(app.buttons["profile.create"].isEnabled)
        app.terminate(); app.launchArguments = ["--preserve"]; app.launch()
        XCTAssertTrue(app.buttons["profile.create"].waitForExistence(timeout: 15))
        button("profile.discard").tap(); app.alerts.buttons["profile.confirm"].firstMatch.tap(); waitMessage("Retained copy discarded")
        top(); XCTAssertTrue(app.buttons["profile.import"].isEnabled); capture("rollback-complete")
    }
    func testAdditionalSlotsAndLargeTextRotation() {
        app.launchArguments = ["--large-type"]; app.launch()
        XCTAssertTrue(app.navigationBars["Saves"].waitForExistence(timeout: 15)); _ = button("profile.create"); capture("saves-large-type")
        XCUIDevice.shared.orientation = .landscapeLeft
        sleep(2)
        let slot = app.descendants(matching: .any).matching(identifier: "profile.slot.1000").firstMatch
        for _ in 0..<12 { if slot.exists && slot.isHittable { break }; scrollUp() }
        XCTAssertTrue(slot.exists && slot.isHittable); capture("save-slot-1001-landscape")
    }
    func testUsedProcessDisablesProfileChanges() {
        app.launchArguments = ["--used"]; app.launch()
        XCTAssertTrue(app.buttons["profile.create"].waitForExistence(timeout: 15)); XCTAssertFalse(app.buttons["profile.create"].isEnabled); XCTAssertFalse(app.buttons["profile.import"].isEnabled)
    }
    func testFailureKeepsDiagnosticsExport() {
        app.launchArguments = ["--failure"]; app.launch()
        XCTAssertTrue(app.buttons["profile.exportDiagnostics"].waitForExistence(timeout: 15)); button("profile.exportDiagnostics").tap()
        XCTAssertTrue(app.alerts["Export requested"].waitForExistence(timeout: 3)); app.alerts.buttons["OK"].tap(); capture("profile-error-export")
    }
}
