import Foundation
import ZIPFoundation
import Darwin

// Desktop-compatible files, unchanged internally. Everest assigns the slot index
// from the filename on load. Custom mod bytes are never parsed or rewritten.
enum SaveTransfer {
    static let maxBytes: UInt64 = 536_870_912
    static let maxFile: UInt64 = 134_217_728
    static let maxFiles = 4096
    struct Manifest: Codable {
        var format = "CabrilloSave"
        var schema = 1
        let created: String
        let sourceSlot: Int
        let files: [ProfileIO.File]
    }
    struct Review {
        let id: String
        let source: Int
        let target: Int
        let files: [ProfileIO.File]
        let currentRevision: String
        let incoming: [String: Any]
        let existing: [String: Any]
        let mainOnly: Bool
    }
    static func slot(_ name: String) -> Int? {
        guard ProfileIO.safe(name), !name.contains("/"), let id = ProfileSlots.identifier("Saves/" + name),
              name == "\(id).celeste" || name.hasPrefix("\(id)-mod") else { return nil }
        return id
    }
    static func files(_ directory: URL, slot id: Int? = nil) throws -> [ProfileIO.File] {
        let rows = try ProfileIO.tree(directory, portable: true)
        let selected = id.map { value in rows.filter { ProfileSlots.identifier("Saves/" + $0.path) == value } } ?? rows
        guard !selected.isEmpty, selected.count <= maxFiles, selected.allSatisfy({ !$0.directory && slot($0.path) != nil && $0.bytes <= maxFile }), selected.reduce(UInt64(0), { $0 + $1.bytes }) <= maxBytes else { throw LibraryError("Choose one save’s numbered .celeste files, up to 512 MiB and 4,096 files. Folders and unrelated files are not save data.") }
        return selected
    }
    static func copy(_ source: URL, to target: URL) throws {
        let fd = open(target.path, O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW, S_IRUSR | S_IWUSR)
        guard fd >= 0 else { throw LibraryError("A save file could not be staged, or its name is duplicated.") }
        let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true); defer { try? handle.close() }
        _ = try ProfileIO.stream(source, limit: maxBytes + 16_777_216) { try handle.write(contentsOf: $0) }
        try handle.synchronize(); try handle.close()
        let stamp = try ProfileIO.attributes(source).st_mtimespec.tv_sec
        try ProfileIO.fm.setAttributes([.modificationDate: Date(timeIntervalSince1970: Double(stamp))], ofItemAtPath: target.path)
    }
    static func unpack(_ url: URL, to output: URL) throws {
        let archive = try Archive(url: url, accessMode: .read)
        var names = Set<String>(), total: UInt64 = 0, count = 0, metadata: Data?
        for entry in archive {
            count += 1
            guard count <= maxFiles + 3, entry.type != .symlink, ProfileIO.safe(entry.path.hasSuffix("/") ? String(entry.path.dropLast()) : entry.path) else { throw LibraryError("The save ZIP has unsafe or too many entries.") }
            if entry.type == .directory && entry.path == "Saves/" { continue }
            let name = entry.path.hasPrefix("Saves/") ? String(entry.path.dropFirst(6)) : entry.path
            let isManifest = entry.path == "cabrillo-save.json", isReadme = entry.path == "README.txt"
            guard entry.type == .file, names.insert(ProfileIO.key(name)).inserted,
                  (slot(name) != nil || isManifest || isReadme), entry.uncompressedSize <= (isManifest || isReadme ? 1_048_576 : maxFile) else { throw LibraryError("Choose a ZIP containing one slot’s .celeste files, at its root or inside Saves. Unrelated files, links and duplicate names are not supported.") }
            total += entry.uncompressedSize
            guard total <= maxBytes else { throw LibraryError("The save ZIP expands beyond 512 MiB.") }
            let destination = output.appendingPathComponent(name)
            var handle: FileHandle?, data = Data(), bytes: UInt64 = 0
            if !isManifest && !isReadme {
                let fd = open(destination.path, O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW, S_IRUSR | S_IWUSR)
                guard fd >= 0 else { throw LibraryError("Could not stage a save file.") }
                handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
            }
            defer { try? handle?.close() }
            let crc = try archive.extract(entry, bufferSize: 65_536) { chunk in
                bytes += UInt64(chunk.count)
                guard bytes <= entry.uncompressedSize else { throw LibraryError("A save file expands beyond its declared size.") }
                if isManifest { data.append(chunk) }
                try handle?.write(contentsOf: chunk)
            }
            guard bytes == entry.uncompressedSize, crc == entry.checksum else { throw LibraryError("A save file failed its ZIP checksum.") }
            try handle?.synchronize(); try handle?.close(); handle = nil
            if isManifest { metadata = data }
            if !isManifest && !isReadme { try ProfileIO.fm.setAttributes([.modificationDate: entry.fileAttributes[.modificationDate] ?? Date()], ofItemAtPath: destination.path) }
        }
        if let metadata {
            let manifest = try JSONDecoder().decode(Manifest.self, from: metadata)
            try ProfileIO.validate(manifest.files, portable: true)
            let actual = try files(output)
            guard manifest.format == "CabrilloSave", manifest.schema == 1, ISO8601DateFormatter().date(from: manifest.created) != nil,
                  manifest.files.allSatisfy({ !$0.directory && slot($0.path) == manifest.sourceSlot }), ProfileIO.revision(actual) == ProfileIO.revision(manifest.files) else { throw LibraryError("The save ZIP does not match its transfer manifest.") }
            for row in manifest.files { try ProfileIO.fm.setAttributes([.modificationDate: Date(timeIntervalSince1970: row.modified)], ofItemAtPath: output.appendingPathComponent(row.path).path) }
        }
    }
}

extension ProfileBackups {
    var slotRoot: URL { vault.appendingPathComponent("SlotReview") }
    func exportSlot(_ id: Int, mainOnly: Bool) throws -> URL { try library.synchronized {
        try recover()
        let saves = profile.appendingPathComponent("Saves")
        let all = try SaveTransfer.files(saves, slot: id)
        let rows = mainOnly ? all.filter { $0.path == "\(id).celeste" } : all
        guard !rows.isEmpty else { throw LibraryError("This slot has no main save file. Export its mod files together to preserve them.") }
        let root = vault.appendingPathComponent("SlotExport")
        if ProfileIO.fm.fileExists(atPath: root.path) { try ProfileIO.fm.removeItem(at: root) }
        try ProfileIO.directory(root)
        let output = root.appendingPathComponent(mainOnly ? "\(id).celeste" : "Celeste-Slot-\(id + 1).zip")
        if mainOnly { try SaveTransfer.copy(saves.appendingPathComponent(rows[0].path), to: output) }
        else {
            do {
                let archive = try Archive(url: output, accessMode: .create)
                let manifest = SaveTransfer.Manifest(created: ISO8601DateFormatter().string(from: Date()), sourceSlot: id, files: rows)
                let readme = """
                Celeste slot \(id + 1) (files start with \(id)).
                Close Celeste on both devices and back up the destination Saves folder first.
                Copy ALL .celeste files together into the desktop Saves folder. To change slots,
                rename the numeric prefix on every file consistently. Vanilla uses 0, 1 and 2.
                Remove the destination slot's old -mod*.celeste files when replacing a complete
                slot, so unrelated mod progress is not mixed. Keep a backup of those old files.
                Cabrillo: choose a slot > Replace from Files, or Import another save; select this ZIP.
                Compatible Everest/mod versions and maps are needed for mod progress and sessions.
                Files stored by mods outside this slot's standard Saves files are not included.
                Older game versions and other platform containers may use incompatible formats.
                Time and deaths describe progress; modification dates alone do not establish which
                copy is newer. This is manual replacement, not a merge or automatic cloud sync.
                Windows: <game folder>/Saves
                macOS: ~/Library/Application Support/Celeste/Saves
                Linux: ~/.local/share/Celeste/Saves (or $XDG_DATA_HOME/Celeste/Saves)
                """
                for (name, data) in [("cabrillo-save.json", try ProfileIO.encode(manifest)), ("README.txt", Data(readme.utf8))] {
                    try archive.addEntry(with: name, type: .file, uncompressedSize: Int64(data.count), compressionMethod: .deflate) { offset, size in data.subdata(in: Int(offset)..<Int(offset) + size) }
                }
                for row in rows { try archive.addEntry(with: row.path, fileURL: saves.appendingPathComponent(row.path), compressionMethod: .deflate) }
            }
            let verify = root.appendingPathComponent("Verified"); try ProfileIO.directory(verify)
            try SaveTransfer.unpack(output, to: verify)
            guard ProfileIO.revision(try SaveTransfer.files(verify)) == ProfileIO.revision(rows) else { throw LibraryError("The exported files failed verification.") }
            try ProfileIO.fm.removeItem(at: verify)
        }
        guard ProfileIO.revision(try SaveTransfer.files(saves, slot: id)) == ProfileIO.revision(all) else { throw LibraryError("The save changed during export. Try again with the game closed.") }
        if mainOnly { guard try ProfileIO.stream(output, limit: SaveTransfer.maxFile).0 == rows[0].sha256 else { throw LibraryError("The exported save failed verification.") } }
        try ProfileIO.sync(output); return output
    } }
    @discardableResult func prepareSlot(_ urls: [URL], target requested: Int) throws -> SaveTransfer.Review { try library.synchronized {
        guard review == nil, slotReview == nil else { throw LibraryError("Close the current restore review first.") }
        try recover()
        guard try !hasRetainedProfile() else { throw LibraryError("A previous profile is retained. Roll it back or discard it before importing another save.") }
        guard !urls.isEmpty, urls.count <= SaveTransfer.maxFiles else { throw LibraryError("Select one slot’s .celeste files or one save ZIP.") }
        if ProfileIO.fm.fileExists(atPath: slotRoot.path) { try ProfileIO.fm.removeItem(at: slotRoot) }
        let incoming = slotRoot.appendingPathComponent("Incoming"); try ProfileIO.directory(incoming)
        do {
            if urls.count == 1 && urls[0].pathExtension.lowercased() == "zip" {
                let copy = slotRoot.appendingPathComponent("input.zip")
                try SaveTransfer.copy(urls[0], to: copy); try SaveTransfer.unpack(copy, to: incoming)
            } else {
                var total: UInt64 = 0
                for url in urls {
                    let info = try ProfileIO.attributes(url)
                    guard info.st_size >= 0, UInt64(info.st_size) <= SaveTransfer.maxFile else { throw LibraryError("A save file exceeds 128 MiB.") }
                    total += UInt64(info.st_size)
                    guard total <= SaveTransfer.maxBytes else { throw LibraryError("The selected files exceed 512 MiB.") }
                    guard SaveTransfer.slot(url.lastPathComponent) != nil else { throw LibraryError("Select the numbered save files, such as 0.celeste and 0-modsavedata.celeste. Keep files from one slot together.") }
                    try SaveTransfer.copy(url, to: incoming.appendingPathComponent(url.lastPathComponent))
                }
            }
            let files = try SaveTransfer.files(incoming), ids = Set(files.compactMap { SaveTransfer.slot($0.path) })
            guard ids.count == 1, let source = ids.first, files.contains(where: { $0.path == "\(source).celeste" }) else { throw LibraryError("Import one complete slot at a time, including its main numbered .celeste file. Mod files alone cannot create a playable save.") }
            let main = try ProfileIO.read(incoming.appendingPathComponent("\(source).celeste"), limit: 33_554_432)
            guard SaveSummary.parse(main) != nil else { throw LibraryError("The main file is not supported Celeste SaveData XML, or it is damaged. The current slot is unchanged.") }
            let slots = try ProfileSlots.read(profile), occupied = Set(slots.filter { ($0["files"] as? Int ?? 0) > 0 }.compactMap { $0["id"] as? Int })
            let target = requested == -1 ? (0..<ProfileIO.maxEntries).first(where: { !occupied.contains($0) }) ?? -1 : requested
            guard (0..<ProfileIO.maxEntries).contains(target) else { throw LibraryError("No safe destination slot is available. Choose an existing lower slot.") }
            let sourceRow = try ProfileSlots.row(id: source, related: files.map { "Saves/" + $0.path }, saves: incoming)
            let existing = slots.first { $0["id"] as? Int == target } ?? ProfileSlots.empty(target)
            if occupied.contains(target) { _ = try SaveTransfer.files(profile.appendingPathComponent("Saves"), slot: target) }
            let result = SaveTransfer.Review(id: UUID().uuidString, source: source, target: target, files: files, currentRevision: ProfileIO.revision(try ProfileIO.tree(profile, portable: false)), incoming: sourceRow, existing: existing, mainOnly: urls.count == 1 && urls[0].pathExtension.lowercased() != "zip" && files.count == 1)
            slotReview = result; return result
        } catch { try? ProfileIO.fm.removeItem(at: slotRoot); throw error }
    } }
    func importSlot(_ id: String, keepModData: Bool) throws { try library.synchronized {
        guard let review = slotReview, review.id == id, !keepModData || review.mainOnly, try !hasRetainedProfile() else { throw LibraryError("Review the save again before importing it.") }
        let incoming = slotRoot.appendingPathComponent("Incoming")
        guard ProfileIO.revision(try SaveTransfer.files(incoming)) == ProfileIO.revision(review.files) else { throw LibraryError("The incoming save changed. Cancel and import it again.") }
        try verifyTree(profile, review.currentRevision)
        let staged = slotRoot.appendingPathComponent("Profile")
        if ProfileIO.fm.fileExists(atPath: staged.path) { try ProfileIO.fm.removeItem(at: staged) }
        try ProfileIO.fm.copyItem(at: profile, to: staged)
        try verifyTree(staged, review.currentRevision)
        let saves = staged.appendingPathComponent("Saves"); try ProfileIO.directory(saves)
        for url in try ProfileIO.fm.contentsOfDirectory(at: saves, includingPropertiesForKeys: nil) where ProfileSlots.identifier("Saves/" + url.lastPathComponent) == review.target {
            if !keepModData || url.lastPathComponent == "\(review.target).celeste" { try ProfileIO.fm.removeItem(at: url) }
        }
        for row in review.files {
            let suffix = String(row.path.dropFirst(String(review.source).count)), name = "\(review.target)" + suffix
            let target = saves.appendingPathComponent(name)
            try SaveTransfer.copy(incoming.appendingPathComponent(row.path), to: target)
            guard try ProfileIO.stream(target, limit: SaveTransfer.maxFile).0 == row.sha256 else { throw LibraryError("An imported save changed while staging.") }
        }
        try commitProfile(staged, currentRevision: review.currentRevision, id: review.id)
        slotReview = nil
    } }
}
