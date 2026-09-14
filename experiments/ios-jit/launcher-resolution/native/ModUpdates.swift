import Foundation

struct ModUpdate: Codable {
    let archive: ModArchive
    let candidate: DownloadCandidate
    let enabled: Bool
    let reason: String
    let canUpdate: Bool
    var json: [String: Any] {
        ["filename": archive.filename, "name": archive.modules.map(\.name).joined(separator: " + "),
         "current": archive.modules.map { $0.version.text }.joined(separator: ", "),
         "latest": candidate.modules.map { $0.version.text }.joined(separator: ", "),
         "bytes": candidate.bytes, "enabled": enabled, "reason": reason, "canUpdate": canUpdate]
    }
}
enum ModUpdates {
    struct CheckCache: Codable {
        let schema: Int
        let checked: Date
        let revision: String
        let updates: [ModUpdate]
        let index: [String: String]
        func fresh(for revision: String, at now: Date = Date()) -> Bool {
            schema == 1 && self.revision == revision && now.timeIntervalSince(checked) >= 0 && now.timeIntervalSince(checked) < 86400
        }
    }
    static func cacheFile(_ profile: URL) -> URL { profile.appendingPathComponent("LauncherIndex/update-check.json") }
    static func readCache(_ profile: URL) -> CheckCache? {
        guard let data = try? InstallJournal.boundedRead(cacheFile(profile), limit: 2_097_152), let cache = try? JSONDecoder().decode(CheckCache.self, from: data), cache.schema == 1 else { return nil }
        return cache
    }
    static func check(_ inventory: LibraryInventory, library: ModLibrary, database: DependencyDatabase,
                      cancellation: InstallCancellation, progress: (String) -> Void) throws -> [ModUpdate] {
        let retained = try InstallJournal.retainedArchives(profile: library.profile)
        let hashesURL = library.profile.appendingPathComponent("LauncherIndex/update-hashes.json")
        var hashes = (try? InstallJournal.boundedRead(hashesURL, limit: 1_048_576)).flatMap { try? JSONDecoder().decode([String: DownloadIdentity].self, from: $0) } ?? [:]
        var result: [ModUpdate] = []
        for archive in inventory.archives {
            try cancellation.check()
            guard archive.filename != ModLibrary.ownMod, archive.problem == nil,
                  !retained.contains(archive.filename) || !inventory.disabled.contains(archive.filename) else { continue }
            progress(archive.modules.map(\.name).joined(separator: " + "))
            let candidates = archive.modules.compactMap { database.indexedByName[$0.name] }
            guard let candidate = candidates.first, candidates.count == archive.modules.count,
                  Set(candidates.map(\.key)).count == 1,
                  archive.modules.allSatisfy({ old in candidate.modules.contains { $0.name == old.name && !$0.version.parts.lexicographicallyPrecedes(old.version.parts) } }) else { continue }
            let newer = archive.modules.contains { old in candidate.modules.contains { $0.name == old.name && old.version.parts.lexicographicallyPrecedes($0.version.parts) } }
            var repacked = false
            if !newer {
                let identity = try hashes[archive.digest] ?? DownloadIdentity.read(library.mods.appendingPathComponent(archive.filename))
                guard identity.sha256 == archive.digest else { throw LibraryError("A mod changed while checking updates. Rescan and try again.") }
                hashes[archive.digest] = identity
                repacked = !candidate.accepts(identity)
            }
            guard newer || repacked else { continue }
            let protected = archive.modules.contains { library.specialPins[$0.name] != nil }
            let runtimeIssues = try DependencyPlanner.runtimeIssues(candidate.modules)
            result.append(ModUpdate(archive: archive, candidate: candidate, enabled: !inventory.disabled.contains(archive.filename),
                                    reason: protected ? "App-managed compatibility release. A future app update must approve this version." : !runtimeIssues.isEmpty ? Array(Set(runtimeIssues)).sorted().joined(separator: " ") + " Available after an app runtime update." : repacked ? "New archive published with the same version number." : "",
                                    canUpdate: !protected && runtimeIssues.isEmpty && candidate.modules.allSatisfy { DependencyPlanner.builtins[$0.name] == nil && library.specialPins[$0.name] == nil }))
        }
        // Keyed by the SHA already verified by the library, so an unchanged
        // large ZIP is not read again during subsequent availability checks.
        let currentHashes = Set(inventory.archives.map(\.digest))
        hashes = hashes.filter { currentHashes.contains($0.key) && $0.key == $0.value.sha256 }
        try InstallJournal.directory(hashesURL.deletingLastPathComponent())
        try InstallJournal.atomicWrite(try canonicalData(hashes), to: hashesURL)
        return result.sorted { $0.archive.filename < $1.archive.filename }
    }
}
