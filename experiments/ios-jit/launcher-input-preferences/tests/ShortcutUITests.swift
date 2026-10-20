import XCTest
final class LoadingUITests:XCTestCase {
    let app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.shortcuts.preview")
    override func setUp(){continueAfterFailure=false;XCUIDevice.shared.orientation = .portrait}
    override func tearDown(){app.terminate();XCUIDevice.shared.orientation = .portrait}
    func capture(_ name:String){let a=XCTAttachment(screenshot:XCUIScreen.main.screenshot());a.name=name;a.lifetime = .keepAlways;add(a)}
    func reveal(_ element:XCUIElement){
        for _ in 0..<10 {
            if element.exists && element.isHittable && app.frame.contains(element.frame){return}
            let list=app.collectionViews.element(boundBy:max(0,app.collectionViews.count-1))
            let area=list.exists ? list : app
            area.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.72)).press(forDuration:0.05,thenDragTo:area.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.3)))
        }
        XCTAssertTrue(element.exists && element.isHittable)
    }
    func testReadyAndTravelPreset(){
        app.launch();XCTAssertTrue(app.staticTexts["shortcut.status"].waitForExistence(timeout:15))
        XCTAssertEqual(app.progressIndicators.count,0);capture("shortcut-ready")
        let wifi=app.switches["Wi-Fi after Travel"];reveal(wifi);XCTAssertEqual(wifi.value as? String,"1");wifi.coordinate(withNormalizedOffset:CGVector(dx:0.92,dy:0.5)).tap();XCTAssertTrue(NSPredicate(format:"value == %@","0").evaluate(with:wifi))
        let cell=app.switches["Cellular data after Travel"];reveal(cell);cell.coordinate(withNormalizedOffset:CGVector(dx:0.92,dy:0.5)).tap();XCTAssertEqual(cell.value as? String,"0")
        let start=app.buttons["Test installed shortcut"];reveal(start);start.tap();XCTAssertTrue(app.alerts["Fixture action received"].waitForExistence(timeout:5));XCTAssertTrue(app.staticTexts["shortcut.install.test"].exists)
        print("PASS_SHORTCUT_PRESET_CONTROLS")
    }
    func testActiveCancel(){
        app.launchArguments=["--active"];app.launch();XCTAssertTrue(app.staticTexts["shortcut.status"].waitForExistence(timeout:15))
        XCTAssertTrue(app.descendants(matching:.any)["shortcut.progress"].firstMatch.waitForExistence(timeout:5));capture("shortcut-working")
        let setup=app.buttons["shortcut.setup"];reveal(setup);XCTAssertFalse(setup.isEnabled)
        app.swipeDown()
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
    func testLiveContainerSetupAndExportAction(){
        app.launch();let setup=app.buttons["shortcut.setup"];XCTAssertTrue(setup.waitForExistence(timeout:15));reveal(setup);setup.tap()
        let export=app.buttons["shortcut.install.export"];XCTAssertTrue(export.waitForExistence(timeout:5));reveal(export);XCTAssertTrue(export.isEnabled)
        XCTAssertTrue(app.buttons["Copy launch link again"].exists);capture("shortcut-setup-livecontainer")
        export.tap();XCTAssertTrue(app.staticTexts["shortcut.install.export"].waitForExistence(timeout:5));print("PASS_SHORTCUT_INSTALL_EXPORT_ACTION")
    }
    func testStandaloneHelperSetup(){
        app.launchArguments=["--standalone"];app.launch();let setup=app.buttons["shortcut.setup"];XCTAssertTrue(setup.waitForExistence(timeout:15));reveal(setup);setup.tap()
        let field=app.textFields["shortcut.helperLink"];XCTAssertTrue(field.waitForExistence(timeout:5));reveal(field)
        let save=app.buttons["Save helper link"];XCTAssertFalse(save.isEnabled)
        field.tap();field.typeText("livecontainer://livecontainer-launch?bundle-name=Stik.app")
        app.buttons["shortcut.helperDone"].tap();reveal(save);XCTAssertTrue(save.isEnabled);capture("shortcut-setup-standalone-helper");save.tap()
        XCTAssertTrue(app.staticTexts["shortcut.install.helper"].waitForExistence(timeout:5));print("PASS_SHORTCUT_HELPER_SETUP_ACTION")
    }
    func testSetupLargeTextAndRotation(){
        app.launchArguments=["--large-type"];app.launch();let setup=app.buttons["shortcut.setup"];XCTAssertTrue(setup.waitForExistence(timeout:15));reveal(setup);setup.tap()
        let export=app.buttons["shortcut.install.export"];XCTAssertTrue(export.waitForExistence(timeout:5));reveal(export);capture("shortcut-setup-large-portrait")
        XCUIDevice.shared.orientation = .landscapeLeft;sleep(2);reveal(app.buttons["Open Cabrillo in Shortcuts"]);capture("shortcut-setup-large-landscape")
        XCTAssertTrue(app.buttons["Done"].isHittable);app.buttons["Done"].tap();print("PASS_SHORTCUT_SETUP_LAYOUT")
    }

}
