import Foundation
import Darwin

struct VerifiedDownload: Codable {
    let source: DownloadCandidate
    let identity: DownloadIdentity
    let archive: ModArchive
}

enum InstallJournal {
    struct Entry: Codable {
        let filename: String
        let cacheKey: String
        let sha256: String
        let bytes: UInt64
    }
    struct Record: Codable {
        var schema = 1
        let id: String
        var phase: String
        let revision: String
        let created: Date
        let oldState: Data?
        let newState: Data
        let files: [Entry]
        let sources: [DownloadCandidate]
        let retainedArchives: [String]
        var outcome: String?
    }
    static func root(_ profile: URL) -> URL { profile.appendingPathComponent("LauncherInstalls", isDirectory: true) }
    static func cache(_ profile: URL) -> URL { profile.appendingPathComponent("LauncherDownloads", isDirectory: true) }
    static func safeFile(_ name: String) -> Bool {
        !name.isEmpty && name.count <= 200 && name == (name as NSString).lastPathComponent &&
        !name.hasPrefix(".") && !name.contains("\\") && !name.contains(":") && name.rangeOfCharacter(from: .controlCharacters) == nil && name.lowercased().hasSuffix(".zip")
    }
    static func hex(_ text: String) -> Bool { text.count == 64 && text.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) } }
    static func directory(_ url: URL) throws {
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        let a = try FileManager.default.attributesOfItem(atPath: url.path)
        guard a[.type] as? FileAttributeType == .typeDirectory else { throw LibraryError("An install folder is not a regular directory.") }
    }
    static func atomicWrite(_ data: Data, to url: URL) throws {
        try data.write(to: url, options: .atomic)
        let f = try FileHandle(forWritingTo: url); defer { try? f.close() }; try f.synchronize()
        let fd = open(url.deletingLastPathComponent().path, O_RDONLY)
        if fd >= 0 { defer { close(fd) }; if fsync(fd) != 0 && errno != EINVAL { throw LibraryError("Could not synchronize the install journal.") } }
    }
    static func readState(_ url: URL) throws -> Data? {
        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        return try boundedRead(url, limit: 1_048_576)
    }
    static func boundedRead(_ url: URL, limit: Int) throws -> Data {
        let fd = open(url.path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw LibraryError("Could not read a launcher metadata file.") }
        let file = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
        defer { try? file.close() }
        var info = stat()
        guard fstat(fd, &info) == 0, (info.st_mode & S_IFMT) == S_IFREG, info.st_size >= 0, info.st_size <= limit else { throw LibraryError("A launcher metadata file is not a bounded regular file.") }
        let data = try file.read(upToCount: limit + 1) ?? Data()
        guard data.count <= limit, data.count == info.st_size else { throw LibraryError("A launcher metadata file changed while it was read.") }
        return data
    }
    private static func matches(_ file: URL, _ entry: Entry) -> Bool {
        guard let result = try? ModLibrary.hash(file) else { return false }; return result.0 == entry.sha256 && result.1 == entry.bytes
    }
    private static func validate(_ record: Record) throws {
        guard record.schema == 1, UUID(uuidString: record.id) != nil, record.files.count <= 1024,
              ["committing", "rollingBack", "committed", "rolledBack"].contains(record.phase),
              record.newState.count <= 1_048_576, (record.oldState?.count ?? 0) <= 1_048_576,
              Set(record.files.map(\.filename)).count == record.files.count,
              record.retainedArchives.count <= 1024, record.retainedArchives.allSatisfy(safeFile),
              record.sources.count == record.files.count,
              record.files.allSatisfy({ safeFile($0.filename) && $0.filename != ModLibrary.ownMod && hex($0.sha256) && hex($0.cacheKey) && $0.bytes > 0 && $0.bytes <= 4_294_967_296 }) else { throw LibraryError("The install journal is invalid. Existing files are preserved; export diagnostics.") }
        let next = try JSONDecoder().decode(LibraryState.self, from: record.newState)
        guard next.schema == 1 else { throw LibraryError("Unknown mod-choice format in the install journal.") }
    }
    private static func rollback(_ record: inout Record, profile: URL, journal: URL) throws {
        let fm = FileManager.default, mods = profile.appendingPathComponent("Mods"), state = profile.appendingPathComponent("launcher-mod-state.json")
        let current = try readState(state)
        guard current == record.oldState || current == record.newState else { throw LibraryError("Mod choices changed during an interrupted installation. Existing files are retained; export diagnostics before recovery.") }
        record.phase = "rollingBack"; try atomicWrite(try canonicalData(record), to: journal)
        for file in record.files {
            let installed = mods.appendingPathComponent(file.filename), staged = cache(profile).appendingPathComponent(file.cacheKey + ".zip")
            if fm.fileExists(atPath: installed.path) {
                guard matches(installed, file) else { throw LibraryError("A newly installed ZIP changed during recovery. It has been retained for inspection.") }
                if fm.fileExists(atPath: staged.path) {
                    guard matches(staged, file) else { throw LibraryError("The staged ZIP changed during recovery.") }
                    try fm.removeItem(at: installed)
                } else { try fm.moveItem(at: installed, to: staged) }
            }
        }
        if let old = record.oldState { try atomicWrite(old, to: state) }
        else if fm.fileExists(atPath: state.path) { try fm.removeItem(at: state) }
        record.phase = "rolledBack"; record.outcome = "Original mod selection restored; verified downloads retained."
        try atomicWrite(try canonicalData(record), to: journal)
    }
    static func recover(profile: URL) throws {
        let fm = FileManager.default, folder = root(profile)
        guard fm.fileExists(atPath: folder.path) else { return }
        try directory(folder); try directory(cache(profile)); try directory(profile.appendingPathComponent("Mods"))
        let files = try fm.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil).filter { $0.pathExtension == "json" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
        guard files.count <= 2048 else { throw LibraryError("There are too many installation receipts. Export them before continuing.") }
        for path in files {
            let data = try boundedRead(path, limit: 8_388_608)
            var record = try JSONDecoder().decode(Record.self, from: data); try validate(record)
            guard record.phase == "committing" || record.phase == "rollingBack" else { continue }
            let state = try readState(profile.appendingPathComponent("launcher-mod-state.json"))
            let installed = record.files.allSatisfy { matches(profile.appendingPathComponent("Mods").appendingPathComponent($0.filename), $0) }
            if record.phase == "committing" && state == record.newState && installed {
                record.phase = "committed"; record.outcome = "Completed installation recovered after process interruption."
                try atomicWrite(try canonicalData(record), to: path)
            } else { try rollback(&record, profile: profile, journal: path) }
        }
    }
    // Add new ZIPs without deleting/replacing any original archive. The single
    // mod-state rename is the commit point. Startup recovery runs before scans.
    static func commit(library: ModLibrary, inventory: LibraryInventory, plan: DependencyPlan,
                       verified: [String: VerifiedDownload], fault: ((String) throws -> Void)? = nil) throws -> Record {
        try library.synchronized {
            guard plan.issues.isEmpty, plan.revision == inventory.revision,
                  try LibraryInventory.read(library).revision == plan.revision else { throw LibraryError("Your mod library changed. Review a fresh dependency plan before installing.") }
            let fm = FileManager.default, profile = library.profile
            try directory(root(profile)); try directory(cache(profile)); try directory(library.mods)
            var entries: [Entry] = [], newDisabled = Set(inventory.disabled)
            for name in plan.enable { newDisabled.remove(name) }; newDisabled.formUnion(plan.disable)
            for source in plan.downloads {
                guard let value = verified[source.key], value.source.key == source.key, source.accepts(value.identity) else { throw LibraryError("A required download has not been verified.") }
                let name = value.archive.filename
                guard safeFile(name), !fm.fileExists(atPath: library.mods.appendingPathComponent(name).path) else { throw LibraryError("A download destination already exists. Rescan and review a fresh plan.") }
                let entry = Entry(filename: name, cacheKey: source.key, sha256: value.identity.sha256, bytes: value.identity.bytes)
                guard matches(cache(profile).appendingPathComponent(source.key + ".zip"), entry) else { throw LibraryError("A staged download changed. Download it again before installing.") }
                entries.append(entry)
                if plan.disabledDownloads.contains(where: { $0.key == source.key }) { newDisabled.insert(name) }
                else { newDisabled.remove(name) }
            }
            let next = LibraryState(disabled: newDisabled.sorted())
            var record = Record(id: UUID().uuidString, phase: "committing", revision: inventory.revision, created: Date(),
                                oldState: try readState(library.stateURL), newState: try canonicalData(next), files: entries, sources: plan.downloads, retainedArchives: plan.disable)
            try validate(record)
            let journal = root(profile).appendingPathComponent(record.id + ".json")
            let initial = try canonicalData(record)
            guard initial.count < 8_000_000 else { throw LibraryError("This installation receipt is too large. Choose fewer updates at once.") }
            try atomicWrite(initial, to: journal)
            do {
                try fault?("journal")
                for (i, file) in entries.enumerated() {
                    try fm.moveItem(at: cache(profile).appendingPathComponent(file.cacheKey + ".zip"), to: library.mods.appendingPathComponent(file.filename))
                    try fault?("file:\(i)")
                }
                try atomicWrite(record.newState, to: library.stateURL); try fault?("state")
                record.phase = "committed"; record.outcome = "Applied verified mod changes. Prior archives retained; disabled update choices preserved."
                try atomicWrite(try canonicalData(record), to: journal)
                library.invalidateCache(); return record
            } catch {
                // Fault-injection process exits do not enter this branch;
                // subsequent startup follows the same persisted journal.
                try rollback(&record, profile: profile, journal: journal)
                library.invalidateCache(); throw error
            }
        }
    }
    static func retainedArchives(profile: URL) throws -> Set<String> {
        let folder = root(profile)
        guard FileManager.default.fileExists(atPath: folder.path) else { return [] }
        var names = Set<String>()
        for path in try FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil) where path.pathExtension == "json" {
            let data = try boundedRead(path, limit: 8_388_608)
            let record = try JSONDecoder().decode(Record.self, from: data); try validate(record)
            if record.phase == "committed" { names.formUnion(record.retainedArchives) }
        }
        return names
    }
    static func diagnostics(profile: URL) -> [String: Any] {
        do {
            let folder = root(profile)
            guard FileManager.default.fileExists(atPath: folder.path) else { return ["schema": 1, "receipts": []] }
            let files = try FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: [.contentModificationDateKey]).filter { $0.pathExtension == "json" }.sorted {
                ((try? $0.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast) > ((try? $1.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast)
            }
            let receipts: [[String: Any]] = try files.prefix(8).map { path in
                let data = try boundedRead(path, limit: 8_388_608), record = try JSONDecoder().decode(Record.self, from: data)
                try validate(record)
                return ["id": record.id, "phase": record.phase, "revision": record.revision, "receiptSHA256": digestData(data), "created": ISO8601DateFormatter().string(from: record.created), "fileCount": record.files.count,
                        "files": try JSONSerialization.jsonObject(with: canonicalData(Array(record.files.prefix(128)))),
                        "sources": try JSONSerialization.jsonObject(with: canonicalData(Array(record.sources.prefix(128)))),
                        "retainedArchives": record.retainedArchives, "outcome": record.outcome ?? "", "selectionSHA256": digestData(record.newState)]
            }
            return ["schema": 1, "totalReceipts": files.count, "receipts": receipts, "boundedToRecent": 8, "filesPerReceiptLimit": 128]
        } catch { return ["schema": 1, "error": error.localizedDescription] }
    }
}
