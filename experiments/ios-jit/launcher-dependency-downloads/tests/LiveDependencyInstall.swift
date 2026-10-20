import Foundation
import Darwin
import ZIPFoundation

// Host-only integration of the production resolver/installer and real HTTPS
// transport. No game, mod DLL, Mono runtime, signing or device operation runs.
@main struct LiveDependencyInstall {
    static var checks: [String] = []
    static let femtoSHA = "5a845805bae30490ed7c9da84410fbe672628b8fe927a830f5f2eb148eb88419"
    static func check(_ condition: @autoclosure () throws -> Bool, _ label: String) throws {
        guard try condition() else { throw LibraryError("Live integration check failed: " + label) }
        checks.append(label)
    }
    static func json(_ value: Any, to file: URL) throws {
        try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .prettyPrinted]).write(to: file, options: .atomic)
    }
    static func encoded<T: Encodable>(_ value: T) throws -> Any {
        try JSONSerialization.jsonObject(with: canonicalData(value))
    }
    static func database(_ profile: URL, pins: [DownloadCandidate], earlier: [DownloadCandidate]) throws -> DependencyDatabase {
        let root = profile.appendingPathComponent("LauncherIndex")
        let generation = try String(contentsOf: root.appendingPathComponent("current.txt"), encoding: .utf8)
        guard UUID(uuidString: generation) != nil else { throw LibraryError("Invalid captured live index generation") }
        let folder = root.appendingPathComponent(generation)
        let receipt = try JSONDecoder().decode([String: String].self, from: Data(contentsOf: folder.appendingPathComponent("receipt.json")))
        let updates = try Data(contentsOf: folder.appendingPathComponent("updates.yaml"))
        let graph = try Data(contentsOf: folder.appendingPathComponent("graph.yaml"))
        try check(digestData(updates) == receipt["updatesSHA256"] && digestData(graph) == receipt["graphSHA256"], "captured live index and graph match production provenance")
        return try DependencyDatabase(updates: updates, graph: graph, provenance: receipt, pins: pins, earlier: earlier)
    }
    static func sentinels(_ profile: URL) throws -> [String: Data] {
        let values = ["Saves/LiveSyntheticSave.bin": Data("synthetic host save sentinel; not Celeste game data".utf8),
                      "Unknown/live-future-data.bin": Data("retain arbitrary unknown profile bytes".utf8)]
        for (name, bytes) in values {
            let file = profile.appendingPathComponent(name)
            try InstallJournal.directory(file.deletingLastPathComponent())
            try bytes.write(to: file)
        }
        return values
    }
    static func preserved(_ profile: URL, _ values: [String: Data]) throws {
        for (name, bytes) in values {
            try check(Data(contentsOf: profile.appendingPathComponent(name)) == bytes, "synthetic profile sentinel preserved: " + name)
        }
    }
    static func modules(_ rows: [ModMetadata]) -> [ModMetadata] {
        rows.map { ModMetadata(name: $0.name, version: $0.version, dll: nil,
            dependencies: $0.dependencies.sorted { $0.name < $1.name },
            optionalDependencies: $0.optionalDependencies.sorted { $0.name < $1.name }) }.sorted { $0.name < $1.name }
    }
    static func verifiedRecords(_ library: ModLibrary) throws -> [VerifiedDownload] {
        let cache = InstallJournal.cache(library.profile)
        let records = try FileManager.default.contentsOfDirectory(at: cache, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }.map { try JSONDecoder().decode(VerifiedDownload.self, from: Data(contentsOf: $0)) }.sorted { $0.source.key < $1.source.key }
        for record in records {
            let staged = cache.appendingPathComponent(record.source.key + ".zip")
            let file = FileManager.default.fileExists(atPath: staged.path) ? staged : library.mods.appendingPathComponent(record.archive.filename)
            let identity = try DownloadIdentity.read(file)
            let inspected = try ModLibrary.inspect(file, filename: record.archive.filename, digest: identity.sha256, bytes: identity.bytes)
            try check(record.source.accepts(identity) && identity.sha256 == record.identity.sha256 && identity.xxHash == record.identity.xxHash,
                      "full-byte SHA/xxHash re-verification: " + record.source.title)
            try check(canonicalData(modules(inspected.modules)) == canonicalData(record.source.modules),
                      "ZIP metadata matches verified requirements: " + record.source.title)
        }
        return records
    }
    static func relocation(_ folder: URL, source: URL, timeout: TimeInterval) throws {
        try InstallJournal.directory(folder)
        let rows = try JSONSerialization.jsonObject(with: Data(contentsOf: source.appendingPathComponent("CompatibilityDownloads.json"))) as! [[String: Any]]
        guard var row = rows.first(where: { ($0["modules"] as? [[String: Any]])?.contains { $0["name"] as? String == "FemtoHelper" } == true }) else {
            throw LibraryError("Missing current production Femto compatibility candidate")
        }
        row["url"] = "https://gamebanana.com/mmdl/1776026"
        row["mirrorName"] = "1776026"
        row["gameBananaPage"] = "https://gamebanana.com/mods/53722"
        let stale = try JSONDecoder().decode(DownloadCandidate.self, from: JSONSerialization.data(withJSONObject: row))
        try check(stale.pinnedSHA256 == femtoSHA && stale.bytes == 11_103_153, "real relocation control preserves the exact original Femto version/size/hash")
        let library = ModLibrary(profile: folder.appendingPathComponent("Profile"), specialPins: ["FemtoHelper": femtoSHA])
        let sentinel = try sentinels(library.profile)
        let rootZIP = folder.appendingPathComponent("LiveRelocationRoot.zip")
        let metadata = Data("- Name: LiveRelocationRoot\n  Version: 1.0.0\n  Dependencies:\n    - Name: FemtoHelper\n      Version: 1.15.22\n".utf8)
        do {
            let archive = try Archive(url: rootZIP, accessMode: .create)
            try archive.addEntry(with: "everest.yaml", type: .file, uncompressedSize: Int64(metadata.count), compressionMethod: .deflate) { offset, size in
                metadata.subdata(in: Int(offset)..<Int(offset) + size)
            }
        }
        let original = try library.importZIP(rootZIP)
        let installer = DependencyInstaller(library: library, pins: [stale])
        var events: [[String: Any]] = []
        func wait(_ action: () -> Void) throws -> [String: Any] {
            var terminal: [String: Any]?
            installer.update = { state in
                if state["phase"] as? String != "downloading" || state["retryURL"] != nil {
                    events.append(state); try? json(events, to: folder.appendingPathComponent("events.json"))
                }
                if state["retryURL"] != nil { print("RELOCATION ATTEMPT", state["retryURL"] ?? ""); fflush(stdout) }
                if state["active"] as? Bool == false { terminal = state }
            }
            action()
            let deadline = Date().addingTimeInterval(timeout)
            while terminal == nil && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
            guard let state = terminal else { installer.cancel(); throw LibraryError("Real old-Femto relocation timed out") }
            if state["phase"] as? String == "failed" || state["phase"] as? String == "cancelled" {
                try json(state, to: folder.appendingPathComponent("failure-state.json"))
                throw LibraryError(state["message"] as? String ?? "Real old-Femto relocation failed")
            }
            return state
        }
        print("START real stale Femto1776026 relocation"); fflush(stdout)
        var state = try wait { installer.resolve() }
        for _ in 0..<4 {
            guard let plan = state["plan"] as? [String: Any], plan["canApply"] as? Bool == true,
                  let id = plan["id"] as? String, let downloads = plan["downloads"] as? [[String: Any]],
                  downloads.count == 1, downloads[0]["key"] as? String == stale.key else {
                throw LibraryError("Old-Femto control must review exactly its original one stale pinned candidate")
            }
            try check(LibraryInventory.read(library).archives.count == 1, "relocation review leaves the synthetic root unchanged and installation pending")
            try preserved(library.profile, sentinel)
            state = try wait { installer.apply(planID: id) }
            if state["phase"] as? String == "complete" { break }
            try check(state["phase"] as? String == "review" && state["revised"] as? Bool == true, "relocated archive metadata receives an explicit compatible re-review")
        }
        try check(state["phase"] as? String == "complete", "real stale1776026 archive automatically relocates and installs")
        let records = try verifiedRecords(library)
        guard records.count == 1, let downloaded = records.first else { throw LibraryError("Expected exactly one real relocated archive") }
        try check(downloaded.source.key == stale.key && downloaded.source.url == stale.url,
                  "relocation preserves the reviewed source and cache identity")
        try check(downloaded.identity.sha256 == femtoSHA && downloaded.identity.bytes == 11_103_153
                  && downloaded.archive.modules.contains { $0.name == "FemtoHelper" && $0.version.text == "1.15.22" },
                  "relocated actual ZIP matches original SHA/size/version and full metadata")
        let after = try LibraryInventory.read(library)
        try check(after.archives.count == 2 && after.archives.contains { $0.filename == original.filename && $0.digest == original.digest },
                  "relocation installs only Femto and preserves the original synthetic root")
        try preserved(library.profile, sentinel)
        let recoveredURL = "https://gamebanana.com/mmdl/1838255"
        try check(events.contains { $0["phase"] as? String == "verified" && $0["resolvedURL"] as? String == recoveredURL
                  && $0["requestedArchiveKey"] as? String == stale.key && $0["verifiedSHA256"] as? String == femtoSHA },
                  "production verified event binds actual recovered1838255 transport to original key and exact SHA")
        let report = try InstallReport.read(library.profile)
        try check(report.outcome == "completed" && report.applicationState == "applied", "relocation produces a completed production transaction report")
        try json(["status": "PASS_REAL_BUILD56_STALE_FEMTO_RELOCATION", "checks": checks,
                  "originalSource": try encoded(stale), "verifiedDownload": try encoded(downloaded),
                  "installationReport": report.json, "journal": InstallJournal.diagnostics(profile: library.profile),
                  "canonicalPage": "https://gamebanana.com/mods/53722", "recoveredFileID": "1838255",
                  "verifiedResolvedURL": recoveredURL,
                  "realProductionFoundationTransport": true, "providerOverrides": false,
                  "syntheticMetadataRootOnly": true, "gameOrModDLLExecuted": false,
                  "physicalDeviceTested": false], to: folder.appendingPathComponent("relocation-result.json"))
        print("PASS_REAL_BUILD56_STALE_FEMTO_RELOCATION"); fflush(stdout)
    }
    static func run(_ folder: URL, source: URL, earlierFile: URL, timeout: TimeInterval) throws {
        try InstallJournal.directory(folder)
        let pins = try JSONDecoder().decode([DownloadCandidate].self, from: Data(contentsOf: source.appendingPathComponent("CompatibilityDownloads.json")))
        let earlier = try JSONDecoder().decode([DownloadCandidate].self, from: Data(contentsOf: earlierFile))
        let special = Dictionary(uniqueKeysWithValues: pins.flatMap { p in p.modules.map { ($0.name, p.pinnedSHA256!) } })
        try check(RuntimeIdentity.builtins["Everest"] == "1.6642.0" && RuntimeIdentity.builtins["EverestCore"] == "1.6642.0", "production runtime planner is stable1.6642")
        guard let femto = pins.first(where: { $0.modules.contains { $0.name == "FemtoHelper" } }) else { throw LibraryError("Missing production Femto pin") }
        try check(femto.url == "https://gamebanana.com/mmdl/1838255" && femto.pinnedSHA256 == femtoSHA && femto.bytes == 11_103_153,
                  "production Femto1.15.22 uses the byte-identical1838255 reupload")
        let library = ModLibrary(profile: folder.appendingPathComponent("Profile"), specialPins: special)
        let sentinel = try sentinels(library.profile)
        let before = try LibraryInventory.read(library)
        try check(before.archives.isEmpty && before.disabled.isEmpty, "live isolated profile starts without mods")
        // Defaults exercise production URLSession, index pointer fallback, mirrors,
        // hash/ZIP metadata checks, re-review, reports and journal commit.
        let installer = DependencyInstaller(library: library, pins: pins, earlier: earlier)
        var history: [[String: Any]] = [], lastPhase = ""
        var reviews: [[String: Any]] = []
        func wait(_ engine: DependencyInstaller, _ label: String, action: () -> Void) throws -> [String: Any] {
            var terminal: [String: Any]?
            engine.update = { state in
                let phase = state["phase"] as? String ?? ""
                if phase != lastPhase || phase == "verified" || phase == "review" || state["retryURL"] != nil {
                    history.append(state); lastPhase = phase
                    try? json(history, to: folder.appendingPathComponent("events.json"))
                }
                if phase == "verified" {
                    print("VERIFIED", state["message"] ?? "", state["completedFiles"] ?? "", "/", state["totalFiles"] ?? ""); fflush(stdout)
                }
                if state["retryURL"] != nil { print("MIRROR", state["retryURL"] ?? ""); fflush(stdout) }
                if state["active"] as? Bool == false { terminal = state }
            }
            print("START", label); fflush(stdout)
            action()
            let deadline = Date().addingTimeInterval(timeout)
            while terminal == nil && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
            guard let state = terminal else { engine.cancel(); throw LibraryError("Timed out during " + label) }
            if ["failed", "cancelled"].contains(state["phase"] as? String ?? "") {
                try json(state, to: folder.appendingPathComponent("failure-state.json"))
                throw LibraryError(state["message"] as? String ?? "Live installation failed")
            }
            return state
        }
        _ = try wait(installer, "fresh production index/graph") { installer.checkUpdates() }
        let firstDatabase = try database(library.profile, pins: pins, earlier: earlier)
        guard let strawberry = firstDatabase.indexedByName["StrawberryJam2021"], let id = CatalogueSafety.fileID(strawberry.url) else {
            throw LibraryError("Current official index lacks an unambiguous StrawberryJam2021 download")
        }
        let selection = CatalogueSelection(pageURL: "https://gamebanana.com/mods/424541", fileIDs: [id])
        var state = try wait(installer, "live Strawberry Jam catalogue review") { installer.planCatalogue(selection) }
        let db = try database(library.profile, pins: pins, earlier: earlier)
        let sources = try selection.candidates(in: db)
        try check(sources.count == 1 && sources[0].modules.contains { $0.name == "StrawberryJam2021" }, "explicit root file is the live indexed Strawberry Jam module")
        let independentPlan = try DependencyPlanner.resolve(before, database: db, pins: special, installs: sources)
        try check(independentPlan.issues.isEmpty, "fresh snapshot produces a compatible dependency plan")
        guard let initialJSON = state["plan"] as? [String: Any], let initialDownloads = initialJSON["downloads"] as? [[String: Any]] else {
            throw LibraryError("Production installer did not expose its reviewed plan")
        }
        try check(Set(initialDownloads.compactMap { $0["key"] as? String }) == Set(independentPlan.downloads.map(\.key)), "installer review exactly matches independently resolved captured snapshot")
        try check(independentPlan.downloads.contains { $0.key == femto.key }, "live Strawberry Jam plan selects the corrected exact Femto pin")
        try json(["plan": independentPlan.json, "index": db.provenance, "root": try encoded(sources),
                  "historicalExpectedDownloadCount": 52, "actualInitialDownloadCount": initialDownloads.count], to: folder.appendingPathComponent("initial-plan.json"))
        print("PLAN", initialDownloads.count, "files", independentPlan.totalBytes, "bytes"); fflush(stdout)
        for number in 0..<8 {
            guard let plan = state["plan"] as? [String: Any], plan["canApply"] as? Bool == true,
                  let planID = plan["id"] as? String, let issues = plan["issues"] as? [String], issues.isEmpty else {
                throw LibraryError("Live reviewed plan is blocked: \(state)")
            }
            try check(LibraryInventory.read(library).archives.isEmpty, "review\(number) leaves all mod installation pending")
            try preserved(library.profile, sentinel)
            _ = try verifiedRecords(library)
            reviews.append(plan)
            try json(reviews, to: folder.appendingPathComponent("accepted-host-reviews.json"))
            state = try wait(installer, "download/verify/review/apply\(number)") { installer.apply(planID: planID) }
            if state["phase"] as? String == "complete" { break }
            try check(state["phase"] as? String == "review" && state["revised"] as? Bool == true, "changed ZIP requirements require a new explicit host review")
            try check(LibraryInventory.read(library).archives.isEmpty, "revised ZIP metadata review commits no partial selection")
        }
        try check(state["phase"] as? String == "complete", "bounded actual-ZIP review sequence converges and commits")
        let after = try LibraryInventory.read(library)
        let report = try InstallReport.read(library.profile)
        let finalReviewedDownloads = reviews.last?["downloads"] as? [[String: Any]] ?? []
        try check(after.archives.count == finalReviewedDownloads.count && after.disabled.isEmpty, "final selection contains exactly the final reviewed download set")
        try check(report.outcome == "completed" && report.applicationState == "applied" && report.commitStarted
                  && report.downloads.allSatisfy { $0.status == "installed" }, "persisted production report records the completed atomic transaction")
        try preserved(library.profile, sentinel)
        let cache = InstallJournal.cache(library.profile)
        let records = try verifiedRecords(library)
        let installedRecords = records.filter { record in after.archives.contains { $0.digest == record.identity.sha256 && $0.filename == record.archive.filename } }
        try check(installedRecords.count == after.archives.count, "every installed archive has a production verified-download record")
        let actualDatabase = records.reduce(into: db) { $0.replaceWithVerified($1.source) }
        let final = try DependencyPlanner.resolve(after, database: actualDatabase, pins: special)
        try check(final.issues.isEmpty && final.downloads.isEmpty && final.enable.isEmpty && final.disable.isEmpty, "actual ZIP metadata resolves without missing downloads or changes")
        let runnable = try library.snapshot(force: true, prepare: true)
        try check(runnable["canRun"] as? Bool == true, "production library preflight accepts the installed selection")
        try json(try encoded(records), to: folder.appendingPathComponent("downloaded-archives.json"))
        // A second isolated profile rechecks every real downloaded ZIP through the
        // production cache validator. Providers explicitly prohibit network here.
        let warm = ModLibrary(profile: folder.appendingPathComponent("WarmProfile"), specialPins: special)
        let warmSentinel = try sentinels(warm.profile)
        _ = try LibraryInventory.read(warm)
        try InstallJournal.directory(InstallJournal.cache(warm.profile))
        for record in records {
            let staged = cache.appendingPathComponent(record.source.key + ".zip")
            let file = FileManager.default.fileExists(atPath: staged.path) ? staged : library.mods.appendingPathComponent(record.archive.filename)
            try FileManager.default.copyItem(at: file,
                to: InstallJournal.cache(warm.profile).appendingPathComponent(record.source.key + ".zip"))
        }
        var offlineDownloadAttempts = 0
        let offline = DependencyInstaller(library: warm, pins: pins, earlier: earlier, indexProvider: { _ in db },
            downloadProvider: { _, _, _, _, _, _ in offlineDownloadAttempts += 1; throw LibraryError("Verified-cache control must not download") })
        var warmState = try wait(offline, "cached real ZIP dependency review") { offline.planCatalogue(selection) }
        for number in 0..<8 {
            guard let plan = warmState["plan"] as? [String: Any], plan["canApply"] as? Bool == true, let planID = plan["id"] as? String else {
                throw LibraryError("Verified-cache review blocked")
            }
            warmState = try wait(offline, "cached real ZIP apply\(number)") { offline.apply(planID: planID) }
            if warmState["phase"] as? String == "complete" { break }
        }
        try check(warmState["phase"] as? String == "complete" && offlineDownloadAttempts == 0, "all real verified ZIPs install from cache with zero download attempts")
        let warmAfter = try LibraryInventory.read(warm)
        try check(Set(warmAfter.archives.map(\.digest)) == Set(after.archives.map(\.digest)), "warm-cache installation exactly preserves the live installed ZIP identities")
        try preserved(warm.profile, warmSentinel)
        let result: [String: Any] = ["status": "PASS_LIVE_BUILD56_STRAWBERRY_JAM_DEPENDENCY_INSTALL",
            "checks": checks, "runtime": RuntimeIdentity.builtins, "index": db.provenance,
            "rootSelection": try encoded(selection), "initialDownloadCount": initialDownloads.count,
            "historicalExpectedDownloadCount": 52, "actualInstalledArchiveCount": after.archives.count,
            "verifiedDownloadedArchiveCount": records.count, "unusedVerifiedCacheCount": records.count - installedRecords.count,
            "totalDownloadedBytes": records.reduce(UInt64(0)) { $0 + $1.identity.bytes },
            "acceptedHostReviews": reviews.count, "allArchivesRehashedAndMetadataReinspected": true,
            "installedArchiveEvidence": "downloaded-archives.json", "finalPlan": final.json,
            "libraryPreflight": runnable, "installationReport": report.json,
            "journal": InstallJournal.diagnostics(profile: library.profile),
            "femtoCorrectedPinVerified": true, "syntheticSaveAndUnknownDataPreserved": true,
            "cacheReuseDownloadAttempts": offlineDownloadAttempts, "sameWarmArchiveIdentities": true,
            "freshNetworkArchiveVerifications": history.filter { $0["phase"] as? String == "verifying" }.count,
            "livePositiveUsesProductionFoundationTransport": true, "livePositiveUsesProviderOverrides": false,
            "warmControlUsesCapturedLiveIndexAndRejectingTransport": true,
            "gameOrModDLLExecuted": false, "iosJITExecuted": false, "physicalDeviceTested": false]
        try json(result, to: folder.appendingPathComponent("result.json"))
        print("PASS_LIVE_BUILD56_STRAWBERRY_JAM_DEPENDENCY_INSTALL", after.archives.count, "archives", checks.count, "checks"); fflush(stdout)
    }
    static func main() throws {
        let arguments = CommandLine.arguments
        guard arguments.count == 5 || (arguments.count == 6 && arguments[5] == "--relocation-only") else {
            throw LibraryError("Expected fresh result directory, production manifest directory, earlier-release manifest and timeout seconds")
        }
        let root = URL(fileURLWithPath: arguments[1], isDirectory: true)
        do {
            if arguments.count == 6 { try relocation(root, source: URL(fileURLWithPath: arguments[2], isDirectory: true), timeout: TimeInterval(arguments[4]) ?? 3600) }
            else { try run(root, source: URL(fileURLWithPath: arguments[2], isDirectory: true), earlierFile: URL(fileURLWithPath: arguments[3]), timeout: TimeInterval(arguments[4]) ?? 3600) }
        }
        catch {
            try? json(["status": "FAIL_LIVE_BUILD56_DEPENDENCY_INSTALL", "error": error.localizedDescription, "checks": checks,
                       "physicalDeviceTested": false], to: root.appendingPathComponent("failure.json"))
            throw error
        }
    }
}
