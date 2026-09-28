import XCTest
final class LoadingUITests:XCTestCase {
    let app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.shortcuts.preview")
    override func setUp(){continueAfterFailure=false;XCUIDevice.shared.orientation = .portrait}
    override func tearDown(){app.terminate();XCUIDevice.shared.orientation = .portrait}
    func capture(_ name:String){let a=XCTAttachment(screenshot:XCUIScreen.main.screenshot());a.name=name;a.lifetime = .keepAlways;add(a)}
    func reveal(_ element:XCUIElement){for _ in 0..<6 {if element.isHittable && app.frame.contains(element.frame){return};app.swipeUp()};XCTAssertTrue(element.isHittable)}
    func testReadyAndTravelPreset(){
        app.launch();XCTAssertTrue(app.staticTexts["shortcut.status"].waitForExistence(timeout:15))
        XCTAssertEqual(app.progressIndicators.count,0);capture("shortcut-ready")
        let wifi=app.switches["Wi-Fi after Travel"];reveal(wifi);XCTAssertEqual(wifi.value as? String,"1");wifi.coordinate(withNormalizedOffset:CGVector(dx:0.92,dy:0.5)).tap();XCTAssertTrue(NSPredicate(format:"value == %@","0").evaluate(with:wifi))
        let cell=app.switches["Cellular data after Travel"];reveal(cell);cell.coordinate(withNormalizedOffset:CGVector(dx:0.92,dy:0.5)).tap();XCTAssertEqual(cell.value as? String,"0")
        let start=app.buttons["Start shortcut launch"];reveal(start);start.tap();XCTAssertTrue(app.alerts["Fixture action received"].waitForExistence(timeout:5));XCTAssertTrue(app.staticTexts["shortcut.start"].exists)
        print("PASS_SHORTCUT_PRESET_CONTROLS")
    }
    func testActiveCancel(){
        app.launchArguments=["--active"];app.launch();XCTAssertTrue(app.staticTexts["shortcut.status"].waitForExistence(timeout:15))
        XCTAssertTrue(app.descendants(matching:.any)["shortcut.progress"].firstMatch.waitForExistence(timeout:5));capture("shortcut-working")
        app.buttons["Cancel launch"].tap();XCTAssertTrue(app.staticTexts["shortcut.cancel"].waitForExistence(timeout:5))
        print("PASS_SHORTCUT_ACTIVE_PRESENTATION")
    }
    func testRecoveryWithLargeTextAndRotation(){
        app.launchArguments=["--recovery","--large-type"];app.launch();XCTAssertTrue(app.buttons["shortcut.recover"].waitForExistence(timeout:15))
        XCTAssertEqual(app.progressIndicators.count,0);capture("shortcut-recovery-portrait")
        XCUIDevice.shared.orientation = .landscapeLeft;sleep(1);capture("shortcut-recovery-landscape")
        app.buttons["shortcut.recover"].tap();XCTAssertTrue(app.staticTexts["shortcut.recover"].waitForExistence(timeout:5))
        print("PASS_SHORTCUT_RECOVERY_PRESENTATION")
    }
    func testDetachWaitCannotCancelAgain(){
        app.launchArguments=["--waiting"];app.launch();XCTAssertTrue(app.buttons["Cancel launch"].waitForExistence(timeout:15));XCTAssertFalse(app.buttons["Cancel launch"].isEnabled)
        capture("shortcut-detach-wait");print("PASS_SHORTCUT_DETACH_PRESENTATION")
    }
}
