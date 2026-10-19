import XCTest

// Actual Apple picker/delegate and production staging; no entitlement test seam,
// delegate injection, game files, or physical device control.
final class PickerUITests:XCTestCase {
    let app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.copypicker.preview")
    override func setUp(){super.setUp();continueAfterFailure=false}
    func attach(_ name:String){let item=XCTAttachment(screenshot:XCUIScreen.main.screenshot());item.name=name;item.lifetime = .keepAlways;add(item)}
    func openAndSelect(_ selection:Int,_ copy:Bool){
        app.buttons["import-zip"].tap()
        let zip=app.cells.matching(NSPredicate(format:"identifier == %@","synthetic.zip, zip")).firstMatch
        XCTAssertTrue(zip.waitForExistence(timeout:15),app.debugDescription)
        attach("ZIP-ready-for-single-tap-\(selection)")
        zip.tap()
        let result=app.staticTexts["result"]
        expectation(for:NSPredicate(format:"label BEGINSWITH %@","PASS selection \(selection); staged SHA256 "),evaluatedWith:result)
        waitForExpectations(timeout:20)
        XCTAssertEqual(app.staticTexts["picker-mode"].label,copy ? "copy54 mode Import":"open-control53 mode Open")
        attach("ZIP-selected-staged-source-preserved-\(selection)")
    }
    func exercise(_ copy:Bool){
        app.launchArguments=copy ? ["--copy"]:[];app.launch()
        XCTAssertTrue(app.buttons["import-zip"].waitForExistence(timeout:15))
        openAndSelect(1,copy)
        app.buttons["import-zip"].tap()
        let cancel=app.buttons["Cancel"].firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout:15));cancel.tap()
        expectation(for:NSPredicate(format:"label == %@","Cancelled; source preserved"),evaluatedWith:app.staticTexts["result"])
        waitForExpectations(timeout:10)
        attach("picker-cancelled-source-preserved")
        openAndSelect(2,copy)
        print(copy ? "PASS_COPY54_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT":"PASS_OPEN53_CONTROL_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT")
        app.terminate()
    }
    func test01OriginalOpenControlStagesCancelsAndRepeats(){exercise(false)}
    func test02Copy54StagesCancelsAndRepeats(){exercise(true)}
}
