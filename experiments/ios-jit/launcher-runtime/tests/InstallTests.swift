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
    let gb = URL(string: "https://gamebanana.com/mmdl/870370")!
    try check("upstream mirrors retain the exact file ID", InstallDownload.archiveSources(gb).map(\.absoluteString) == [gb.absoluteString, "https://banana-mirror-mods.celestemods.com/870370.zip", "https://celestemodupdater.0x0a.de/banana-mirror/870370.zip"])
    for text in ["https://gamebanana.com/mmdl/0", "https://gamebanana.com/mmdl/42?other=1", "https://other.example/mmdl/42", "https://gamebanana.com/mods/42", "https://gamebanana.com/mmdl/4294967296"] {
        let url = URL(string: text)!
        try check("no guessed mirror for " + text, InstallDownload.archiveSources(url) == [url])
    }
    let target = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".part")
    defer { try? FileManager.default.removeItem(at: target) }
    var attempts = [URL](), retries = [URL]()
    try InstallDownload.fetchWithMirrors(gb, destination: target, cancellation: InstallCancellation(), retry: { url, _ in retries.append(url) }, transport: { url in
        attempts.append(url)
        if url == gb { throw LibraryError("HTTP 503") }
        try Data("verified separately".utf8).write(to: target)
    })
    try check("one failed server falls back once and retains successful bytes", attempts.count == 2 && retries == [attempts[1]] && (try Data(contentsOf: target)) == Data("verified separately".utf8))
    try rejects("fallback refuses to overwrite an occupied destination") { try InstallDownload.fetchWithMirrors(gb, destination: target, cancellation: InstallCancellation(), retry: { _, _ in }, transport: { _ in throw LibraryError("must not reach") }) }
    try FileManager.default.removeItem(at: target)
    let cancelled = InstallCancellation(); attempts = []
    try rejects("cancellation never triggers another mirror") { try InstallDownload.fetchWithMirrors(gb, destination: target, cancellation: cancelled, retry: { _, _ in }, transport: { url in attempts.append(url); cancelled.cancel(); throw LibraryError("cancelled") }) }
    try check("cancelled after first request", attempts == [gb])
    attempts = []
    try rejects("all unavailable mirrors stop after three requests") { try InstallDownload.fetchWithMirrors(gb, destination: target, cancellation: InstallCancellation(), retry: { _, _ in }, transport: { url in attempts.append(url); throw LibraryError("HTTP 503") }) }
    try check("bounded fallback leaves no staged archive", attempts.count == 3 && !FileManager.default.fileExists(atPath: target.path))
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
    let olderRequirements = ["1.0.0", "1.1643.0", "1.1703.0", "1.1888.0", "1.1963.0", "1.3000.0", "1.3300.0", "1.4465.0", "1.5986.0", "1.6314.0", "1.6458.0", "1.808.0"]
    let legacy = try local("legacy", [module("LegacyMap", "1.0", olderRequirements.map { ("Everest", $0) })])
    p = try DependencyPlanner.resolve(inventory([legacy]), database: db, pins: [:])
    try check("all older requirements in the phone screenshot are satisfied", p.issues.isEmpty && p.downloads.isEmpty)
    let runtimeFuture = try remote([module("Helper", "1.5", [("Everest", "1.9999.0")])])
    p = try DependencyPlanner.resolve(inventory([legacy, good]), database: try database([runtimeFuture]), pins: [:], updates: [good.filename: runtimeFuture])
    try check("runtime warning identifies only the unsatisfied source and version", p.issues == ["Helper 1.5 requires Everest 1.9999.0; the app runtime includes 1.6531.0."] && p.json["canApply"] as? Bool == false)
    p = try DependencyPlanner.resolve(inventory([good], disabled: [good.filename]), database: db, pins: [:], updates: [good.filename: runtimeFuture])
    try check("direct planner cannot install incompatible runtime update even disabled", !p.issues.isEmpty && p.json["canApply"] as? Bool == false)
    let earlier = try remote([module("Helper", "1.4", [("Everest", "1.6458.0")])], pinned: String(repeating: "c", count: 64))
    var fallbackDB = try database([runtimeFuture]); fallbackDB.earlierByName["Helper"] = [earlier]
    p = try DependencyPlanner.resolve(inventory([root]), database: fallbackDB, pins: [:])
    try check("missing dependency chooses verified runtime-compatible earlier release", p.issues.isEmpty && p.downloads.map(\.key) == [earlier.key] && p.compatibilityChoices.count == 1)
    p = try DependencyPlanner.resolve(inventory([root, good]), database: fallbackDB, pins: [:])
    try check("fallback does not replace an already compatible installed mod", p.issues.isEmpty && p.downloads.isEmpty)
    let strictRoot = try local("strict", [module("StrictMap", "1.0", [("Helper", "1.5")])])
    p = try DependencyPlanner.resolve(inventory([strictRoot]), database: fallbackDB, pins: [:])
    try check("fallback never relaxes a mod's minimum dependency version", !p.issues.isEmpty && p.json["canApply"] as? Bool == false && !p.downloads.contains { $0.key == earlier.key })
    fallbackDB.byName["Helper"] = helper
    p = try DependencyPlanner.resolve(inventory([root]), database: fallbackDB, pins: [:])
    try check("compatible latest release preferred to a historical alternative", p.downloads.contains { $0.key == helper.key } && !p.downloads.contains { $0.key == earlier.key })
    fallbackDB.replaceWithVerified(earlier)
    try check("verified earlier metadata does not overwrite latest indexed candidate", fallbackDB.byName["Helper"]?.key == helper.key && fallbackDB.indexedByName["Helper"]?.key == runtimeFuture.key)
    try rejects("unverified historical catalogue entry rejected") { _ = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), earlier: [runtimeFuture], allowEmpty: true) }
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
        case "runtime-cache": try runtimeCache()
        case "blocked": try blockedUpdates()
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
        let failedReport = try InstallReport.read(broken.profile)
        try check("failed report separates failed and unattempted downloads with zero changes", failedReport.outcome == "failed" && failedReport.applicationState == "unchanged" && failedReport.changes.isEmpty && Set(failedReport.downloads.map(\.status)) == Set(["failed", "notAttempted"]))
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
        let cancelledReport = try InstallReport.read(cancelledLib.profile)
        try check("cancel report distinguishes verified cache from cancelled download", cancelledReport.outcome == "cancelled" && cancelledReport.changes.isEmpty && Set(cancelledReport.downloads.map(\.status)) == Set(["verified", "cancelled"]))
        cancelOnce = false
        state = try awaitState(cancelled) { cancelled.resolve() }; id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(cancelled) { cancelled.apply(planID: id) }
        try check("retry downloads only unfinished archive", state["phase"] as? String == "complete" && calls == 3)
        let installedReport = try InstallReport.read(cancelledLib.profile)
        try check("dependency completion report records actual installed versions", installedReport.outcome == "completed" && installedReport.applicationState == "applied" && installedReport.changes.count == 2 && installedReport.changes.allSatisfy { $0.action == "installed" && $0.beforeVersion == nil && $0.enabled } && installedReport.downloads.allSatisfy { $0.status == "installed" })
        let disabledReport = try InstallReport.read(updatesLib.profile)
        try check("update report records before after and disabled choice", disabledReport.changes.count == 1 && disabledReport.changes[0].beforeVersion == "1.0" && disabledReport.changes[0].afterVersion == "1.3" && disabledReport.changes[0].action == "updated" && !disabledReport.changes[0].enabled)
        let enableLib = ModLibrary(profile: base.appendingPathComponent("engine-enable-report"))
        for name in ["root", "helper-new", "leaf-new"] { _ = try enableLib.importZIP(fixtures.appendingPathComponent(name + ".zip")) }
        try enableLib.setEnabled(false, filename: "helper-new.zip")
        let enabler = DependencyInstaller(library: enableLib, pins: [], indexProvider: { _ in throw TestFailure(description: "Enable-only plan must work offline") })
        state = try awaitState(enabler) { enabler.resolve() }; id = (state["plan"] as! [String: Any])["id"] as! String
        state = try awaitState(enabler) { enabler.apply(planID: id) }
        let enableReport = try InstallReport.read(enableLib.profile)
        try check("dependency enabling reports Off to On without an invented update", state["phase"] as? String == "complete" && enableReport.downloads.isEmpty && enableReport.changes.count == 1 && enableReport.changes[0].action == "enabled" && enableReport.changes[0].enabled && enableReport.changes[0].beforeVersion == enableReport.changes[0].afterVersion)
        state = try awaitState(enabler) { enabler.showLastReport() }
        try check("saved report can be reopened independently", state["phase"] as? String == "report" && (state["report"] as? [String: Any])?["outcome"] as? String == "completed")
        let pendingPlan = try DependencyPlanner.resolve(LibraryInventory.read(broken), database: exact, pins: [:])
        var interrupted = InstallReport(plan: pendingPlan); interrupted.mark(pendingPlan.downloads[0], "verified"); try interrupted.save(broken.profile)
        let interruptedReport = try InstallReport.read(broken.profile)
        try check("unfinished persisted report does not assume success or rollback", interruptedReport.outcome == "interrupted" && interruptedReport.applicationState == "unconfirmed" && interruptedReport.downloads.count == 2 && interruptedReport.downloads[0].status == "verificationRecorded" && interruptedReport.downloads[1].status == "interrupted" && interruptedReport.changes.isEmpty)
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
        var transportURL = URL(string: source.url)!, retries = [[String: String]]()
        let token = InstallCancellation()
        try InstallDownload.fetchWithMirrors(transportURL, destination: target, cancellation: token, retry: { url, error in retries.append(["url": url.absoluteString, "error": error.localizedDescription]) }, transport: { url in
            transportURL = url
            try InstallDownload(destination: target, limit: Int64(source.bytes), expected: Int64(source.bytes), cancellation: token, progress: { _, _ in }).fetch(url)
        })
        let identity = try DownloadIdentity.read(target)
        try check("real HTTPS helper matches published size and xxHash", source.accepts(identity))
        let archive = try ModLibrary.inspect(target, filename: "memorialHelper.zip", digest: identity.sha256, bytes: identity.bytes)
        try check("real downloaded identity/version matches index", archive.modules[0].name == "memorialHelper" && archive.modules[0].version.parts == source.modules[0].version.parts)
        try rejects("real HTTPS streamed size cap rejects oversized file") {
            try InstallDownload(destination: base.appendingPathComponent("oversized.zip"), limit: 100, expected: nil, cancellation: InstallCancellation(), progress: { _, _ in }).fetch(transportURL)
        }
        try check("oversized file never staged", !FileManager.default.fileExists(atPath: base.appendingPathComponent("oversized.zip").path))
        try rejects("real HTTPS expected length mismatch rejected") {
            try InstallDownload(destination: base.appendingPathComponent("wrong-length.zip"), limit: Int64(source.bytes + 10), expected: Int64(source.bytes + 1), cancellation: InstallCancellation(), progress: { _, _ in }).fetch(transportURL)
        }
        try writeResult(["status": "PASS_REAL_HTTPS_DOWNLOAD", "checks": checks, "url": source.url, "transportURL": transportURL.absoluteString, "retries": retries, "identity": try JSONSerialization.jsonObject(with: canonicalData(identity))], "network.json")
    }
    static func blockedUpdates() throws {
        let candidates = try loadCandidates(), lib = ModLibrary(profile: base.appendingPathComponent("blocked-updates"))
        _ = try lib.importZIP(fixtures.appendingPathComponent("helper-old.zip"))
        var future = candidates["helper-new"]!
        future.modules = try [module("Helper", "1.3", [("Everest", "1.9999.0")])]
        let db = try database([future]); var downloads = 0
        let engine = DependencyInstaller(library: lib, pins: [], indexProvider: { _ in db }, downloadProvider: { _,_,_,_,_,_ in downloads += 1; throw TestFailure(description: "Blocked update attempted a download") })
        let before = try LibraryInventory.read(lib), stateBytes = try InstallJournal.readState(lib.stateURL)
        var state = try awaitState(engine) { engine.checkUpdates() }
        let rows = state["updates"] as! [[String: Any]]
        try check("blocked update visible with explicit runtime reason", rows.count == 1 && rows[0]["canUpdate"] as? Bool == false && (rows[0]["reason"] as? String)?.contains("1.9999.0") == true)
        state = try awaitState(engine) { engine.planUpdates(["helper-old.zip"]) }
        try check("direct blocked update command rejected by coordinator", state["phase"] as? String == "failed")
        state = try awaitState(engine) { engine.apply(planID: UUID().uuidString) }
        try check("forged apply rejected with no files or state changed", state["phase"] as? String == "failed" && downloads == 0 && LibraryInventory.read(lib).revision == before.revision && InstallJournal.readState(lib.stateURL) == stateBytes)
        let blocker = ModLibrary(profile: base.appendingPathComponent("blocked-resolution"))
        _ = try blocker.importZIP(fixtures.appendingPathComponent("root.zip"))
        let resolver = DependencyInstaller(library: blocker, pins: [], indexProvider: { _ in db }, downloadProvider: { _,_,_,_,_,_ in downloads += 1; throw TestFailure(description: "Blocked plan attempted a download") })
        state = try awaitState(resolver) { resolver.resolve() }
        let plan = state["plan"] as! [String: Any]
        try check("fresh resolution runtime blocker cannot apply", plan["canApply"] as? Bool == false && (plan["issues"] as! [String]).count == 1)
        state = try awaitState(resolver) { resolver.apply(planID: plan["id"] as! String) }
        try check("real blocked plan ID rejected before download or commit", state["phase"] as? String == "failed" && downloads == 0 && LibraryInventory.read(blocker).archives.count == 1)
        try writeResult(["status": "PASS_BLOCKED_RUNTIME_UPDATE_AND_APPLY", "checks": checks, "downloads": downloads], "blocked.json")
    }
    static func runtimeCache() throws {
        let settings = UserDefaults.standard
        defer { settings.removeObject(forKey: "launcher.autoUpdateChecks"); settings.removeObject(forKey: "launcher.lastAutomaticUpdateAttempt") }
        var cases = [[String: Any]]()
        let current = try RuntimeIdentity.compatibilityFingerprint(pins: [:])
        var older = RuntimeIdentity.builtins; older["Everest"] = "1.6458.0"; older["EverestCore"] = "1.6458.0"
        var future = RuntimeIdentity.builtins; future["Everest"] = "1.9999.0"; future["EverestCore"] = "1.9999.0"
        let olderKey = try RuntimeIdentity.compatibilityFingerprint(builtins: older, pins: [:])
        let futureKey = try RuntimeIdentity.compatibilityFingerprint(builtins: future, pins: [:])
        try check("runtime fingerprints distinguish upgrade and downgrade", current != olderKey && current != futureKey && olderKey != futureKey)
        try check("compatibility policy revision invalidates results", current != RuntimeIdentity.compatibilityFingerprint(pins: [:], policy: 2))
        for name in ["legacy-upgrade", "upgrade", "opt-out", "backoff", "downgrade", "pins"] {
            let profile = base.appendingPathComponent("cache-" + name)
            let seed = ModLibrary(profile: profile); _ = try seed.importZIP(fixtures.appendingPathComponent("helper-old.zip"))
            let inv = try LibraryInventory.read(seed), pinned = name == "pins"
            let lib = ModLibrary(profile: profile, specialPins: pinned ? ["Helper": inv.archives[0].digest] : [:])
            let root = profile.appendingPathComponent("LauncherIndex"), generation = UUID().uuidString, folder = root.appendingPathComponent(generation)
            try InstallJournal.directory(folder)
            let u = try Data(contentsOf: fixtures.appendingPathComponent("index-updates.yaml"))
            let required = name == "downgrade" ? "1.9999.0" : "1.6531.0"
            let g = Data("Helper:\n  URL: https://mods.example.org/helper-new.zip\n  Dependencies:\n    - Name: Everest\n      Version: \(required)\n  OptionalDependencies: []\n".utf8)
            let provenance = ["generation": generation, "fetched": "2026-09-13T00:00:00Z", "updatesSHA256": digestData(u), "graphSHA256": digestData(g)]
            try u.write(to: folder.appendingPathComponent("updates.yaml")); try g.write(to: folder.appendingPathComponent("graph.yaml"))
            try canonicalData(provenance).write(to: folder.appendingPathComponent("receipt.json")); try Data(generation.utf8).write(to: root.appendingPathComponent("current.txt"))
            let db = try DependencyDatabase(updates: u, graph: g, provenance: provenance)
            let shouldAllow = name != "downgrade" && !pinned
            let stale = ModUpdate(archive: inv.archives[0], candidate: db.indexedByName["Helper"]!, enabled: true, reason: "Stale previous runtime decision", canUpdate: !shouldAllow)
            let checked = Date().addingTimeInterval(name == "opt-out" || name == "backoff" ? -90000 : -100)
            let record = ModUpdates.CheckCache(schema: name == "legacy-upgrade" ? 1 : 2, checked: checked, revision: inv.revision,
                updates: [stale], index: provenance, policyFingerprint: name == "legacy-upgrade" ? nil : name == "downgrade" ? futureKey : pinned ? current : olderKey)
            try canonicalData(record).write(to: ModUpdates.cacheFile(profile))
            let hashes = root.appendingPathComponent("update-hashes.json"), hashBytes = Data("{}".utf8)
            try hashBytes.write(to: hashes)
            let cache = InstallJournal.cache(profile); try InstallJournal.directory(cache)
            let retained = cache.appendingPathComponent("retained.zip"); let retainedBytes = Data("independent retained download".utf8); try retainedBytes.write(to: retained)
            settings.set(name != "opt-out", forKey: "launcher.autoUpdateChecks")
            settings.set(name == "backoff" ? Date().timeIntervalSince1970 : 0, forKey: "launcher.lastAutomaticUpdateAttempt")
            var fetches = 0, downloads = 0
            let engine = DependencyInstaller(library: lib, pins: [], indexProvider: { _ in fetches += 1; throw LibraryError("Offline") }, downloadProvider: { _,_,_,_,_,_ in downloads += 1; throw LibraryError("No install authorized") })
            var state = try awaitState(engine) { engine.checkUpdates(automatic: true) }
            let rows = state["updates"] as? [[String: Any]] ?? []
            try check(name + " re-evaluates stale availability without network", state["phase"] as? String == "updates" && state["runtimePolicyReevaluated"] as? Bool == true && rows.count == 1 && rows[0]["canUpdate"] as? Bool == shouldAllow && fetches == 0 && downloads == 0)
            let saved = ModUpdates.readCache(profile)!
            try check(name + " binds schema2 policy without pretending a new index fetch", saved.schema == 2 && saved.policyFingerprint == RuntimeIdentity.compatibilityFingerprint(pins: lib.specialPins) && abs(saved.checked.timeIntervalSince(checked)) < 0.001)
            try check(name + " preserves archives, choice state, index and verified download bytes", LibraryInventory.read(lib).revision == inv.revision && Data(contentsOf: retained) == retainedBytes && Data(contentsOf: folder.appendingPathComponent("updates.yaml")) == u && Data(contentsOf: folder.appendingPathComponent("graph.yaml")) == g && Data(contentsOf: hashes) == hashBytes)
            state = try awaitState(engine) { engine.checkUpdates(automatic: true) }
            try check(name + " subsequent visit reuses the matching policy", state["runtimePolicyReevaluated"] as? Bool == false && fetches == 0 && downloads == 0)
            cases.append(["case": name, "updates": rows, "networkFetches": fetches, "archiveDownloads": downloads, "policy": saved.policyFingerprint!])
        }
        try writeResult(["status": "PASS_RUNTIME_CACHE_UPGRADE_DOWNGRADE_OFFLINE_POLICY", "checks": checks, "cases": cases], "runtime-cache.json")
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
