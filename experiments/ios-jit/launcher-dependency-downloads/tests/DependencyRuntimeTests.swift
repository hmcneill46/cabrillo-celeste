import Foundation
import ZIPFoundation

// Runs the selected production planner/library/installer with local, metadata-only
// ZIP fixtures. The injected transport never reaches a network or executes a mod.
@main struct DependencyRuntimeTests {
    static let fm = FileManager.default
    static var checks = [String]()
    static var versionRuleCases = [[String: Any]]()

    static func check(_ value: @autoclosure () throws -> Bool, _ name: String) throws {
        guard try value() else { throw LibraryError("FAILED: " + name) }
        checks.append(name)
    }
    static func module(_ name: String, _ version: String = "1.0", dependencies: [(String, String)] = [], optional: [(String, String)] = []) throws -> ModMetadata {
        func rows(_ input: [(String, String)]) throws -> [ModDependency] {
            try input.map { ModDependency(name: $0.0, version: try ModVersion($0.1)) }
        }
        return ModMetadata(name: name, version: try ModVersion(version), dll: nil,
                           dependencies: try rows(dependencies), optionalDependencies: try rows(optional))
    }
    static func dependencyYAML(_ rows: [ModDependency], key: String) -> String {
        rows.isEmpty ? "" : "  \(key):\n" + rows.map { "  - Name: \($0.name)\n    Version: \($0.version.text)\n" }.joined()
    }
    static func yaml(_ modules: [ModMetadata]) -> Data {
        Data(modules.map {
            "- Name: \($0.name)\n  Version: \($0.version.text)\n" +
            dependencyYAML($0.dependencies, key: "Dependencies") +
            dependencyYAML($0.optionalDependencies, key: "OptionalDependencies")
        }.joined().utf8)
    }
    static func zip(_ root: URL, _ filename: String, _ modules: [ModMetadata]) throws -> URL {
        try InstallJournal.directory(root)
        let file = root.appendingPathComponent(filename), data = yaml(modules)
        do {
            let archive = try Archive(url: file, accessMode: .create)
            try archive.addEntry(with: "everest.yaml", type: .file, uncompressedSize: Int64(data.count), compressionMethod: .deflate) { offset, size in
                data.subdata(in: Int(offset)..<Int(offset) + size)
            }
        }
        return file
    }
    // Deliberately permits graph metadata to differ from the real ZIP. The real
    // production installer must reject/replan those fixtures after verification.
    static func candidate(_ file: URL, _ claimed: [ModMetadata], id: Int) throws -> DownloadCandidate {
        let identity = try DownloadIdentity.read(file)
        return DownloadCandidate(url: "https://gamebanana.com/mmdl/\(id)", bytes: identity.bytes,
                                 hashes: [identity.xxHash], pinnedSHA256: nil, modules: claimed,
                                 mirrorName: "runtime_fixture_\(id)")
    }
    static func database(_ candidates: [DownloadCandidate]) throws -> DependencyDatabase {
        var updates = "", graph = ""
        for source in candidates {
            for item in source.modules {
                updates += "\(item.name):\n  URL: \(source.url)\n  Size: \(source.bytes)\n  Version: \(item.version.text)\n  xxHash: [\(source.hashes.joined(separator: ","))]\n"
                if let mirrorName = source.mirrorName { updates += "  MirrorName: \(mirrorName)\n" }
                graph += "\(item.name):\n  URL: \(source.url)\n" + dependencyYAML(item.dependencies, key: "Dependencies") + dependencyYAML(item.optionalDependencies, key: "OptionalDependencies")
            }
        }
        return try DependencyDatabase(updates: Data((updates.isEmpty ? "{}" : updates).utf8), graph: Data((graph.isEmpty ? "{}" : graph).utf8), allowEmpty: true)
    }
    static func seededLibrary(_ root: URL, rootZIP: URL) throws -> ModLibrary {
        let library = ModLibrary(profile: root.appendingPathComponent("Profile"))
        _ = try library.importZIP(rootZIP)
        for (name, value) in [("Saves/0.celeste", "original save bytes"), ("Saves/settings.celeste", "original settings bytes"), ("Unknown/opaque.sidecar", "unknown bytes")] {
            let target = library.profile.appendingPathComponent(name)
            try InstallJournal.directory(target.deletingLastPathComponent())
            try Data(value.utf8).write(to: target)
        }
        return library
    }
    static func protectedSnapshot(_ library: ModLibrary) throws -> [String: String] {
        var result = [String: String]()
        for folder in ["Mods", "Saves", "Unknown"] {
            let parent = library.profile.appendingPathComponent(folder)
            guard let files = fm.enumerator(at: parent, includingPropertiesForKeys: [.isRegularFileKey]) else { continue }
            for case let file as URL in files {
                if try file.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile == true {
                    result[String(file.path.dropFirst(library.profile.path.count + 1))] = digestData(try Data(contentsOf: file))
                }
            }
        }
        result["enabledChoices"] = digestData(try canonicalData(library.state()))
        return result
    }
    static func wait(_ installer: DependencyInstaller, _ action: () -> Void) throws -> [String: Any] {
        var terminal: [String: Any]?
        installer.update = { if $0["active"] as? Bool == false { terminal = $0 } }
        action()
        let deadline = Date().addingTimeInterval(30)
        while terminal == nil && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.01)) }
        guard let terminal else { throw LibraryError("Runtime fixture installer timed out") }
        return terminal
    }
    static func plan(_ state: [String: Any]) throws -> [String: Any] {
        guard let plan = state["plan"] as? [String: Any], plan["id"] is String else { throw LibraryError("Expected a review plan: \(state)") }
        return plan
    }
    static func applicableID(_ state: [String: Any]) throws -> String {
        let value = try plan(state)
        guard value["canApply"] as? Bool == true, let id = value["id"] as? String else { throw LibraryError("Expected applicable review: \(state)") }
        return id
    }
    static func versionRules() throws {
        let cases: [(String, String, Bool)] = [
            ("1.6642.0", "1.6580.0", true), ("1.6642.0", "1.6642", true),
            ("1.6642.0", "1.6642.0", true), ("1.6642.0", "1.6642.0-cjit-fixture", true),
            ("1.6642.0", "1.6642.0.0", false), ("1.6642.0", "1.6642.1", false),
            ("1.6642.0", "1.6643.0", false), ("1.6642.0", "2.0", false),
            ("1.6642.0", "0.0", false), ("0.0.0-dummy", "99.99", true),
            ("1.2.3.4", "1.2.3.3", true), ("1.2", "1.2.0", false),
            ("1.3", "1.2.999.999", true), ("1.02.003", "1.2.3", true)
        ]
        for (installed, required, expected) in cases {
            let actual = try ModVersion(installed).satisfies(ModVersion(required))
            try check(actual == expected,
                      "production version rule \(installed) satisfies \(required) = \(expected)")
            versionRuleCases.append(["installed": installed, "required": required, "actual": actual])
        }
        for text in ["1", "1.2.3.4.5", "1..0", "-1.0", "1.2147483648", "1.0+metadata"] {
            var rejected = false
            do { _ = try ModVersion(text) } catch { rejected = true }
            try check(rejected, "unsupported numeric version is rejected explicitly: \(text)")
        }
    }
    static func builtinMatrix(_ root: URL) throws {
        let expected = ["Celeste": "1.4.0.0", "CelesteIOS": "1.0.0", "Everest": "1.6642.0", "EverestCore": "1.6642.0"]
        try check(RuntimeIdentity.builtins == expected && DependencyPlanner.builtins == expected,
                  "actual selected native runtime and planner both know all four shipped builtin versions")
        try check(RuntimeIdentity.everestVersionString == "1.6642.0-cjit-5abd787" && RuntimeIdentity.everestSourceCommit == "5abd7876821223c20711c1844a5187321d6e904c",
                  "selected native version and exact source agree with compiled55 Everest")
        let runtimeRequirements: [(String, Bool)] = [("1.6580.0", true), ("1.6642", true), ("1.6642.0", true), ("1.6642.0-fixture", true), ("1.6642.0.0", false), ("1.6642.1", false), ("1.6643.0", false), ("2.0", false)]
        var cases: [(String, String, Bool, Bool)] = []
        for alias in ["Everest", "EverestCore", "API"] {
            cases += runtimeRequirements.map { (alias, $0.0, $0.1, false) }
            // Upstream only canonicalizes required API. A literal optional API
            // is ignored while absent, like every other unknown optional module.
            cases += [(alias, "1.6642.0", true, true), (alias, "1.6643.0", alias == "API", true)]
        }
        cases += [("Celeste", "1.4.0.0", true, false), ("Celeste", "1.4.0.1", false, false),
                  ("CelesteIOS", "1.0.0", true, false), ("CelesteIOS", "1.0.1", false, false)]
        for (index, item) in cases.enumerated() {
            let (alias, version, accepted, optional) = item
            let row = try module("RuntimeMatrix\(index)", dependencies: optional ? [] : [(alias, version)], optional: optional ? [(alias, version)] : [])
            let folder = root.appendingPathComponent("matrix-\(index)")
            let original = try zip(folder, "root.zip", [row])
            let library = try seededLibrary(folder, rootZIP: original)
            let inventory = try LibraryInventory.read(library)
            let canonicalName = alias == "API" && !optional ? "Everest" : alias
            let fake = DownloadCandidate(url: "https://gamebanana.com/mmdl/\(910000 + index)", bytes: 10, hashes: ["0123456789abcdef"], pinnedSHA256: nil, modules: [try module(canonicalName, version)])
            let db = try database([fake])
            let resolved = try DependencyPlanner.resolve(inventory, database: db, pins: [:])
            let snapshot = try library.snapshot()
            try check(resolved.issues.isEmpty == accepted && (snapshot["canRun"] as? Bool) == accepted,
                      "real ZIP snapshot and planner agree: \(optional ? "optional" : "required") \(alias) \(version)")
            try check(resolved.downloads.isEmpty && resolved.enable.isEmpty && resolved.disable.isEmpty,
                      "builtin \(alias) \(version) is never downloaded or replaced despite an indexed provider")
            if alias == "API" {
                let parsed = inventory.active[0].modules[0]
                try check((optional ? parsed.optionalDependencies : parsed.dependencies).first?.name == canonicalName,
                          "actual ZIP legacy API is \(optional ? "literal when optional" : "canonicalized when required")")
            }
            if !accepted {
                try check(resolved.issues.contains { $0.contains(expected[canonicalName]!) && $0.contains(version) },
                          "incompatible builtin requirement reports both required and shipped versions: \(alias) \(version)")
            }
        }
        for name in expected.keys.sorted() {
            let source = DownloadCandidate(url: "https://gamebanana.com/mmdl/920000", bytes: 10, hashes: ["0123456789abcdef"], pinnedSHA256: nil, modules: [try module("HarmlessHelper"), try module(name, expected[name]!)])
            let empty = LibraryInventory(archives: [], disabled: [])
            let rejected = try DependencyPlanner.resolve(empty, database: database([]), pins: [:], installs: [source])
            try check(!rejected.issues.isEmpty && rejected.downloads.isEmpty, "explicit multi-module catalogue choice cannot shadow builtin " + name)
        }
    }
    static func aliasParity(_ root: URL) throws {
        let claimed = try module("AliasParity", dependencies: [("API", "1.6642.0")], optional: [("API", "99.0"), ("EverestCore", "1.6643.0")])
        let file = try zip(root, "alias-parity.zip", [claimed])
        let parsed = try ModLibrary.metadata(yaml([claimed]))[0]
        let source = try candidate(file, [claimed], id: 925000)
        let db = try database([source])
        guard let online = db.byName[claimed.name]?.modules.first else { throw LibraryError("Missing actual parsed graph fixture") }
        try check(parsed.dependencies.first?.name == "Everest" && online.dependencies.first?.name == "Everest",
                  "actual YAML and online graph canonicalize required API exactly like upstream PostParse")
        try check(parsed.optionalDependencies.map(\.name) == ["API", "EverestCore"] && Set(online.optionalDependencies.map(\.name)) == ["API", "EverestCore"],
                  "actual YAML and online graph retain literal optional API and the real EverestCore alias")
        let futureRuntime = try DependencyPlanner.runtimeIssues([online])
        try check(futureRuntime.count == 1 && futureRuntime[0].contains("EverestCore") && futureRuntime[0].contains("1.6643.0"),
                  "unknown optional API is ignored while present builtin EverestCore still enforces its minimum")
        for version in ["1.0", "2.0"] {
            let folder = root.appendingPathComponent("enabled-api-" + version)
            let original = try zip(folder, "root.zip", [try module("OptionalAPIRoot", dependencies: [("API", "1.6642.0")], optional: [("API", "2.0")])])
            let provider = try zip(folder, "literal-api-provider.zip", [try module("API", version)])
            let library = try seededLibrary(folder, rootZIP: original)
            let empty = try database([])
            let absent = try DependencyPlanner.resolve(LibraryInventory.read(library), database: empty, pins: [:])
            try check(absent.issues.isEmpty && absent.downloads.isEmpty && (try library.snapshot())["canRun"] as? Bool == true,
                      "required API is satisfied by Everest while absent literal optional API never causes installation")
            _ = try library.importZIP(provider)
            let present = try DependencyPlanner.resolve(LibraryInventory.read(library), database: empty, pins: [:])
            try check(present.issues.isEmpty == (version == "2.0") && (try library.snapshot())["canRun"] as? Bool == (version == "2.0"),
                      "literal optional API provider enforces its own version only when enabled: " + version)
        }
    }
    static func hiddenBuiltinZIPs(_ root: URL) throws {
        for (index, builtin) in ["Everest", "EverestCore", "Celeste", "CelesteIOS"].enumerated() {
            let folder = root.appendingPathComponent("hidden-\(builtin)")
            let rootZIP = try zip(folder, "root.zip", [try module("RuntimeRoot", dependencies: [("RuntimeHelper", "1.0")])])
            let helper = try module("RuntimeHelper")
            let downloadZIP = try zip(folder, "actual-extra-builtin.zip", [helper, try module(builtin, RuntimeIdentity.builtins[builtin]!)])
            let advertised = try candidate(downloadZIP, [helper], id: 930000 + index)
            let db = try database([advertised])
            let library = try seededLibrary(folder, rootZIP: rootZIP)
            let before = try protectedSnapshot(library), revision = try LibraryInventory.read(library).revision
            var downloads = 0
            let installer = DependencyInstaller(library: library, pins: [], indexProvider: { _ in db }, metadataProvider: { _, _ in Data("[]".utf8) }, downloadProvider: { _, destination, _, _, _, _ in
                downloads += 1
                try fm.copyItem(at: downloadZIP, to: destination)
            })
            var state = try wait(installer) { installer.resolve() }
            let id = try applicableID(state)
            state = try wait(installer) { installer.apply(planID: id) }
            let report = try InstallReport.read(library.profile)
            try check(downloads == 1 && state["phase"] as? String == "failed" && (state["message"] as? String)?.localizedCaseInsensitiveContains("built") == true,
                      "hash-valid ZIP with unadvertised builtin \(builtin) is rejected by real metadata verification")
            try check(!report.commitStarted && report.applicationState == "unchanged" && report.outcome == "failed",
                      "builtin spoof \(builtin) fails before transaction commit")
            try check(try protectedSnapshot(library) == before && LibraryInventory.read(library).revision == revision,
                      "builtin spoof \(builtin) preserves original ZIPs, enabled choices, saves and unknown sidecars")
            let cache = try fm.contentsOfDirectory(at: InstallJournal.cache(library.profile), includingPropertiesForKeys: nil)
            try check(cache.allSatisfy { !["zip", "part"].contains($0.pathExtension) }, "builtin spoof \(builtin) leaves no accepted or partial archive")
        }
    }
    static func tooNewZIP(_ root: URL) throws {
        for (index, alias) in ["Everest", "EverestCore", "API"].enumerated() {
            let folder = root.appendingPathComponent("too-new-\(alias)")
            let rootZIP = try zip(folder, "root.zip", [try module("RuntimeRoot", dependencies: [("RuntimeHelper", "1.0")])])
            let advertisedMetadata = try module("RuntimeHelper", dependencies: [(alias, "1.6580.0")])
            let actualMetadata = try module("RuntimeHelper", dependencies: [(alias, "1.6643.0")])
            let actualZIP = try zip(folder, "actual-future-runtime.zip", [actualMetadata])
            let advertised = try candidate(actualZIP, [advertisedMetadata], id: 940000 + index)
            // A plausible future runtime in the online index must never become a
            // way around the app's immutable builtin module/compiled-code identity.
            let fakeRuntime = DownloadCandidate(url: "https://gamebanana.com/mmdl/949999", bytes: 10, hashes: ["0123456789abcdef"], pinnedSHA256: nil, modules: [try module(alias == "API" ? "Everest" : alias, "1.6643.0")])
            let db = try database([advertised, fakeRuntime])
            let library = try seededLibrary(folder, rootZIP: rootZIP)
            let before = try protectedSnapshot(library), revision = try LibraryInventory.read(library).revision
            var urls = [String](), metadataRequests = 0
            let installer = DependencyInstaller(library: library, pins: [], indexProvider: { _ in db }, metadataProvider: { _, _ in
                metadataRequests += 1
                throw LibraryError("Runtime incompatibility must be handled by dependency planning, not relocation")
            }, downloadProvider: { url, destination, _, _, _, _ in
                urls.append(url)
                guard url == advertised.url else { throw LibraryError("A builtin runtime download must never be requested") }
                try fm.copyItem(at: actualZIP, to: destination)
            })
            var state = try wait(installer) { installer.resolve() }
            let originalID = try applicableID(state)
            state = try wait(installer) { installer.apply(planID: originalID) }
            let revised = try plan(state), issues = revised["issues"] as? [String] ?? []
            let report = try InstallReport.read(library.profile)
            try check(state["phase"] as? String == "review" && state["revised"] as? Bool == true && revised["canApply"] as? Bool == false,
                      "actual ZIP future \(alias) requirement changes the reviewed graph into a blocked plan")
            try check(issues.contains { $0.contains("1.6643.0") && $0.contains("1.6642.0") }, "future \(alias) replan explains actual and shipped runtime versions")
            try check(!report.commitStarted && report.outcome == "needsReview" && report.applicationState == "unchanged",
                      "future \(alias) metadata disagreement requires review before any transaction")
            try check(urls == [advertised.url] && metadataRequests == 0 && (revised["downloads"] as? [[String: Any]] ?? []).allSatisfy { $0["key"] as? String != fakeRuntime.key },
                      "future \(alias) ZIP cannot trigger a runtime archive download")
            try check(try protectedSnapshot(library) == before && LibraryInventory.read(library).revision == revision,
                      "future \(alias) replan preserves originals, mod choices, saves and unknown sidecars")
            let cached = InstallJournal.cache(library.profile).appendingPathComponent(advertised.key + ".zip")
            try check(advertised.accepts(DownloadIdentity.read(cached)), "future \(alias) ZIP remains only as verified disposable cache")
            // Reusing either review ID must remain unable to commit the incompatible
            // selection. The second resolve also checks actual cached ZIP metadata.
            state = try wait(installer) { installer.resolve() }
            let again = try plan(state)
            try check(again["canApply"] as? Bool == false && !(again["issues"] as? [String] ?? []).isEmpty,
                      "cached actual future \(alias) metadata remains blocked on a fresh review")
            guard let blockedID = again["id"] as? String else { throw LibraryError("Blocked plan has no identity") }
            state = try wait(installer) { installer.apply(planID: blockedID) }
            try check(state["phase"] as? String == "failed" && urls == [advertised.url] && (try protectedSnapshot(library)) == before,
                      "attempting to apply blocked future \(alias) review cannot mutate or redownload anything")
        }
    }
    static func main() throws {
        guard CommandLine.arguments.count == 2 else { throw LibraryError("Expected a fresh local runtime-fixture results directory") }
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        try InstallJournal.directory(root)
        try versionRules()
        try builtinMatrix(root)
        try aliasParity(root.appendingPathComponent("alias-parity"))
        try hiddenBuiltinZIPs(root)
        try tooNewZIP(root)
        let result: [String: Any] = ["status": "PASS_DEPENDENCY56_RUNTIME", "checks": checks,
                                   "runtimeBuiltins": RuntimeIdentity.builtins,
                                   "versionRuleCases": versionRuleCases,
                                   "networkUsed": false, "fixtureZIPsContainExecutablePayload": false,
                                   "gameOrAdapterExecuted": false, "physicalDeviceTested": false]
        try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]).write(to: root.appendingPathComponent("results.json"))
        print("PASS_DEPENDENCY56_RUNTIME", checks.count)
    }
}
