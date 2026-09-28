import XCTest

// Runs only in an iOS simulator. ImportPreview owns the test URL schemes: no
// LiveContainer, VPN, JIT service or phone radios are involved in these tests.
final class LoadingUITests:XCTestCase {
    let app=XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.import.preview")
    let shortcuts=XCUIApplication(bundleIdentifier:"com.apple.shortcuts")
    let launchLink="livecontainer2://livecontainer-launch?bundle-name=Example%20Guest.app&container-folder-name=00000000-1111-2222-3333-444444444444&open-url=Y2FicmlsbG86Ly9sYXVuY2g%3D"

    override func setUp(){super.setUp();continueAfterFailure=false;shortcuts.terminate()}
    func configure(_ variant:String){
        app.launch()
        XCTAssertTrue(app.buttons[variant].waitForExistence(timeout:15))
        app.buttons["copy-link"].tap();app.buttons[variant].tap()
        let share=app.cells["Shortcuts"]
        XCTAssertTrue(share.waitForExistence(timeout:5));share.tap()
        let setup=shortcuts.buttons["Set Up Shortcut"]
        XCTAssertTrue(setup.waitForExistence(timeout:15))
        // The import card exposes accessibility before its presentation finishes.
        sleep(2);setup.tap()
    }
    func attach(_ name:String){
        let item=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        item.name=name;item.lifetime = .keepAlways;add(item)
    }
    func test01OriginalURLQuestionRestoresOldText(){
        configure("Original48")
        let field=shortcuts.textFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout:5))
        let original=field.value as? String
        XCTAssertEqual(original,"cabrillo://shortcut-setup-required")
        field.tap();field.typeText("example");sleep(2)
        XCTAssertEqual(field.value as? String,original,"Original48 reproduces the lost-edit defect")
        attach("Original48-restores-old-value")
        print("PASS_ORIGINAL48_IMPORT_LOST_EDIT_REPRODUCED")
        shortcuts.terminate()
    }
    func test02TextQuestionRetainsTypedAndPastedLinkAndRuns(){
        configure("Candidate49")
        let field=shortcuts.textViews.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout:5))
        XCTAssertEqual(shortcuts.textFields.count,0)
        field.tap();field.typeText("example");sleep(2)
        XCTAssertEqual(field.value as? String,"example")
        print("PASS_SHORTCUT49_TYPED_TEXT_RETAINED")
        field.typeText(String(repeating:XCUIKeyboardKey.delete.rawValue,count:7))
        field.press(forDuration:1)
        XCTAssertTrue(shortcuts.menuItems["Paste"].waitForExistence(timeout:5))
        shortcuts.menuItems["Paste"].tap();sleep(2)
        XCTAssertEqual(field.value as? String,launchLink)
        attach("Candidate49-retains-complete-pasted-link")
        print("PASS_SHORTCUT49_PASTED_LINK_RETAINED")
        if shortcuts.buttons["Close"].exists {shortcuts.buttons["Close"].tap()}
        XCTAssertEqual(field.value as? String,launchLink,"Value survives ending editing")
        shortcuts.buttons["Add Shortcut"].tap()
        if shortcuts.buttons["Replace"].waitForExistence(timeout:3){shortcuts.buttons["Replace"].tap()}
        XCTAssertTrue(shortcuts.buttons["play"].waitForExistence(timeout:10))
        shortcuts.buttons["play"].tap()
        let consent=XCUIApplication(bundleIdentifier:"com.apple.ShortcutsUI")
        if consent.buttons["Allow"].waitForExistence(timeout:10){consent.buttons["Allow"].tap()}
        XCTAssertTrue(app.wait(for:.runningForeground,timeout:15))
        XCTAssertTrue(app.staticTexts["received-url"].waitForExistence(timeout:5))
        XCTAssertEqual(app.staticTexts["received-url"].label,launchLink)
        attach("Candidate49-exact-imported-URL-received")
        print("PASS_SHORTCUT49_APPLE_IMPORT_AND_EXACT_URL_EXECUTION")
    }
}
