import Foundation
import ZIPFoundation
import Darwin

@main struct ProfileBackupTests {
    static var checks: [String] = []
    static let defaults = ["launcher.metrics": true, "launcher.cellularDownloads": false, "launcher.autoUpdateChecks": true]
    static func check(_ yes: @autoclosure () throws -> Bool, _ name: String) throws {
        guard try yes() else { throw LibraryError("FAILED: " + name) }; checks.append(name)
    }
    static func rejects(_ name: String, _ body: () throws -> Void) throws {
        do { try body() } catch { checks.append(name); return }; throw LibraryError("Accepted invalid case: " + name)
    }
    static func put(_ root: URL, _ path: String, _ text: String) throws { try ProfileIO.write(Data(text.utf8), to: root.appendingPathComponent(path)) }
    static func store(_ root: URL) -> ProfileBackups { ProfileBackups(library: ModLibrary(profile: root.appendingPathComponent("Profile")), vault: root.appendingPathComponent("Vault")) }
    static func add(_ archive: Archive, _ path: String, _ data: Data, type: Entry.EntryType = .file) throws {
        try archive.addEntry(with: path, type: type, uncompressedSize: Int64(data.count), compressionMethod: .deflate) { offset, size in data.subdata(in: Int(offset)..<Int(offset)+size) }
    }
    static func seed(_ s: ProfileBackups) throws {
        _ = try s.initialize(defaults: defaults)
        try put(s.profile, "Saves/0.celeste", "<SaveData><Name>Madeline</Name><Time>36000000000</Time><TotalDeaths>42</TotalDeaths></SaveData>")
        try put(s.profile, "Saves/7.celeste", "<SaveData><Name>Theo</Name></SaveData>")
        try put(s.profile, "Saves/1000-modsave-Custom.celeste", "opaque mod bytes")
        try put(s.profile, "Saves/settings.celeste", "settings A")
        try put(s.profile, "Saves/modsettings-Custom.celeste", "unknown settings")
        try put(s.profile, "Unknown/deep/sidecar.bin", "future mod data")
        try put(s.profile, "Backups/0.celeste", "Everest's own backup")
        try put(s.profile, "Mods/favorites.txt", "SampleHelper")
        try put(s.profile, "Mods/Cache/disposable.dll", "compiled cache")
        try put(s.profile, "Cache/scratch", "temporary")
        try ProfileIO.directory(s.profile.appendingPathComponent("Unknown/Empty"))
        do { let archive = try Archive(url: s.profile.appendingPathComponent("Mods/Sample.zip"), accessMode: .create); try add(archive, "everest.yaml", Data("- Name: SampleHelper\n  Version: 1.2.3\n".utf8)) }
        try s.library.setEnabled(false, filename: "Sample.zip")
    }
    static func changed(_ s: ProfileBackups) throws {
        try put(s.profile, "Saves/0.celeste", "<SaveData><Name>Changed</Name></SaveData>")
        try put(s.profile, "Saves/88.celeste", "later save")
        try put(s.profile, "Unknown/new-only", "must disappear on exact restore")
        try s.setPreferences(["launcher.metrics": false, "launcher.cellularDownloads": true, "launcher.autoUpdateChecks": false])
        try s.library.setEnabled(true, filename: "Sample.zip")
    }
    static func setup(_ root: URL) throws -> (ProfileBackups, URL, String, String) {
        let s = store(root); try seed(s)
        let portable = ProfileIO.revision(try ProfileIO.tree(s.profile, portable: true)), url = try s.create()
        try changed(s)
        return (s, url, portable, ProfileIO.revision(try ProfileIO.tree(s.profile, portable: false)))
    }
    static func crash(_ root: URL, _ phase: String) throws {
        let (s, url, original, changedRevision) = try setup(root)
        try put(root, "expected.json", String(data: try ProfileIO.encode(["portable": original, "changed": changedRevision]), encoding: .utf8)!)
        if phase.hasPrefix("undo") {
            let review = try s.prepare(url); try s.restore(review.id)
            s.fault = { if $0 == phase { _exit(86) } }; try s.rollback()
        } else { let review = try s.prepare(url); s.fault = { if $0 == phase { _exit(86) } }; try s.restore(review.id) }
        throw LibraryError("Did not reach fault point")
    }
    static func main() throws {
        let args = CommandLine.arguments, root = URL(fileURLWithPath: args[1], isDirectory: true)
        if args.count == 4 && args[2] == "--crash" { try crash(root, args[3]); return }
        if args.count == 4 && args[2] == "--slot-crash" { try slotCrash(root, args[3]); return }
        try ProfileIO.directory(root)
        try transfers(root)
        let (s, backup, expected, beforeRestore) = try setup(root.appendingPathComponent("roundtrip"))
        let archive = try Archive(url: backup, accessMode: .read)
        try check(!archive.contains(where: { $0.path.hasSuffix(".zip") || $0.path.contains("/Cache/") }), "mod ZIPs and explicitly owned caches excluded")
        try check(archive.contains(where: { $0.path == "Profile/Unknown/deep/sidecar.bin" }), "unknown files included")
        try check(ProfileSlots.identifiers(["Saves/0.celeste", "Saves/7-modsave-a.celeste", "Saves/1000-modsession-a.celeste", "Saves/-1.celeste"]) == [0,7,1000], "sparse Everest slots and mod-only slot discovered")
        let review = try s.prepare(backup)
        try check(review.issues.isEmpty, "same archive accepted despite changed enabled choice")
        try s.restore(review.id)
        try check(ProfileIO.revision(ProfileIO.tree(s.profile, portable: true)) == expected, "whole-profile exact restore including empty directories")
        try check(!ProfileIO.fm.fileExists(atPath: s.profile.appendingPathComponent("Saves/88.celeste").path), "later save removed from active profile")
        try check(ProfileIO.revision(ProfileIO.tree(s.old, portable: false)) == beforeRestore, "old profile retained byte for byte including caches and ZIPs")
        try check(s.library.state().disabled.contains("Sample.zip"), "disabled choices restored")
        try check(s.preferences() == defaults, "launcher preferences restored")
        let slots = try ProfileSlots.read(s.profile)
        try check(slots.count == 5 && slots[0]["name"] as? String == "Madeline" && slots[0]["summary"] as? String == "1h 0m · 42 deaths", "native summaries read without mod execution")
        try rejects("second restore requires explicit retained-copy decision") { _ = try s.prepare(backup) }
        try s.rollback()
        try check(ProfileIO.revision(ProfileIO.tree(s.profile, portable: false)) == beforeRestore, "rollback restores all previous profile bytes")
        try s.discardRetainedProfile()
        try check(!s.hasRetainedProfile(), "explicit discard affects only retained tree")
        let r = try s.prepare(backup); try s.cancelReview()
        try check(ProfileIO.revision(ProfileIO.tree(s.profile, portable: false)) == beforeRestore, "cancel leaves active profile untouched")
        try rejects("stale confirmation ID rejected") { try s.restore(r.id) }
        _ = try s.prepare(backup); try put(s.profile, "Unknown/new-change", "new")
        try rejects("concurrent profile change rejected") { try s.restore(s.review!.id) }; try s.cancelReview()
        try ProfileIO.fm.removeItem(at: s.profile.appendingPathComponent("Mods/Sample.zip")); s.library.invalidateCache()
        try check(!s.prepare(backup).issues.isEmpty, "missing exact archive blocks restore")
        try rejects("incompatible review cannot restore") { try s.restore(s.review!.id) }; try s.cancelReview()

        for phase in ["prepared", "old_moved", "new_moved", "committed", "undo_prepared", "undo_current_moved", "undo_old_moved", "undone"] {
            let location = root.appendingPathComponent("crash-" + phase)
            let child = Process(); child.executableURL = URL(fileURLWithPath: args[0]); child.arguments = [location.path, "--crash", phase]
            try child.run(); child.waitUntilExit(); try check(child.terminationStatus == 86, "process killed at " + phase)
            let recovered = store(location); _ = try recovered.initialize(defaults: defaults)
            let data = try ProfileIO.read(location.appendingPathComponent("expected.json"), limit: 4096), expected = try JSONDecoder().decode([String: String].self, from: data)
            if phase == "committed" { try check(ProfileIO.revision(ProfileIO.tree(recovered.profile, portable: true)) == expected["portable"], "committed restore survives process death") }
            else { try check(ProfileIO.revision(ProfileIO.tree(recovered.profile, portable: false)) == expected["changed"], "complete prior profile recovered after " + phase) }
            _ = try recovered.initialize(defaults: defaults)
            try check(ProfileIO.fm.fileExists(atPath: recovered.profile.path), "recovery idempotent after " + phase)
        }
        let invalid = root.appendingPathComponent("invalid"); try ProfileIO.directory(invalid)
        let validManifest = try s.readBundle(backup, destination: nil)
        let source = try Archive(url: backup, accessMode: .read)
        // Mutate actual ZIPs, not just the validator's intermediate model.
        for mode in ["traversal", "absolute", "backslash", "case-collision", "unicode-collision", "symlink", "unlisted", "digest", "reserved", "future-schema", "truncated", "oversized", "file-parent"] {
            let url = invalid.appendingPathComponent(mode + ".zip")
            do {
                let target = try Archive(url: url, accessMode: .create)
                for entry in source {
                    var data = Data(); _ = try source.extract(entry) { data.append($0) }
                    if entry.path == "manifest.json" && ["digest", "reserved", "future-schema", "oversized", "file-parent"].contains(mode) {
                        var json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
                        if mode == "future-schema" { json["schema"] = 99 }
                        else {
                            var files = json["files"] as! [[String: Any]]
                            let index = files.firstIndex { $0["path"] as? String == "Saves/0.celeste" }!
                            if mode == "digest" { files[index]["sha256"] = String(repeating: "0", count: 64) }
                            if mode == "reserved" { files[index]["path"] = "Mods/Injected.zip" }
                            if mode == "oversized" { files[index]["bytes"] = 536_870_913 }
                            if mode == "file-parent" { files[index]["path"] = "Saves/settings.celeste/child" }
                            json["files"] = files
                        }
                        data = try JSONSerialization.data(withJSONObject: json)
                    }
                    if mode == "truncated" && entry.path == "Profile/Saves/0.celeste" { data = Data(data.dropLast()) }
                    try add(target, entry.path, data, type: entry.type)
                }
                switch mode {
                case "traversal": try add(target, "../escaped", Data("x".utf8))
                case "absolute": try add(target, "/escaped", Data("x".utf8))
                case "backslash": try add(target, "Profile\\..\\escaped", Data("x".utf8))
                case "case-collision": try add(target, "profile/saves/0.celeste", Data("x".utf8))
                case "unicode-collision": try add(target, "Profile/é", Data()); try add(target, "Profile/e\u{301}", Data())
                case "symlink": try add(target, "Profile/link", Data("/tmp".utf8), type: .symlink)
                case "unlisted": try add(target, "Profile/hidden", Data("x".utf8))
                default: break
                }
            }
            try rejects("hostile ZIP rejected: " + mode) { _ = try s.readBundle(url, destination: nil) }
        }
        try check(validManifest.mods[0].modules[0].name == "SampleHelper" && !validManifest.mods[0].enabled, "manifest uses exact module identity and disabled state")
        let many = store(root.appendingPathComponent("many-slots")); _ = try many.initialize(defaults: defaults)
        for n in 0..<350 { try put(many.profile, "Saves/\(n * 7).celeste", n == 0 ? "<!DOCTYPE SaveData [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><SaveData><Name>&x;</Name></SaveData>" : "opaque") }
        try check(ProfileSlots.read(many.profile).count == 352, "350 sparse save slots have no three-slot cap")
        try check(ProfileSlots.read(many.profile)[0]["name"] == nil, "XML external entities never resolved")
        try ProfileIO.fm.createSymbolicLink(atPath: many.profile.appendingPathComponent("linked").path, withDestinationPath: "/tmp")
        try rejects("local profile symlink rejected") { _ = try many.create() }
        try ProfileIO.fm.removeItem(at: many.profile.appendingPathComponent("linked"))
        let results: [String: Any] = ["status": "PASS_PROFILE_BACKUPS", "checks": checks]
        try ProfileIO.write(JSONSerialization.data(withJSONObject: results, options: [.sortedKeys, .prettyPrinted]), to: root.appendingPathComponent("results.json"))
        print("PASS_PROFILE_BACKUPS \(checks.count) checks")
    }
}
