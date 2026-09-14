import Foundation

@main struct FreshResolutionTests {
    static func main() throws {
        let args = CommandLine.arguments, folder = URL(fileURLWithPath: args[1]), service = URL(fileURLWithPath: args[2]), source = URL(fileURLWithPath: args[3])
        let pins = try JSONDecoder().decode([DownloadCandidate].self, from: Data(contentsOf: source.appendingPathComponent("CompatibilityDownloads.json")))
        let earlier = try JSONDecoder().decode([DownloadCandidate].self, from: Data(contentsOf: source.appendingPathComponent("RuntimeCompatibleReleases.json")))
        let u = try Data(contentsOf: service.appendingPathComponent("live-updates.yaml")), g = try Data(contentsOf: service.appendingPathComponent("live-graph.yaml"))
        let provenance = ["updatesSHA256": digestData(u), "graphSHA256": digestData(g), "source": "13 September captured official index pointers"]
        let currentOnly = try DependencyDatabase(updates: u, graph: g, provenance: provenance, pins: pins)
        let database = try DependencyDatabase(updates: u, graph: g, provenance: provenance, pins: pins, earlier: earlier)
        let library = ModLibrary(profile: folder.appendingPathComponent("Profile"), specialPins: Dictionary(uniqueKeysWithValues: pins.flatMap { p in p.modules.map { ($0.name, p.pinnedSHA256!) } }))
        let original = service.appendingPathComponent("SpringCollab2020.zip")
        if !FileManager.default.fileExists(atPath: library.mods.appendingPathComponent(original.lastPathComponent).path) { _ = try library.importZIP(original) }
        let sentinel = library.profile.appendingPathComponent("unknown-mod-save.bin"), sentinelBytes = Data("preserve complete arbitrary mod data".utf8)
        if !FileManager.default.fileExists(atPath: sentinel.path) { try sentinelBytes.write(to: sentinel) }
        let before = try LibraryInventory.read(library)
        guard before.archives.count == 1 else { throw LibraryError("Fresh-install fixture must start with only the original map ZIP") }
        let baseline = try DependencyPlanner.resolve(before, database: currentOnly, pins: library.specialPins)
        guard baseline.issues.isEmpty, baseline.json["canApply"] as? Bool == true else { throw LibraryError("The upgraded runtime must accept current Spring dependencies: \(baseline.issues)") }
        let planned = try DependencyPlanner.resolve(before, database: database, pins: library.specialPins)
        guard planned.issues.isEmpty, planned.compatibilityChoices.isEmpty else { throw LibraryError("Fresh compatible resolution failed: \(planned.json)") }
        for item in earlier {
            guard !planned.downloads.contains(where: { $0.key == item.key }), planned.downloads.contains(where: { $0.modules[0].name == item.modules[0].name && $0.modules[0].version.parts.lexicographicallyPrecedes(item.modules[0].version.parts) == false }) else { throw LibraryError("Current compatible release not selected: \(item.title)") }
            let input = service.appendingPathComponent(item.modules[0].name + "-earlier.zip"), identity = try DownloadIdentity.read(input)
            let actual = try ModLibrary.inspect(input, filename: input.lastPathComponent, digest: identity.sha256, bytes: identity.bytes)
            let modules = actual.modules.map { ModMetadata(name: $0.name, version: $0.version, dll: nil, dependencies: $0.dependencies.sorted { $0.name < $1.name }, optionalDependencies: $0.optionalDependencies.sorted { $0.name < $1.name }) }
            guard item.accepts(identity), try canonicalData(modules) == canonicalData(item.modules) else { throw LibraryError("Earlier-release metadata or bytes differ") }
        }
        var history: [[String: Any]] = []
        let installer = DependencyInstaller(library: library, pins: pins, earlier: earlier, indexProvider: { _ in database })
        func wait(_ action: () -> Void) throws -> [String: Any] {
            var terminal: [String: Any]?
            installer.update = { state in
                let phase = state["phase"] as? String ?? ""
                if phase != "downloading" || state["retryURL"] != nil { history.append(state) }
                if phase == "verified" { print("VERIFIED", state["message"] ?? ""); fflush(stdout) }
                if state["active"] as? Bool == false { terminal = state }
            }
            action(); let deadline = Date().addingTimeInterval(1200)
            while terminal == nil && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
            guard let result = terminal else { throw LibraryError("Installer timed out") }
            if result["phase"] as? String == "failed" {
                try JSONSerialization.data(withJSONObject: ["result": result, "history": history], options: [.prettyPrinted, .sortedKeys]).write(to: folder.appendingPathComponent("failure-state.json"))
                throw LibraryError(result["message"] as? String ?? "Installation failed")
            }
            return result
        }
        var state = try wait { installer.resolve() }
        var evidence: [String: Any] = ["status": "PASS_FRESH_SPRING_DEPENDENCY_PLAN", "baselineWithoutEarlierReleases": baseline.json,
            "plan": planned.json, "originalSHA256": before.archives[0].digest, "index": provenance, "earlierOriginalMetadataVerified": true]
        try JSONSerialization.data(withJSONObject: evidence, options: [.prettyPrinted, .sortedKeys]).write(to: folder.appendingPathComponent("plan-result.json"))
        print("PASS_FRESH_SPRING_DEPENDENCY_PLAN", planned.downloads.count, planned.totalBytes); fflush(stdout)
        if args.contains("--install") {
            for _ in 0..<6 {
                guard let plan = state["plan"] as? [String: Any], plan["canApply"] as? Bool == true, let id = plan["id"] as? String else { throw LibraryError("Reviewed plan blocked: \(state)") }
                state = try wait { installer.apply(planID: id) }
                if state["phase"] as? String == "complete" { break }
            }
            guard state["phase"] as? String == "complete" else { throw LibraryError("Original metadata did not converge to a reviewed complete selection") }
            let after = try LibraryInventory.read(library), selection = try library.snapshot(force: true, prepare: true)
            let report = try InstallReport.read(library.profile)
            let installedNames = Set(after.archives.filter { $0.filename != before.archives[0].filename }.flatMap { $0.modules.map(\.name) })
            guard report.applicationState == "applied", report.outcome == "completed", report.changes.allSatisfy({ $0.action == "installed" && $0.enabled }), Set(report.changes.map(\.name)) == installedNames else { throw LibraryError("Dependency completion report differs from committed mod identities") }
            guard selection["canRun"] as? Bool == true, after.disabled.isEmpty,
                  after.archives.contains(where: { $0.filename == before.archives[0].filename && $0.digest == before.archives[0].digest }),
                  try Data(contentsOf: sentinel) == sentinelBytes else { throw LibraryError("Final installed selection or retained original data differs") }
            evidence.merge(["status": "PASS_REAL_FRESH_SPRING_DEPENDENCY_INSTALL", "selection": selection,
                "archiveCount": after.archives.count, "history": history, "receipts": InstallJournal.diagnostics(profile: library.profile),
                "originalAndUnknownSavePreserved": true, "installationReport": report.json]) { _, new in new }
            try JSONSerialization.data(withJSONObject: evidence, options: [.prettyPrinted, .sortedKeys]).write(to: folder.appendingPathComponent("result.json"))
            print("PASS_REAL_FRESH_SPRING_DEPENDENCY_INSTALL", after.archives.count)
        }
    }
}
