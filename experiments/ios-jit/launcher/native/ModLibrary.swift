import Foundation
import CryptoKit
import ZIPFoundation
import CYaml
import Darwin

struct LibraryError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

// Parse scalar values as text, matching Everest's Version setter. The event
// parser bounds depth/work before building nodes; no object-tag construction.
private indirect enum YAMLValue {
    case scalar(String), sequence([YAMLValue]), mapping([String: YAMLValue]), null
    var text: String? { if case .scalar(let x) = self { return x }; return nil }
    var map: [String: YAMLValue]? { if case .mapping(let x) = self { return x }; return nil }
    var list: [YAMLValue]? { if case .sequence(let x) = self { return x }; return nil }
}
private final class ManifestYAML {
    private var parser = yaml_parser_t()
    private var event = yaml_event_t()
    private var eventLive = false
    private var events = 0
    private var anchors: [String: YAMLValue] = [:]
    private func advance() throws {
        if eventLive { yaml_event_delete(&event); eventLive = false }
        events += 1
        guard events <= 20_000, yaml_parser_parse(&parser, &event) != 0 else {
            throw LibraryError("Invalid or overly complex everest.yaml (line \(parser.problem_mark.line + 1)).")
        }
        eventLive = true
    }
    private func string(_ value: UnsafePointer<UInt8>?) -> String? {
        value.map { String(cString: $0) }
    }
    private func node(_ depth: Int) throws -> YAMLValue {
        guard depth <= 32 else { throw LibraryError("Mod metadata nesting exceeds 32 levels.") }
        var anchor: String?
        let result: YAMLValue
        switch event.type {
        case YAML_SCALAR_EVENT:
            let value = String(decoding: UnsafeBufferPointer(start: event.data.scalar.value, count: event.data.scalar.length), as: UTF8.self)
            anchor = string(event.data.scalar.anchor)
            if event.data.scalar.style == YAML_PLAIN_SCALAR_STYLE && (value.isEmpty || ["null", "Null", "NULL", "~"].contains(value)) { result = .null }
            else { result = .scalar(value) }
            try advance()
        case YAML_SEQUENCE_START_EVENT:
            anchor = string(event.data.sequence_start.anchor)
            try advance(); var values: [YAMLValue] = []
            while event.type != YAML_SEQUENCE_END_EVENT { values.append(try node(depth + 1)) }
            try advance(); result = .sequence(values)
        case YAML_MAPPING_START_EVENT:
            anchor = string(event.data.mapping_start.anchor)
            try advance(); var values: [String: YAMLValue] = [:]
            while event.type != YAML_MAPPING_END_EVENT {
                guard let key = try node(depth + 1).text, values[key] == nil else { throw LibraryError("Mod metadata has a complex or duplicate key.") }
                values[key] = try node(depth + 1)
            }
            try advance(); result = .mapping(values)
        case YAML_ALIAS_EVENT:
            guard let name = string(event.data.alias.anchor), let value = anchors[name] else { throw LibraryError("Undefined or recursive YAML alias in mod metadata.") }
            result = value; try advance()
        default: throw LibraryError("Unexpected YAML event in mod metadata.")
        }
        if let anchor { guard anchors.count < 256 else { throw LibraryError("Too many YAML anchors.") }; anchors[anchor] = result }
        return result
    }
    func parse(_ data: Data) throws -> YAMLValue {
        guard data.count <= 1_048_576, String(data: data, encoding: .utf8) != nil else { throw LibraryError("Mod metadata must be UTF-8 and at most 1 MiB.") }
        guard yaml_parser_initialize(&parser) != 0 else { throw LibraryError("Could not initialize YAML parser.") }
        defer { if eventLive { yaml_event_delete(&event) }; yaml_parser_delete(&parser) }
        return try data.withUnsafeBytes { bytes in
            yaml_parser_set_input_string(&parser, bytes.bindMemory(to: UInt8.self).baseAddress, data.count)
            try advance(); guard event.type == YAML_STREAM_START_EVENT else { throw LibraryError("Missing YAML stream.") }
            try advance(); guard event.type == YAML_DOCUMENT_START_EVENT else { throw LibraryError("Missing YAML document.") }
            try advance(); let result = try node(0)
            guard event.type == YAML_DOCUMENT_END_EVENT else { throw LibraryError("Invalid YAML document end.") }
            try advance(); guard event.type == YAML_STREAM_END_EVENT else { throw LibraryError("Only one YAML document is supported.") }
            return result
        }
    }
}

struct ModVersion: Equatable {
    let text: String
    let parts: [Int]
    init(_ text: String) throws {
        let core = text.split(separator: "-", maxSplits: 1, omittingEmptySubsequences: false)[0]
        let words = core.split(separator: ".", omittingEmptySubsequences: false)
        guard (2...4).contains(words.count), words.allSatisfy({ !$0.isEmpty && $0.utf8.allSatisfy { (48...57).contains($0) } }),
              words.allSatisfy({ Int($0).map { $0 <= Int32.max } ?? false }) else { throw LibraryError("Unsupported version ‘\(text)’; expected two to four numbers.") }
        self.text = text
        self.parts = words.map { Int($0)! } + Array(repeating: -1, count: 4 - words.count)
    }
    // Everest.Loader.VersionSatisfiesDependency, including 0.0.* special case
    // and absent Build/Revision = -1 (System.Version semantics).
    func satisfies(_ required: ModVersion) -> Bool {
        if parts[0] == 0 && parts[1] == 0 { return true }
        guard parts[0] == required.parts[0] else { return false }
        return !parts.dropFirst().lexicographicallyPrecedes(required.parts.dropFirst())
    }
}
struct ModDependency { let name: String; let version: ModVersion }
struct ModMetadata {
    let name: String
    let version: ModVersion
    let dll: String?
    let dependencies: [ModDependency]
    let optionalDependencies: [ModDependency]
    var json: [String: Any] { ["name": name, "version": version.text] }
}
struct ModArchive {
    let filename: String
    let digest: String
    let bytes: UInt64
    let modules: [ModMetadata]
    let problem: String?
}
private struct LibraryState: Codable { var schema = 1; var disabled: [String] = [] }

final class ModLibrary {
    static let ownMod = "CJITCodeCanary-v1.0.0.zip"
    let profile: URL
    var mods: URL { profile.appendingPathComponent("Mods", isDirectory: true) }
    private let lock = NSRecursiveLock()
    private var cache: [ModArchive]?
    private let specialPins: [String: String]
    private let archiveNames: [String: String]
    private var stateURL: URL { profile.appendingPathComponent("launcher-mod-state.json") }
    init(profile: URL, specialPins: [String: String] = [:], archiveNames: [String: String] = [:]) { self.profile = profile; self.specialPins = specialPins; self.archiveNames = archiveNames }
    private func synchronized<T>(_ body: () throws -> T) rethrows -> T { lock.lock(); defer { lock.unlock() }; return try body() }
    static func safePath(_ name: String) -> Bool {
        let clean = name.replacingOccurrences(of: "\\", with: "/")
        return !clean.isEmpty && !clean.hasPrefix("/") && !clean.contains(":") && !clean.contains("\0") &&
            !clean.split(separator: "/", omittingEmptySubsequences: false).contains("..")
    }
    private func state() throws -> LibraryState {
        guard FileManager.default.fileExists(atPath: stateURL.path) else {
            let prior = (try? String(contentsOf: mods.appendingPathComponent("blacklist.txt"), encoding: .utf8)) ?? ""
            return LibraryState(disabled: prior.components(separatedBy: .newlines).filter { !$0.hasPrefix("#") }.map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty && $0 != Self.ownMod })
        }
        do { let result = try JSONDecoder().decode(LibraryState.self, from: Data(contentsOf: stateURL)); guard result.schema == 1 else { throw LibraryError("Unknown version") }; return result }
        catch { throw LibraryError("Could not read this profile’s mod choices. The existing file has been retained; export diagnostics before repairing it.") }
    }
    private static func opened(_ url: URL) throws -> (FileHandle, UInt64) {
        let fd = open(url.path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw LibraryError("Could not open \(url.lastPathComponent).") }
        var s = stat()
        guard fstat(fd, &s) == 0, (s.st_mode & S_IFMT) == S_IFREG, s.st_size > 0, s.st_size <= 4_294_967_296 else { close(fd); throw LibraryError("Select a regular mod ZIP of at most 4 GiB.") }
        return (FileHandle(fileDescriptor: fd, closeOnDealloc: true), UInt64(s.st_size))
    }
    private static func hash(_ url: URL, copyingTo output: FileHandle? = nil) throws -> (String, UInt64) {
        let (input, expected) = try opened(url); defer { try? input.close() }
        var hash = SHA256(); var bytes: UInt64 = 0
        while let data = try input.read(upToCount: 65_536), !data.isEmpty {
            bytes += UInt64(data.count); guard bytes <= expected else { throw LibraryError("The mod ZIP changed while reading it.") }
            hash.update(data: data); try output?.write(contentsOf: data)
        }
        guard bytes == expected else { throw LibraryError("The mod ZIP was truncated while reading it.") }
        try output?.synchronize()
        return (hash.finalize().map { String(format: "%02x", $0) }.joined(), bytes)
    }
    private static func metadata(_ data: Data) throws -> [ModMetadata] {
        let document = try ManifestYAML().parse(data)
        guard let list = document.list, !list.isEmpty, list.count <= 64 else { throw LibraryError("everest.yaml must contain a list of 1–64 modules.") }
        func dependency(_ value: YAMLValue) throws -> ModDependency {
            guard let map = value.map, let name = map["Name"]?.text, !name.isEmpty, name.count <= 200 else { throw LibraryError("A dependency is missing its Name.") }
            return ModDependency(name: name == "API" ? "Everest" : name, version: try ModVersion(map["Version"]?.text ?? "1.0"))
        }
        func dependencies(_ value: YAMLValue?) throws -> [ModDependency] {
            guard let value else { return [] }; if case .null = value { return [] }
            guard let items = value.list, items.count <= 256 else { throw LibraryError("Invalid dependency list.") }
            return try items.map(dependency)
        }
        var seen = Set<String>()
        return try list.map { value in
            guard let map = value.map, let name = map["Name"]?.text, !name.isEmpty, name.count <= 200,
                  name.rangeOfCharacter(from: .controlCharacters) == nil, seen.insert(name).inserted else { throw LibraryError("A module has a missing or duplicate Name.") }
            let dll = map["DLL"]?.text.flatMap { $0.isEmpty ? nil : $0.replacingOccurrences(of: "\\", with: "/") }
            if let dll, !safePath(dll) { throw LibraryError("The module DLL path leaves its ZIP.") }
            return ModMetadata(name: name, version: try ModVersion(map["Version"]?.text ?? "1.0"), dll: dll,
                               dependencies: try dependencies(map["Dependencies"]), optionalDependencies: try dependencies(map["OptionalDependencies"]))
        }
    }
    private static func inspect(_ url: URL, filename: String, digest: String, bytes: UInt64) throws -> ModArchive {
        let archive = try Archive(url: url, accessMode: .read)
        var entries: [String: Entry] = [:]; var count = 0
        for entry in archive {
            count += 1
            guard count <= 100_000, safePath(entry.path), entry.type != .symlink else { throw LibraryError("ZIP contains an unsupported path, symlink or too many entries.") }
            guard entries[entry.path] == nil else { throw LibraryError("ZIP contains duplicate entries: \(entry.path).") }
            entries[entry.path] = entry
        }
        let meta = entries["everest.yaml"] ?? entries["everest.yml"]
        let modules: [ModMetadata]
        if let meta {
            guard meta.type == .file, meta.uncompressedSize <= 1_048_576 else { throw LibraryError("Mod metadata exceeds 1 MiB.") }
            var data = Data(); let crc = try archive.extract(meta, bufferSize: 65_536) { chunk in
                guard data.count + chunk.count <= 1_048_576 else { throw LibraryError("Decompressed metadata exceeds 1 MiB.") }; data.append(chunk)
            }
            guard crc == meta.checksum && UInt64(data.count) == meta.uncompressedSize else { throw LibraryError("Mod metadata checksum or length is incorrect.") }
            modules = try metadata(data)
        } else {
            // Match Everest's metadata-free asset ZIP identity after import.
            modules = [ModMetadata(name: (filename as NSString).deletingPathExtension, version: try ModVersion("0.0.0-dummy"), dll: nil, dependencies: [], optionalDependencies: [])]
        }
        for module in modules {
            if let dll = module.dll, entries[dll]?.type != .file { throw LibraryError("\(module.name) refers to a missing DLL: \(dll).") }
        }
        return ModArchive(filename: filename, digest: digest, bytes: bytes, modules: modules, problem: nil)
    }
    func scan(force: Bool = false) throws -> [ModArchive] { try synchronized {
        if !force, let cache { return cache }
        try FileManager.default.createDirectory(at: mods, withIntermediateDirectories: true)
        let files = try FileManager.default.contentsOfDirectory(at: mods, includingPropertiesForKeys: nil).filter { $0.pathExtension.lowercased() == "zip" && !$0.lastPathComponent.hasPrefix(".") }.sorted { $0.lastPathComponent < $1.lastPathComponent }
        guard files.count <= 1024 else { throw LibraryError("This profile exceeds 1,024 mod ZIPs.") }
        cache = files.map { file in
            do { let (digest, bytes) = try Self.hash(file); return try Self.inspect(file, filename: file.lastPathComponent, digest: digest, bytes: bytes) }
            catch { return ModArchive(filename: file.lastPathComponent, digest: "", bytes: 0, modules: [], problem: error.localizedDescription) }
        }
        return cache!
    } }
    func setEnabled(_ enabled: Bool, filename: String) throws { try synchronized {
        guard filename != Self.ownMod, try scan().contains(where: { $0.filename == filename }) else { throw LibraryError("Unknown or internal module.") }
        var selection = try state(); var disabled = Set(selection.disabled)
        if enabled { disabled.remove(filename) } else { disabled.insert(filename) }
        selection.disabled = disabled.sorted(); let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
        try encoder.encode(selection).write(to: stateURL, options: .atomic)
    } }
    func setAllEnabled(_ enabled: Bool) throws { try synchronized {
        var selection = try state()
        selection.disabled = enabled ? [] : try scan().filter { $0.filename != Self.ownMod }.map(\.filename).sorted()
        try JSONEncoder().encode(selection).write(to: stateURL, options: .atomic)
    } }
    func importZIP(_ selected: URL) throws -> ModArchive { try synchronized {
        try FileManager.default.createDirectory(at: mods, withIntermediateDirectories: true)
        let temp = mods.appendingPathComponent(".import-\(UUID().uuidString).zip")
        guard FileManager.default.createFile(atPath: temp.path, contents: nil) else { throw LibraryError("Could not stage the mod ZIP.") }
        defer { try? FileManager.default.removeItem(at: temp) }
        let handle = try FileHandle(forWritingTo: temp); defer { try? handle.close() }
        let (digest, bytes) = try Self.hash(selected, copyingTo: handle); try handle.close()
        let installed = try scan()
        if let same = installed.first(where: { $0.digest == digest }) { return same }
        guard installed.count < 1024 else { throw LibraryError("This profile already has 1,024 mod ZIPs.") }
        var stem = (selected.deletingPathExtension().lastPathComponent).unicodeScalars.map { CharacterSet.alphanumerics.contains($0) || "-_".unicodeScalars.contains($0) ? String($0) : "_" }.joined()
        if stem.isEmpty { stem = "mod" }; stem = String(stem.prefix(80))
        var filename = archiveNames[digest] ?? (stem + ".zip")
        if FileManager.default.fileExists(atPath: mods.appendingPathComponent(filename).path) { filename = stem + "-" + digest.prefix(12) + ".zip" }
        let result = try Self.inspect(temp, filename: filename, digest: digest, bytes: bytes)
        let destination = mods.appendingPathComponent(filename)
        guard !FileManager.default.fileExists(atPath: destination.path) else { throw LibraryError("A different file already occupies the import destination.") }
        try FileManager.default.moveItem(at: temp, to: destination)
        cache = (installed + [result]).sorted { $0.filename < $1.filename }
        return result
    } }
    func snapshot(force: Bool = false, prepare: Bool = false) throws -> [String: Any] { try synchronized {
        let records = try scan(force: force); let selection = try state(); let disabled = Set(selection.disabled)
        let active = records.filter { !disabled.contains($0.filename) }
        var issues = active.compactMap { row in row.problem.map { row.filename + ": " + $0 } }
        var provided: [String: (ModVersion, String)] = [:]
        for (name, version) in ["Celeste": "1.4.0.0", "Everest": "1.6458.0", "EverestCore": "1.6458.0"] { provided[name] = (try ModVersion(version), "Built in") }
        for row in active {
            for module in row.modules {
                if let prior = provided[module.name] { issues.append("\(module.name) appears in both \(prior.1) and \(row.filename). Disable one version.") }
                else { provided[module.name] = (module.version, row.filename) }
                if let expected = specialPins[module.name], row.digest != expected { issues.append("\(module.name) needs the iOS-tested release for its compatibility adjustment. Keep this imported version disabled for now.") }
            }
        }
        // Missing/incompatible required dependencies block launch; optional
        // dependencies only constrain versions when actually enabled.
        for row in active {
            for module in row.modules {
                for dependency in module.dependencies {
                    guard let actual = provided[dependency.name] else { issues.append("\(module.name) needs \(dependency.name) \(dependency.version.text). Import or enable it."); continue }
                    if !actual.0.satisfies(dependency.version) { issues.append("\(module.name) needs \(dependency.name) \(dependency.version.text); enabled version is \(actual.0.text).") }
                }
                for dependency in module.optionalDependencies {
                    if let actual = provided[dependency.name], !actual.0.satisfies(dependency.version) { issues.append("\(module.name)’s optional \(dependency.name) dependency is enabled at an incompatible version (\(actual.0.text)).") }
                }
            }
        }
        let graph = Dictionary(active.flatMap { $0.modules }.map { ($0.name, $0.dependencies.map(\.name)) }, uniquingKeysWith: { first, _ in first })
        var visiting = Set<String>(), visited = Set<String>()
        func visit(_ name: String) {
            if visiting.contains(name) { issues.append("Required dependency cycle involving " + name + ". Disable the conflicting mod set."); return }
            guard !visited.contains(name), let edges = graph[name] else { return }
            visiting.insert(name); for edge in edges { visit(edge) }; visiting.remove(name); visited.insert(name)
        }
        for name in graph.keys.sorted() { visit(name) }
        let modules = active.flatMap { $0.modules.map(\.json) }
        let rows: [[String: Any]] = records.map { row in
            ["id": row.filename, "filename": row.filename, "sha256": row.digest, "bytes": row.bytes,
             "name": row.modules.map(\.name).joined(separator: " + "), "version": row.modules.map { $0.version.text }.joined(separator: ", "),
             "enabled": !disabled.contains(row.filename), "internal": row.filename == Self.ownMod, "problem": row.problem ?? "",
             "dependencies": row.modules.flatMap { $0.dependencies }.map { $0.name + " " + $0.version.text }]
        }
        if prepare {
            guard issues.isEmpty else { throw LibraryError(issues.prefix(8).joined(separator: "\n")) }
            let blacklist = "# Written by Celeste JIT launcher; choices are saved per profile.\n" + records.filter { disabled.contains($0.filename) }.map(\.filename).sorted().joined(separator: "\n") + "\n"
            try blacklist.write(to: mods.appendingPathComponent("blacklist.txt"), atomically: true, encoding: .utf8)
            let run: [String: Any] = ["schema": 1, "modules": modules, "archives": rows.filter { $0["enabled"] as? Bool == true }]
            try JSONSerialization.data(withJSONObject: run, options: [.sortedKeys, .prettyPrinted]).write(to: profile.appendingPathComponent("launcher-run.json"), options: .atomic)
        }
        return ["mods": rows, "issues": Array(Set(issues)).sorted(), "canRun": issues.isEmpty, "enabledCount": active.count, "installedCount": records.count, "modules": modules]
    } }
}

@objc public final class CJModLibrary: NSObject {
    private let library: ModLibrary
    @objc(initWithProfile:compatibilityPins:archiveNames:) public init(profile: URL, compatibilityPins: [String: String], archiveNames: [String: String]) { library = ModLibrary(profile: profile, specialPins: compatibilityPins, archiveNames: archiveNames); super.init() }
    @objc(scanWithForce:error:) public func scan(force: Bool) throws -> NSDictionary { try library.snapshot(force: force) as NSDictionary }
    @objc(prepareWithError:) public func prepare() throws -> NSDictionary { try library.snapshot(force: true, prepare: true) as NSDictionary }
    @objc(setEnabled:filename:error:) public func setEnabled(_ value: Bool, filename: String) throws { try library.setEnabled(value, filename: filename) }
    @objc(setAllEnabled:error:) public func setAllEnabled(_ value: Bool) throws { try library.setAllEnabled(value) }
    @objc(importZIP:error:) public func importZIP(_ url: URL) throws -> NSDictionary { let row = try library.importZIP(url); return ["filename": row.filename, "sha256": row.digest, "bytes": row.bytes] }
}
