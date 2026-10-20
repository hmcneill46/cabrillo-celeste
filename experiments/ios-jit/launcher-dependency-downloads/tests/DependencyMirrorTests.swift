import Foundation
import ZIPFoundation

@main struct DependencyMirrorTests {
    static var checks = [String]()
    static let fm = FileManager.default
    static func check(_ value: @autoclosure () throws -> Bool, _ name: String) throws {
        guard try value() else { throw LibraryError("FAILED: " + name) }; checks.append(name)
    }
    static func rejects(_ name: String, _ body: () throws -> Void) throws {
        do { try body() } catch { checks.append(name); return }; throw LibraryError("Accepted invalid case: " + name)
    }
    static func urls(_ source: String, _ name: String? = nil) -> [String] {
        InstallDownload.archiveSources(URL(string: source)!, mirrorName: name).map(\.absoluteString)
    }
    static func candidateJSON(_ extra: String = "") -> Data {
        Data(("{\"url\":\"https://gamebanana.com/mmdl/42\",\"bytes\":10,\"hashes\":[\"0123456789abcdef\"],\"modules\":[]" + extra + "}").utf8)
    }
    static func database(_ fields: [String], names: [String]? = nil, pins: [DownloadCandidate] = []) throws -> DependencyDatabase {
        let modules = names ?? fields.indices.map { "Module\($0)" }
        let updates = Swift.zip(modules, fields).map { name, field in
            "\(name):\n  URL: https://gamebanana.com/mmdl/42\n  Size: 10\n  Version: 1.0\n  xxHash: [0123456789abcdef]\n" + field
        }.joined()
        let graph = modules.map { "\($0):\n  URL: https://gamebanana.com/mmdl/42\n  Dependencies: []\n" }.joined()
        return try DependencyDatabase(updates: Data(updates.utf8), graph: Data(graph.utf8), pins: pins, allowEmpty: true)
    }
    static func transport(_ root: URL) throws {
        let original = "https://gamebanana.com/mmdl/42"
        try check(urls(original) == [original, "https://banana-mirror-mods.celestemods.com/42.zip", "https://celestemodupdater.0x0a.de/banana-mirror/42.zip"], "legacy absent MirrorName keeps canonical numeric mirrors")
        for name in ["1838255", "replacement_56", "Release-1.2_3", String(repeating: "a", count: 200)] {
            try check(validMirrorName(name) == name && urls(original, name) == [original, "https://banana-mirror-mods.celestemods.com/\(name).zip", "https://celestemodupdater.0x0a.de/banana-mirror/\(name).zip"], "explicit published basename retained: " + String(name.prefix(30)))
        }
        let other = "https://downloads.example.org/published/mod.zip?release=56"
        try check(urls(other, "published_56").count == 3 && urls(other, "published_56")[1].hasSuffix("/published_56.zip"), "valid MirrorName supports any accepted HTTPS original like Everest6642")
        try check(urls(other) == [other], "unrelated original without MirrorName never gets guessed mirrors")
        for name in ["", ".", "..", "../42", "a/42", "a\\42", "a..b", ".hidden", "x?key=y", "x#fragment", "x%2f42", "x%252f42", "https://evil.example/x", "x:443", "x@y", "x y", "x\n42", "x\u{0}42", "café", String(repeating: "x", count: 201)] {
            try check(validMirrorName(name) == nil && urls(original, name) == [original], "invalid explicit basename never becomes numeric fallback: " + name.debugDescription)
        }
        for source in ["https://gamebanana.com/mmdl/0", "https://gamebanana.com/mmdl/042", "https://gamebanana.com/mmdl/4294967296", "https://gamebanana.com/mmdl/42?x=y", "https://gamebanana.com:443/mmdl/42", "https://gamebanana.com/mmdl/42/", "https://gamebanana.com/mmdl//42", "https://gamebanana.com/mmdl/%34%32", "https://gamebanana.com/mods/42", "https://other.example/mmdl/42"] {
            try check(urls(source) == [source], "numeric fallback requires canonical GameBanana file URL: " + source)
        }
        for source in ["http://gamebanana.com/mmdl/42", "https://user:password@gamebanana.com/mmdl/42", "https://localhost/mmdl/42", "https://gamebanana.com/mmdl/42#fragment"] {
            try check(urls(source, "valid_56") == [source], "explicit MirrorName cannot authorize an invalid original URL: " + source)
        }
        let target = root.appendingPathComponent("transport.part"), good = Data("reviewed mirror bytes".utf8)
        var attempts = [String](), retries = [String]()
        try InstallDownload.fetchWithMirrors(URL(string: original)!, mirrorName: "replacement_56", destination: target, cancellation: InstallCancellation(), retry: { url, _ in retries.append(url.absoluteString) }, transport: { url in
            attempts.append(url.absoluteString)
            if url.absoluteString == original { try Data("incomplete".utf8).write(to: target); throw LibraryError("HTTP 404") }
            guard url.path == "/replacement_56.zip", !fm.fileExists(atPath: target.path) else { throw LibraryError("Wrong mirror or stale partial file") }
            try good.write(to: target)
        })
        try check(attempts == [original, "https://banana-mirror-mods.celestemods.com/replacement_56.zip"] && retries == [attempts[1]] && (try Data(contentsOf: target)) == good, "original differing-MirrorName404 now reaches correct mirror and cleans partial bytes")
        try rejects("occupied staging target is never overwritten") { try InstallDownload.fetchWithMirrors(URL(string: original)!, mirrorName: "replacement_56", destination: target, cancellation: InstallCancellation(), retry: { _, _ in }, transport: { _ in throw LibraryError("must not execute") }) }
        try fm.removeItem(at: target)
        let token = InstallCancellation(); attempts = []
        try rejects("cancellation stops before another MirrorName server") {
            try InstallDownload.fetchWithMirrors(URL(string: original)!, mirrorName: "replacement_56", destination: target, cancellation: token, retry: { _, _ in }, transport: { url in attempts.append(url.absoluteString); token.cancel(); throw LibraryError("cancel") })
        }
        try check(attempts == [original] && !fm.fileExists(atPath: target.path), "cancelled attempt produces no retry or accepted file")
        attempts = []
        try rejects("all404 MirrorName servers remain bounded") {
            try InstallDownload.fetchWithMirrors(URL(string: original)!, mirrorName: "replacement_56", destination: target, cancellation: InstallCancellation(), retry: { _, _ in }, transport: { url in attempts.append(url.absoluteString); try Data("partial".utf8).write(to: target); throw LibraryError("HTTP 404") })
        }
        try check(attempts.count == 3 && !fm.fileExists(atPath: target.path), "all failed transports remove staged bytes")
    }
    static func metadata() throws {
        let decoder = JSONDecoder(), old = try decoder.decode(DownloadCandidate.self, from: candidateJSON())
        let null = try decoder.decode(DownloadCandidate.self, from: candidateJSON(",\"mirrorName\":null"))
        let explicit = try decoder.decode(DownloadCandidate.self, from: candidateJSON(",\"mirrorName\":\"replacement_56\""))
        let empty = try decoder.decode(DownloadCandidate.self, from: candidateJSON(",\"mirrorName\":\"\""))
        try check(old.mirrorName == nil && null.mirrorName == nil, "old and explicit-null candidate JSON remain compatible")
        try check(empty.mirrorName == "" && urls(empty.url, empty.mirrorName) == [empty.url], "explicit empty candidate JSON stays original-only")
        try check(try decoder.decode(DownloadCandidate.self, from: canonicalData(explicit)).mirrorName == explicit.mirrorName, "MirrorName survives candidate JSON roundtrip")
        try check(old.key == explicit.key && old.key == empty.key && old.key == null.key, "transport metadata does not invalidate verified archive cache identity")
        try rejects("non-string JSON MirrorName cannot silently become numeric fallback") { _ = try decoder.decode(DownloadCandidate.self, from: candidateJSON(",\"mirrorName\":[]")) }
        let fields = ["", "  MirrorName: null\n", "  MirrorName: \"\"\n", "  MirrorName: [42]\n", "  MirrorName: {bad: 42}\n", "  MirrorName: replacement_56\n"]
        for (index, field) in fields.enumerated() {
            let db = try database([field]), source = db.byName["Module0"]!
            let expected: String? = index < 2 ? nil : index < 5 ? "" : "replacement_56"
            try check(source.mirrorName == expected, "online MirrorName distinguishes omitted/null and malformed/empty, case\(index)")
        }
        let combined = try database(["  MirrorName: shared_56\n", "  MirrorName: shared_56\n"])
        try check(combined.byName["Module0"]?.modules.count == 2 && combined.byName["Module1"]?.mirrorName == "shared_56", "multi-module archive carries one agreed mirror identity")
        let conflict = try database(["  MirrorName: first_56\n", "  MirrorName: second_56\n"])
        try check(conflict.byName["Module1"] == nil && conflict.problems["Module1"]?.contains("ambiguous") == true, "conflicting MirrorName rows are rejected as ambiguous archive metadata")
        var pin = old; pin.mirrorName = "pinned_56"
        pin.modules = [ModMetadata(name: "Module0", version: try ModVersion("1.0"), dll: nil, dependencies: [], optionalDependencies: [])]
        let pinned = try database(["  MirrorName: latest_56\n"], pins: [pin])
        try check(pinned.byName["Module0"]?.mirrorName == "pinned_56" && pinned.indexedByName["Module0"]?.mirrorName == "latest_56", "bundled compatibility pin overrides online transport without losing indexed availability")
    }
    static func zip(_ root: URL, name: String, dependencies: [String] = [], version: String = "1.0") throws -> (URL, DownloadCandidate) {
        let file = root.appendingPathComponent(name + "-" + version + ".zip")
        let metadata = "- Name: \(name)\n  Version: \(version)\n" + (dependencies.isEmpty ? "" : "  Dependencies:\n" + dependencies.map { "  - Name: \($0)\n    Version: 1.0\n" }.joined())
        do {
            let archive = try Archive(url: file, accessMode: .create), data = Data(metadata.utf8)
            try archive.addEntry(with: "everest.yaml", type: .file, uncompressedSize: Int64(data.count), compressionMethod: .deflate) { offset, size in data.subdata(in: Int(offset)..<Int(offset)+size) }
        }
        let identity = try DownloadIdentity.read(file), archive = try ModLibrary.inspect(file, filename: file.lastPathComponent, digest: identity.sha256, bytes: identity.bytes)
        return (file, DownloadCandidate(url: "https://gamebanana.com/mmdl/\(name == "MirrorHelper" ? 900001 : 900002)", bytes: identity.bytes, hashes: [identity.xxHash], pinnedSHA256: nil, modules: archive.modules, mirrorName: "archive_" + name))
    }
    static func wait(_ installer: DependencyInstaller, _ action: () -> Void) throws -> [String: Any] {
        var terminal: [String: Any]?
        installer.update = { if $0["active"] as? Bool == false { terminal = $0 } }
        action(); let deadline = Date().addingTimeInterval(30)
        while terminal == nil && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.01)) }
        guard let terminal else { throw LibraryError("Isolated installer timed out") }; return terminal
    }
    static func planID(_ state: [String: Any]) throws -> String {
        guard let plan = state["plan"] as? [String: Any], plan["canApply"] as? Bool == true, let id = plan["id"] as? String else { throw LibraryError("Expected an applicable review: \(state)") }; return id
    }
    static func coordinator(_ root: URL) throws {
        let files = root.appendingPathComponent("fixtures"); try InstallJournal.directory(files)
        let (rootZIP, _) = try zip(files, name: "MirrorRoot", dependencies: ["MirrorHelper", "MirrorLeaf"])
        let (helperZIP, helper) = try zip(files, name: "MirrorHelper"), (leafZIP, leaf) = try zip(files, name: "MirrorLeaf")
        var db = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), allowEmpty: true)
        for source in [helper, leaf] { for module in source.modules { db.byName[module.name] = source; db.indexedByName[module.name] = source } }
        let library = ModLibrary(profile: root.appendingPathComponent("Profile")); _ = try library.importZIP(rootZIP)
        let sentinel = library.profile.appendingPathComponent("unknown-save.bin"), saved = Data("save bytes retained".utf8); try saved.write(to: sentinel)
        let before = try LibraryInventory.read(library), initial = try DependencyPlanner.resolve(before, database: db, pins: [:])
        let first = initial.downloads[0], second = initial.downloads[1]
        let origins = [helper.url: helperZIP, leaf.url: leafZIP], sources = [helper.url: helper, leaf.url: leaf]
        var fail = true, counts = [String: Int]()
        let installer = DependencyInstaller(library: library, pins: [], indexProvider: { _ in db }, downloadProvider: { url, destination, _, _, token, _ in
            counts[url, default: 0] += 1; let source = sources[url]!
            try InstallDownload.fetchWithMirrors(URL(string: url)!, mirrorName: source.mirrorName, destination: destination, cancellation: token, retry: { _, _ in }, transport: { endpoint in
                if endpoint.absoluteString == url || (fail && url == second.url) { throw LibraryError("HTTP 404") }
                guard endpoint.path == "/\(source.mirrorName!).zip" else { throw LibraryError("Wrong published mirror") }
                try fm.copyItem(at: origins[url]!, to: destination)
            })
        })
        var state = try wait(installer) { installer.resolve() }, id = try planID(state)
        state = try wait(installer) { installer.apply(planID: id) }
        let failed = try InstallReport.read(library.profile)
        try check(state["phase"] as? String == "failed" && failed.outcome == "failed" && !failed.commitStarted && failed.applicationState == "unchanged", "archive404 fails before transaction commit")
        try check(try LibraryInventory.read(library).revision == before.revision && Data(contentsOf: sentinel) == saved, "failed archive transport preserves originals, enabled choices and saves")
        let cached = InstallJournal.cache(library.profile).appendingPathComponent(first.key + ".zip")
        try check(first.accepts(DownloadIdentity.read(cached)) && !fm.fileExists(atPath: InstallJournal.cache(library.profile).appendingPathComponent(second.key + ".zip").path), "completed verified archive retained while failed archive is absent")
        fail = false
        state = try wait(installer) { installer.resolve() }; id = try planID(state)
        state = try wait(installer) { installer.apply(planID: id) }
        let after = try LibraryInventory.read(library), completed = try InstallReport.read(library.profile)
        try check(state["phase"] as? String == "complete" && counts[first.url] == 1 && counts[second.url] == 2, "retry reuses completed cache and downloads only the unfinished archive")
        try check(after.archives.count == 3 && after.disabled.isEmpty && completed.outcome == "completed" && completed.applicationState == "applied", "all verified dependencies commit as one compatible installation")
        try check(after.archives.contains { $0.filename == before.archives[0].filename && $0.digest == before.archives[0].digest } && (try Data(contentsOf: sentinel)) == saved, "successful commit retains root original and unknown save bytes")
        let cancelled = ModLibrary(profile: root.appendingPathComponent("CancelledProfile")); _ = try cancelled.importZIP(rootZIP)
        let cancelledBefore = try LibraryInventory.read(cancelled)
        let canceller = DependencyInstaller(library: cancelled, pins: [], indexProvider: { _ in db }, downloadProvider: { url, target, _, _, token, _ in
            if url == second.url { try Data("cancelled partial".utf8).write(to: target); token.cancel(); throw LibraryError("cancelled fixture") }
            try fm.copyItem(at: origins[url]!, to: target)
        })
        state = try wait(canceller) { canceller.resolve() }; id = try planID(state)
        state = try wait(canceller) { canceller.apply(planID: id) }
        let cancelledReport = try InstallReport.read(cancelled.profile)
        try check(state["phase"] as? String == "cancelled" && cancelledReport.outcome == "cancelled" && !cancelledReport.commitStarted && (try LibraryInventory.read(cancelled).revision) == cancelledBefore.revision, "cancellation after a verified archive applies no mod changes")
        try check(first.accepts(DownloadIdentity.read(InstallJournal.cache(cancelled.profile).appendingPathComponent(first.key + ".zip"))) && (try fm.contentsOfDirectory(at: InstallJournal.cache(cancelled.profile), includingPropertiesForKeys: nil)).allSatisfy { $0.pathExtension != "part" }, "cancellation retains completed verified cache and removes its incomplete staging file")
        var pinned = helper; pinned = DownloadCandidate(url: helper.url, bytes: helper.bytes, hashes: [], pinnedSHA256: try DownloadIdentity.read(helperZIP).sha256, modules: helper.modules, mirrorName: "replacement_56")
        let local = ModLibrary(profile: root.appendingPathComponent("ImportedPin"), specialPins: ["MirrorHelper": pinned.pinnedSHA256!], archiveNames: [pinned.pinnedSHA256!: "MirrorHelper-tested.zip"])
        let imported = try local.importZIP(helperZIP)
        try check(imported.filename == "MirrorHelper-tested.zip" && imported.digest == pinned.pinnedSHA256, "manual exact pinned ZIP uses its approved archive name and digest")
        let localInstaller = DependencyInstaller(library: local, pins: [pinned], indexProvider: { _ in throw LibraryError("exact installed pin should resolve offline") }, downloadProvider: { _, _, _, _, _, _ in throw LibraryError("exact installed pin must not redownload") })
        state = try wait(localInstaller) { localInstaller.resolve() }
        try check(((state["plan"] as? [String: Any])?["downloads"] as? [[String: Any]])?.isEmpty == true, "approved imported compatibility pin needs no archive download")
        try check(state["phase"] as? String == "review" && ((state["plan"] as? [String: Any])?["issues"] as? [String])?.isEmpty == true, "approved imported pin resolves offline without changing the library")
        let (newZIP, newer) = try zip(files, name: "MirrorHelper", version: "2.0")
        let unapproved = ModLibrary(profile: root.appendingPathComponent("UnapprovedPin"), specialPins: local.specialPins)
        _ = try unapproved.importZIP(newZIP)
        let rejected = try DependencyPlanner.resolve(LibraryInventory.read(unapproved), database: db, pins: unapproved.specialPins)
        try check(!rejected.issues.isEmpty && rejected.issues.contains { $0.contains("iOS-compatible") }, "MirrorName never weakens compatibility hash pin for a manually imported newer version")
        let wrong = ModLibrary(profile: root.appendingPathComponent("WrongArchive")); _ = try wrong.importZIP(rootZIP)
        let wrongInstaller = DependencyInstaller(library: wrong, pins: [], indexProvider: { _ in db }, downloadProvider: { _, target, _, _, _, _ in try fm.copyItem(at: newZIP, to: target) })
        let wrongBefore = try LibraryInventory.read(wrong)
        state = try wait(wrongInstaller) { wrongInstaller.resolve() }; id = try planID(state)
        state = try wait(wrongInstaller) { wrongInstaller.apply(planID: id) }
        try check(state["phase"] as? String == "failed" && (state["message"] as? String)?.contains("integrity hash") == true && (try LibraryInventory.read(wrong).revision) == wrongBefore.revision, "wrong ZIP from a successful mirror fails integrity before mod changes")
        try check(try fm.contentsOfDirectory(at: InstallJournal.cache(wrong.profile), includingPropertiesForKeys: nil).allSatisfy { $0.pathExtension != "zip" && $0.pathExtension != "part" }, "rejected mirror bytes leave neither accepted cache ZIP nor partial file")
        try check(newer.modules[0].version.text == "2.0", "wrong-version control is an actual distinct metadata ZIP")
    }
    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1]); try InstallJournal.directory(root)
        try transport(root); try metadata(); try coordinator(root)
        let result: [String: Any] = ["status": "PASS_DEPENDENCY56_MIRRORS", "checks": checks,
            "networkUsed": false, "fixtureZIPsContainExecutablePayload": false, "gameOrAdapterExecuted": false,
            "physicalDeviceTested": false]
        try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]).write(to: root.appendingPathComponent("results.json"))
        print("PASS_DEPENDENCY56_MIRRORS", checks.count)
    }
}
