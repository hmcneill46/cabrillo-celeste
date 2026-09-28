import Foundation
import CryptoKit
import ZIPFoundation
import Darwin

// The vault is a sibling of Profiles, never a child of the profile being saved.
// Callers serialize all operations and keep the managed runtime unused.
enum ProfileIO {
    static let fm = FileManager.default
    static let maxEntries = 50_000
    static let maxData: UInt64 = 2_147_483_648
    static let disposable = ["Cache", "Mods/Cache", "LauncherDownloads", "LauncherIndex"]
    static func key(_ path: String) -> String { path.precomposedStringWithCanonicalMapping.folding(options: [.caseInsensitive], locale: Locale(identifier: "en_US_POSIX")) }
    static func safe(_ path: String) -> Bool {
        let parts = path.split(separator: "/", omittingEmptySubsequences: false)
        return !path.isEmpty && path.utf8.count <= 1024 && parts.count <= 32 && !path.contains("\\") && !path.contains(":") && path.rangeOfCharacter(from: .controlCharacters) == nil && parts.allSatisfy { !$0.isEmpty && $0 != "." && $0 != ".." && $0.utf8.count <= 255 }
    }
    static func archivePath(_ path: String) -> Bool {
        let parts = path.split(separator: "/")
        return parts.count == 2 && key(String(parts[0])) == "mods" && path.lowercased().hasSuffix(".zip")
    }
    static func excluded(_ path: String) -> Bool {
        let k = key(path)
        return archivePath(path) || disposable.contains { k == key($0) || k.hasPrefix(key($0) + "/") }
    }
    static func attributes(_ url: URL) throws -> stat {
        var value = stat()
        guard lstat(url.path, &value) == 0, value.st_mode & S_IFMT != S_IFLNK else { throw LibraryError("A profile path is missing or is a symbolic link: \(url.lastPathComponent).") }
        return value
    }
    static func directory(_ url: URL) throws {
        guard url.isFileURL, url.standardizedFileURL.path == url.path, url.resolvingSymlinksInPath().path == url.path else { throw LibraryError("The profile location is not a direct local folder.") }
        if !fm.fileExists(atPath: url.path) { try fm.createDirectory(at: url, withIntermediateDirectories: true) }
        guard try attributes(url).st_mode & S_IFMT == S_IFDIR else { throw LibraryError("Expected a profile folder.") }
    }
    static func sync(_ url: URL) throws {
        let fd = open(url.path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw LibraryError("Could not synchronize profile storage.") }
        defer { close(fd) }
        guard fsync(fd) == 0 else { throw LibraryError("Profile storage could not be synchronized.") }
    }
    static func write(_ data: Data, to url: URL) throws {
        try directory(url.deletingLastPathComponent())
        try data.write(to: url, options: .atomic); try sync(url); try sync(url.deletingLastPathComponent())
    }
    static func encode<T: Encodable>(_ value: T) throws -> Data {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        return try encoder.encode(value)
    }
    static func read(_ url: URL, limit: UInt64) throws -> Data {
        var result = Data()
        _ = try stream(url, limit: limit) { result.append($0) }
        return result
    }
    static func stream(_ url: URL, limit: UInt64, consume: (Data) throws -> Void = { _ in }) throws -> (String, UInt64) {
        let fd = open(url.path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw LibraryError("Could not read \(url.lastPathComponent).") }
        let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true); defer { try? handle.close() }
        var before = stat()
        guard fstat(fd, &before) == 0, before.st_mode & S_IFMT == S_IFREG, before.st_nlink == 1, before.st_size >= 0, UInt64(before.st_size) <= limit else { throw LibraryError("Unsupported or oversized file: \(url.lastPathComponent). Hard links are not supported.") }
        var bytes: UInt64 = 0, hash = SHA256()
        while let data = try handle.read(upToCount: 65_536), !data.isEmpty {
            bytes += UInt64(data.count)
            guard bytes <= UInt64(before.st_size) else { throw LibraryError("A profile file changed while it was read.") }
            hash.update(data: data); try consume(data)
        }
        var after = stat()
        guard fstat(fd, &after) == 0, bytes == UInt64(before.st_size), before.st_mtimespec.tv_sec == after.st_mtimespec.tv_sec, before.st_mtimespec.tv_nsec == after.st_mtimespec.tv_nsec else { throw LibraryError("A profile file changed while it was read. Try again after closing the game.") }
        return (hash.finalize().map { String(format: "%02x", $0) }.joined(), bytes)
    }
    static func hash(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
    struct File: Codable, Equatable {
        let path: String
        let directory: Bool
        let bytes: UInt64
        let sha256: String
        let modified: Double
    }
    static func validate(_ files: [File], portable: Bool) throws {
        guard files.count <= maxEntries else { throw LibraryError("A profile may contain at most 50,000 entries.") }
        var paths: [String: Bool] = [:], total: UInt64 = 0
        for row in files {
            guard safe(row.path), paths[key(row.path)] == nil, row.modified.isFinite,
                  !portable || !excluded(row.path), row.bytes <= (portable ? 536_870_912 : 4_294_967_296),
                  row.directory ? row.bytes == 0 && row.sha256.isEmpty : InstallJournal.hex(row.sha256) else { throw LibraryError("Invalid, duplicate, reserved or oversized profile entry: \(row.path).") }
            paths[key(row.path)] = row.directory
            total += row.bytes
            guard total <= (portable ? maxData : 68_719_476_736) else { throw LibraryError("This profile exceeds the backup size limit (2 GiB of persistent data).") }
        }
        for row in files {
            var parts = row.path.split(separator: "/"); parts.removeLast()
            while !parts.isEmpty {
                guard paths[key(parts.joined(separator: "/"))] == true else { throw LibraryError("A profile entry has a missing or conflicting parent folder.") }
                parts.removeLast()
            }
        }
    }
    static func tree(_ root: URL, portable: Bool) throws -> [File] {
        try directory(root)
        var rows: [File] = [], seen = Set<String>()
        func visit(_ folder: URL, prefix: String) throws {
            for url in try fm.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil).sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) {
                let path = prefix + url.lastPathComponent
                guard safe(path), seen.insert(key(path)).inserted else { throw LibraryError("A profile contains conflicting file names.") }
                let value = try attributes(url)
                if portable && excluded(path) { continue }
                let isDir = value.st_mode & S_IFMT == S_IFDIR
                guard isDir || value.st_mode & S_IFMT == S_IFREG else { throw LibraryError("The profile contains a special file: \(path).") }
                let identity = isDir ? ("", UInt64(0)) : try stream(url, limit: portable ? 536_870_912 : 4_294_967_296)
                rows.append(File(path: path, directory: isDir, bytes: identity.1, sha256: identity.0, modified: Double(value.st_mtimespec.tv_sec)))
                guard rows.count <= maxEntries else { throw LibraryError("Too many profile files.") }
                if isDir { try visit(url, prefix: path + "/") }
            }
        }
        try visit(root, prefix: ""); try validate(rows, portable: portable)
        return rows.sorted { $0.path < $1.path }
    }
    static func revision(_ rows: [File]) -> String {
        hash(Data(rows.sorted { $0.path < $1.path }.map { "\($0.path)\u{0}\($0.directory)\u{0}\($0.bytes)\u{0}\($0.sha256)" }.joined(separator: "\n").utf8))
    }
    static func move(_ source: URL, _ target: URL) throws {
        guard !fm.fileExists(atPath: target.path) else { throw LibraryError("A restore destination already exists. Existing files have been retained.") }
        try fm.moveItem(at: source, to: target); try sync(source.deletingLastPathComponent()); try sync(target.deletingLastPathComponent())
    }
}

final class ProfileBackups {
    struct Module: Codable, Equatable { let name: String; let version: String }
    struct Mod: Codable, Equatable { let filename: String; let sha256: String; let bytes: UInt64; let modules: [Module]; let enabled: Bool }
    struct Manifest: Codable {
        var format = "CabrilloProfile"
        var schema = 1
        var launcherSettingsSchema = 1
        var touchLayoutSchema = "builtin-shared-ios-v1"
        let id: String
        let created: String
        let runtime: [String: String]
        let files: [ProfileIO.File]
        let mods: [Mod]
    }
    struct Journal: Codable {
        var schema = 1
        var phase: String
        let backupID: String
        let oldRevision: String
        var newRevision: String
    }
    struct Review {
        let id: String
        let manifest: Manifest
        let currentRevision: String
        let issues: [String]
    }
    let library: ModLibrary
    let vault: URL
    var profile: URL { library.profile }
    var archives: URL { vault.appendingPathComponent("Archives") }
    var reviewRoot: URL { vault.appendingPathComponent("Review") }
    var transaction: URL { vault.appendingPathComponent("Transaction") }
    var journalURL: URL { transaction.appendingPathComponent("journal.json") }
    var old: URL { transaction.appendingPathComponent("Old") }
    var next: URL { transaction.appendingPathComponent("New") }
    var review: Review?
    var slotReview: SaveTransfer.Review?
    var fault: ((String) throws -> Void)? // Only injected by the isolated host harness.
    static let preferenceKeys = ["launcher.metrics", "launcher.cellularDownloads", "launcher.autoUpdateChecks"]
    static let preferencesFile = "launcher-preferences.json"
    init(library: ModLibrary, vault: URL) { self.library = library; self.vault = vault }
    func initialize(defaults: [String: Bool]) throws -> [String: Bool] {
        try ProfileIO.directory(vault); try ProfileIO.directory(archives)
        try recover()
        try ProfileIO.directory(profile)
        let path = profile.appendingPathComponent(Self.preferencesFile)
        if !ProfileIO.fm.fileExists(atPath: path.path) { try setPreferences(defaults) }
        return try preferences()
    }
    func preferences() throws -> [String: Bool] {
        let data = try ProfileIO.read(profile.appendingPathComponent(Self.preferencesFile), limit: 16_384)
        let values = try JSONDecoder().decode([String: Bool].self, from: data)
        guard Set(values.keys) == Set(Self.preferenceKeys) else { throw LibraryError("The launcher settings format is unsupported. Your files are retained.") }
        return values
    }
    func setPreferences(_ values: [String: Bool]) throws {
        guard Set(values.keys) == Set(Self.preferenceKeys) else { throw LibraryError("Invalid launcher preferences.") }
        try ProfileIO.write(try ProfileIO.encode(values), to: profile.appendingPathComponent(Self.preferencesFile))
    }
    func modList() throws -> [Mod] {
        let disabled = Set(try library.state().disabled)
        let records = try library.scan(force: true)
        let zipNames = try ProfileIO.fm.contentsOfDirectory(at: library.mods, includingPropertiesForKeys: nil).filter { $0.pathExtension.lowercased() == "zip" }.map(\.lastPathComponent)
        guard Set(zipNames) == Set(records.map(\.filename)) else { throw LibraryError("An unrecognized or unfinished ZIP is present in Mods. Finish or remove that import before backing up.") }
        return try records.map { row in
            guard row.problem == nil, InstallJournal.safeFile(row.filename), !row.digest.isEmpty else { throw LibraryError("Resolve the mod library issue for \(row.filename) before making a backup.") }
            return Mod(filename: row.filename, sha256: row.digest, bytes: row.bytes,
                       modules: row.modules.map { Module(name: $0.name, version: $0.version.text) }, enabled: !disabled.contains(row.filename))
        }.sorted { $0.filename < $1.filename }
    }
    func create() throws -> URL { try library.synchronized {
        guard review == nil, slotReview == nil else { throw LibraryError("Close the restore review first.") }
        try recover(); _ = try preferences()
        guard try ProfileIO.fm.contentsOfDirectory(at: archives, includingPropertiesForKeys: nil).count < 100 else { throw LibraryError("Export and remove a backup before making another (100 retained backups).") }
        let mods = try modList(), files = try ProfileIO.tree(profile, portable: true)
        let manifest = Manifest(id: UUID().uuidString, created: ISO8601DateFormatter().string(from: Date()), runtime: RuntimeIdentity.builtins, files: files, mods: mods)
        let temporary = archives.appendingPathComponent(manifest.id + ".partial"), final = archives.appendingPathComponent(manifest.id + ".zip")
        defer { try? ProfileIO.fm.removeItem(at: temporary) }
        do {
            let archive = try Archive(url: temporary, accessMode: .create)
            let data = try ProfileIO.encode(manifest)
            try archive.addEntry(with: "manifest.json", type: .file, uncompressedSize: Int64(data.count), compressionMethod: .deflate) { offset, size in data.subdata(in: Int(offset)..<Int(offset) + size) }
            for row in files {
                try archive.addEntry(with: "Profile/" + row.path, fileURL: profile.appendingPathComponent(row.path), compressionMethod: .deflate)
            }
        }
        _ = try readBundle(temporary, destination: nil)
        guard ProfileIO.revision(files) == ProfileIO.revision(try ProfileIO.tree(profile, portable: true)), mods == (try modList()) else { throw LibraryError("The profile changed during backup. Try again with the game closed.") }
        try ProfileIO.sync(temporary); try ProfileIO.move(temporary, final)
        return final
    } }
    func readManifest(_ archive: Archive) throws -> Manifest {
        guard let entry = archive["manifest.json"], entry.type == .file, entry.uncompressedSize <= 16_777_216 else { throw LibraryError("Choose a Cabrillo profile backup with a supported manifest.") }
        var data = Data()
        let crc = try archive.extract(entry, bufferSize: 65_536) { chunk in
            guard data.count + chunk.count <= 16_777_216 else { throw LibraryError("Backup manifest is too large.") }; data.append(chunk)
        }
        guard crc == entry.checksum, UInt64(data.count) == entry.uncompressedSize else { throw LibraryError("Backup manifest checksum failed.") }
        let manifest = try JSONDecoder().decode(Manifest.self, from: data)
        guard manifest.format == "CabrilloProfile", manifest.schema == 1, manifest.launcherSettingsSchema == 1, manifest.touchLayoutSchema == "builtin-shared-ios-v1", UUID(uuidString: manifest.id) != nil, ISO8601DateFormatter().date(from: manifest.created) != nil, manifest.mods.count <= 1024 else { throw LibraryError("This backup uses an unsupported format or layout version.") }
        try ProfileIO.validate(manifest.files, portable: true)
        var names = Set<String>()
        for mod in manifest.mods {
            guard InstallJournal.safeFile(mod.filename), names.insert(ProfileIO.key(mod.filename)).inserted, InstallJournal.hex(mod.sha256), mod.bytes > 0, mod.bytes <= 4_294_967_296, !mod.modules.isEmpty, mod.modules.count <= 64, mod.modules.allSatisfy({ !$0.name.isEmpty && $0.name.count <= 200 && $0.version.count <= 200 }) else { throw LibraryError("Invalid mod identities in this backup.") }
        }
        return manifest
    }
    @discardableResult func readBundle(_ url: URL, destination: URL?) throws -> Manifest {
        _ = try ProfileIO.attributes(url)
        guard try ProfileIO.attributes(url).st_size <= Int64(ProfileIO.maxData + 33_554_432) else { throw LibraryError("This backup exceeds 2 GiB.") }
        let archive = try Archive(url: url, accessMode: .read), manifest = try readManifest(archive)
        var entries: [String: Entry] = [:]
        for entry in archive {
            let path = entry.type == .directory && entry.path.hasSuffix("/") ? String(entry.path.dropLast()) : entry.path
            guard ProfileIO.safe(path), entry.type != .symlink, entries[ProfileIO.key(path)] == nil, entries.count <= ProfileIO.maxEntries else { throw LibraryError("Backup contains duplicate, unsafe or unsupported entries.") }
            entries[ProfileIO.key(path)] = entry
        }
        let expected = Set(["manifest.json"] + manifest.files.map { ProfileIO.key("Profile/" + $0.path) })
        guard Set(entries.keys) == expected else { throw LibraryError("Backup contents do not match its manifest.") }
        if let destination { try ProfileIO.directory(destination) }
        for row in manifest.files.sorted(by: { $0.path < $1.path }) {
            guard let entry = entries[ProfileIO.key("Profile/" + row.path)], entry.type == (row.directory ? .directory : .file), entry.uncompressedSize == row.bytes else { throw LibraryError("A backup entry has an incorrect type or length.") }
            let output = destination?.appendingPathComponent(row.path)
            if row.directory { if let output { try ProfileIO.directory(output) }; continue }
            var handle: FileHandle?
            if let output {
                let fd = open(output.path, O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW, S_IRUSR | S_IWUSR)
                guard fd >= 0 else { throw LibraryError("Could not stage a profile file.") }
                handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
            }
            defer { try? handle?.close() }
            var hash = SHA256(), count: UInt64 = 0
            let crc = try archive.extract(entry, bufferSize: 65_536) { data in
                count += UInt64(data.count)
                guard count <= row.bytes else { throw LibraryError("A backup entry expands beyond its declared size.") }
                hash.update(data: data); try handle?.write(contentsOf: data)
            }
            guard count == row.bytes, crc == entry.checksum, hash.finalize().map({ String(format: "%02x", $0) }).joined() == row.sha256 else { throw LibraryError("A backup file failed its SHA-256 or ZIP checksum.") }
            try handle?.synchronize(); try handle?.close(); handle = nil
            if let output { try ProfileIO.fm.setAttributes([.modificationDate: Date(timeIntervalSince1970: row.modified)], ofItemAtPath: output.path) }
        }
        return manifest
    }
    func issues(for manifest: Manifest, current: [Mod]) -> [String] {
        var issues: [String] = []
        if manifest.runtime != RuntimeIdentity.builtins { issues.append("This backup needs a different bundled Everest/runtime version.") }
        let currentMap = Dictionary(uniqueKeysWithValues: current.map { ($0.filename, $0) })
        let expected = Set(manifest.mods.map(\.filename))
        for mod in manifest.mods {
            guard let installed = currentMap[mod.filename] else { issues.append("Missing \(mod.filename) · SHA-256 \(mod.sha256)"); continue }
            if installed.sha256 != mod.sha256 || installed.bytes != mod.bytes || installed.modules != mod.modules { issues.append("Different archive: \(mod.filename) · requires SHA-256 \(mod.sha256)") }
        }
        for mod in current where !expected.contains(mod.filename) { issues.append("Additional archive: \(mod.filename). The installed archive set must match before restoring.") }
        return issues
    }
    func prepare(_ url: URL) throws -> Review { try library.synchronized {
        guard review == nil, slotReview == nil else { throw LibraryError("A backup is already being reviewed.") }
        try recover()
        guard try !hasRetainedProfile() else { throw LibraryError("A previous profile is still retained. Roll it back or explicitly discard it before another restore.") }
        if ProfileIO.fm.fileExists(atPath: reviewRoot.path) { try ProfileIO.fm.removeItem(at: reviewRoot) }
        try ProfileIO.directory(reviewRoot)
        do {
            let copied = reviewRoot.appendingPathComponent("backup.zip")
            let fd = open(copied.path, O_CREAT | O_EXCL | O_WRONLY, S_IRUSR | S_IWUSR)
            guard fd >= 0 else { throw LibraryError("Could not stage the backup.") }
            let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true); defer { try? handle.close() }
            _ = try ProfileIO.stream(url, limit: ProfileIO.maxData + 33_554_432) { try handle.write(contentsOf: $0) }; try handle.synchronize(); try handle.close()
            let manifest = try readBundle(copied, destination: reviewRoot.appendingPathComponent("Profile"))
            let current = try modList()
            let preferencesURL = reviewRoot.appendingPathComponent("Profile/" + Self.preferencesFile)
            let prefs = try JSONDecoder().decode([String: Bool].self, from: ProfileIO.read(preferencesURL, limit: 16_384))
            guard Set(prefs.keys) == Set(Self.preferenceKeys) else { throw LibraryError("The backup is missing its launcher settings.") }
            let stagedLibrary = ModLibrary(profile: reviewRoot.appendingPathComponent("Profile"))
            let disabled = Set(try stagedLibrary.state().disabled)
            guard manifest.mods.allSatisfy({ $0.enabled == !disabled.contains($0.filename) }) else { throw LibraryError("The backup’s mod choices disagree with its manifest.") }
            let value = Review(id: UUID().uuidString, manifest: manifest, currentRevision: ProfileIO.revision(try ProfileIO.tree(profile, portable: false)), issues: issues(for: manifest, current: current))
            review = value; return value
        } catch { try? ProfileIO.fm.removeItem(at: reviewRoot); throw error }
    } }
    func cancelReview() throws { slotReview = nil; if ProfileIO.fm.fileExists(atPath: slotRoot.path) { try ProfileIO.fm.removeItem(at: slotRoot) }; review = nil; if ProfileIO.fm.fileExists(atPath: reviewRoot.path) { try ProfileIO.fm.removeItem(at: reviewRoot) } }
    func readJournal() throws -> Journal? {
        guard ProfileIO.fm.fileExists(atPath: transaction.path) else { return nil }
        try ProfileIO.directory(transaction)
        // A directory created before the first durable journal is staging only.
        guard ProfileIO.fm.fileExists(atPath: journalURL.path) else {
            guard !ProfileIO.fm.fileExists(atPath: old.path) else { throw LibraryError("A retained profile has no recovery record. Export diagnostics before repairing it.") }; return nil
        }
        let journal = try JSONDecoder().decode(Journal.self, from: ProfileIO.read(journalURL, limit: 16_384))
        guard journal.schema == 1, ["prepared", "committed", "aborted", "undoing", "undone"].contains(journal.phase), UUID(uuidString: journal.backupID) != nil, InstallJournal.hex(journal.oldRevision), InstallJournal.hex(journal.newRevision) else { throw LibraryError("The restore recovery record is unsupported. All files are retained.") }
        return journal
    }
    func saveJournal(_ value: Journal) throws { try ProfileIO.write(try ProfileIO.encode(value), to: journalURL) }
    func verifyTree(_ url: URL, _ revision: String) throws {
        guard ProfileIO.fm.fileExists(atPath: url.path), ProfileIO.revision(try ProfileIO.tree(url, portable: false)) == revision else { throw LibraryError("A retained or staged profile changed. All copies have been retained; export diagnostics before recovery.") }
    }
    func recover() throws {
        guard var journal = try readJournal() else { return }
        if journal.phase == "prepared" {
            if ProfileIO.fm.fileExists(atPath: old.path) {
                try verifyTree(old, journal.oldRevision)
                if ProfileIO.fm.fileExists(atPath: profile.path) { try verifyTree(profile, journal.newRevision); try ProfileIO.move(profile, next) }
                try ProfileIO.move(old, profile)
            } else { try verifyTree(profile, journal.oldRevision) }
            journal.phase = "aborted"; try saveJournal(journal); library.invalidateCache()
        } else if journal.phase == "undoing" {
            if ProfileIO.fm.fileExists(atPath: old.path) {
                try verifyTree(old, journal.oldRevision)
                if ProfileIO.fm.fileExists(atPath: profile.path) { try verifyTree(profile, journal.newRevision); try ProfileIO.move(profile, next) }
                try ProfileIO.move(old, profile)
            } else { try verifyTree(profile, journal.oldRevision) }
            journal.phase = "undone"; try saveJournal(journal); library.invalidateCache()
        }
        guard ProfileIO.fm.fileExists(atPath: profile.path) else { throw LibraryError("The current profile is missing. Recovery requires inspection; existing copies are retained.") }
    }
    func hasRetainedProfile() throws -> Bool { guard let journal = try readJournal() else { return false }; return journal.phase == "committed" || journal.phase == "undone" }
    func restore(_ id: String) throws { try library.synchronized {
        guard let review, review.id == id, review.issues.isEmpty else { throw LibraryError("Review a compatible backup before restoring.") }
        guard try !hasRetainedProfile(), ProfileIO.revision(try ProfileIO.tree(profile, portable: false)) == review.currentRevision, issues(for: review.manifest, current: try modList()).isEmpty else { throw LibraryError("The current profile changed. Cancel and review the backup again.") }
        let staged = reviewRoot.appendingPathComponent("Profile")
        guard ProfileIO.revision(try ProfileIO.tree(staged, portable: true)) == ProfileIO.revision(review.manifest.files) else { throw LibraryError("The reviewed backup changed.") }
        if ProfileIO.fm.fileExists(atPath: transaction.path) { try ProfileIO.fm.removeItem(at: transaction) }
        try ProfileIO.directory(transaction)
        // Copy only the exact verified archives; all persistent profile files come
        // from the snapshot. FileManager uses copy-on-write where available.
        for mod in review.manifest.mods {
            let target = staged.appendingPathComponent("Mods/" + mod.filename)
            try ProfileIO.directory(target.deletingLastPathComponent())
            try ProfileIO.fm.copyItem(at: profile.appendingPathComponent("Mods/" + mod.filename), to: target)
            let identity = try ProfileIO.stream(target, limit: 4_294_967_296)
            guard identity.0 == mod.sha256, identity.1 == mod.bytes else { throw LibraryError("A mod archive changed while staging the restore.") }
            try ProfileIO.sync(target)
        }
        try commitProfile(staged, currentRevision: review.currentRevision, id: review.manifest.id)
        self.review = nil
    } }
    // Both whole-profile restores and individual save replacements use the same
    // durable profile swap and recovery record. Old profiles never get merged.
    func commitProfile(_ staged: URL, currentRevision: String, id: String) throws {
        guard try !hasRetainedProfile() else { throw LibraryError("A previous profile is still retained.") }
        let rows = try ProfileIO.tree(staged, portable: false)
        for row in rows where !row.directory { try ProfileIO.sync(staged.appendingPathComponent(row.path)) }
        for row in rows.reversed() where row.directory { try ProfileIO.sync(staged.appendingPathComponent(row.path)) }
        try ProfileIO.sync(staged)
        try verifyTree(profile, currentRevision)
        if ProfileIO.fm.fileExists(atPath: transaction.path) { try ProfileIO.fm.removeItem(at: transaction) }
        try ProfileIO.directory(transaction)
        try ProfileIO.move(staged, next)
        let newRevision = ProfileIO.revision(try ProfileIO.tree(next, portable: false))
        var journal = Journal(phase: "prepared", backupID: id, oldRevision: currentRevision, newRevision: newRevision)
        try saveJournal(journal); try fault?("prepared")
        try ProfileIO.move(profile, old); try fault?("old_moved")
        try ProfileIO.move(next, profile); try fault?("new_moved")
        journal.phase = "committed"; try saveJournal(journal); try fault?("committed")
        library.invalidateCache()
    }
    func rollback() throws { try library.synchronized {
        guard review == nil, slotReview == nil, var journal = try readJournal(), journal.phase == "committed" else { throw LibraryError("There is no previous profile available to roll back.") }
        try verifyTree(old, journal.oldRevision)
        journal.newRevision = ProfileIO.revision(try ProfileIO.tree(profile, portable: false))
        journal.phase = "undoing"; try saveJournal(journal); try fault?("undo_prepared")
        try ProfileIO.move(profile, next); try fault?("undo_current_moved")
        try ProfileIO.move(old, profile); try fault?("undo_old_moved")
        journal.phase = "undone"; try saveJournal(journal); try fault?("undone")
        library.invalidateCache()
    } }
    func discardRetainedProfile() throws {
        guard review == nil, slotReview == nil, let journal = try readJournal(), ["committed", "undone"].contains(journal.phase) else { throw LibraryError("No completed restore can be cleared.") }
        try ProfileIO.directory(profile)
        // Detach the completed record atomically before deletion. A process death
        // while removing its tree must not leave an active half-deleted journal.
        let discarded = vault.appendingPathComponent("Discarded-" + UUID().uuidString)
        try ProfileIO.move(transaction, discarded)
        try ProfileIO.fm.removeItem(at: discarded); try ProfileIO.sync(vault)
    }
    func archive(_ id: String) throws -> URL {
        guard UUID(uuidString: id) != nil else { throw LibraryError("Unknown backup.") }
        let url = archives.appendingPathComponent(id + ".zip")
        guard try readManifest(Archive(url: url, accessMode: .read)).id == id else { throw LibraryError("The backup identity does not match its file.") }
        return url
    }
    func state() throws -> [String: Any] {
        var backups: [[String: Any]] = []
        for url in try ProfileIO.fm.contentsOfDirectory(at: archives, includingPropertiesForKeys: nil).filter({ $0.pathExtension == "zip" }).prefix(100) {
            let id = url.deletingPathExtension().lastPathComponent
            do {
                let m = try readManifest(Archive(url: archive(id), accessMode: .read))
                backups.append(["id": id, "created": m.created, "files": m.files.filter { !$0.directory }.count, "slots": ProfileSlots.identifiers(m.files.map(\.path)).count, "bytes": m.files.reduce(UInt64(0)) { $0 + $1.bytes }])
            } catch { backups.append(["id": id, "created": "Unreadable backup", "error": error.localizedDescription]) }
        }
        let journal = try readJournal()
        var result: [String: Any] = ["slots": try ProfileSlots.read(profile), "backups": backups.sorted { ($0["created"] as? String ?? "") > ($1["created"] as? String ?? "") }, "canRollback": journal?.phase == "committed", "retained": journal?.phase == "committed" || journal?.phase == "undone", "preferences": try preferences()]
        if let review {
            result["review"] = ["id": review.id, "created": review.manifest.created, "files": review.manifest.files.filter { !$0.directory }.count, "slots": ProfileSlots.identifiers(review.manifest.files.map(\.path)).count, "bytes": review.manifest.files.reduce(UInt64(0)) { $0 + $1.bytes }, "mods": review.manifest.mods.map { ["filename": $0.filename, "sha256": $0.sha256, "enabled": $0.enabled, "modules": $0.modules.map { ["name": $0.name, "version": $0.version] }] }, "issues": review.issues]
        }
        if let slotReview {
            result["slotReview"] = ["id": slotReview.id, "source": slotReview.source, "target": slotReview.target, "incoming": slotReview.incoming, "existing": slotReview.existing, "mainOnly": slotReview.mainOnly, "files": slotReview.files.map(\.path)]
        }
        return result
    }
}
