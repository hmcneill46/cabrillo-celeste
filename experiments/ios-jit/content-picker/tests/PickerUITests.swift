import XCTest

@MainActor
final class PickerUITests: XCTestCase {
    private var app: XCUIApplication!
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication(bundleIdentifier: "io.github.hmcneill46.celeste.everest.jit.everest")
        app.launchArguments = ["--content-ui-picker-interaction"]
        app.launch()
        XCTAssertTrue(app.buttons["content.import"].waitForExistence(timeout: 10))
    }
    override func tearDownWithError() throws { app.terminate() }
    private func staged() {
        let status = app.staticTexts["probe.status"]
        let ready = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value == %@", "content-staged"), object: status)
        XCTAssertEqual(XCTWaiter.wait(for: [ready], timeout: 30), .completed, app.debugDescription)
        XCTAssertFalse(app.buttons["probe.run"].isEnabled)
        let capture = XCTAttachment(screenshot: app.screenshot()); capture.lifetime = .keepAlways; add(capture)
    }
    func testActualDocumentPickerReturnsCopy() {
        app.buttons["content.import"].tap()
        let zip = app.descendants(matching: .any).matching(NSPredicate(format: "label CONTAINS %@", "celeste-picker-fixture")).firstMatch
        XCTAssertTrue(zip.waitForExistence(timeout: 15), app.debugDescription)
        zip.tap()
        let open = app.buttons["Open"].firstMatch
        if open.waitForExistence(timeout: 2) && open.isHittable { open.tap() }
        staged()
        print("PASS_REAL_PICKER_TAP_DELEGATE_COPY_AND_JIT_GATE")
    }
    func testFolderImportButton() {
        let button = app.buttons["content.folder_import"]
        for _ in 0..<5 {
            if button.isHittable { break }
            app.swipeUp()
        }
        XCTAssertTrue(button.isHittable, app.debugDescription)
        button.tap()
        staged()
        print("PASS_REAL_FOLDER_BUTTON_COPY_AND_JIT_GATE")
    }
}
