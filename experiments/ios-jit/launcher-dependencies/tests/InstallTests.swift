import Foundation
import Darwin

struct TestFailure: Error, CustomStringConvertible { let description: String }
var checks: [String] = []
func check(_ name: String, _ condition: @autoclosure () throws -> Bool) throws {
    guard try condition() else { throw TestFailure(description: name) }; checks.append(name)
}
func rejects(_ name: String, _ body: () throws -> Void) throws {
    do { try body() } catch { checks.append(name); return }; throw TestFailure(description: name + " accepted invalid input")
}
func module(_ name: String, _ version: String = "1.0", _ deps: [(String, String)] = [], _ optional: [(String, String)] = []) throws -> ModMetadata {
    try ModMetadata(name: name, version: ModVersion(version), dll: nil, dependencies: deps.map { try ModDependency(name: $0.0, version: ModVersion($0.1)) }, optionalDependencies: optional.map { try ModDependency(name: $0.0, version: ModVersion($0.1)) })
}
func local(_ name: String, _ modules: [ModMetadata], sha: String = String(repeating: "a", count: 64)) -> ModArchive {
    ModArchive(filename: name + ".zip", digest: sha, bytes: 100, modules: modules, problem: nil)
}
func remote(_ modules: [ModMetadata], pinned: String? = nil) -> DownloadCandidate {
    DownloadCandidate(url: "https://mods.example.org/" + modules.map(\.name).joined(separator: "-") + ".zip", bytes: 100, hashes: ["0123456789abcdef"], pinnedSHA256: pinned, modules: modules)
}
func database(_ candidates: [DownloadCandidate]) throws -> DependencyDatabase {
    var db = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), allowEmpty: true)
    for row in candidates { for m in row.modules { db.byName[m.name] = row; db.indexedByName[m.name] = row } }; return db
}
func inventory(_ archives: [ModArchive], disabled: [String] = []) -> LibraryInventory { LibraryInventory(archives: archives.sorted { $0.filename < $1.filename }, disabled: disabled.sorted()) }
func plannerTests() throws {
    let root = try local("root", [module("Root", "1.0", [("Helper", "1.2")])]), old = try local("old", [module("Helper", "1.0")]), good = try local("good", [module("Helper", "1.3")])
    let helper = try remote([module("Helper", "1.4", [("Leaf", "1.0")])]), leaf = try remote([module("Leaf")]), db = try database([helper, leaf])
    var p = try DependencyPlanner.resolve(inventory([root, good]), database: db, pins: [:])
    try check("keep compatible installed release", p.issues.isEmpty && p.downloads.isEmpty && p.enable.isEmpty && p.disable.isEmpty)
    p = try DependencyPlanner.resolve(inventory([root, good], disabled: [good.filename]), database: db, pins: [:])
    try check("enable compatible disabled ZIP without network", p.issues.isEmpty && p.downloads.isEmpty && p.enable == [good.filename])
    p = try DependencyPlanner.resolve(inventory([root, old]), database: db, pins: [:])
    try check("replace incompatible and resolve recursive graph", p.issues.isEmpty && p.downloads.count == 2 && p.disable == [old.filename])
    try check("plan identity stable across unordered inventory", p.signature == DependencyPlanner.resolve(inventory([old, root]), database: db, pins: [:]).signature)
    p = try DependencyPlanner.resolve(inventory([root, good, old]), database: db, pins: [:])
    try check("duplicate active providers block", !p.issues.isEmpty)
    let other = try local("other", [module("Helper", "1.5")])
    p = try DependencyPlanner.resolve(inventory([root, good, other], disabled: [good.filename, other.filename]), database: db, pins: [:])
    try check("ambiguous installed providers block", p.issues.contains { $0.contains("Several installed") })
    let major = try local("major", [module("Other", "1.0", [("Helper", "2.0")])])
    p = try DependencyPlanner.resolve(inventory([root, major]), database: db, pins: [:])
    try check("incompatible major requirements block", !p.issues.isEmpty)
    let optional = try local("optional", [module("Optional", "1.0", [], [("Helper", "2.0")])])
    p = try DependencyPlanner.resolve(inventory([optional]), database: db, pins: [:])
    try check("absent optional dependency not downloaded", p.issues.isEmpty && p.downloads.isEmpty)
    p = try DependencyPlanner.resolve(inventory([optional, good]), database: db, pins: [:])
    try check("present optional incompatible version blocks", !p.issues.isEmpty)
    let cycle = try database([remote([module("Helper", "1.2", [("Leaf", "1.0")])]), remote([module("Leaf", "1.0", [("Helper", "1.0")])])])
    p = try DependencyPlanner.resolve(inventory([root]), database: cycle, pins: [:])
    try check("required cycle blocked", p.issues.contains { $0.contains("cycle") })
    let bundled = try local("override", [module("Everest", "99.0")])
    p = try DependencyPlanner.resolve(inventory([bundled]), database: db, pins: [:])
    try check("builtin provider protected", !p.issues.isEmpty)
    let future = try local("future", [module("Future", "1.0", [("Everest", "1.99999")])])
    p = try DependencyPlanner.resolve(inventory([future]), database: db, pins: [:])
    try check("desktop runtime dependency cannot replace app", p.issues.contains { $0.contains("app runtime") })
    let multi = try local("multi", [module("Helper", "1.0"), module("Second", "1.0")])
    p = try DependencyPlanner.resolve(inventory([root, multi]), database: db, pins: [:])
    try check("cannot split multi-module replacement", p.issues.contains { $0.contains("split") })
    let pin = String(repeating: "b", count: 64)
    p = try DependencyPlanner.resolve(inventory([root]), database: db, pins: ["Helper": pin])
    try check("unapproved compatibility download blocked", !p.issues.isEmpty)
    let pinDB = try database([remote([module("Helper", "1.4")], pinned: pin)])
    p = try DependencyPlanner.resolve(inventory([root]), database: pinDB, pins: ["Helper": pin])
    try check("approved pinned download allowed", p.issues.isEmpty && p.downloads.first?.pinnedSHA256 == pin)
    p = try DependencyPlanner.resolve(inventory([root, good]), database: db, pins: [:], updates: [good.filename: helper])
    try check("individual explicit update downloads newer plus dependency", p.issues.isEmpty && p.downloads.count == 2 && p.disable == [good.filename])
    p = try DependencyPlanner.resolve(inventory([good], disabled: [good.filename]), database: db, pins: [:], updates: [good.filename: helper])
    try check("disabled update stays disabled without activating its dependencies", p.issues.isEmpty && p.selected.isEmpty && p.downloads.count == 1 && p.disabledDownloads.count == 1)
    let incompatible = try remote([module("Helper", "2.0")])
    p = try DependencyPlanner.resolve(inventory([root, good]), database: try database([incompatible]), pins: [:], updates: [good.filename: incompatible])
    try check("explicit incompatible update cannot silently revert", !p.issues.isEmpty && p.downloads.contains { $0.key == incompatible.key })
    let rootUpdate = try remote([module("Root", "1.1", [("Helper", "2.0")])])
    p = try DependencyPlanner.resolve(inventory([root, good]), database: try database([rootUpdate, incompatible]), pins: [:], updates: [good.filename: incompatible, root.filename: rootUpdate])
    try check("batch resolves together rather than one at a time", p.issues.isEmpty && p.downloads.count == 2 && p.disable.count == 2)
    p = try DependencyPlanner.resolve(inventory([good]), database: db, pins: ["Helper": good.digest], updates: [good.filename: helper])
    try check("explicit update cannot override app pin", !p.issues.isEmpty)
    let duplicateDownload = try remote([module("Helper", "1.4"), module("Root", "1.0")])
    p = try DependencyPlanner.resolve(inventory([root, good]), database: try database([duplicateDownload]), pins: [:], updates: [good.filename: duplicateDownload])
    try check("update introducing duplicate identity blocks", !p.issues.isEmpty)
    try check("0.0 provider numeric wildcard", ModVersion("0.0.0-dummy").satisfies(ModVersion("9.2")))
    try check("missing build component follows System.Version", !ModVersion("1.2").satisfies(ModVersion("1.2.0")))
    try check("version prerelease suffix follows existing policy", ModVersion("1.3.0-beta").satisfies(ModVersion("1.2")))
    for url in ["http://mods.example.org/a", "https://user:pass@mods.example.org/a", "https://localhost/a", "https://127.0.0.1/a", "file:///a", "https://x.local/a", "https://mods.example.org:80/a"] { try check("reject URL " + url, validDownloadURL(url) == nil) }
    try check("accept HTTPS mirror", validDownloadURL("https://gamebanana.com/mmdl/870370") != nil)
    let now = Date(timeIntervalSince1970: 1_000_000), cache = ModUpdates.CheckCache(schema: 1, checked: now, revision: "same", updates: [], index: [:])
    try check("automatic cache fresh within 24 hours", cache.fresh(for: "same", at: now.addingTimeInterval(86399)))
    try check("automatic cache expires at 24 hours", !cache.fresh(for: "same", at: now.addingTimeInterval(86400)))
    try check("library change invalidates update cache", !cache.fresh(for: "different", at: now))
    try check("clock reversal does not hide stale check", !cache.fresh(for: "same", at: now.addingTimeInterval(-1)))
    try rejects("duplicate index names rejected") { _ = try DependencyDatabase(updates: Data("A: {}\nA: {}".utf8), graph: Data("{}".utf8)) }
    try rejects("recursive index alias rejected") { _ = try DependencyDatabase(updates: Data("A: &a [*a]".utf8), graph: Data("{}".utf8)) }
    try rejects("32 MiB online cap independent") { _ = try DependencyDatabase(updates: Data(repeating: 32, count: 33_554_433), graph: Data("{}".utf8)) }
}

@main struct InstallTests {
    static var base: URL { URL(fileURLWithPath: CommandLine.arguments[2]) }
    static var fixtures: URL { base.appendingPathComponent("fixtures") }
    static func loadCandidates() throws -> [String: DownloadCandidate] { try JSONDecoder().decode([String: DownloadCandidate].self, from: Data(contentsOf: fixtures.appendingPathComponent("candidates.json"))) }
    static func writeResult(_ object: [String: Any], _ name: String) throws { try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys,.prettyPrinted]).write(to: base.appendingPathComponent(name)); print(String(describing: object["status"] ?? "DONE")) }
    static func main() throws {
        switch CommandLine.arguments[1] {
        case "pure":
            try plannerTests()
            let vectors = try JSONSerialization.jsonObject(with: Data(contentsOf: fixtures.appendingPathComponent("hash-vectors.json"))) as! [[String: Any]]
            for vector in vectors {
                let length = vector["length"] as! Int, expected = vector["xxHash"] as! String
                let data = Data((0..<length).map { UInt8(truncatingIfNeeded: $0 &* 131 &+ ($0 >> 3)) })
                for chunk in [1, 7, 31, 32, 33, 65536] {
                    var hash = XXHash64(), offset = 0
                    while offset < data.count { let end = min(data.count, offset + chunk); hash.update(data.subdata(in: offset..<end)); offset = end }
                    try check("xxHash oracle length=\(length) chunk=\(chunk)", hash.finish() == expected)
                }
            }
            let service = URL(fileURLWithPath: CommandLine.arguments[3]), pins = try JSONDecoder().decode([DownloadCandidate].self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[4])))
            let db = try DependencyDatabase(updates: Data(contentsOf: service.appendingPathComponent("updates.yaml")), graph: Data(contentsOf: service.appendingPathComponent("graph.yaml")), pins: pins)
            try writeResult(["status": "INDEX_PARSE", "identities": db.indexedByName.count, "problems": db.problems], "index-parse.json")
            try check("actual online database >6000 identities", db.indexedByName.count > 6000)
            try check("actual MemorialHelper indexed", db.byName["memorialHelper"] != nil)
            let corpus = ModLibrary(profile: URL(fileURLWithPath: CommandLine.arguments[5]), specialPins: Dictionary(uniqueKeysWithValues: pins.flatMap { p in p.modules.map { ($0.name, p.pinnedSHA256!) } }))
            let inv = try LibraryInventory.read(corpus), plan = try DependencyPlanner.resolve(inv, database: db, pins: corpus.specialPins)
            try check("full original SJ corpus remains unchanged", inv.archives.count == 53 && plan.issues.isEmpty && plan.downloads.isEmpty && plan.enable.isEmpty && plan.disable.isEmpty)
            let updates = try ModUpdates.check(inv, library: corpus, database: db, cancellation: InstallCancellation(), progress: { _ in })
            try writeResult(["status": "PASS_NATIVE_INSTALL_PLANNER_HASH_INDEX", "checks": checks, "indexIdentities": db.indexedByName.count, "indexProblems": db.problems, "corpusUpdates": updates.map(\.json)], "pure.json")
        case "journal": try journal()
        case "recover":
            let profile = base.appendingPathComponent(CommandLine.arguments[3]); let lib = ModLibrary(profile: profile)
            let inv = try LibraryInventory.read(lib)
            try writeResult(["status": "RECOVERED", "inventory": try JSONSerialization.jsonObject(with: canonicalData(inv)), "diagnostics": InstallJournal.diagnostics(profile: profile)], CommandLine.arguments[3] + "-recovery.json")
        case "recover-fails":
            try rejects("recovery refuses changed files or state") { _ = try LibraryInventory.read(ModLibrary(profile: base.appendingPathComponent(CommandLine.arguments[3]))) }
            try writeResult(["status": "PASS_RECOVERY_PRESERVES_UNKNOWN_CHANGES", "checks": checks], CommandLine.arguments[3] + "-recovery.json")
        case "engine": try engine()
        case "automatic": try automatic()
        case "network": try network()
        default: throw TestFailure(description: "Unknown mode")
        }
    }
    static func journal() throws {
        let profile = base.appendingPathComponent(CommandLine.arguments[3]); let lib = ModLibrary(profile: profile), candidates = try loadCandidates()
        try InstallJournal.directory(profile)
        _ = try lib.importZIP(fixtures.appendingPathComponent("root.zip")); _ = try lib.importZIP(fixtures.appendingPathComponent("helper-old.zip"))
        try Data("complete mod save and unknown sidecar".utf8).write(to: profile.appendingPathComponent("unknown.save.dat"))
        try InstallJournal.atomicWrite(try canonicalData(LibraryState(disabled: [])), to: lib.stateURL)
        let inv = try LibraryInventory.read(lib), db = try database([candidates["helper-new"]!, candidates["leaf-new"]!])
        let plan = try DependencyPlanner.resolve(inv, database: db, pins: [:]); try check("journal complete plan", plan.issues.isEmpty && plan.downloads.count == 2)
        var verified: [String: VerifiedDownload] = [:]; try InstallJournal.directory(InstallJournal.cache(profile))
        for source in plan.downloads {
            let key = candidates.first { $0.value.key == source.key }!.key, input = fixtures.appendingPathComponent(key + ".zip"), identity = try DownloadIdentity.read(input)
            let archive = try ModLibrary.inspect(input, filename: key + ".zip", digest: identity.sha256, bytes: identity.bytes)
            verified[source.key] = VerifiedDownload(source: source, identity: identity, archive: archive)
            try FileManager.default.copyItem(at: input, to: InstallJournal.cache(profile).appendingPathComponent(source.key + ".zip"))
        }
        let fault = CommandLine.arguments[4]
        if fault == "tamper" { try Data("bad".utf8).write(to: InstallJournal.cache(profile).appendingPathComponent(plan.downloads[0].key + ".zip")) }
        if fault == "stale" { try lib.setEnabled(false, filename: inv.active[0].filename) }
        do {
            _ = try InstallJournal.commit(library: lib, inventory: inv, plan: plan, verified: verified) { stage in
                if stage == fault { _exit(75) }
                if "throw:" + stage == fault { throw TestFailure(description: "Simulated disk failure") }
            }
            if fault == "tamper" || fault == "stale" || fault.hasPrefix("throw:") { throw TestFailure(description: "fault was not rejected") }
        } catch {
            guard fault == "tamper" || fault == "stale" || fault.hasPrefix("throw:") else { throw error }
            try check("injected fault leaves originals", FileManager.default.fileExists(atPath: lib.mods.appendingPathComponent("root.zip").path) && FileManager.default.fileExists(atPath: lib.mods.appendingPathComponent("helper-old.zip").path))
        }
        try writeResult(["status": "JOURNAL_TEST_FINISHED", "checks": checks, "diagnostics": InstallJournal.diagnostics(profile: profile)], CommandLine.arguments[3] + "-result.json")
    }
    static func awaitState(_ installer: DependencyInstaller, action: () -> Void) throws -> [String: Any] {
        var terminal: [String: Any]?
        installer.update = { state in if state["active"] as? Bool == false { terminal = state } }
        action(); let end = Date().addingTimeInterval(120)
        while terminal == nil && Date() < end { RunLoop.current.run(until: Date().addingTimeInterval(0.01)) }
        guard let terminal else { throw TestFailure(description: "Installer did not finish") }; return terminal
    }
    static func engine() throws {
        let candidates = try loadCandidates(), helper = candidates["helper-new"]!, leaf = candidates["leaf-new"]!
        let lib = ModLibrary(profile: base.appendingPathComponent("engine-profile"))
        _ = try lib.importZIP(fixtures.appendingPathComponent("root.zip"))
        var inaccurate = helper; inaccurate.modules = try [module("Helper", "1.3")]
        let db = try database([inaccurate, leaf]); var downloads = 0
        let engine = DependencyInstaller(library: lib, pins: [], indexProvider: { _ in db }, downloadProvider: { url, target, _, _, token, progress in
            try token.check(); downloads += 1
            let key = candidates.first { $0.value.url == url }!.key, data = try Data(contentsOf: fixtures.appendingPathComponent(key + ".zip"))
            try data.write(to: target); progress(Int64(data.count), Int64(data.count))
        })
        var state = try awaitState(engine) { engine.resolve() }
        try check("engine review before mutation", state["phase"] as? String == "review" && LibraryInventory.read(lib).archives.count == 1)
        var id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(engine) { engine.apply(planID: id) }
        try check("actual ZIP changes graph and requires new review", state["phase"] as? String == "review" && state["revised"] as? Bool == true && LibraryInventory.read(lib).archives.count == 1 && downloads == 1)
        id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(engine) { engine.apply(planID: id) }
        try check("revised plan reuses verified download and commits", state["phase"] as? String == "complete" && downloads == 2 && LibraryInventory.read(lib).archives.count == 3 && lib.snapshot()["canRun"] as? Bool == true)
        let updatesLib = ModLibrary(profile: base.appendingPathComponent("engine-updates"))
        _ = try updatesLib.importZIP(fixtures.appendingPathComponent("helper-old.zip")); try updatesLib.setEnabled(false, filename: "helper-old.zip")
        let exact = try database([helper, leaf])
        let updater = DependencyInstaller(library: updatesLib, pins: [], indexProvider: { _ in exact }, downloadProvider: { url, target, _, _, token, _ in
            try token.check(); let key = candidates.first { $0.value.url == url }!.key
            try FileManager.default.copyItem(at: fixtures.appendingPathComponent(key + ".zip"), to: target)
        })
        state = try awaitState(updater) { updater.checkUpdates() }
        try check("updates list reports disabled mod", state["phase"] as? String == "updates" && (state["updates"] as? [[String: Any]])?.first?["enabled"] as? Bool == false)
        state = try awaitState(updater) { updater.planUpdates(["helper-old.zip"]) }
        try check("update review ready", state["phase"] as? String == "review")
        id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(updater) { updater.apply(planID: id) }
        try check("disabled updated archive and original both stay disabled", state["phase"] as? String == "complete" && LibraryInventory.read(updatesLib).active.isEmpty && LibraryInventory.read(updatesLib).archives.count == 2)
        state = try awaitState(updater) { updater.checkUpdates() }
        try check("retained previous versions excluded from update list", state["phase"] as? String == "updates" && (state["updates"] as? [[String: Any]])?.count == 0)
        try updatesLib.setAllEnabled(true)
        try check("enable all excludes retained recovery ZIP", LibraryInventory.read(updatesLib).active.count == 1 && LibraryInventory.read(updatesLib).active.first?.filename != "helper-old.zip")
        let broken = ModLibrary(profile: base.appendingPathComponent("engine-rejected")); _ = try broken.importZIP(fixtures.appendingPathComponent("root.zip"))
        let bad = DependencyInstaller(library: broken, pins: [], indexProvider: { _ in exact }, downloadProvider: { _, target, _, _, _, _ in try Data("damaged zip".utf8).write(to: target) })
        state = try awaitState(bad) { bad.resolve() }; id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(bad) { bad.apply(planID: id) }
        try check("failed integrity keeps library unchanged", state["phase"] as? String == "failed" && LibraryInventory.read(broken).archives.count == 1)
        let cancelledLib = ModLibrary(profile: base.appendingPathComponent("engine-cancelled")); _ = try cancelledLib.importZIP(fixtures.appendingPathComponent("root.zip"))
        var calls = 0, cancelOnce = true
        let cancelled = DependencyInstaller(library: cancelledLib, pins: [], indexProvider: { _ in exact }, downloadProvider: { url, target, _, _, token, progress in
            calls += 1
            if calls == 2 && cancelOnce { try Data("partial".utf8).write(to: target); token.cancel(); try token.check() }
            let key = candidates.first { $0.value.url == url }!.key
            try FileManager.default.copyItem(at: fixtures.appendingPathComponent(key + ".zip"), to: target); progress(100, 100)
        })
        state = try awaitState(cancelled) { cancelled.resolve() }; id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(cancelled) { cancelled.apply(planID: id) }
        let cacheFiles = try FileManager.default.contentsOfDirectory(at: InstallJournal.cache(cancelledLib.profile), includingPropertiesForKeys: nil)
        try check("cancel preserves verified first file and removes partial", state["phase"] as? String == "cancelled" && LibraryInventory.read(cancelledLib).archives.count == 1 && cacheFiles.filter { $0.pathExtension == "zip" }.count == 1 && cacheFiles.filter { $0.pathExtension == "part" }.isEmpty)
        cancelOnce = false
        state = try awaitState(cancelled) { cancelled.resolve() }; id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(cancelled) { cancelled.apply(planID: id) }
        try check("retry downloads only unfinished archive", state["phase"] as? String == "complete" && calls == 3)
        let corruptLib = ModLibrary(profile: base.appendingPathComponent("engine-corrupt-cache")); _ = try corruptLib.importZIP(fixtures.appendingPathComponent("root.zip"))
        try InstallJournal.directory(InstallJournal.cache(corruptLib.profile))
        try Data("corrupt cached archive".utf8).write(to: InstallJournal.cache(corruptLib.profile).appendingPathComponent(helper.key + ".zip"))
        let corrected = DependencyInstaller(library: corruptLib, pins: [], indexProvider: { _ in exact }, downloadProvider: { url, target, _, _, _, _ in
            let key = candidates.first { $0.value.url == url }!.key
            try FileManager.default.copyItem(at: fixtures.appendingPathComponent(key + ".zip"), to: target)
        })
        state = try awaitState(corrected) { corrected.resolve() }; id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(corrected) { corrected.apply(planID: id) }
        try check("corrupt cache redownloads instead of trapping retry", state["phase"] as? String == "complete" && LibraryInventory.read(corruptLib).archives.count == 3)
        let repackLib = ModLibrary(profile: base.appendingPathComponent("engine-repack")); _ = try repackLib.importZIP(fixtures.appendingPathComponent("helper-old.zip"))
        let repackDB = try database([candidates["helper-repacked"]!])
        let repacks = try ModUpdates.check(LibraryInventory.read(repackLib), library: repackLib, database: repackDB, cancellation: InstallCancellation(), progress: { _ in })
        try check("same version repack detected from published archive hash", repacks.count == 1 && repacks[0].reason.contains("same version"))
        try writeResult(["status": "PASS_NATIVE_INSTALL_COORDINATOR", "checks": checks, "downloadCount": downloads], "engine.json")
    }
    static func network() throws {
        let service = URL(fileURLWithPath: CommandLine.arguments[3])
        let db = try DependencyDatabase(updates: Data(contentsOf: service.appendingPathComponent("updates.yaml")), graph: Data(contentsOf: service.appendingPathComponent("graph.yaml")))
        let source = db.byName["memorialHelper"]!, target = base.appendingPathComponent("real-memorialHelper.zip")
        try InstallDownload(destination: target, limit: Int64(source.bytes), expected: Int64(source.bytes), cancellation: InstallCancellation(), progress: { _, _ in }).fetch(URL(string: source.url)!)
        let identity = try DownloadIdentity.read(target)
        try check("real HTTPS helper matches published size and xxHash", source.accepts(identity))
        let archive = try ModLibrary.inspect(target, filename: "memorialHelper.zip", digest: identity.sha256, bytes: identity.bytes)
        try check("real downloaded identity/version matches index", archive.modules[0].name == "memorialHelper" && archive.modules[0].version.parts == source.modules[0].version.parts)
        try rejects("real HTTPS streamed size cap rejects oversized file") {
            try InstallDownload(destination: base.appendingPathComponent("oversized.zip"), limit: 100, expected: nil, cancellation: InstallCancellation(), progress: { _, _ in }).fetch(URL(string: source.url)!)
        }
        try check("oversized file never staged", !FileManager.default.fileExists(atPath: base.appendingPathComponent("oversized.zip").path))
        try rejects("real HTTPS expected length mismatch rejected") {
            try InstallDownload(destination: base.appendingPathComponent("wrong-length.zip"), limit: Int64(source.bytes + 10), expected: Int64(source.bytes + 1), cancellation: InstallCancellation(), progress: { _, _ in }).fetch(URL(string: source.url)!)
        }
        try writeResult(["status": "PASS_REAL_HTTPS_DOWNLOAD", "checks": checks, "url": source.url, "identity": try JSONSerialization.jsonObject(with: canonicalData(identity))], "network.json")
    }
    static func automatic() throws {
        let lib = ModLibrary(profile: base.appendingPathComponent("automatic-profile")); _ = try lib.importZIP(fixtures.appendingPathComponent("helper-old.zip"))
        let inv = try LibraryInventory.read(lib), generation = UUID().uuidString, root = lib.profile.appendingPathComponent("LauncherIndex"), folder = root.appendingPathComponent(generation)
        try InstallJournal.directory(folder)
        let u = try Data(contentsOf: fixtures.appendingPathComponent("index-updates.yaml")), g = try Data(contentsOf: fixtures.appendingPathComponent("index-graph.yaml"))
        let provenance = ["generation": generation, "fetched": ISO8601DateFormatter().string(from: Date()), "updatesSHA256": digestData(u), "graphSHA256": digestData(g)]
        try u.write(to: folder.appendingPathComponent("updates.yaml")); try g.write(to: folder.appendingPathComponent("graph.yaml"))
        try canonicalData(provenance).write(to: folder.appendingPathComponent("receipt.json")); try Data(generation.utf8).write(to: root.appendingPathComponent("current.txt"))
        let db = try DependencyDatabase(updates: u, graph: g, provenance: provenance)
        let updates = try ModUpdates.check(inv, library: lib, database: db, cancellation: InstallCancellation(), progress: { _ in })
        func setCache(age: TimeInterval) throws {
            try canonicalData(ModUpdates.CheckCache(schema: 1, checked: Date().addingTimeInterval(-age), revision: inv.revision, updates: updates, index: provenance)).write(to: ModUpdates.cacheFile(lib.profile))
        }
        try setCache(age: 100); var networkCalls = 0, fail = false, downloads = 0
        let engine = DependencyInstaller(library: lib, pins: [], indexProvider: { _ in networkCalls += 1; if fail { throw LibraryError("Simulated offline check") }; return db }, downloadProvider: { _,_,_,_,_,_ in downloads += 1; throw LibraryError("Availability check must not download mods") })
        let settings = UserDefaults.standard
        settings.set(true, forKey: "launcher.autoUpdateChecks"); settings.removeObject(forKey: "launcher.lastAutomaticUpdateAttempt")
        var state = try awaitState(engine) { engine.checkUpdates(automatic: true) }
        try check("automatic fresh visit restores rows without network", state["phase"] as? String == "updates" && state["cachedAvailability"] as? Bool == true && (state["updates"] as? [[String: Any]])?.count == 1 && networkCalls == 0)
        try setCache(age: 90000); settings.set(false, forKey: "launcher.autoUpdateChecks")
        state = try awaitState(engine) { engine.checkUpdates(automatic: true) }
        try check("automatic opt-out retains cached display without network", state["phase"] as? String == "updates" && networkCalls == 0)
        settings.set(true, forKey: "launcher.autoUpdateChecks")
        state = try awaitState(engine) { engine.checkUpdates(automatic: true) }
        try check("expired successful cache triggers one metadata check", state["phase"] as? String == "updates" && networkCalls == 1)
        state = try awaitState(engine) { engine.checkUpdates() }
        try check("manual check bypasses successful cache interval", state["phase"] as? String == "updates" && networkCalls == 2)
        try setCache(age: 90000); settings.set(Date().timeIntervalSince1970 - 3601, forKey: "launcher.lastAutomaticUpdateAttempt"); fail = true
        state = try awaitState(engine) { engine.checkUpdates(automatic: true) }
        try check("automatic network failure reported", state["phase"] as? String == "failed" && networkCalls == 3)
        state = try awaitState(engine) { engine.checkUpdates(automatic: true) }
        try check("automatic failure backs off one hour", state["phase"] as? String == "updates" && networkCalls == 3)
        fail = false
        state = try awaitState(engine) { engine.checkUpdates() }
        try check("manual retry bypasses failure backoff", state["phase"] as? String == "updates" && networkCalls == 4 && downloads == 0)
        settings.removeObject(forKey: "launcher.autoUpdateChecks"); settings.removeObject(forKey: "launcher.lastAutomaticUpdateAttempt")
        try writeResult(["status": "PASS_AUTOMATIC_UPDATE_CHECK_RESOURCE_POLICY", "checks": checks, "metadataFetches": networkCalls, "modDownloads": downloads], "automatic.json")
    }
}
