import Foundation
import ZIPFoundation
import Darwin

extension ProfileBackupTests {
    static func slotCrash(_ root: URL, _ phase: String) throws {
        let s = store(root); try seed(s)
        try put(s.profile, "Saves/0-modsave-Future.celeste", "opaque future bytes")
        let before = ProfileIO.revision(try ProfileIO.tree(s.profile, portable: false))
        let zip = try s.exportSlot(0, mainOnly: false), review = try s.prepareSlot([zip], target: 2)
        let expected = root.appendingPathComponent("Expected")
        try ProfileIO.fm.copyItem(at: s.profile, to: expected)
        for row in review.files { try ProfileIO.fm.copyItem(at: s.slotRoot.appendingPathComponent("Incoming/" + row.path), to: expected.appendingPathComponent("Saves/2" + row.path.dropFirst())) }
        let after = ProfileIO.revision(try ProfileIO.tree(expected, portable: false))
        try put(root, "expected.json", String(data: try ProfileIO.encode(["before": before, "after": after]), encoding: .utf8)!)
        s.fault = { if $0 == phase { _exit(86) } }
        try s.importSlot(review.id, keepModData: false)
        throw LibraryError("Did not reach save transfer fault point")
    }
    static func transfers(_ root: URL) throws {
        let empty = store(root.appendingPathComponent("empty")); _ = try empty.initialize(defaults: defaults)
        try check(ProfileSlots.read(empty.profile).compactMap { $0["id"] as? Int } == [0,1,2], "fresh profile shows all three empty vanilla slots")
        try put(empty.profile, "Saves/2.celeste", "<SaveData><Name>Only third</Name></SaveData>")
        let gaps = try ProfileSlots.read(empty.profile)
        try check(gaps.count == 3 && gaps[0]["empty"] as? Bool == true && gaps[1]["empty"] as? Bool == true && gaps[2]["name"] as? String == "Only third", "occupied slot3 keeps empty slot1 and slot2 visible")
        let vanillaZIP = try empty.exportSlot(2, mainOnly: false)
        try check(!empty.prepareSlot([vanillaZIP], target: 0).mainOnly, "a complete slot ZIP with no sidecars still replaces the complete destination slot")
        try empty.cancelReview()
        let s = store(root.appendingPathComponent("transfer")); try seed(s)
        let sidecars = ["0-modsavedata.celeste": Data("<ModSaveData>vanilla fallback</ModSaveData>".utf8), "0-modsave-Future.celeste": Data([0,255,3,0,4]), "0-modsession-Future.celeste": Data("opaque session".utf8)]
        for (name, bytes) in sidecars { try ProfileIO.write(bytes, to: s.profile.appendingPathComponent("Saves/" + name)) }
        try put(s.profile, "Saves/7-modsave-Stale.celeste", "other player's mod data")
        let before = ProfileIO.revision(try ProfileIO.tree(s.profile, portable: false))
        let zip = try s.exportSlot(0, mainOnly: false)
        let archive = try Archive(url: zip, accessMode: .read)
        try check(Set(archive.map(\.path)) == Set(["0.celeste", "cabrillo-save.json", "README.txt"] + Array(sidecars.keys)), "slot ZIP uses plain desktop filenames and includes every standard mod sidecar")
        let reviewed = try s.prepareSlot([zip], target: 7)
        try check(reviewed.source == 0 && reviewed.target == 7 && reviewed.existing["name"] as? String == "Theo" && reviewed.incoming["name"] as? String == "Madeline", "import review compares actual source and destination progress")
        try rejects("whole restore and save reviews cannot overlap") { _ = try s.create() }
        try rejects("full slot cannot silently mix old mod data") { try s.importSlot(reviewed.id, keepModData: true) }
        try rejects("stale per-slot confirmation rejected") { try s.importSlot(UUID().uuidString, keepModData: false) }
        try s.importSlot(reviewed.id, keepModData: false)
        for (name, bytes) in sidecars {
            try check(ProfileIO.read(s.profile.appendingPathComponent("Saves/7" + name.dropFirst()), limit: 1024) == bytes, "opaque sidecar remapped byte-exactly: " + name)
        }
        try check(!ProfileIO.fm.fileExists(atPath: s.profile.appendingPathComponent("Saves/7-modsave-Stale.celeste").path), "full replacement removes stale destination mod data")
        try check(ProfileIO.revision(ProfileIO.tree(s.old, portable: false)) == before, "slot replacement retains the complete previous profile")
        let prior = try ProfileIO.tree(s.old, portable: false).filter { ProfileSlots.identifier($0.path) != 7 }
        let current = try ProfileIO.tree(s.profile, portable: false).filter { ProfileSlots.identifier($0.path) != 7 }
        try check(ProfileIO.revision(prior) == ProfileIO.revision(current), "all other slots, caches, archives, unknown files and settings unchanged")
        try rejects("second slot replacement blocked until retained decision") { _ = try s.prepareSlot([zip], target: 2) }
        try s.rollback(); try check(ProfileIO.revision(ProfileIO.tree(s.profile, portable: false)) == before, "slot import rolls back byte-exactly")
        try s.discardRetainedProfile()
        let raw = try s.exportSlot(0, mainOnly: true)
        try check(raw.lastPathComponent == "0.celeste" && ProfileIO.read(raw, limit: 4096) == ProfileIO.read(s.profile.appendingPathComponent("Saves/0.celeste"), limit: 4096), "main-only export keeps exact native file bytes and filename")
        let rawReview = try s.prepareSlot([raw], target: 7)
        try check(rawReview.mainOnly, "main-only import offers existing mod-data choice")
        try s.importSlot(rawReview.id, keepModData: true)
        try check(ProfileIO.read(s.profile.appendingPathComponent("Saves/7-modsave-Stale.celeste"), limit: 1024) == Data("other player's mod data".utf8), "vanilla update can preserve existing mod files")
        try s.rollback(); try s.discardRetainedProfile()
        let raw2 = try s.prepareSlot([raw], target: 7); try s.importSlot(raw2.id, keepModData: false)
        try check(!ProfileIO.fm.fileExists(atPath: s.profile.appendingPathComponent("Saves/7-modsave-Stale.celeste").path), "explicit replace-all choice clears old mod files for a different climb")
        try s.rollback(); try s.discardRetainedProfile()
        let again = try s.prepareSlot([raw], target: -1)
        try check(again.target == 1, "import another save uses the first empty slot without overwriting occupied slots")
        try s.cancelReview(); try check(ProfileIO.revision(ProfileIO.tree(s.profile, portable: false)) == before, "cancelled slot import leaves every active byte unchanged")
        let external = root.appendingPathComponent("Desktop"); try ProfileIO.directory(external)
        try put(external, "9.celeste", "<SaveData><Version>1.4.0.0</Version><Name>Desktop</Name><Time>72000000000</Time></SaveData>")
        try put(external, "9-modsave-Custom.celeste", "binary/yaml is opaque")
        let desktop = [external.appendingPathComponent("9.celeste"), external.appendingPathComponent("9-modsave-Custom.celeste")]
        let multi = try s.prepareSlot(desktop, target: 2)
        try put(external, "9.celeste", "changed after selecting")
        try s.importSlot(multi.id, keepModData: false)
        try check(ProfileSlots.read(s.profile).first { $0["id"] as? Int == 2 }?["name"] as? String == "Desktop", "multi-file desktop import uses its checked private copy")
        try s.rollback(); try s.discardRetainedProfile()
        let stale = try s.prepareSlot([raw], target: 2)
        try put(s.profile, "Unknown/changed", "concurrent")
        try rejects("profile revision change invalidates slot review") { try s.importSlot(stale.id, keepModData: true) }; try s.cancelReview()
        try ProfileIO.fm.removeItem(at: s.profile.appendingPathComponent("Unknown/changed"))
        let tamper = try s.prepareSlot([raw], target: 2)
        try put(s.slotRoot, "Incoming/0.celeste", "<SaveData><Name>tampered</Name></SaveData>")
        try rejects("staged save tampering rejected") { try s.importSlot(tamper.id, keepModData: true) }; try s.cancelReview()
        let folderZip = root.appendingPathComponent("desktop-folder.zip")
        do { let z = try Archive(url: folderZip, accessMode: .create); try add(z, "Saves/", Data(), type: .directory); try add(z, "Saves/4.celeste", Data("<SaveData><Name>Folder ZIP</Name></SaveData>".utf8)); try add(z, "Saves/4-modsave-Custom.celeste", Data("opaque".utf8)) }
        try check(s.prepareSlot([folderZip], target: 2).files.count == 2, "ordinary desktop ZIP with Saves folder accepted without Cabrillo metadata"); try s.cancelReview()
        for mode in ["traversal", "absolute", "duplicate", "case", "symlink", "multiple-slots", "no-main", "settings", "leading-zero", "bad-xml", "doctype", "manifest-digest", "folder-as-save"] {
            let url = root.appendingPathComponent("save-invalid-" + mode + ".zip")
            do {
                let z = try Archive(url: url, accessMode: .create)
                if mode != "no-main" && mode != "folder-as-save" {
                    let xml = mode == "bad-xml" ? "<Settings/>" : mode == "doctype" ? "<!DOCTYPE SaveData [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><SaveData><Name>&x;</Name></SaveData>" : "<SaveData><Name>Valid</Name></SaveData>"
                    try add(z, "0.celeste", Data(xml.utf8))
                }
                switch mode {
                case "traversal": try add(z, "../0.celeste", Data())
                case "absolute": try add(z, "/0.celeste", Data())
                case "duplicate": try add(z, "Saves/0.celeste", Data())
                case "case": try add(z, "0.CELESTE", Data())
                case "symlink": try add(z, "0-modsave-x.celeste", Data("/tmp".utf8), type: .symlink)
                case "multiple-slots": try add(z, "1.celeste", Data("<SaveData/>".utf8))
                case "no-main": try add(z, "0-modsave-x.celeste", Data())
                case "settings": try add(z, "settings.celeste", Data())
                case "leading-zero": try add(z, "00.celeste", Data())
                case "folder-as-save": try add(z, "0.celeste/", Data(), type: .directory)
                case "manifest-digest":
                    let m = SaveTransfer.Manifest(created: ISO8601DateFormatter().string(from: Date()), sourceSlot: 0, files: [ProfileIO.File(path: "0.celeste", directory: false, bytes: 1, sha256: String(repeating: "0", count: 64), modified: 0)])
                    try add(z, "cabrillo-save.json", ProfileIO.encode(m))
                default: break
                }
            }
            try rejects("invalid save ZIP rejected: " + mode) { _ = try s.prepareSlot([url], target: 2) }
            try check(ProfileIO.revision(ProfileIO.tree(s.profile, portable: false)) == before, "invalid save leaves active profile intact: " + mode)
        }
        for phase in ["prepared", "old_moved", "new_moved", "committed"] {
            let location = root.appendingPathComponent("slot-crash-" + phase)
            let child = Process(); child.executableURL = URL(fileURLWithPath: CommandLine.arguments[0]); child.arguments = [location.path, "--slot-crash", phase]
            try child.run(); child.waitUntilExit(); try check(child.terminationStatus == 86, "save transfer process killed at " + phase)
            let recovered = store(location); _ = try recovered.initialize(defaults: defaults)
            let data = try ProfileIO.read(location.appendingPathComponent("expected.json"), limit: 4096), expected = try JSONDecoder().decode([String: String].self, from: data)
            try check(ProfileIO.revision(ProfileIO.tree(recovered.profile, portable: false)) == expected[phase == "committed" ? "after" : "before"], "save transfer recovers complete profile after " + phase)
        }
    }
}
