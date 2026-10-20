import XCTest

// Uses Apple's actual document picker and the production archive staging code.
// No delegate injection, game files, pairing, VPN, JIT, or physical device access.
final class PickerUITests:XCTestCase {
    let app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.signingpicker.preview")
    override func setUp(){super.setUp();continueAfterFailure=false}
    func attach(_ name:String){let item=XCTAttachment(screenshot:XCUIScreen.main.screenshot());item.name=name;item.lifetime = .keepAlways;add(item)}
    func openAndSelect(_ selection:Int){
        app.buttons["import-zip"].tap()
        let zip=app.cells.matching(NSPredicate(format:"identifier == %@","synthetic.zip, zip")).firstMatch
        XCTAssertTrue(zip.waitForExistence(timeout:15),app.debugDescription)
        attach("ZIP-ready-for-single-tap-\(selection)")
        zip.tap()
        let result=app.staticTexts["result"]
        let staged=NSPredicate(format:"label BEGINSWITH %@","PASS selection \(selection); staged SHA256 ")
        expectation(for:staged,evaluatedWith:result)
        waitForExpectations(timeout:20)
        attach("ZIP-selected-staged-source-preserved-\(selection)")
    }
    func exercise(_ compatible:Bool){
        app.launchArguments=compatible ? ["--compatibility"]:[];app.launch()
        XCTAssertTrue(app.buttons["import-zip"].waitForExistence(timeout:15))
        openAndSelect(1)
        if compatible {XCTAssertTrue(app.staticTexts["compatibility"].label.contains("installed"))}
        app.buttons["import-zip"].tap()
        let cancel=app.buttons["Cancel"].firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout:15));cancel.tap()
        let result=app.staticTexts["result"]
        expectation(for:NSPredicate(format:"label == %@","Cancelled; source preserved"),evaluatedWith:result)
        waitForExpectations(timeout:10)
        attach("picker-cancelled-source-preserved")
        openAndSelect(2)
        print(compatible ? "PASS_COMPATIBILITY_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT":"PASS_ORIGINAL_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT")
        app.terminate()
    }
    func test01OriginalPickerStagesCancelsAndRepeats(){exercise(false)}
    func test02CompatibilityPickerStagesCancelsAndRepeats(){exercise(true)}
}
