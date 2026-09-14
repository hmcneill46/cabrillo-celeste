import Foundation

struct CatalogueTestFailure: Error { let name: String }
actor Counter {
    var n = 0
    var fail = false
    func hit() { n += 1 }
    func value() -> Int { n }
    func failing() -> Bool { fail }
    func setFail() { fail = true }
}
@main struct CatalogueTests {
    static var checks: [String] = []
    static func check(_ name: String, _ good: Bool) throws { guard good else { throw CatalogueTestFailure(name: name) }; checks.append(name) }
    static func rejects(_ name: String, _ action: () throws -> Void) throws {
        do { try action() } catch { checks.append(name); return }; throw CatalogueTestFailure(name: name + " did not reject")
    }
    static func main() async throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1]), refs = URL(fileURLWithPath: CommandLine.arguments[2]), fixtures = URL(fileURLWithPath: CommandLine.arguments[3])
        let read: (String) throws -> Data = { try Data(contentsOf: refs.appendingPathComponent($0)) }
        let entries = try CatalogueEntry.parse(read("community-downloads.json")), spring = try CatalogueEntry.parse(read("community-spring.json")).first { $0.pageURL.lastPathComponent == "150813" }!
        try check("20 real entries parsed, stable PageURL despite Obsolete type", entries.count == 20 && entries.first?.id == "https://gamebanana.com/mods/424541")
        try check("separate Spring files remain three independent choices", spring.files.count == 3 && Set(spring.files.map(\.id)) == ["1691049", "484937", "539975"] && spring.files.allSatisfy(\.selectable))
        try check("previous version visible but never default download", entries[0].files.contains { !$0.latest && !$0.selectable })
        let categories = try CatalogueCategory.parse(read("community-categories.json"), subcategories: read("community-subcategories.yaml"))
        try check("native category hierarchy includes map subcategories and tools", categories.first { $0.name == "Maps" }?.children.count == 4 && categories.contains { $0.id == "GameBanana_Tool_Root" })
        let detail = try GameBananaDetails(read("spring-profile.json"), entry: spring)
        try check("official profile joins exact game and page with individual files", detail.availableFiles.contains("484937") && detail.images.count == 2 && detail.downloads! > 0)
        let q = try CatalogueQuery(search: " Maddy & spring? ").url(page: 1)
        try check("search query correctly encoded and not falsely filtered", URLComponents(url: q, resolvingAgainstBaseURL: false)?.queryItems == [URLQueryItem(name: "q", value: "Maddy & spring?")])
        let filtered = try CatalogueQuery(sort: .likes, category: "GameBanana_Mod_6800", subcategory: "GameBanana_Mod_6803").url(page: 2)
        try check("server sorting, paging and nested category use exact IDs", filtered.absoluteString.contains("page=2&sort=likes&category=GameBanana_Mod_6800&subcategory=GameBanana_Mod_6803"))
        try check("five clearly defined sort modes", CatalogueSort.allCases.count == 5)
        try rejects("bad category rejected") { _ = try CatalogueQuery(category: "../../private").url(page: 1) }
        try rejects("unbounded paging rejected") { _ = try CatalogueQuery().url(page: 501) }
        for value in ["http://gamebanana.com/mods/42", "https://gamebanana.com.evil.test/mods/42", "https://gamebanana.com/mods/42?key=x", "file:///mods/42", "https://user:pass@gamebanana.com/mods/42"] { try check("unsafe page rejected " + value, CatalogueSafety.page(value) == nil) }
        try check("external media and executable media rejected", CatalogueSafety.media("https://attacker.example/a.png") == nil && CatalogueSafety.media("https://images.gamebanana.com/file.exe") == nil)
        try check("description script removed and encoded text remains inert", CatalogueSafety.text("<p>Hello<br>world</p><script>alert('secret')</script>&lt;b&gt;&#x1f353;&amp;", limit: 1000) == "Hello\nworld\n<b>🍓&")
        try check("description bounded", CatalogueSafety.text(String(repeating: "x", count: 1000), limit: 20).count == 20)
        try rejects("malformed response rejected") { _ = try CatalogueEntry.parse(Data("{\"error\":true}".utf8)) }
        try rejects("oversized response rejected") { _ = try CatalogueEntry.parse(Data(repeating: 32, count: 4_194_305)) }
        var wrong = try JSONSerialization.jsonObject(with: read("spring-profile.json")) as! [String: Any]; wrong["_aGame"] = ["_idRow": 1]
        try rejects("unrelated game profile rejected") { _ = try GameBananaDetails(JSONSerialization.data(withJSONObject: wrong), entry: spring) }

        var candidates = try JSONDecoder().decode([String: DownloadCandidate].self, from: Data(contentsOf: fixtures.appendingPathComponent("candidates.json")))
        // Real ZIP fixtures retain byte hashes; only their transport IDs change.
        func source(_ name: String, _ id: Int) -> DownloadCandidate { let old = candidates[name]!; return DownloadCandidate(url: "https://gamebanana.com/mmdl/\(id)", bytes: old.bytes, hashes: old.hashes, pinnedSHA256: nil, modules: old.modules) }
        candidates["root"] = source("root", 900001); candidates["helper-new"] = source("helper-new", 900002); candidates["leaf-new"] = source("leaf-new", 900003)
        var db = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), allowEmpty: true)
        for name in ["root", "helper-new", "leaf-new"] { for m in candidates[name]!.modules { db.byName[m.name] = candidates[name]!; db.indexedByName[m.name] = candidates[name]! } }
        let selection = CatalogueSelection(pageURL: spring.id, fileIDs: ["900001"])
        let roots = try selection.candidates(in: db), empty = LibraryInventory(archives: [], disabled: [])
        var plan = try DependencyPlanner.resolve(empty, database: db, pins: [:], installs: roots)
        try check("selected catalogue root plus complete recursive dependencies", plan.issues.isEmpty && plan.downloads.count == 3)
        try rejects("unindexed file never replaced by guessed title match") { _ = try CatalogueSelection(pageURL: spring.id, fileIDs: ["909090"]).candidates(in: db) }
        try rejects("noncanonical file ID rejected") { _ = try CatalogueSelection(pageURL: spring.id, fileIDs: ["0900001"]).candidates(in: db) }
        try check("valid indexed helper can be on a Tools page", CatalogueSelection(pageURL: "https://gamebanana.com/tools/42", fileIDs: ["900001"]).candidates(in: db).count == 1)
        try rejects("unindexed desktop tool cannot be downloaded by the mod installer") { _ = try CatalogueSelection(pageURL: "https://gamebanana.com/tools/42", fileIDs: ["999999"]).candidates(in: db) }
        plan = try DependencyPlanner.resolve(empty, database: db, pins: [:], installs: [roots[0], roots[0]])
        try check("overlapping selected files block before changes", !plan.issues.isEmpty && plan.json["canApply"] as? Bool == false)
        let future = DownloadCandidate(url: roots[0].url, bytes: 100, hashes: [], pinnedSHA256: nil, modules: [ModMetadata(name: "Future", version: try ModVersion("1.0"), dll: nil, dependencies: [ModDependency(name: "Everest", version: try ModVersion("1.99999.0"))], optionalDependencies: [])])
        plan = try DependencyPlanner.resolve(empty, database: db, pins: [:], installs: [future])
        try check("browser cannot bypass actual runtime minimum", !plan.issues.isEmpty && plan.json["canApply"] as? Bool == false)
        plan = try DependencyPlanner.resolve(empty, database: db, pins: ["Root": String(repeating: "a", count: 64)], installs: roots)
        try check("browser cannot bypass app-managed release pins", !plan.issues.isEmpty)
        let original = try DownloadIdentity.read(fixtures.appendingPathComponent("root.zip"))
        let archive = try ModLibrary.inspect(fixtures.appendingPathComponent("root.zip"), filename: "original.zip", digest: original.sha256, bytes: original.bytes)
        plan = try DependencyPlanner.resolve(LibraryInventory(archives: [archive], disabled: [archive.filename]), database: db, pins: [:], installs: roots, identities: [archive.filename: original])
        try check("exact disabled root is enabled without downloading twice", plan.enable == ["original.zip"] && plan.downloads.count == 2 && !plan.downloads.contains { $0.key == roots[0].key })

        let counter = Counter(), url = try CatalogueQuery().url(page: 1), payload = try read("community-downloads.json")
        let provider = CatalogueProvider(root: root.appendingPathComponent("cache")) { _, _, _ in
            await counter.hit(); try await Task.sleep(for: .milliseconds(100))
            if await counter.failing() { throw URLError(.notConnectedToInternet) }; return CatalogueResponse(data: payload, date: Date(), total: 6162)
        }
        async let a = provider.page(CatalogueQuery(), page: 1)
        async let b = provider.page(CatalogueQuery(), page: 1)
        _ = try await (a, b); try check("simultaneous requests coalesce to one transfer", await counter.value() == 1)
        _ = try await provider.page(CatalogueQuery(), page: 1)
        try check("fresh revisit uses disk cache without network", await counter.value() == 1)
        await counter.setFail()
        let stale = try await provider.fetch(url, refresh: true)
        try check("offline refresh retains explicit dated stale copy", stale.stale && stale.cached && stale.data == payload)
        _ = try await provider.fetch(url, refresh: true)
        try check("failed endpoint has one-minute request backoff", await counter.value() == 2)
        let cancelCounter = Counter()
        let cancelProvider = CatalogueProvider(root: root.appendingPathComponent("cancel-cache")) { _, _, _ in
            await cancelCounter.hit(); try await Task.sleep(for: .seconds(20)); return CatalogueResponse(data: payload, date: Date(), total: nil)
        }
        let task = Task { try await cancelProvider.fetch(url) }
        try await Task.sleep(for: .milliseconds(80)); task.cancel()
        do { _ = try await task.value; throw CatalogueTestFailure(name: "cancellation ignored") } catch is CancellationError { checks.append("cancelled search cancels underlying transfer") }
        try check("cancelled request leaves no active flight", await cancelProvider.diagnostics()["activeRequests"] as? Int == 0)
        let pending = Task { try await cancelProvider.fetch(url) }
        try await Task.sleep(for: .milliseconds(80))
        await cancelProvider.suspendForGame()
        do { _ = try await pending.value; throw CatalogueTestFailure(name: "game startup retained browsing transfer") } catch is CancellationError { checks.append("game startup awaits cancelled browsing transfers") }
        do { _ = try await cancelProvider.fetch(url); throw CatalogueTestFailure(name: "suspended browser started a request") } catch is CancellationError { checks.append("game session rejects new browsing transfers") }
        try check("game startup records zero active requests", await cancelProvider.diagnostics()["activeRequests"] as? Int == 0)
        let invalid = CatalogueProvider(root: root.appendingPathComponent("invalid-cache")) { _, _, _ in CatalogueResponse(data: Data("{\"error\":true}".utf8), date: Date(), total: nil) }
        do { _ = try await invalid.page(CatalogueQuery(), page: 1); throw CatalogueTestFailure(name: "invalid page cached") } catch is LibraryError { checks.append("invalid response rejected before cache write") }
        try check("invalid response not persisted", !FileManager.default.fileExists(atPath: root.appendingPathComponent("invalid-cache/pages").path))
        let offline = CatalogueProvider(root: root.appendingPathComponent("offline-cache")) { _, _, _ in throw URLError(.notConnectedToInternet) }
        do { _ = try await offline.fetch(url); throw CatalogueTestFailure(name: "offline request succeeded") }
        catch let error as LibraryError { try check("offline guidance is readable without implementation codes", error.localizedDescription.contains("You're offline.") && !error.localizedDescription.contains("NSURLError")) }
        let failure = await offline.diagnostics()["lastFailure"] as? [String: Any]
        try check("technical network failure retained in diagnostics", failure?["code"] as? Int == URLError.notConnectedToInternet.rawValue)

        try await transaction(root: root, fixtures: fixtures, candidates: candidates, database: db, selection: selection)
        if CommandLine.arguments.contains("--live") { try await live(root: root) }
        let output: [String: Any] = ["status": "PASS_NATIVE_CATALOGUE_CONTRACT_CACHE_INSTALLS", "checks": checks, "serviceEntries": entries.count, "categories": categories.count, "provider": await provider.diagnostics()]
        try JSONSerialization.data(withJSONObject: output, options: [.prettyPrinted, .sortedKeys]).write(to: root.appendingPathComponent("results.json"))
        print("PASS_NATIVE_CATALOGUE_CONTRACT_CACHE_INSTALLS", checks.count)
    }
    static func state(_ installer: DependencyInstaller, action: () -> Void) async -> [String: Any] {
        await withCheckedContinuation { continuation in
            var completed = false
            installer.update = { value in if !completed && value["active"] as? Bool == false { completed = true; continuation.resume(returning: value) } }
            action()
        }
    }
    static func live(root: URL) async throws {
        let provider = CatalogueProvider(root: root.appendingPathComponent("live-cache"))
        var serviceRows: [[String: Any]] = []
        for sort in CatalogueSort.allCases {
            let query = CatalogueQuery(sort: sort, category: "GameBanana_Mod_6800")
            let page = try await provider.page(query, page: 1, refresh: true)
            try check("live server sort " + sort.rawValue, page.entries.count == 20 && page.entries.allSatisfy { $0.category == "Maps" })
            serviceRows.append(["url": try query.url(page: 1).absoluteString, "sha256": digestData(page.response.data), "bytes": page.response.data.count, "fetched": page.response.date.timeIntervalSince1970, "cached": page.response.cached])
        }
        let search = try await provider.page(CatalogueQuery(search: "Memorial Helper"), page: 1, refresh: true)
        guard let entry = search.entries.first(where: { $0.id == "https://gamebanana.com/tools/6850" }), let file = entry.files.first(where: \.selectable) else { throw CatalogueTestFailure(name: "live Memorial Helper discovery") }
        try check("live Tools-category helper remains installable", entry.installable && file.id == "870370")
        let library = ModLibrary(profile: root.appendingPathComponent("live-profile"))
        let installer = DependencyInstaller(library: library, pins: [])
        var result = await state(installer) { installer.planCatalogue(CatalogueSelection(pageURL: entry.id, fileIDs: [file.id])) }
        guard let plan = result["plan"] as? [String: Any], plan["canApply"] as? Bool == true else { throw LibraryError("Live catalogue plan failed: \(result)") }
        let index = (result["index"] as? [String: String]) ?? [:]
        try check("live root maps to exact module name and small verified archive", (plan["downloads"] as? [[String: Any]])?.first?["name"] as? String == "memorialHelper 1.0.4" && (plan["totalBytes"] as? UInt64) == 13965)
        result = await state(installer) { installer.apply(planID: plan["id"] as! String) }
        if result["phase"] as? String == "review" { let id = (result["plan"] as! [String: Any])["id"] as! String; result = await state(installer) { installer.apply(planID: id) } }
        let inventory = try LibraryInventory.read(library)
        try check("real catalogue HTTP ZIP verified committed enabled", result["phase"] as? String == "complete" && inventory.active.first?.modules.first?.name == "memorialHelper")
        let report = try InstallReport.read(library.profile)
        try check("real online browser installation reports actual result", report.applicationState == "applied" && report.changes.count == 1 && report.changes[0].afterVersion == "1.0.4" && report.changes[0].enabled)
        let skinSearch = try await provider.page(CatalogueQuery(search: "Cateline"), page: 1, refresh: true)
        guard let skin = skinSearch.entries.first(where: { $0.id == "https://gamebanana.com/mods/251793" }), let skinFile = skin.files.first(where: \.selectable) else { throw CatalogueTestFailure(name: "live skin discovery") }
        result = await state(installer) { installer.planCatalogue(CatalogueSelection(pageURL: skin.id, fileIDs: [skinFile.id])) }
        guard let skinPlan = result["plan"] as? [String: Any], skinPlan["canApply"] as? Bool == true else { throw CatalogueTestFailure(name: "live skin review") }
        result = await state(installer) { installer.apply(planID: skinPlan["id"] as! String) }
        if result["phase"] as? String == "review" { let id = (result["plan"] as! [String: Any])["id"] as! String; result = await state(installer) { installer.apply(planID: id) } }
        let final = try LibraryInventory.read(library), skinReport = try InstallReport.read(library.profile)
        try check("live Cateline downloaded and enabled alongside prior helper", result["phase"] as? String == "complete" && final.active.count == 2 && final.active.contains { $0.modules.first?.name == "Cateline" && $0.modules.first?.version.text == "0.1.0" })
        try JSONSerialization.data(withJSONObject: ["status": "PASS_LIVE_CATALOGUE_TO_VERIFIED_INSTALL", "listResponses": serviceRows, "pageURL": entry.id, "fileID": file.id, "skinPageURL": skin.id, "skinFileID": skinFile.id, "index": index, "inventory": try JSONSerialization.jsonObject(with: canonicalData(final)), "helperReport": report.json, "skinReport": skinReport.json], options: [.prettyPrinted,.sortedKeys]).write(to: root.appendingPathComponent("live-results.json"))
    }
    static func transaction(root: URL, fixtures: URL, candidates: [String: DownloadCandidate], database: DependencyDatabase, selection: CatalogueSelection) async throws {
        let library = ModLibrary(profile: root.appendingPathComponent("profile"), specialPins: [:])
        try InstallJournal.directory(library.profile)
        let save = library.profile.appendingPathComponent("UnknownMod.save.dat"); try Data("keep all mod save data".utf8).write(to: save)
        let installer = DependencyInstaller(library: library, pins: [], indexProvider: { _ in database }, downloadProvider: { url, target, _, _, token, progress in
            try token.check(); let name = candidates.first { $0.value.url == url }!.key
            let bytes = try Data(contentsOf: fixtures.appendingPathComponent(name + ".zip")); try bytes.write(to: target); progress(Int64(bytes.count), Int64(bytes.count))
        })
        var result = await state(installer) { installer.planCatalogue(selection) }
        let plan = result["plan"] as! [String: Any]
        try check("real coordinator returns review without installing", result["phase"] as? String == "review" && (plan["downloads"] as? [[String: Any]])?.count == 3 && (try LibraryInventory.read(library)).archives.isEmpty)
        result = await state(installer) { installer.apply(planID: plan["id"] as! String) }
        // Actual ZIP metadata can legitimately revise the initial online plan.
        if result["phase"] as? String == "review" { let id = (result["plan"] as! [String: Any])["id"] as! String; result = await state(installer) { installer.apply(planID: id) } }
        try check("reviewed browser install commits all three real ZIPs", result["phase"] as? String == "complete" && (try LibraryInventory.read(library)).archives.count == 3)
        let report = try InstallReport.read(library.profile)
        try check("browser uses complete persisted installed/enabled report", report.outcome == "completed" && report.changes.filter { $0.action == "installed" && $0.enabled }.count == 3)
        try check("unknown save sidecar preserved", Data(contentsOf: save) == Data("keep all mod save data".utf8))
        result = await state(installer) { installer.planCatalogue(selection) }
        let repeatPlan = result["plan"] as! [String: Any]
        try check("repeat browser install is a no-op after exact hash reuse", repeatPlan["canApply"] as? Bool == false && (repeatPlan["downloads"] as? [[String: Any]])?.isEmpty == true)
    }
}
