import Foundation
import CryptoKit

func canonicalData<T: Encodable>(_ value: T) throws -> Data {
    let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]; return try encoder.encode(value)
}
func digestData(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func validDownloadURL(_ text: String) -> URL? {
    guard let url = URL(string: text), url.scheme == "https", let host = url.host, !host.isEmpty,
          url.user == nil, url.password == nil, url.fragment == nil,
          url.port == nil || url.port == 443,
          host != "localhost", !host.hasSuffix(".local"), !host.hasSuffix(".localhost"),
          host.contains("."), host.rangeOfCharacter(from: .letters) != nil else { return nil }
    return url
}

struct DownloadCandidate: Codable {
    let url: String
    let bytes: UInt64
    let hashes: [String]
    let pinnedSHA256: String?
    var modules: [ModMetadata]
    var key: String { digestData(Data((url + "|" + String(bytes) + "|" + hashes.sorted().joined(separator: ",") + "|" + (pinnedSHA256 ?? "")).utf8)) }
    var title: String { modules.map { $0.name + " " + $0.version.text }.joined(separator: " + ") }
    func accepts(_ identity: DownloadIdentity) -> Bool {
        identity.bytes == bytes && (pinnedSHA256.map { $0 == identity.sha256 } ?? hashes.contains(identity.xxHash))
    }
}

struct DependencyDatabase {
    var byName: [String: DownloadCandidate] = [:]
    var indexedByName: [String: DownloadCandidate] = [:]
    var earlierByName: [String: [DownloadCandidate]] = [:]
    var problems: [String: String] = [:]
    let provenance: [String: String]
    init(updates: Data, graph: Data, provenance: [String: String] = [:], pins: [DownloadCandidate] = [], earlier: [DownloadCandidate] = [], allowEmpty: Bool = false) throws {
        self.provenance = provenance
        struct Row { let url: String; let bytes: UInt64; let hashes: [String]; let version: ModVersion }
        var rows: [String: Row] = [:]
        try ManifestYAML(online: true).mappingEntries(updates) { name, value in
            do {
                guard let m = value.map, let url = m["URL"]?.text, validDownloadURL(url) != nil,
                      let size = m["Size"]?.text.flatMap(UInt64.init), size > 0, size <= 4_294_967_296,
                      let version = m["Version"]?.text, let raw = m["xxHash"]?.list, !raw.isEmpty, raw.count <= 64 else { throw LibraryError("Incomplete download record.") }
                let hashes = raw.compactMap(\.text).map { $0.lowercased() }
                guard hashes.count == raw.count, hashes.allSatisfy({ $0.count == 16 && $0.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) } }) else { throw LibraryError("Invalid integrity hash.") }
                rows[name] = Row(url: url, bytes: size, hashes: hashes, version: try ModVersion(version))
            } catch { problems[name] = error.localizedDescription }
        }
        var grouped: [String: DownloadCandidate] = [:]
        try ManifestYAML(online: true).mappingEntries(graph) { name, value in
            guard let row = rows[name] else { return }
            do {
                guard let m = value.map, m["URL"]?.text == row.url else { throw LibraryError("The index and dependency graph disagree; refresh the index.") }
                func dependencies(_ key: String) throws -> [ModDependency] {
                    guard let raw = m[key] else { return [] }
                    if case .null = raw { return [] }
                    guard let list = raw.list, list.count <= 256 else { throw LibraryError("Unsupported dependency list.") }
                    return try list.map { v in
                        guard let d = v.map, let n = d["Name"]?.text, !n.isEmpty, n.count <= 200 else { throw LibraryError("Invalid dependency identity.") }
                        // The community backend serializes an absent Version
                        // as NoVersion; Everest defaults that field to 1.0.
                        // Actual ZIP metadata is still parsed and rechecked.
                        let rawVersion = d["Version"]?.text ?? "1.0"
                        return ModDependency(name: n == "API" ? "Everest" : n, version: try ModVersion(rawVersion == "NoVersion" ? "1.0" : rawVersion))
                    }.sorted { $0.name < $1.name }
                }
                let module = ModMetadata(name: name, version: row.version, dll: nil, dependencies: try dependencies("Dependencies"), optionalDependencies: try dependencies("OptionalDependencies"))
                var candidate = DownloadCandidate(url: row.url, bytes: row.bytes, hashes: row.hashes, pinnedSHA256: nil, modules: [module])
                if var old = grouped[row.url] {
                    guard old.bytes == row.bytes, Set(old.hashes) == Set(row.hashes), old.modules.count < 64 else { throw LibraryError("This download has ambiguous multi-module metadata.") }
                    old.modules.append(module); old.modules.sort { $0.name < $1.name }; candidate = old
                }
                grouped[row.url] = candidate
            } catch { problems[name] = error.localizedDescription }
        }
        for row in grouped.values { for module in row.modules { byName[module.name] = row } }
        for name in rows.keys where byName[name] == nil && problems[name] == nil { problems[name] = "No matching dependency graph entry is available." }
        indexedByName = byName
        for pin in pins { for module in pin.modules { byName[module.name] = pin; problems.removeValue(forKey: module.name) } }
        for release in earlier {
            guard let hash = release.pinnedSHA256, InstallJournal.hex(hash), validDownloadURL(release.url) != nil,
                  release.bytes > 0, release.bytes <= 4_294_967_296, !release.modules.isEmpty,
                  release.modules.count <= 64, Set(release.modules.map(\.name)).count == release.modules.count,
                  release.modules.allSatisfy({ DependencyPlanner.builtins[$0.name] == nil }) else { throw LibraryError("Invalid earlier-release catalogue entry.") }
            for module in release.modules { earlierByName[module.name, default: []].append(release) }
        }
        guard allowEmpty || !byName.isEmpty else { throw LibraryError("The community mod index contains no usable entries.") }
    }
    func candidates(for name: String) -> [DownloadCandidate] {
        let primary = byName[name].map { [$0] } ?? []
        let earlier = (earlierByName[name] ?? []).sorted { a, b in
            let av = a.modules.first { $0.name == name }!.version.parts, bv = b.modules.first { $0.name == name }!.version.parts
            return av == bv ? a.key < b.key : bv.lexicographicallyPrecedes(av)
        }
        var seen = Set<String>()
        return (primary + earlier).filter { seen.insert($0.key).inserted }
    }
    mutating func replaceWithVerified(_ candidate: DownloadCandidate) {
        // Keep historical releases separate from the latest index entry. Otherwise
        // inspecting an older staged ZIP could make a newer download disappear.
        if earlierByName.values.contains(where: { $0.contains { $0.key == candidate.key } }) {
            for name in Array(earlierByName.keys) { earlierByName[name]?.removeAll { $0.key == candidate.key } }
            for module in candidate.modules { earlierByName[module.name, default: []].append(candidate) }
            return
        }
        byName = byName.filter { $0.value.key != candidate.key }
        for module in candidate.modules { byName[module.name] = candidate; problems.removeValue(forKey: module.name) }
    }
}

struct LibraryInventory: Codable {
    let archives: [ModArchive]
    let disabled: [String]
    var revision: String { digestData((try? canonicalData(self)) ?? Data()) }
    var active: [ModArchive] { let disabled = Set(disabled); return archives.filter { !disabled.contains($0.filename) } }
    static func read(_ library: ModLibrary, force: Bool = true) throws -> LibraryInventory {
        try library.synchronized { LibraryInventory(archives: try library.scan(force: force), disabled: try library.state().disabled.sorted()) }
    }
}
struct PlannedArchive: Codable {
    let local: ModArchive?
    let download: DownloadCandidate?
    var key: String { local.map { "local:" + $0.filename } ?? "download:" + download!.key }
    var modules: [ModMetadata] { local?.modules ?? download!.modules }
}
struct DependencyPlan: Codable {
    let id: String
    let revision: String
    let selected: [PlannedArchive]
    let enable: [String]
    let disable: [String]
    let disabledDownloads: [DownloadCandidate]
    let requestedUpdates: [String]
    let compatibilityChoices: [String]
    let issues: [String]
    var downloads: [DownloadCandidate] { (selected.compactMap(\.download) + disabledDownloads).sorted { $0.key < $1.key } }
    var totalBytes: UInt64 { downloads.reduce(0) { $0 + $1.bytes } }
    var signature: String {
        struct Signature: Encodable { let selected: [PlannedArchive]; let enable: [String]; let disable: [String]; let disabledDownloads: [DownloadCandidate]; let requestedUpdates: [String]; let issues: [String] }
        return digestData((try? canonicalData(Signature(selected: selected, enable: enable, disable: disable, disabledDownloads: disabledDownloads, requestedUpdates: requestedUpdates, issues: issues))) ?? Data())
    }
    var json: [String: Any] {
        ["id": id, "revision": revision, "downloads": downloads.map { source in ["key": source.key, "name": source.title, "bytes": source.bytes, "pinned": source.pinnedSHA256 != nil, "staysDisabled": disabledDownloads.contains(where: { $0.key == source.key })] as [String: Any] },
         "enable": enable, "disable": disable, "updates": requestedUpdates, "issues": issues, "compatibilityChoices": compatibilityChoices, "totalBytes": totalBytes,
         "canApply": issues.isEmpty && (!downloads.isEmpty || !enable.isEmpty || !disable.isEmpty)]
    }
}

enum DependencyPlanner {
    static let builtins = RuntimeIdentity.builtins
    static func runtimeIssues(_ modules: [ModMetadata], name: String? = nil) throws -> [String] {
        var issues = Set<String>()
        for module in modules {
            for dep in module.dependencies + module.optionalDependencies {
                guard name == nil || dep.name == name, let current = builtins[dep.name],
                      !(try ModVersion(current)).satisfies(dep.version) else { continue }
                issues.insert("\(module.name) \(module.version.text) requires \(dep.name) \(dep.version.text); the app runtime includes \(current).")
            }
        }
        return issues.sorted()
    }
    static func resolve(_ inventory: LibraryInventory, database: DependencyDatabase, pins: [String: String], updates: [String: DownloadCandidate] = [:], installs: [DownloadCandidate] = [], identities: [String: DownloadIdentity] = [:]) throws -> DependencyPlan {
        var chosen = Dictionary(uniqueKeysWithValues: inventory.active.map { ("local:" + $0.filename, PlannedArchive(local: $0, download: nil)) })
        var roots = Set(inventory.active.flatMap { $0.modules.map(\.name) })
        var fixedIssues: [String] = [], disabledUpdates: [String: DownloadCandidate] = [:], lockedNames = Set<String>()
        // Explicit browser choices are roots, not suggestions the solver may
        // silently replace with another release. Reuse only exact verified ZIPs.
        var requestedNames = Set<String>()
        for source in installs.sorted(by: { $0.key < $1.key }) {
            let names = Set(source.modules.map(\.name))
            guard !names.isEmpty, names.count == source.modules.count, requestedNames.isDisjoint(with: names) else { fixedIssues.append("The selected files provide overlapping modules. Choose one release of each mod."); continue }
            requestedNames.formUnion(names)
            guard names.allSatisfy({ builtins[$0] == nil }) else { fixedIssues.append("A catalogue download cannot replace built-in app modules."); continue }
            guard names.allSatisfy({ pins[$0].map { $0 == source.pinnedSHA256 } ?? true }) else { fixedIssues.append("This release is app-managed for iOS compatibility. Keep the supported installed release or use Resolve dependencies."); continue }
            let runtime = try runtimeIssues(source.modules)
            guard runtime.isEmpty else { fixedIssues += runtime; continue }
            let overlaps = chosen.values.filter { !Set($0.modules.map(\.name)).isDisjoint(with: names) }
            guard overlaps.allSatisfy({ Set($0.modules.map(\.name)).isSubset(of: names) }) else { fixedIssues.append("This file would split an installed multi-module ZIP. Choose the intended archives in Installed."); continue }
            let exact = inventory.archives.filter { archive in
                guard archive.problem == nil, let identity = identities[archive.filename], identity.sha256 == archive.digest, source.accepts(identity),
                      Set(archive.modules.map(\.name)) == names else { return false }
                return source.modules.allSatisfy { m in archive.modules.contains { $0.name == m.name && $0.version.parts == m.version.parts } }
            }
            let active = exact.filter { !inventory.disabled.contains($0.filename) }
            guard active.count <= 1, !active.isEmpty || exact.count <= 1 else { fixedIssues.append("More than one installed copy matches this file. Choose the copy to enable in Installed."); continue }
            for old in overlaps { chosen.removeValue(forKey: old.key) }
            let local = active.first ?? exact.first
            let row = PlannedArchive(local: local, download: local == nil ? source : nil)
            chosen[row.key] = row; roots.formUnion(names); lockedNames.formUnion(names)
        }
        for (filename, candidate) in updates.sorted(by: { $0.key < $1.key }) {
            guard let old = inventory.archives.first(where: { $0.filename == filename }), old.problem == nil, filename != ModLibrary.ownMod else { fixedIssues.append("An update target is no longer installed."); continue }
            guard old.modules.allSatisfy({ pins[$0.name] == nil }), candidate.modules.allSatisfy({ builtins[$0.name] == nil && pins[$0.name] == nil }) else { fixedIssues.append("An app-managed compatibility release cannot be updated by the mod installer."); continue }
            guard Set(old.modules.map(\.name)).isSubset(of: Set(candidate.modules.map(\.name))) else { fixedIssues.append("An update would remove a module from a multi-module ZIP. Choose the intended archive manually."); continue }
            let runtime = try runtimeIssues(candidate.modules)
            guard runtime.isEmpty else { fixedIssues += runtime; continue }
            if inventory.disabled.contains(filename) { disabledUpdates[candidate.key] = candidate }
            else {
                chosen.removeValue(forKey: "local:" + filename)
                let row = PlannedArchive(local: nil, download: candidate); chosen[row.key] = row
                lockedNames.formUnion(candidate.modules.map(\.name))
            }
        }
        var issues = fixedIssues, converged = false
        let stayDisabled = Set(disabledUpdates.values.flatMap { $0.modules.map(\.name) })
        var seen = Set<String>()
        for _ in 0..<2048 {
            issues = fixedIssues + chosen.values.compactMap { row in row.local?.problem.map { (row.local?.filename ?? "Mod") + ": " + $0 } }
            let stamp = chosen.keys.sorted().joined(separator: "\n")
            guard seen.insert(stamp).inserted else { issues.append("These versions cannot be resolved together automatically. Choose compatible versions in Mods."); converged = true; break }
            var provided: [String: PlannedArchive] = [:]
            var duplicate = false
            for row in chosen.values {
                for module in row.modules {
                    if builtins[module.name] != nil || provided[module.name] != nil {
                        issues.append("\(module.name) has more than one enabled provider. Disable one version in Mods."); duplicate = true
                    }
                    if let local = row.local, let pin = pins[module.name], pin != local.digest {
                        issues.append("\(module.name) is not the iOS-compatible release. Disable this version before resolving dependencies.")
                    }
                    provided[module.name] = row
                }
            }
            if duplicate { converged = true; break }
            var required: [String: [ModVersion]] = Dictionary(uniqueKeysWithValues: roots.map { ($0, []) })
            for row in chosen.values {
                for module in row.modules {
                    for dep in module.dependencies { required[dep.name, default: []].append(dep.version) }
                    for dep in module.optionalDependencies where provided[dep.name] != nil || builtins[dep.name] != nil { required[dep.name, default: []].append(dep.version) }
                }
            }
            var changed = false
            for name in required.keys.sorted() {
                let versions = required[name]!
                func compatible(_ v: ModVersion) -> Bool { versions.allSatisfy { v.satisfies($0) } }
                if let version = builtins[name] {
                    if !compatible(try ModVersion(version)) { issues += try runtimeIssues(chosen.values.flatMap(\.modules), name: name) }
                    continue
                }
                if let current = provided[name], let module = current.modules.first(where: { $0.name == name }), compatible(module.version) { continue }
                if lockedNames.contains(name) { issues.append("The selected release of \(name) conflicts with another enabled mod's requirements. Choose compatible files together or keep the installed version."); continue }
                if stayDisabled.contains(name) { issues.append("\(name) was selected to remain disabled, but an enabled mod requires it. Resolve that selection in Mods before updating."); continue }
                let installed = inventory.archives.filter { archive in
                    archive.problem == nil && archive.modules.contains { $0.name == name && compatible($0.version) } &&
                    (try? runtimeIssues(archive.modules).isEmpty) == true &&
                    archive.modules.allSatisfy { pins[$0.name].map { $0 == archive.digest } ?? true }
                }
                var replacement: PlannedArchive?
                if installed.count == 1 { replacement = PlannedArchive(local: installed[0], download: nil) }
                else if installed.count > 1 { issues.append("Several installed ZIPs can provide \(name). Enable the version you want in Mods."); continue }
                else if let candidate = {
                    let candidates = database.candidates(for: name).filter { $0.modules.contains { $0.name == name && compatible($0.version) } }
                    // Latest is preferred. Only verified, explicitly catalogued
                    // originals are alternatives; never guess an old URL/version.
                    return candidates.first { (try? runtimeIssues($0.modules).isEmpty) == true } ?? candidates.first
                }() {
                    if candidate.modules.contains(where: { builtins[$0.name] != nil }) { issues.append("A download cannot replace built-in app modules."); continue }
                    if candidate.modules.contains(where: { pins[$0.name].map { $0 != candidate.pinnedSHA256 } ?? false }) { issues.append("\(name) needs an app-compatible release that is unavailable in this index."); continue }
                    replacement = PlannedArchive(local: nil, download: candidate)
                } else {
                    let versionText = versions.map(\.text).sorted().joined(separator: ", ")
                    issues.append("Cannot resolve \(name)\(versionText.isEmpty ? "" : " (" + versionText + ")"). " + (database.problems[name] ?? "No compatible indexed release is available. Import a compatible ZIP or disable the dependent mod.")); continue
                }
                guard let replacement else { continue }
                let names = Set(replacement.modules.map(\.name))
                let overlaps = chosen.values.filter { !Set($0.modules.map(\.name)).isDisjoint(with: names) }
                if overlaps.contains(where: { !Set($0.modules.map(\.name)).isSubset(of: names) }) {
                    issues.append("Replacing \(name) would split a multi-module ZIP. Choose the intended archive in Mods."); continue
                }
                for row in overlaps { chosen.removeValue(forKey: row.key) }
                chosen[replacement.key] = replacement; changed = true; break
            }
            if changed { continue }
            let graph = Dictionary(chosen.values.flatMap { $0.modules }.map { ($0.name, $0.dependencies.map(\.name)) }, uniquingKeysWith: { a, _ in a })
            var visiting = Set<String>(), visited = Set<String>()
            func visit(_ name: String) {
                if visiting.contains(name) { issues.append("Required dependency cycle involving \(name)."); return }
                guard !visited.contains(name), let deps = graph[name] else { return }
                visiting.insert(name); deps.forEach(visit); visiting.remove(name); visited.insert(name)
            }
            graph.keys.sorted().forEach(visit)
            converged = true
            break
        }
        if !converged { issues.append("The dependency graph exceeded the planning limit. Choose a smaller mod set.") }
        let selected = chosen.values.sorted { $0.key < $1.key }
        let oldNames = Set(inventory.active.map(\.filename)), newNames = Set(selected.compactMap { $0.local?.filename })
        let enable = newNames.subtracting(oldNames).sorted(), disable = oldNames.subtracting(newNames).union(updates.keys).sorted()
        let activeDownloads = Set(selected.compactMap { $0.download?.key })
        if !activeDownloads.isDisjoint(with: Set(disabledUpdates.keys)) { issues.append("One update ZIP combines enabled and disabled update targets. Choose one consistent enabled state for those modules before updating.") }
        let disabledDownloads = disabledUpdates.values.filter { !activeDownloads.contains($0.key) }.sorted { $0.key < $1.key }
        if disable.contains(ModLibrary.ownMod) { issues.append("The internal verification module cannot be replaced.") }
        if inventory.archives.count + selected.filter({ $0.download != nil }).count + disabledDownloads.count > 1024 { issues.append("This installation would exceed 1,024 mod ZIPs.") }
        if (selected.compactMap(\.download) + disabledDownloads).reduce(UInt64(0), { $0 + $1.bytes }) > 8_589_934_592 { issues.append("This plan exceeds the 8 GiB download limit. Install a smaller mod set first.") }
        let earlierKeys = Set(database.earlierByName.values.flatMap { $0.map(\.key) })
        let choices = selected.compactMap(\.download).filter { earlierKeys.contains($0.key) }.map {
            "\($0.title): using a verified earlier release that meets this selection's requirements and the app runtime."
        }.sorted()
        return DependencyPlan(id: UUID().uuidString, revision: inventory.revision, selected: selected, enable: enable, disable: disable, disabledDownloads: disabledDownloads, requestedUpdates: updates.keys.sorted(), compatibilityChoices: choices, issues: Array(Set(issues)).sorted())
    }
}
