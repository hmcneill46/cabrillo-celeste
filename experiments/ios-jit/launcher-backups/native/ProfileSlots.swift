import Foundation
#if canImport(FoundationXML)
import FoundationXML
#endif

// Summaries are optional; files do not need to parse to be preserved in a backup.
enum ProfileSlots {
    static func identifier(_ path: String) -> Int? {
        guard path.hasPrefix("Saves/"), path.split(separator: "/").count == 2, path.hasSuffix(".celeste") else { return nil }
        let name = String(path.dropFirst(6).dropLast(8))
        let stem = name.components(separatedBy: "-mod").first ?? name
        guard !stem.isEmpty, stem.utf8.allSatisfy({ (48...57).contains($0) }), let value = Int(stem), value <= Int32.max else { return nil }
        return value
    }
    static func identifiers(_ paths: [String]) -> [Int] { Array(Set(paths.compactMap(identifier))).sorted() }
    static func read(_ profile: URL) throws -> [[String: Any]] {
        let saves = profile.appendingPathComponent("Saves")
        guard ProfileIO.fm.fileExists(atPath: saves.path) else { return [] }
        try ProfileIO.directory(saves)
        let files = try ProfileIO.fm.contentsOfDirectory(at: saves, includingPropertiesForKeys: nil)
        guard files.count <= ProfileIO.maxEntries else { throw LibraryError("Too many files to summarize saves.") }
        let paths = files.map { "Saves/" + $0.lastPathComponent }
        let groups = Dictionary(grouping: paths.compactMap { path in identifier(path).map { ($0, path) } }, by: { $0.0 })
        return groups.keys.sorted().map { id in
            let related = (groups[id] ?? []).map { $0.1 }
            let main = related.first { Int(String($0.dropFirst(6).dropLast(8))) == id }
            var row: [String: Any] = ["id": id, "slot": id + 1, "files": related.count, "summary": "Mod data is preserved. Game summary unavailable."]
            if let main {
                let url = profile.appendingPathComponent(main)
                if let info = try? ProfileIO.attributes(url) { row["modified"] = ISO8601DateFormatter().string(from: Date(timeIntervalSince1970: Double(info.st_mtimespec.tv_sec))) }
                if let data = try? ProfileIO.read(url, limit: 4_194_304), let fields = SaveSummary.parse(data) {
                    row["name"] = fields["Name"]
                    var summary: [String] = []
                    if let value = fields["Time"], let ticks = UInt64(value) {
                        let minutes = ticks / 600_000_000
                        summary.append("\(minutes / 60)h \(minutes % 60)m")
                    }
                    if let deaths = fields["TotalDeaths"], let value = UInt64(deaths) { summary.append("\(value) deaths") }
                    row["summary"] = summary.isEmpty ? "Save file and mod sidecars preserved." : summary.joined(separator: " · ")
                } else { row["summary"] = "Summary unavailable. The original save and sidecars are preserved." }
            }
            return row
        }
    }
}
private final class SaveSummary: NSObject, XMLParserDelegate {
    var depth = 0, nodes = 0, text = "", field: String?, valid = true
    var fields: [String: String] = [:]
    static func parse(_ data: Data) -> [String: String]? {
        // Refuse DTDs and entities, including encodings that could obscure them.
        guard let source = String(data: data, encoding: .utf8), !source.uppercased().contains("<!DOCTYPE"), !source.uppercased().contains("<!ENTITY") else { return nil }
        let delegate = SaveSummary(), parser = XMLParser(data: data)
        parser.shouldResolveExternalEntities = false; parser.delegate = delegate
        return parser.parse() && delegate.valid ? delegate.fields : nil
    }
    func parser(_ parser: XMLParser, didStartElement elementName: String, namespaceURI: String?, qualifiedName: String?, attributes: [String: String]) {
        depth += 1; nodes += 1
        if depth > 64 || nodes > 100_000 { valid = false; parser.abortParsing() }
        if depth == 1 && elementName != "SaveData" { valid = false; parser.abortParsing() }
        if depth == 2 && ["Name", "Time", "TotalDeaths"].contains(elementName) { field = elementName; text = "" }
    }
    func parser(_ parser: XMLParser, foundCharacters string: String) {
        guard field != nil else { return }; text += string
        if text.count > 200 { valid = false; parser.abortParsing() }
    }
    func parser(_ parser: XMLParser, didEndElement elementName: String, namespaceURI: String?, qualifiedName: String?) {
        if depth == 2, field == elementName { fields[elementName] = text.trimmingCharacters(in: .whitespacesAndNewlines); field = nil }
        depth -= 1
    }
}

@objc public final class CJProfileBackupBridge: NSObject {
    let store: ProfileBackups
    @objc(initWithLibrary:vault:) public init(library: CJModLibrary, vault: URL) { store = ProfileBackups(library: library.library, vault: vault); super.init() }
    @objc(initializeWithDefaults:error:) public func initialize(defaults: [String: Bool]) throws -> NSDictionary {
        _ = try store.initialize(defaults: defaults); return try store.state() as NSDictionary
    }
    @objc(stateWithError:) public func state() throws -> NSDictionary { try store.state() as NSDictionary }
    @objc(createWithError:) public func create() throws -> NSURL { try store.create() as NSURL }
    @objc(reviewURL:error:) public func review(url: URL) throws { _ = try store.prepare(url) }
    @objc(cancelReviewWithError:) public func cancelReview() throws { try store.cancelReview() }
    @objc(restoreID:error:) public func restore(id: String) throws { try store.restore(id) }
    @objc(rollbackWithError:) public func rollback() throws { try store.rollback() }
    @objc(discardRetainedWithError:) public func discardRetained() throws { try store.discardRetainedProfile() }
    @objc(archiveID:error:) public func archive(id: String) throws -> NSURL { try store.archive(id) as NSURL }
    @objc(removeArchiveID:error:) public func removeArchive(id: String) throws { try ProfileIO.fm.removeItem(at: store.archive(id)) }
    @objc(setPreferences:error:) public func setPreferences(_ values: [String: Bool]) throws { try store.setPreferences(values) }
    @objc(recoverWithError:) public func recover() throws { try store.recover() }
}
