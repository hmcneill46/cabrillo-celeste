import Foundation
@main struct VanillaSaveImport {
    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let store = ProfileBackups(library: ModLibrary(profile: root.appendingPathComponent("Profile")), vault: root.appendingPathComponent("Vault"))
        _ = try store.initialize(defaults: ["launcher.metrics": true, "launcher.cellularDownloads": false, "launcher.autoUpdateChecks": true])
        let saves = store.profile.appendingPathComponent("Saves")
        let baseline = try ProfileIO.tree(store.profile, portable: false)
        let original = try SaveSummary.parse(ProfileIO.read(root.appendingPathComponent("desktop-main.celeste"), limit: 33_554_432))!
        let incoming = root.appendingPathComponent("Incoming/0.celeste")
        let fields = try SaveSummary.parse(ProfileIO.read(incoming, limit: 33_554_432))!
        guard Int64(fields["Time"]!) == Int64(original["Time"]!)! + 600_000_000, Int(fields["TotalDeaths"]!) == Int(original["TotalDeaths"]!)! + 1 else { throw LibraryError("Vanilla progress change missing") }
        let review = try store.prepareSlot([incoming], target: 0); try store.importSlot(review.id, keepModData: true)
        let after = try ProfileIO.tree(store.profile, portable: false)
        guard ProfileIO.revision(baseline.filter { $0.path != "Saves/0.celeste" }) == ProfileIO.revision(after.filter { $0.path != "Saves/0.celeste" }) else { throw LibraryError("Vanilla import changed unrelated profile data") }
        guard try ProfileIO.read(saves.appendingPathComponent("0.celeste"), limit: 33_554_432) == ProfileIO.read(incoming, limit: 33_554_432) else { throw LibraryError("Vanilla bytes were rewritten") }
        try store.discardRetainedProfile()
        let export = try store.exportSlot(0, mainOnly: false)
        let copy = try store.prepareSlot([export], target: 2); try store.importSlot(copy.id, keepModData: false)
        print("PASS_ORIGINAL_VANILLA_TO_NATIVE_IMPORT_WITH_MOD_DATA_PRESERVED")
    }
}
