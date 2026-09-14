import XCTest

@MainActor final class CatalogueUITests: XCTestCase {
    private var app: XCUIApplication!
    override func setUpWithError() throws {
        continueAfterFailure = false; XCUIDevice.shared.orientation = .portrait
        app = XCUIApplication(bundleIdentifier: "io.github.hmcneill46.celeste.everest.jit.everest")
    }
    override func tearDownWithError() throws { app.terminate(); XCUIDevice.shared.orientation = .portrait }
    private func start(_ extra: [String] = ["--catalogue-ui-fixture"]) {
        app.launchArguments = ["--launcher-ui-test"] + extra; app.launch()
        XCTAssertTrue(app.buttons["launcher.importGame"].waitForExistence(timeout: 20))
        app.tabBars.buttons["Mods"].tap()
        XCTAssertTrue(app.segmentedControls["mods.pages"].waitForExistence(timeout: 10))
        app.segmentedControls["mods.pages"].buttons["Browse"].tap()
    }
    private func capture(_ name: String) { let a = XCTAttachment(screenshot: XCUIScreen.main.screenshot()); a.name = name; a.lifetime = .keepAlways; add(a) }
    private func reveal(_ element: XCUIElement) {
        for _ in 0..<18 { if element.isHittable { return }; app.swipeUp() }
        XCTAssertTrue(element.isHittable, app.debugDescription)
    }
    private func query(_ text: String) {
        let field = app.searchFields.firstMatch
        for _ in 0..<8 { if field.isHittable { break }; app.swipeDown() }
        XCTAssertTrue(field.waitForExistence(timeout: 5)); field.tap()
        if field.buttons["Clear text"].exists { field.buttons["Clear text"].tap() }
        field.typeText(text)
        if app.keyboards.buttons["Search"].exists { app.keyboards.buttons["Search"].tap() }
    }
    func testAFileChoiceReviewInstallAndReport() {
        start()
        let card = app.buttons["browse.mod.900001"]
        XCTAssertTrue(card.waitForExistence(timeout: 15), app.debugDescription); capture("catalogue-fixture-grid")
        card.tap()
        let review = app.buttons["browse.review"]
        XCTAssertTrue(review.waitForExistence(timeout: 5)); XCTAssertEqual(review.label, "Choose files"); review.tap()
        let file = app.buttons["browse.file.900001"]; reveal(file); capture("native-file-choice")
        file.tap(); XCTAssertTrue(review.isEnabled); review.tap()
        let apply = app.buttons["install.apply"]
        XCTAssertTrue(apply.waitForExistence(timeout: 20), app.debugDescription)
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", "Review your selected files")).firstMatch.exists)
        reveal(apply); capture("catalogue-dependency-review"); apply.tap()
        XCTAssertTrue(app.staticTexts["Changes applied"].waitForExistence(timeout: 35), app.debugDescription)
        capture("catalogue-install-result")
        app.buttons["install.close"].tap()
        XCTAssertTrue(review.waitForExistence(timeout: 10)); review.tap()
        XCTAssertTrue(app.staticTexts["All required dependencies are ready"].waitForExistence(timeout: 20), app.debugDescription)
        XCTAssertFalse(app.buttons["install.apply"].exists)
        capture("exact-install-reused"); app.buttons["install.close"].tap()
        print("PASS_CATALOGUE_NATIVE_FILE_CHOICE_REVIEW_COMMIT_REPORT_REUSE")
    }
    func testBFiltersSortingPaginationAndSearch() {
        start(); XCTAssertTrue(app.buttons["browse.mod.900001"].waitForExistence(timeout: 15))
        app.buttons["browse.categories"].tap()
        XCTAssertTrue(app.navigationBars["Categories"].waitForExistence(timeout: 5))
        app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "Maps")).firstMatch.tap()
        XCTAssertTrue(app.navigationBars["Maps"].waitForExistence(timeout: 5))
        app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "Standalone")).firstMatch.tap()
        XCTAssertTrue(app.buttons["browse.sort"].waitForExistence(timeout: 10))
        app.buttons["browse.sort"].tap()
        XCTAssertTrue(app.buttons["Most liked"].waitForExistence(timeout: 5))
        Thread.sleep(forTimeInterval: 1.2) // Cross multiple native status-poll ticks with the menu open.
        app.buttons["Most liked"].tap()
        XCTAssertEqual(XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: NSPredicate(format: "label CONTAINS %@", "Most liked"), object: app.buttons["browse.sort"])], timeout: 8), .completed)
        XCTAssertTrue(app.buttons["browse.mod.900001"].waitForExistence(timeout: 10)); capture("category-sort-selection")
        let more = app.buttons["browse.more"]; reveal(more); more.tap()
        XCTAssertTrue(app.staticTexts["You're all caught up here."].waitForExistence(timeout: 10)); capture("paged-results")
        let visibleCard = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "browse.mod.")).allElementsBoundByIndex.last(where: { $0.isHittable })
        XCTAssertNotNil(visibleCard, app.debugDescription)
        let visibleID = visibleCard?.identifier ?? "missing"
        visibleCard?.tap()
        XCTAssertTrue(app.navigationBars["Mod details"].waitForExistence(timeout: 5))
        app.navigationBars.buttons.firstMatch.tap()
        XCTAssertTrue(app.staticTexts["You're all caught up here."].waitForExistence(timeout: 8), "Returning from details must preserve loaded pages")
        XCTAssertFalse(app.buttons["browse.more"].exists)
        XCTAssertTrue(app.buttons[visibleID].isHittable, "Returning from details must preserve the visible row")
        capture("back-preserves-loaded-pages")
        query("slow"); Thread.sleep(forTimeInterval: 0.5); query("alpine")
        XCTAssertTrue(app.buttons["browse.mod.900001"].waitForExistence(timeout: 5), "Cancelled query must not hold up its replacement")
        XCTAssertTrue(app.staticTexts["Up to 20 best matches · all categories"].exists)
        capture("native-search-results")
        query("zzzznomatch"); XCTAssertTrue(app.staticTexts["No matching mods"].waitForExistence(timeout: 8)); capture("search-empty-state")
        print("PASS_CATALOGUE_FILTERS_SORT_PAGINATION_SEARCH_CANCELLATION_EMPTY")
    }
    func testCOfflineCacheAndInstalledLauncher() {
        start(); XCTAssertTrue(app.buttons["browse.mod.900001"].waitForExistence(timeout: 15)); app.terminate()
        start(["--catalogue-ui-fixture", "--catalogue-ui-offline"])
        XCTAssertTrue(app.buttons["browse.mod.900001"].waitForExistence(timeout: 10))
        app.buttons["browse.refresh"].tap()
        XCTAssertTrue(app.otherElements["browse.offline"].waitForExistence(timeout: 8) || app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", "Offline copy")).firstMatch.exists, app.debugDescription)
        capture("offline-cached-catalogue")
        query("notcachedoffline"); XCTAssertTrue(app.staticTexts["Couldn't load mods"].waitForExistence(timeout: 10)); capture("offline-unvisited-search")
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", "You're offline.")).firstMatch.exists)
        XCTAssertFalse(app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", "NSURLErrorDomain")).firstMatch.exists)
        app.tabBars.buttons["Play"].tap()
        XCTAssertTrue(app.buttons["launcher.importGame"].waitForExistence(timeout: 5))
        let run = app.buttons["launcher.run"]; reveal(run)
        XCTAssertTrue(run.isEnabled, "Catalogue outage must not lock the existing launcher")
        print("PASS_CATALOGUE_OFFLINE_CACHE_FAILURE_DOES_NOT_LOCK_PLAY")
    }
    func testDLiveNativeAppearancePortraitLandscapeAndDetails() {
        start([])
        let card = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "browse.mod.")).firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 35), app.debugDescription)
        Thread.sleep(forTimeInterval: 3); capture("live-browser-portrait")
        XCUIDevice.shared.orientation = .landscapeRight; Thread.sleep(forTimeInterval: 3)
        XCTAssertGreaterThan(app.frame.width, app.frame.height); capture("live-browser-landscape")
        XCUIDevice.shared.orientation = .portrait; Thread.sleep(forTimeInterval: 3); card.tap()
        XCTAssertTrue(app.navigationBars["Mod details"].waitForExistence(timeout: 10)); Thread.sleep(forTimeInterval: 3); capture("live-mod-details")
        let choices = app.staticTexts["browse.filesHeading"]
        if choices.exists { reveal(choices) } else { app.swipeUp(); app.swipeUp() }
        capture("live-mod-file-choices")
        print("PASS_LIVE_NATIVE_CATALOGUE_PORTRAIT_LANDSCAPE_DETAILS")
    }
}
