import XCTest
@MainActor final class LauncherUITests: XCTestCase {
    private var app: XCUIApplication!
    override func setUpWithError() throws {
        continueAfterFailure=false
        XCUIDevice.shared.orientation = .portrait
        app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.celeste.everest.jit.everest")
        app.launchArguments=["--launcher-ui-test"]
        app.launch()
        XCTAssertTrue(app.buttons["launcher.importGame"].waitForExistence(timeout:20))
    }
    override func tearDownWithError() throws { app.terminate();XCUIDevice.shared.orientation = .portrait }
    private func ready(_ element:XCUIElement) {
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate(format:"enabled == true"),object:element)],timeout:30),.completed,app.debugDescription)
    }
    private func flip(_ row:XCUIElement) {
        // SwiftUI exposes the labelled row and the actual UISwitch separately.
        let thumb=row.switches.firstMatch
        if thumb.exists {thumb.tap()} else {row.tap()}
    }
    private func capture(_ name:String) {let a=XCTAttachment(screenshot:app.screenshot());a.name=name;a.lifetime = .keepAlways;add(a)}
    private func openMods() {app.tabBars.buttons["Mods"].tap();XCTAssertTrue(app.buttons["launcher.importMods"].waitForExistence(timeout:10));ready(app.buttons["launcher.importMods"])}
    private func search(_ name:String) {
        let field=app.searchFields.firstMatch
        if !field.isHittable {app.swipeDown()}
        XCTAssertTrue(field.waitForExistence(timeout:5),app.debugDescription)
        field.tap();field.typeText(name)
        if app.keyboards.buttons["Search"].exists {app.keyboards.buttons["Search"].tap()}
    }
    func testPortraitLandscapeAndMissingDependency() {
        XCTAssertGreaterThan(app.frame.height,app.frame.width);capture("portrait-play")
        XCUIDevice.shared.orientation = .landscapeRight
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in self.app.frame.width>self.app.frame.height },object:app)],timeout:10),.completed)
        capture("landscape-play");XCUIDevice.shared.orientation = .portrait
        openMods();search("GravityHelper")
        let control=app.switches.matching(NSPredicate(format:"identifier BEGINSWITH %@","mod.GravityHelper-")).firstMatch
        XCTAssertTrue(control.waitForExistence(timeout:10),app.debugDescription);ready(control)
        XCTAssertEqual(control.value as? String,"1");flip(control)
        let issue=app.staticTexts.matching(NSPredicate(format:"label CONTAINS %@","needs GravityHelper")).firstMatch
        XCTAssertTrue(issue.waitForExistence(timeout:15),app.debugDescription);capture("missing-dependency")
        ready(control);flip(control)
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate(format:"exists == false"),object:issue)],timeout:15),.completed)
        app.tabBars.buttons["Play"].tap()
        let run=app.buttons["launcher.run"];for _ in 0..<3 {if run.isHittable {break};app.swipeUp()}
        XCTAssertTrue(run.exists);XCTAssertFalse(run.isEnabled)
        print("PASS_LAUNCHER_PORTRAIT_LANDSCAPE_DEPENDENCY_AND_JIT_GATE")
    }
    func testRealModPickerAndPersistedChoice() {
        openMods();app.buttons["launcher.importMods"].tap()
        let zip=app.descendants(matching:.any).matching(NSPredicate(format:"label CONTAINS %@","CJITLauncherExample-v1.0.0")).firstMatch
        XCTAssertTrue(zip.waitForExistence(timeout:15),app.debugDescription);zip.tap()
        let open=app.buttons["Open"].firstMatch;if open.waitForExistence(timeout:2) && open.isHittable {open.tap()}
        ready(app.buttons["launcher.importMods"])
        search("CJITLauncherExample")
        let toggle=app.switches.matching(NSPredicate(format:"identifier BEGINSWITH %@","mod.CJITLauncherExample-")).firstMatch
        XCTAssertTrue(toggle.waitForExistence(timeout:15),app.debugDescription);ready(toggle)
        if toggle.value as? String == "1" {flip(toggle)};ready(toggle)
        capture("imported-mod")
        app.terminate();app.launch();openMods();search("CJITLauncherExample")
        XCTAssertTrue(toggle.waitForExistence(timeout:15));XCTAssertEqual(toggle.value as? String,"0")
        flip(toggle);ready(toggle)
        app.tabBars.buttons["Settings"].tap()
        XCTAssertTrue(app.switches["launcher.metrics"].waitForExistence(timeout:5));capture("settings")
        let export=app.buttons["launcher.export"];XCTAssertTrue(export.exists);export.tap()
        print("PASS_LAUNCHER_REAL_ZIP_PICKER_AND_FRESH_PROCESS_SELECTION")
    }
}
