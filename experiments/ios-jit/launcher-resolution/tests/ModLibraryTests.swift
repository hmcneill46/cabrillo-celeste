import Foundation

@main struct Tests {
    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1]); let fixture = root.appendingPathComponent("fixtures")
        var checks = 0
        func check(_ condition: Bool, _ name: String) throws { guard condition else { throw LibraryError("FAIL " + name) }; checks += 1 }
        func rejected(_ name: String, _ body: () throws -> Void) throws {
            do { try body() } catch { checks += 1; return }; throw LibraryError("Accepted invalid input: " + name)
        }
        func library(_ name: String) -> ModLibrary { ModLibrary(profile: root.appendingPathComponent(name)) }
        let lib = library("general")
        let one = try lib.importZIP(fixture.appendingPathComponent("consumer.zip"))
        try check(!(try lib.snapshot()["canRun"] as! Bool), "missing required dependency blocks")
        let dep = try lib.importZIP(fixture.appendingPathComponent("dependency.zip"))
        try check(try lib.snapshot()["canRun"] as! Bool, "unquoted version 1.10 is not a float")
        try check(try lib.importZIP(fixture.appendingPathComponent("dependency.zip")).filename == dep.filename, "same ZIP is idempotent")
        try lib.setEnabled(false, filename: dep.filename)
        try check(!(try library("general").snapshot()["canRun"] as! Bool), "persisted disabled required dependency blocks fresh instance")
        try lib.setEnabled(false, filename: one.filename)
        _ = try lib.snapshot(prepare: true)
        let blacklist = try String(contentsOf: lib.mods.appendingPathComponent("blacklist.txt"))
        try check(blacklist.contains(one.filename) && blacklist.contains(dep.filename), "Everest blacklist includes disabled archives")
        let absent = try lib.importZIP(fixture.appendingPathComponent("optional.zip"))
        try check(try lib.snapshot()["canRun"] as! Bool, "absent optional dependency allowed")
        try lib.setEnabled(true, filename: dep.filename)
        try check(!(try lib.snapshot()["canRun"] as! Bool), "enabled incompatible optional dependency blocks")
        try lib.setEnabled(false, filename: absent.filename)
        try lib.setEnabled(true, filename: one.filename)
        _ = try lib.snapshot(prepare: true)
        let run = try JSONSerialization.jsonObject(with: Data(contentsOf: lib.profile.appendingPathComponent("launcher-run.json"))) as! [String: Any]
        try check((run["modules"] as! [[String: Any]]).count == 2, "run manifest freezes enabled modules")
        _ = try lib.importZIP(fixture.appendingPathComponent("duplicate.zip"))
        try check(!(try lib.snapshot()["canRun"] as! Bool), "duplicate versions block")
        for name in ["reserved-support", "traversal", "symlink", "duplicate-entry", "missing-dll", "bad-yaml", "oversize-yaml", "bad-crc", "recursive-alias", "multi-document", "duplicate-key"] {
            try rejected(name) { _ = try lib.importZIP(fixture.appendingPathComponent(name + ".zip")) }
        }
        try check(!(try FileManager.default.contentsOfDirectory(atPath: lib.mods.path)).contains(where: { $0.hasPrefix(".import-") }), "failed staging cleanup")
        let support = library("support"); _ = try support.importZIP(fixture.appendingPathComponent("support-consumer.zip"))
        try check(try support.snapshot()["canRun"] as! Bool, "required bundled support fulfills exact YAML identity")
        try FileManager.default.copyItem(at: fixture.appendingPathComponent("reserved-support.zip"), to: support.mods.appendingPathComponent("manually-copied.zip"))
        try check(!(try support.snapshot(force: true)["canRun"] as! Bool), "manual support override blocks before Everest boots")
        let multi = library("multi"); let row = try multi.importZIP(fixture.appendingPathComponent("multi.zip"))
        try check(row.modules.count == 2 && (try multi.snapshot()["canRun"] as! Bool), "multiple modules and YAML aliases")
        let asset = try multi.importZIP(fixture.appendingPathComponent("asset.zip"))
        try check(asset.modules[0].name == (asset.filename as NSString).deletingPathExtension, "metadata-free identity matches Everest installed basename")
        let cycle = library("cycle"); _ = try cycle.importZIP(fixture.appendingPathComponent("cycle.zip"))
        try check(!(try cycle.snapshot()["canRun"] as! Bool), "required cycle blocked")
        try Data("broken".utf8).write(to: multi.profile.appendingPathComponent("launcher-mod-state.json"))
        try rejected("corrupt state") { _ = try multi.snapshot(prepare: true) }
        try check(try String(contentsOf: multi.profile.appendingPathComponent("launcher-mod-state.json")) == "broken", "corrupt choices preserved")
        let full = ModLibrary(profile: root.appendingPathComponent("full"))
        let snapshot = try full.snapshot(force: true, prepare: true)
        try check(snapshot["canRun"] as! Bool, "full original SJ graph accepted: \(snapshot["issues"]!)")
        try check(snapshot["installedCount"] as! Int == 53 && (snapshot["modules"] as! [[String: Any]]).count == 53, "all 53 original metadata entries")
        // Independent expected truth table, includes System.Version absent components.
        let cases: [(String, String, Bool)] = [("1.10", "1.9.9", true), ("1.0", "1.0.0", false), ("1.0.0", "1.0", true), ("2.0", "1.0", false), ("0.0.9", "8.99", true), ("1.2.3-beta", "1.2.3", true), ("1.2.3.0", "1.2.3.1", false)]
        for (installed, required, expected) in cases { try check(try ModVersion(installed).satisfies(ModVersion(required)) == expected, "Everest version \(installed)/\(required)") }
        for bad in ["1", "1.0.0.0.0", "1..0", "1.2147483648", "1.x"] { try rejected(bad) { _ = try ModVersion(bad) } }
        let evidence: [String: Any] = ["status": "PASS_NATIVE_MOD_LIBRARY", "checks": checks, "full_graph_archives": 53, "snapshot": snapshot]
        try JSONSerialization.data(withJSONObject: evidence, options: [.prettyPrinted, .sortedKeys]).write(to: root.appendingPathComponent("result.json"))
        print("PASS_NATIVE_MOD_LIBRARY \(checks) checks")
    }
}
