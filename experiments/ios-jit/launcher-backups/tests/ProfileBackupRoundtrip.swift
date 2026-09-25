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
        let result: [String: Any] = ["status": "PASS_REAL_PROFILE_NATIVE_BACKUP_ROUNDTRIP", "portable_revision": expected, "baseline_full_revision": baseline, "rollback_full_revision": changed, "backup_sha256": try ProfileIO.stream(backup, limit: ProfileIO.maxData).0, "state": try store.state()]
        try ProfileIO.write(JSONSerialization.data(withJSONObject: result, options: [.sortedKeys, .prettyPrinted]), to: root.appendingPathComponent("roundtrip.json"))
        print("PASS_REAL_PROFILE_NATIVE_BACKUP_ROUNDTRIP")
    }
}
