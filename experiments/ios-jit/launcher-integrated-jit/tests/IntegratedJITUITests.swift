import XCTest
import Darwin
import UIKit

final class LoadingUITests: XCTestCase {
    let app = XCUIApplication(bundleIdentifier: "io.github.hmcneill46.cabrillo.integrated57.preview")
    override func setUp() { continueAfterFailure = false; XCUIDevice.shared.orientation = .portrait }
    override func tearDown() { app.terminate(); XCUIDevice.shared.orientation = .portrait }
    private func reveal(_ item: XCUIElement) {
        for _ in 0..<14 {
            if item.exists && item.frame.height > 0 && app.frame.contains(item.frame) { return }
            let list = app.collectionViews.firstMatch
            if list.exists { list.swipeUp() } else { app.swipeUp() }
        }
        XCTAssertTrue(item.exists); XCTAssertTrue(app.frame.contains(item.frame))
    }
    private func launch(_ state: String, args: [String] = []) {
        app.launchArguments = ["--state=" + state] + args; app.launch()
        XCTAssertTrue(app.navigationBars["Cabrillo"].waitForExistence(timeout: 15))
    }
    private func capture(_ name: String, item: XCUIElement? = nil) {
        let full = XCTAttachment(screenshot: XCUIScreen.main.screenshot()); full.name = name + "-full"; full.lifetime = .keepAlways; add(full)
        if let item = item {
            let crop = XCTAttachment(screenshot: item.screenshot()); crop.name = name + "-button"; crop.lifetime = .keepAlways; add(crop)
            print("BUTTON_FRAME " + name + " " + String(describing: item.frame))
        }
    }
    private func action(_ identifier: String, expected: String) {
        let button = app.buttons[identifier]; reveal(button); XCTAssertTrue(button.isEnabled); button.tap()
        XCTAssertTrue(app.alerts["Fixture action"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.alerts.staticTexts[expected].exists, expected)
        app.alerts.buttons["OK"].tap()
    }
    func testRunStates() {
        let states = UIDevice.current.userInterfaceIdiom == .pad ? ["ready", "busy", "used", "scanning"] : ["empty", "ready", "jitPending", "issues", "busy", "used", "profileBlocked", "shortcutBlocked", "scanning"]
        for state in states {
            launch(state)
            let button = app.buttons["launcher.run"]; reveal(button)
            XCTAssertEqual(button.label, "Run Celeste")
            XCTAssertEqual(button.isEnabled, ["empty", "ready", "jitPending", "issues"].contains(state), state)
            capture(state, item: button)
            if button.isEnabled { action("launcher.run", expected: "run") }
            app.terminate()
        }
        print("PASS_RUN_BUTTON_PRODUCTION_STATES")
    }
    func testRunLargeTypeAndLandscape() {
        launch("ready", args:["--large-type", "--system-light"])
        var button = app.buttons["launcher.run"]; reveal(button); capture("large-type-forced-dark", item: button)
        XCTAssertTrue(app.frame.contains(button.frame)); app.terminate()
        XCUIDevice.shared.orientation = .landscapeLeft
        launch("ready"); button = app.buttons["launcher.run"]; reveal(button); capture("landscape", item: button)
        XCTAssertTrue(app.frame.contains(button.frame))
        print("PASS_RUN_BUTTON_LARGE_TYPE_LANDSCAPE_FORCED_DARK")
    }
    func testRunPressedContrast() {
        launch("ready")
        let button = app.buttons["launcher.run"]; reveal(button); capture("before-press", item: button)
        print("PRESS_SCREENSHOT_BEGIN"); fflush(stdout)
        button.press(forDuration: 5)
        print("PRESS_SCREENSHOT_END"); fflush(stdout)
        XCTAssertTrue(app.alerts["Fixture action"].waitForExistence(timeout:3))
        print("PASS_RUN_BUTTON_ACTUAL_HELD_PRESS")
    }
    func testIntegratedConnectionIsNotJIT() {
        for state in ["integratedMissing", "integratedService", "integratedOldCheck", "integratedProgress", "integratedVerifying", "integratedFailure", "integratedUnavailable"] {
            launch(state)
            let jit = app.staticTexts["integrated.jitStatus"]; reveal(jit)
            XCTAssertTrue(jit.label.contains("Built-in StikJIT")); XCTAssertFalse(jit.label.contains("verified"))
            if state == "integratedOldCheck" {
                XCTAssertEqual(app.staticTexts["integrated.serviceAge"].label, "Checked 2 minutes ago.")
                XCTAssertTrue(app.staticTexts["integrated.serviceStatus"].label.contains("out of date"))
            }
            if state == "integratedProgress" || state == "integratedVerifying" {
                XCTAssertTrue(app.otherElements["integrated.progress"].exists || app.staticTexts["integrated.progress"].exists)
                let run = app.buttons["launcher.run"]; reveal(run); XCTAssertFalse(run.isEnabled)
            }
            if state == "integratedFailure" { XCTAssertTrue(app.staticTexts["integrated.error"].exists) }
            if state == "integratedUnavailable" { XCTAssertTrue(app.staticTexts["integrated.unavailable"].exists) }
            capture(state); app.terminate()
        }
        launch("integratedReady")
        let jit = app.staticTexts["integrated.jitStatus"]; reveal(jit)
        XCTAssertEqual(jit.label, "JIT verified for this running app")
        action("integrated.refresh", expected: "integrated.refresh")
        print("PASS_INTEGRATED_SERVICE_DDI_AND_JIT_DISTINCTION")
    }
    func testIntegratedSettingsActionsAndLocks() {
        launch("integratedMissing"); app.buttons["Settings"].firstMatch.tap()
        let prepare = app.buttons["integrated.prepare"]; reveal(prepare); XCTAssertFalse(prepare.isEnabled)
        let txm = app.staticTexts["integrated.txmStatus"]; reveal(txm)
        XCTAssertTrue(txm.label.contains("Unknown")); capture("integrated-missing-settings")
        app.terminate()
        launch("integratedService"); app.buttons["Settings"].firstMatch.tap()
        XCTAssertTrue(app.navigationBars["Settings"].waitForExistence(timeout:5))
        action("integrated.importPairing", expected:"integrated.importPairing")
        action("integrated.prepare", expected:"integrated.prepare")
        action("integrated.resetDDI", expected:"integrated.resetDDI")
        let toggle = app.switches["integrated.forceScript"]; reveal(toggle); XCTAssertTrue(toggle.isEnabled)
        let switchControl = toggle.switches.firstMatch
        XCTAssertTrue(switchControl.exists); switchControl.tap()
        XCTAssertTrue(app.alerts["Fixture action"].waitForExistence(timeout:3))
        XCTAssertTrue(app.alerts.staticTexts["integrated.forceScript:true"].exists); app.alerts.buttons["OK"].tap()
        capture("integrated-settings")
        app.terminate(); launch("integratedRestart"); app.buttons["Settings"].firstMatch.tap()
        let reset = app.buttons["integrated.resetDDI"]; reveal(reset); XCTAssertFalse(reset.isEnabled)
        let restart = app.staticTexts["integrated.restartRequired"]; reveal(restart); capture("integrated-restart")
        XCTAssertFalse(app.buttons["shortcut.setup"].exists)
        print("PASS_INTEGRATED_SETTINGS_ACTIONS_AND_RESTART_LOCK")
    }
    func testIntegratedLargeTypeProgress() {
        launch("integratedProgress", args:["--large-type"])
        let progress = app.staticTexts["Preparing executable memory for this running app. Keep Cabrillo open."]
        reveal(progress); XCTAssertTrue(app.frame.contains(progress.frame)); capture("integrated-large-progress")
        let run = app.buttons["launcher.run"]; reveal(run); XCTAssertFalse(run.isEnabled)
        XCTAssertEqual(run.label,"Run Celeste"); capture("integrated-large-progress-run", item:run)
        print("PASS_INTEGRATED_LARGE_TYPE_PROGRESS_AND_RUN_LABEL")
    }
    func testLegacyProviderControls() {
        for provider in ["manual", "stikdebug", "livecontainer2", "trollstore"] {
            launch("ready", args:["--provider=" + provider])
            action("launcher.enableJIT", expected:"jit")
            XCTAssertFalse(app.staticTexts["integrated.jitStatus"].exists)
            app.terminate()
        }
        print("PASS_LEGACY_JIT_PROVIDER_CONTROLS_RETAINED")
    }
}
