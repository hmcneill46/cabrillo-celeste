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
    func testNativeClosingPresentation() {
        app.terminate();app.launchArguments=["--launcher-ui-test","--launcher-closing-test"];app.launch()
        XCTAssertTrue(app.staticTexts["Returning to camp"].waitForExistence(timeout:15))
        XCTAssertEqual(app.staticTexts["session.stage"].label,"Closing game and mod hooks")
        XCTAssertFalse(app.buttons["launcher.run"].exists);capture("native-closing-portrait")
        XCUIDevice.shared.orientation = .landscapeRight
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in self.app.frame.width>self.app.frame.height },object:app)],timeout:10),.completed)
        XCTAssertTrue(app.staticTexts["session.stage"].isHittable);capture("native-closing-landscape")
        print("PASS_NATIVE_CLOSING_SCREEN_PORTRAIT_AND_LANDSCAPE")
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
        XCTAssertTrue(run.exists);ready(run);run.tap()
        XCTAssertTrue(app.alerts["Enable JIT first"].waitForExistence(timeout:5),app.debugDescription)
        app.alerts.buttons["OK"].tap()
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
    func testUpdateReviewCancellationAndInstall() {
        app.terminate();app.launchArguments=["--launcher-ui-test","--launcher-install-ui-fixture"]
        app.launch();openMods()
        app.segmentedControls["mods.pages"].buttons["Updates"].tap()
        let check=app.buttons["mods.checkUpdates"];XCTAssertTrue(check.waitForExistence(timeout:10));ready(check)
        if !app.buttons["mods.updateAll"].exists {check.tap();ready(check)}
        let update=app.buttons["update.helper-old.zip"];XCTAssertTrue(update.waitForExistence(timeout:15),app.debugDescription)
        capture("updates-portrait")
        update.tap();let apply=app.buttons["install.apply"];XCTAssertTrue(apply.waitForExistence(timeout:15),app.debugDescription)
        for _ in 0..<5 {if apply.isHittable {break};app.swipeUp()}
        capture("update-review");apply.tap()
        let close=app.buttons["install.close"];XCTAssertTrue(close.waitForExistence(timeout:10));close.tap()
        XCTAssertTrue(app.buttons["install.retry"].waitForExistence(timeout:15),app.debugDescription)
        XCTAssertTrue(app.staticTexts["No mod changes applied"].exists,app.debugDescription)
        capture("download-cancelled");close.tap();ready(check);check.tap();ready(check)
        app.buttons["mods.updateAll"].tap();XCTAssertTrue(apply.waitForExistence(timeout:10))
        for _ in 0..<5 {if apply.isHittable {break};app.swipeUp()};apply.tap()
        XCTAssertTrue(app.staticTexts["Ready for your next climb"].waitForExistence(timeout:30),app.debugDescription)
        XCTAssertTrue(app.staticTexts["Changes applied"].exists,app.debugDescription)
        let change=app.staticTexts["change.Helper"]
        for _ in 0..<6 {if change.exists {break};app.swipeUp()}
        XCTAssertEqual(change.label,"1.0 → 1.3",app.debugDescription)
        XCTAssertTrue(app.staticTexts["Installed mods"].exists,app.debugDescription)
        capture("update-installed");close.tap();ready(check)
        app.buttons["mods.lastReport"].tap()
        XCTAssertTrue(app.staticTexts["Installation report"].waitForExistence(timeout:10))
        XCTAssertTrue(app.staticTexts["Changes applied"].exists)
        capture("saved-installation-report");app.buttons["install.close"].tap();ready(check)
        app.segmentedControls["mods.pages"].buttons["Installed"].tap()
        XCTAssertTrue(app.switches.matching(NSPredicate(format:"label CONTAINS %@","Show retained previous archives")).firstMatch.waitForExistence(timeout:10),app.debugDescription)
        XCUIDevice.shared.orientation = .landscapeRight
        capture("installed-mods-landscape")
        XCUIDevice.shared.orientation = .portrait
        app.tabBars.buttons["Settings"].tap()
        let export=app.buttons["launcher.export"]
        for _ in 0..<5 {if export.exists && export.isHittable {break};app.swipeUp()}
        XCTAssertTrue(export.waitForExistence(timeout:10));export.tap()
        print("PASS_NATIVE_UPDATE_REVIEW_CANCEL_COMMIT")
    }
    func testBlockedUpdateAndInstallationReview() {
        // The host supplies a future-runtime candidate in the existing external
        // simulator fixture. No test transport or ZIP is in the device payload.
        app.terminate(); app.launchArguments=["--launcher-ui-test","--launcher-install-ui-fixture"]
        app.launch(); openMods(); app.segmentedControls["mods.pages"].buttons["Updates"].tap()
        let check=app.buttons["mods.checkUpdates"]; XCTAssertTrue(check.waitForExistence(timeout:10)); ready(check)
        check.tap(); ready(check)
        XCTAssertTrue(app.staticTexts["Requires an app update"].waitForExistence(timeout:15),app.debugDescription)
        XCTAssertFalse(app.buttons["update.helper-old.zip"].exists)
        XCTAssertFalse(app.buttons["mods.updateAll"].exists)
        capture("blocked-update-no-action")
        app.segmentedControls["mods.pages"].buttons["Installed"].tap()
        let resolve=app.buttons["mods.resolve"]; ready(resolve); resolve.tap()
        XCTAssertTrue(app.staticTexts["Installation blocked"].waitForExistence(timeout:15),app.debugDescription)
        XCTAssertTrue(app.staticTexts["install.blocked"].exists)
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format:"label CONTAINS %@","Helper 1.3 requires Everest 1.6531.0")).firstMatch.exists)
        XCTAssertFalse(app.buttons["install.apply"].exists)
        capture("blocked-review-reason-first")
        XCUIDevice.shared.orientation = .landscapeRight
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in self.app.frame.width>self.app.frame.height },object:app)],timeout:10),.completed)
        Thread.sleep(forTimeInterval:2)
        XCTAssertFalse(app.buttons["install.apply"].exists); capture("blocked-review-landscape")
        app.buttons["install.close"].tap()
        print("PASS_NATIVE_BLOCKED_UPDATES_AND_REVIEW")
    }
    func testFreshSpringReviewUsesCompatibleEarlierReleases() {
        openMods(); let resolve=app.buttons["mods.resolve"]; ready(resolve); resolve.tap()
        XCTAssertTrue(app.staticTexts["Compatible earlier releases"].waitForExistence(timeout:90),app.debugDescription)
        XCTAssertFalse(app.staticTexts["Installation blocked"].exists)
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format:"label CONTAINS %@","ExtendedVariantMode 0.50.5: using a verified earlier release")).firstMatch.exists)
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format:"label CONTAINS %@","MaxHelpingHand 1.40.9: using a verified earlier release")).firstMatch.exists)
        capture("fresh-spring-earlier-releases")
        let apply=app.buttons["install.apply"]
        for _ in 0..<16 { if apply.exists && apply.isHittable {break}; app.swipeUp() }
        XCTAssertTrue(apply.exists && apply.isEnabled,app.debugDescription)
        capture("fresh-spring-reviewed-download")
        app.buttons["install.close"].tap()
        print("PASS_NATIVE_FRESH_SPRING_EARLIER_RELEASE_REVIEW")
    }
}
