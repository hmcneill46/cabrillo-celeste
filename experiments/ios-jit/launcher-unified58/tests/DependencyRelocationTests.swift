import Foundation
import ZIPFoundation

@main struct DependencyRelocationTests {
    static let fm = FileManager.default
    static var checks = [String]()
    static func check(_ yes: @autoclosure () throws -> Bool, _ name: String) throws {
        guard try yes() else { throw LibraryError("FAILED: " + name) }; checks.append(name)
    }
    static func rejects(_ name: String, _ action: () throws -> Void) throws {
        do { try action() } catch { checks.append(name); return }; throw LibraryError("Accepted invalid control: " + name)
    }
    static func data(_ value: Any) throws -> Data { try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]) }
    static func zip(_ directory: URL, _ file: String, name: String, version: String = "1.0", dependency: String? = nil, payload: String = "A") throws -> URL {
        try InstallJournal.directory(directory)
        let path = directory.appendingPathComponent(file)
        let text = "- Name: \(name)\n  Version: \(version)\n" + (dependency.map { "  Dependencies:\n  - Name: \($0)\n    Version: 1.0\n" } ?? "")
        do {
            let archive = try Archive(url: path, accessMode: .create)
            for (name, bytes) in [("everest.yaml", Data(text.utf8)), ("fixture.bin", Data(payload.utf8))] {
                try archive.addEntry(with: name, type: .file, uncompressedSize: Int64(bytes.count), compressionMethod: .none) { offset, size in bytes.subdata(in: Int(offset)..<Int(offset) + size) }
            }
        }
        return path
    }
    static func candidate(_ file: URL, id: Int = 100, page: String? = nil) throws -> DownloadCandidate {
        let identity = try DownloadIdentity.read(file), actual = try ModLibrary.inspect(file, filename: file.lastPathComponent, digest: identity.sha256, bytes: identity.bytes)
        return DownloadCandidate(url: "https://gamebanana.com/mmdl/\(id)", bytes: identity.bytes, hashes: [], pinnedSHA256: identity.sha256, modules: actual.modules, mirrorName: String(id), gameBananaPage: page)
    }
    static func file(_ id: Int, _ bytes: UInt64, version: Any? = nil) -> [String: Any] {
        var result: [String: Any] = ["_idRow": id, "_nFilesize": bytes, "_sFile": "published.zip", "_sAvResult": "clean", "_sDownloadUrl": "https://untrusted.example/ignored"]
        if let version { result["_sVersion"] = version }; return result
    }
    static func profile(_ id: Int, current: [[String: Any]] = [], archived: [[String: Any]] = []) -> [String: Any] {
        ["_idRow": id, "_aGame": ["_idRow": 6460], "_bIsPrivate": false, "_bIsTrashed": false, "_bIsWithheld": false,
         "_sProfileUrl": "https://gamebanana.com/mods/\(id)", "_sModelName": "Mod", "_aFiles": current, "_aArchivedFiles": archived]
    }
    static func catalogue(_ id: Int, files: [Int]) -> [[String: Any]] {
        [["PageURL": "https://gamebanana.com/mods/\(id)", "Name": "Human readable title",
          "Files": files.map { ["URL": "https://gamebanana.com/mmdl/\($0)", "Size": 1, "Name": "archive.zip", "HasEverestYaml": true, "IsLatestVersion": true] as [String: Any] }]]
    }
    static func wait(_ installer: DependencyInstaller, _ events: inout [[String: Any]], _ action: () -> Void) throws -> [String: Any] {
        var terminal: [String: Any]?, received = [[String: Any]]()
        installer.update = { received.append($0); if $0["active"] as? Bool == false { terminal = $0 } }
        action(); let deadline = Date().addingTimeInterval(30)
        while terminal == nil && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.01)) }
        events += received
        guard let terminal else { throw LibraryError("Relocation fixture timed out") }; return terminal
    }
    static func planID(_ state: [String: Any]) throws -> String {
        guard let plan = state["plan"] as? [String: Any], plan["canApply"] as? Bool == true, let id = plan["id"] as? String else { throw LibraryError("Expected applicable fixture plan: \(state)") }; return id
    }
    static func snapshot(_ library: ModLibrary) throws -> [String: String] {
        var result = [String: String]()
        for folder in ["Mods", "Saves"] {
            guard let files = fm.enumerator(at: library.profile.appendingPathComponent(folder), includingPropertiesForKeys: [.isRegularFileKey]) else { continue }
            for case let path as URL in files {
                if try path.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile == true { result[String(path.path.dropFirst(library.profile.path.count))] = digestData(try Data(contentsOf: path)) }
            }
        }
        result["choices"] = digestData(try canonicalData(library.state())); return result
    }
    static func metadataControls(_ source: DownloadCandidate) throws {
        let page = URL(string: "https://gamebanana.com/mods/500")!
        let good = file(201, source.bytes, version: "v1.0"), raw = profile(500, archived: [good])
        try check(try ArchiveRelocation.archiveURLs(data(raw), page: page, source: source).map(\.absoluteString) == ["https://gamebanana.com/mmdl/201"], "archived file creates canonicalID request, ignoring advertised URL")
        let labelled = [file(202, source.bytes, version: "special compatible edition"), file(203, source.bytes, version: NSNull()), file(204, source.bytes)]
        try check(try ArchiveRelocation.archiveURLs(data(profile(500, archived: labelled)), page: page, source: source).count == 3, "freeform, null and missing version labels remain eligible for exact hash verification")
        try check(try ArchiveRelocation.archiveURLs(data(profile(500, current: [file(205, source.bytes, version: "v2.0")])), page: page, source: source).isEmpty, "parseable newer presentation version is never substituted")
        var variants = [[String: Any]]()
        var wrong = raw; wrong["_idRow"] = 501; variants.append(wrong)
        wrong = raw; wrong["_aGame"] = ["_idRow": 1]; variants.append(wrong)
        for flag in ["_bIsPrivate", "_bIsTrashed", "_bIsWithheld"] { wrong = raw; wrong[flag] = true; variants.append(wrong) }
        wrong = raw; wrong["_sProfileUrl"] = "https://gamebanana.com/mods/501"; variants.append(wrong)
        wrong = raw; wrong["_sProfileUrl"] = 500; variants.append(wrong)
        wrong = raw; wrong["_sModelName"] = "Tool"; variants.append(wrong)
        wrong = raw; wrong["_aArchivedFiles"] = Array(repeating: good, count: 129); variants.append(wrong)
        wrong = raw; wrong["_aArchivedFiles"] = "not an array"; variants.append(wrong)
        for (index, row) in variants.enumerated() { try rejects("unrelated/private/malformed page rejected, case\(index)") { _ = try ArchiveRelocation.archiveURLs(data(row), page: page, source: source) } }
        for text in ["https://evil.example/mods/500", "https://gamebanana.com:443/mods/500", "https://gamebanana.com/mods/500?x=y", "https://gamebanana.com/mods/%35%30%30", "http://gamebanana.com/mods/500"] {
            try check(ArchiveRelocation.canonicalPage(text) == nil, "unsafe explicit page is not a discovery anchor: " + text)
        }
        let filtered: [[String: Any]] = [file(0, source.bytes), file(206, source.bytes + 1), ["_idRow": true, "_nFilesize": source.bytes, "_sFile": "file.zip"], ["_idRow": 207, "_nFilesize": source.bytes, "_sFile": "file.exe"], ["_idRow": 208, "_nFilesize": source.bytes, "_sFile": "file.zip", "_sAvResult": "INFECTED"]]
        try check(try ArchiveRelocation.archiveURLs(data(profile(500, archived: filtered)), page: page, source: source).isEmpty, "invalidIDs, wrong sizes, nonZIPs and infected files are excluded")
        try check(try ArchiveRelocation.archiveURLs(data(profile(500, current: [good], archived: [good])), page: page, source: source).count == 1, "duplicate fileIDs are considered once")
        let matching = try data(catalogue(500, files: [900]))
        try check(try ArchiveRelocation.anchoredPages(matching, indexedFileIDs: ["900"]).map(\.absoluteString) == [page.absoluteString], "discovery requires exact latest indexed fileID")
        try check(try ArchiveRelocation.anchoredPages(matching, indexedFileIDs: ["901"]).isEmpty, "matching title without indexed fileID is never authority")
        var names = source; names.modules = ["GravityHelper", "CollabUtils2", "ThirdHelper3", "FourthHelper"].map { ModMetadata(name: $0, version: source.modules[0].version, dll: nil, dependencies: [], optionalDependencies: []) }
        let queries = ArchiveRelocation.queries(names)
        try check(queries.count <= 6 && queries.contains("Collab Utils 2") && queries.contains("Gravity Helper"), "search uses bounded raw and CamelCase/letter-digit spaced variants")
        var changed = source; changed.gameBananaPage = page.absoluteString
        try check(changed.key == source.key && (try JSONDecoder().decode(DownloadCandidate.self, from: canonicalData(changed))).gameBananaPage == page.absoluteString, "page metadata survives serialization without changing content cachekey")
    }
    static func coordinator(_ root: URL, name: String, discovered: Bool, cancel: Bool = false, wrongPage: Bool = false, wrongOnly: Bool = false, invalidAnchor: Bool = false, offline: Bool = false, overflow: Bool = false, cancelArchive: Bool = false) throws {
        let files = root.appendingPathComponent("fixtures")
        let goodZIP = try zip(files, "approved.zip", name: name), badZIP = try zip(files, "wrong.zip", name: name, payload: "B")
        let good = try candidate(goodZIP, page: discovered ? nil : invalidAnchor ? "https://evil.example/mods/500" : "https://gamebanana.com/mods/500")
        let bad = try DownloadIdentity.read(badZIP)
        try check(bad.bytes == good.bytes && bad.sha256 != good.pinnedSHA256, name + ": wronghash control has the exact reviewed length")
        let rootZIP = try zip(files, "root.zip", name: "FixtureRoot", dependency: name)
        let library = ModLibrary(profile: root.appendingPathComponent("Profile"), specialPins: [name: good.pinnedSHA256!]); _ = try library.importZIP(rootZIP)
        try InstallJournal.directory(library.profile.appendingPathComponent("Saves")); try Data("original saves".utf8).write(to: library.profile.appendingPathComponent("Saves/unknown.bin"))
        let before = try snapshot(library)
        var db = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), allowEmpty: true)
        db.byName[name] = good
        db.indexedByName[name] = DownloadCandidate(url: "https://gamebanana.com/mmdl/900", bytes: good.bytes, hashes: [], pinnedSHA256: nil, modules: good.modules)
        var attempts = [String](), metadata = [String]()
        let installer = DependencyInstaller(library: library, pins: [], indexProvider: { _ in db }, metadataProvider: { url, token in
            metadata.append(url.absoluteString)
            if offline { throw URLError(.notConnectedToInternet) }
            if cancel { token.cancel(); throw LibraryError("cancelled discovery") }
            if url.host == "maddie480.ovh" {
                let q = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems?.first?.value ?? ""
                return try data(q == name ? [] : catalogue(500, files: [900]))
            }
            return try data(profile(wrongPage ? 501 : 500, archived: overflow ? (200...208).map { file($0, good.bytes) } : [file(200, good.bytes), file(201, good.bytes, version: "v1.0")]))
        }, archiveProvider: { address, destination, _, _, token, _ in
            attempts.append(address)
            let endpoint = URL(string: address)!, id = endpoint.deletingPathExtension().lastPathComponent
            if cancelArchive && id == "200" { try Data("partial cancelled reupload".utf8).write(to: destination); token.cancel(); throw LibraryError("cancelled archive") }
            if let n = Int(id), (200...208).contains(n) { try fm.copyItem(at: (overflow ? n == 208 : n == 201) && !wrongOnly ? goodZIP : badZIP, to: destination) }
            else { throw LibraryError("HTTP 404") }
        })
        var events = [[String: Any]](), state = try wait(installer, &events) { installer.resolve() }, id = try planID(state)
        state = try wait(installer, &events) { installer.apply(planID: id) }
        if cancel || wrongPage || wrongOnly || invalidAnchor || offline || overflow || cancelArchive {
            try check(state["phase"] as? String == (cancel || cancelArchive ? "cancelled" : "failed"), name + ": unsafe/unavailable recovery fails or cancels")
            try check(try snapshot(library) == before, name + ": failed recovery retains original ZIP, choices and saves")
            try check(try fm.contentsOfDirectory(at: InstallJournal.cache(library.profile), includingPropertiesForKeys: nil).allSatisfy { $0.pathExtension != "zip" && $0.pathExtension != "part" }, name + ": failed recovery leaves no unverified ZIP or partial")
            if invalidAnchor { try check(metadata.isEmpty, name + ": malformed explicit page never triggers search fallback") }
            if wrongPage { try check(!attempts.contains { $0.contains("/200") || $0.contains("/201") }, name + ": unrelated profile never authorizes archive requests") }
            if wrongOnly { try check((state["message"] as? String)?.contains("exact reviewed archive") == true, name + ": final failure explains requested exact version instead of indefinite retry") }
            if overflow { try check(!attempts.contains { $0.contains("/208") }, name + ": recovery stops before a ninth metadata candidate") }
            if cancelArchive { try check(attempts.last == "https://gamebanana.com/mmdl/200", name + ": cancelling a relocated download stops all remaining mirrors and candidates") }
            return
        }
        try check(state["phase"] as? String == "complete", name + ": moved archive installs through verified page recovery")
        try check(attempts.contains("https://gamebanana.com/mmdl/200") && attempts.contains("https://celestemodupdater.0x0a.de/banana-mirror/200.zip") && attempts.contains("https://gamebanana.com/mmdl/201"), name + ": wronghash200 continues through mirrors and then next candidate")
        try check(events.contains { $0["resolvedURL"] as? String == "https://gamebanana.com/mmdl/201" && $0["sourceURL"] as? String == good.url && $0["requestedArchiveKey"] as? String == good.key }, name + ": diagnostics bind resolved transport to original reviewed identity")
        try check(events.filter { $0["phase"] as? String == "verified" && $0["sourceURL"] as? String == good.url }.count == 1, name + ": one verified event is recorded per completed archive")
        let installed = try LibraryInventory.read(library).archives.first { $0.modules.contains { $0.name == name } }!
        let cached = library.mods.appendingPathComponent(installed.filename)
        let retained = try JSONDecoder().decode(VerifiedDownload.self, from: Data(contentsOf: InstallJournal.cache(library.profile).appendingPathComponent(good.key + ".json")))
        try check(good.accepts(DownloadIdentity.read(cached)) && retained.source.key == good.key, name + ": committed relocated bytes retain original candidate cachekey and integrity receipt")
        try check(try Data(contentsOf: library.profile.appendingPathComponent("Saves/unknown.bin")) == Data("original saves".utf8), name + ": successful recovery preserves unknown save bytes")
        if discovered { try check(metadata.contains { $0.contains("gamebanana-search") } && metadata.count <= 7, name + ": unanchored module uses bounded current-index anchored discovery") }
        let reused = ModLibrary(profile: root.appendingPathComponent("OfflineProfile"), specialPins: library.specialPins); _ = try reused.importZIP(rootZIP)
        try InstallJournal.directory(InstallJournal.cache(reused.profile)); try fm.copyItem(at: cached, to: InstallJournal.cache(reused.profile).appendingPathComponent(good.key + ".zip"))
        let reuser = DependencyInstaller(library: reused, pins: [], indexProvider: { _ in db }, metadataProvider: { _, _ in throw LibraryError("cache must not rediscover") }, archiveProvider: { _, _, _, _, _, _ in throw LibraryError("cache must not redownload") })
        state = try wait(reuser, &events) { reuser.resolve() }; id = try planID(state)
        state = try wait(reuser, &events) { reuser.apply(planID: id) }
        try check(state["phase"] as? String == "complete", name + ": verified relocated cache completes another install offline")
    }
    static func ordinaryMirrors(_ root: URL, wrongHash: Bool) throws {
        let name = "OrdinaryHelper", files = root.appendingPathComponent("fixtures")
        let good = try zip(files, "good.zip", name: name), bad = try zip(files, "bad.zip", name: name, payload: "B")
        let source = try candidate(good), rootZIP = try zip(files, "root.zip", name: "Root", dependency: name)
        let library = ModLibrary(profile: root.appendingPathComponent("Profile")); _ = try library.importZIP(rootZIP)
        var db = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), allowEmpty: true); db.byName[name] = source
        var attempts = [String](), metadataRequests = 0
        let installer = DependencyInstaller(library: library, pins: [], indexProvider: { _ in db }, metadataProvider: { _, _ in metadataRequests += 1; throw LibraryError("ordinary mirror must complete first") }, archiveProvider: { url, target, _, _, _, _ in
            attempts.append(url)
            if attempts.count == 1 { try Data("<html>HTTP200 error page</html>".utf8).write(to: target) }
            else if attempts.count == 2 {
                if wrongHash { try fm.copyItem(at: bad, to: target) }
                else { try Data(repeating: 0, count: Int(source.bytes) + 1).write(to: target) }
            } else { try fm.copyItem(at: good, to: target) }
        })
        var events = [[String: Any]](), state = try wait(installer, &events) { installer.resolve() }, id = try planID(state)
        state = try wait(installer, &events) { installer.apply(planID: id) }
        try check(state["phase"] as? String == "complete" && attempts.count == 3 && metadataRequests == 0, wrongHash ? "HTTP200HTML and same-size wronghash continue to the next ordinary mirror" : "HTTP200HTML and wrong-size bodies continue to the next ordinary mirror")
        try check(events.contains { ($0["resolvedURL"] as? String)?.contains("celestemodupdater.0x0a.de") == true }, "ordinary successful mirror is recorded after original source verification")
    }
    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1]); try InstallJournal.directory(root)
        let fixture = try zip(root.appendingPathComponent("metadata"), "sample.zip", name: "OtherHelper")
        try metadataControls(candidate(fixture))
        try coordinator(root.appendingPathComponent("explicit"), name: "UnrelatedHelper", discovered: false)
        try coordinator(root.appendingPathComponent("discovered"), name: "DifferentHelper", discovered: true)
        try coordinator(root.appendingPathComponent("cancelled"), name: "CancelledHelper", discovered: false, cancel: true)
        try coordinator(root.appendingPathComponent("unrelated"), name: "UnsafeHelper", discovered: false, wrongPage: true)
        try coordinator(root.appendingPathComponent("wronghash"), name: "WrongHashHelper", discovered: false, wrongOnly: true)
        try coordinator(root.appendingPathComponent("invalid"), name: "BadAnchorHelper", discovered: false, invalidAnchor: true)
        try coordinator(root.appendingPathComponent("offline"), name: "OfflineHelper", discovered: false, offline: true)
        try coordinator(root.appendingPathComponent("bounded"), name: "BoundedHelper", discovered: false, overflow: true)
        try coordinator(root.appendingPathComponent("cancel-archive"), name: "CancelledArchiveHelper", discovered: false, cancelArchive: true)
        try ordinaryMirrors(root.appendingPathComponent("html-size"), wrongHash: false)
        try ordinaryMirrors(root.appendingPathComponent("html-hash"), wrongHash: true)
        let result: [String: Any] = ["status": "PASS_DEPENDENCY56_RELOCATION", "checks": checks, "networkUsed": false,
            "gameOrAdapterExecuted": false, "fixtureZIPsContainExecutablePayload": false, "physicalDeviceTested": false]
        try data(result).write(to: root.appendingPathComponent("results.json")); print("PASS_DEPENDENCY56_RELOCATION", checks.count)
    }
}
