import Foundation
@main struct ProfileBackupRoundtrip {
    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let store = ProfileBackups(library: ModLibrary(profile: root.appendingPathComponent("Profile")), vault: root.appendingPathComponent("Vault"))
        _ = try store.initialize(defaults: ["launcher.metrics": true, "launcher.cellularDownloads": false, "launcher.autoUpdateChecks": true])
        let expected = ProfileIO.revision(try ProfileIO.tree(store.profile, portable: true)), backup = try store.create()
        let baseline = ProfileIO.revision(try ProfileIO.tree(store.profile, portable: false))
        try ProfileIO.write(Data("temporary later save".utf8), to: store.profile.appendingPathComponent("Saves/4096.celeste"))
        let changed = ProfileIO.revision(try ProfileIO.tree(store.profile, portable: false))
        let review = try store.prepare(backup); try store.restore(review.id)
        guard ProfileIO.revision(try ProfileIO.tree(store.profile, portable: true)) == expected else { throw LibraryError("Real profile roundtrip failed") }
        try store.rollback()
        guard ProfileIO.revision(try ProfileIO.tree(store.profile, portable: false)) == changed else { throw LibraryError("Real profile rollback failed") }
        try store.discardRetainedProfile()
        let second = try store.prepare(backup); try store.restore(second.id)
        try store.discardRetainedProfile()
        let exported = try store.exportSlot(0, mainOnly: false)
        let keepExport = root.appendingPathComponent("desktop-slot.zip"); try ProfileIO.fm.copyItem(at: exported, to: keepExport)
        let slotReview = try store.prepareSlot([keepExport], target: 2); try store.importSlot(slotReview.id, keepModData: false)
        let copiedSlot = try SaveTransfer.files(store.profile.appendingPathComponent("Saves"), slot: 2)
        guard copiedSlot.count == slotReview.files.count else { throw LibraryError("Real slot files missing after transfer") }
        for row in slotReview.files {
            guard copiedSlot.contains(where: { $0.path == "2" + row.path.dropFirst() && $0.sha256 == row.sha256 }) else { throw LibraryError("Real slot sidecar remapping failed") }
        }
        try store.discardRetainedProfile()
        let returnExport = try store.exportSlot(2, mainOnly: false)
        let returnReview = try store.prepareSlot([returnExport], target: 0); try store.importSlot(returnReview.id, keepModData: false)
        let mainExport = try store.exportSlot(0, mainOnly: true)
        let exportedMain = root.appendingPathComponent("desktop-main.celeste"); try ProfileIO.fm.copyItem(at: mainExport, to: exportedMain)
        let result: [String: Any] = ["status": "PASS_REAL_PROFILE_NATIVE_BACKUP_ROUNDTRIP", "slot_transfer_files": copiedSlot.count, "desktop_zip_sha256": try ProfileIO.stream(keepExport, limit: SaveTransfer.maxBytes).0, "native_main_sha256": try ProfileIO.stream(exportedMain, limit: SaveTransfer.maxFile).0, "portable_revision": expected, "baseline_full_revision": baseline, "rollback_full_revision": changed, "backup_sha256": try ProfileIO.stream(backup, limit: ProfileIO.maxData).0, "state": try store.state()]
        try ProfileIO.write(JSONSerialization.data(withJSONObject: result, options: [.sortedKeys, .prettyPrinted]), to: root.appendingPathComponent("roundtrip.json"))
        print("PASS_REAL_PROFILE_NATIVE_BACKUP_ROUNDTRIP")
    }
}
