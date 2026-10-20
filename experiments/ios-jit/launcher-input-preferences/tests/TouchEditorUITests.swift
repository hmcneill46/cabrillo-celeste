import XCTest

final class ProfileUITests: XCTestCase {
    func testNativeEditor() {
        let app = XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.touch.preview")
        XCUIDevice.shared.orientation = .portrait
        defer {app.terminate();XCUIDevice.shared.orientation = .portrait}
        func launch(_ args: [String] = []) {
            app.launchArguments = args;app.launch();app.buttons["Settings"].firstMatch.tap()
            XCTAssertTrue(app.buttons["touch.open"].waitForExistence(timeout:10))
        }
        func open() { app.buttons["touch.open"].tap();XCTAssertTrue(app.buttons["touch.save"].waitForExistence(timeout:10)) }
        func toggle(_ id: String) { app.switches[id].coordinate(withNormalizedOffset:CGVector(dx:0.92,dy:0.5)).tap() }
        func reveal(_ element: XCUIElement) {
            for _ in 0..<15 { if element.exists && element.isHittable { return }; app.collectionViews.allElementsBoundByIndex.last!.swipeUp() }
        }
        launch();open()
        XCTAssertTrue(app.descendants(matching:.any)["touch.canvas"].firstMatch.exists)
        app.buttons["touch.mirror"].tap();XCTAssertTrue(app.buttons["touch.undo"].isEnabled);app.buttons["touch.undo"].tap()
        let jump = app.otherElements["touch.canvas.jump"].firstMatch
        if jump.exists { jump.tap() } else { app.staticTexts["Jump"].firstMatch.tap() }
        reveal(app.buttons["touch.duplicate"]);XCTAssertTrue(app.buttons["touch.duplicate"].exists)
        app.buttons["touch.duplicate"].tap()
        for _ in 0..<5 { if app.buttons["touch.selection"].isHittable { break }; app.collectionViews.allElementsBoundByIndex.last!.swipeDown() }
        XCTAssertTrue(app.buttons["touch.selection"].label.contains("9. Jump"))
        app.buttons["touch.undo"].tap();XCTAssertTrue(app.buttons["touch.selection"].label.contains("3. Jump"))
        let canvasShot = XCTAttachment(screenshot:XCUIScreen.main.screenshot());canvasShot.lifetime = .keepAlways;add(canvasShot)
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(app.otherElements["touch.fullScreen"].firstMatch.waitForExistence(timeout:10))
        XCTAssertTrue(app.otherElements["touch.gameGuide"].firstMatch.exists)
        XCUIDevice.shared.orientation = .portrait
        XCTAssertTrue(app.buttons["touch.mirror"].waitForExistence(timeout:10))
        app.buttons["Behavior"].tap()
        let initialSwipe = app.switches["touch.swipe"]
        reveal(initialSwipe);XCTAssertTrue(initialSwipe.exists)
        XCTAssertEqual(app.switches["touch.swipe"].value as? String,"0")
        for _ in 0..<15 { if app.buttons["Tap / Swipe"].isHittable { break }; app.collectionViews.allElementsBoundByIndex.last!.swipeDown() }; app.buttons["Tap / Swipe"].tap();reveal(app.switches["touch.swipe"])
        XCTAssertEqual(app.switches["touch.swipe"].value as? String,"1")
        app.buttons["touch.save"].tap();XCTAssertTrue(app.buttons["touch.open"].waitForExistence(timeout:5))
        app.terminate();launch(["--preserve"]);open();app.buttons["Behavior"].tap();reveal(app.switches["touch.swipe"])
        XCTAssertEqual(app.switches["touch.swipe"].value as? String,"1")
        toggle("touch.swipe");app.buttons["touch.cancel"].tap();app.buttons["Discard changes"].tap()
        open();app.buttons["Behavior"].tap();reveal(app.switches["touch.swipe"]);XCTAssertEqual(app.switches["touch.swipe"].value as? String,"1")
        app.buttons["touch.cancel"].tap()
        app.terminate();launch(["--preserve","--used"]);XCTAssertFalse(app.buttons["touch.open"].isEnabled)
        print("PASS_TOUCH_EDITOR_DRAFT_UNDO_DUPLICATE_PRESET_SAVE_CANCEL_PERSISTENCE_LOCK")
        app.terminate()
    }
    func testLiveInputPreferences() {
        let app = XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.touch.preview")
        defer {app.terminate();XCUIDevice.shared.orientation = .portrait}
        XCUIDevice.shared.orientation = .portrait
        app.launchArguments = ["--pause-editor"]; app.launch()
        app.buttons["test.pauseEditor"].tap()
        XCTAssertTrue(app.buttons["Behavior"].waitForExistence(timeout:10));app.buttons["Behavior"].tap()
        func reveal(_ item: XCUIElement) {
            for _ in 0..<15 {if item.exists && item.isHittable && item.frame.maxY < app.buttons["touch.reset"].frame.minY-8 {return};app.collectionViews.allElementsBoundByIndex.last!.swipeUp()}
        }
        reveal(app.buttons["touch.toggleBehavior"])
        app.buttons["touch.toggleBehavior"].tap();app.buttons["Until untoggled"].tap()
        reveal(app.buttons["touch.controllerPrompts"])
        app.buttons["touch.controllerPrompts"].tap();app.buttons["PlayStation"].tap()
        reveal(app.switches["touch.featherTouch"])
        XCTAssertEqual(app.switches["touch.featherTouch"].value as? String,"0")
        app.switches["touch.featherTouch"].coordinate(withNormalizedOffset:CGVector(dx:0.92,dy:0.5)).tap()
        let shot = XCTAttachment(screenshot:XCUIScreen.main.screenshot());shot.lifetime = .keepAlways;add(shot)
        app.buttons["touch.save"].tap();XCTAssertTrue(app.buttons["test.pauseEditor"].waitForExistence(timeout:8));app.terminate()
        app.launchArguments = ["--preserve","--pause-editor"];app.launch();app.buttons["test.pauseEditor"].tap();app.buttons["Behavior"].tap()
        reveal(app.buttons["touch.toggleBehavior"]);XCTAssertTrue(app.buttons["touch.toggleBehavior"].label.contains("Until untoggled"))
        reveal(app.buttons["touch.controllerPrompts"]);XCTAssertTrue(app.buttons["touch.controllerPrompts"].label.contains("PlayStation"))
        reveal(app.switches["touch.featherTouch"]);XCTAssertEqual(app.switches["touch.featherTouch"].value as? String,"1")
        app.switches["touch.featherTouch"].coordinate(withNormalizedOffset:CGVector(dx:0.92,dy:0.5)).tap()
        app.buttons["touch.cancel"].tap();app.buttons["Discard changes"].tap()
        XCTAssertTrue(app.buttons["Behavior"].waitForNonExistence(timeout:8));app.buttons["test.pauseEditor"].tap();XCTAssertTrue(app.buttons["Behavior"].waitForExistence(timeout:8));app.buttons["Behavior"].tap();reveal(app.switches["touch.featherTouch"])
        XCTAssertEqual(app.switches["touch.featherTouch"].value as? String,"1")
        print("PASS_LIVE_INPUT_PREFERENCES_SAVE_CANCEL_PERSISTENCE")
    }
    func testLandscapeDragAndPauseEditor() {
        let app = XCUIApplication(bundleIdentifier:"io.github.hmcneill46.cabrillo.touch.preview")
        defer {app.terminate();XCUIDevice.shared.orientation = .portrait}
        XCUIDevice.shared.orientation = .portrait
        app.launchArguments = ["--pause-editor"]; app.launch()
        XCTAssertTrue(app.buttons["test.pauseEditor"].waitForExistence(timeout:10))
        XCUIDevice.shared.orientation = .landscapeLeft
        app.buttons["test.pauseEditor"].tap()
        XCTAssertTrue(app.buttons["touch.save"].waitForExistence(timeout:15))
        let screen = app.windows.firstMatch.frame
        let canvas = app.otherElements["touch.canvas"].firstMatch
        XCTAssertEqual(canvas.frame.width,screen.width,accuracy:2)
        XCTAssertEqual(canvas.frame.height,screen.height,accuracy:2)
        let guide = app.otherElements["touch.gameGuide"].firstMatch.frame
        XCTAssertEqual(guide.width/guide.height,16.0/9,accuracy:0.01)
        let jump = app.descendants(matching:.any)["touch.canvas.jump"].firstMatch
        XCTAssertTrue(jump.exists)
        let before = jump.frame
        let start = jump.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5))
        start.press(forDuration:0.1,thenDragTo:start.withOffset(CGVector(dx:-60,dy:-40)),withVelocity:.slow,thenHoldForDuration:0.1)
        XCTAssertTrue(app.buttons["touch.undo"].isEnabled)
        XCTAssertLessThan(jump.frame.midX,before.midX-15)
        XCTAssertLessThan(jump.frame.midY,before.midY-10)
        let moved = jump.frame
        let corner = app.images["touch.resize.jump"].coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5))
        corner.press(forDuration:0.1,thenDragTo:corner.withOffset(CGVector(dx:24,dy:24)),withVelocity:.slow,thenHoldForDuration:0.1)
        XCTAssertGreaterThan(jump.frame.width,moved.width+12)
        let middle = jump.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5))
        middle.press(forDuration:0.1,thenDragTo:app.coordinate(withNormalizedOffset:CGVector(dx:0,dy:0)).withOffset(CGVector(dx:screen.width-2,dy:screen.height-90)),withVelocity:.slow,thenHoldForDuration:0.1)
        XCTAssertEqual(jump.frame.maxX,screen.maxX,accuracy:2)
        let shot = XCTAttachment(screenshot:XCUIScreen.main.screenshot());shot.lifetime = .keepAlways;add(shot)
        app.buttons["touch.save"].tap()
        XCTAssertTrue(app.buttons["Settings"].firstMatch.waitForExistence(timeout:10))
        app.terminate();XCUIDevice.shared.orientation = .portrait
        print("PASS_TOUCH_EDITOR_LANDSCAPE_DRAG_NATIVE_PRESENTATION")
    }

}
