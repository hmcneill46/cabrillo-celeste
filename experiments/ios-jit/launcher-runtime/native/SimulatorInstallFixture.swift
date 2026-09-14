#if targetEnvironment(simulator)
import Foundation

// Test fixtures live in the simulator's Documents, never inside a device IPA.
// This exercises the same planner, ZIP verifier, installer and journal as iOS.
enum SimulatorInstallFixture {
    static func make(_ library: ModLibrary) -> DependencyInstaller? {
        guard ProcessInfo.processInfo.arguments.contains("--launcher-install-ui-fixture") else { return nil }
        do {
            let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let folder = documents.appendingPathComponent("InstallerFixtures")
            let candidates = try JSONDecoder().decode([String: DownloadCandidate].self, from: InstallJournal.boundedRead(folder.appendingPathComponent("candidates.json"), limit: 1_048_576))
            for name in ["root", "helper-old"] where !FileManager.default.fileExists(atPath: library.mods.appendingPathComponent(name + ".zip").path) {
                _ = try library.importZIP(folder.appendingPathComponent(name + ".zip"))
            }
            var db = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), allowEmpty: true)
            for name in ["helper-new", "leaf-new"] {
                guard let row = candidates[name] else { throw LibraryError("Missing simulator index fixture.") }
                for module in row.modules { db.byName[module.name] = row; db.indexedByName[module.name] = row }
            }
            return DependencyInstaller(library: library, pins: [], indexProvider: { token in try token.check(); return db }, downloadProvider: { url, target, _, _, token, progress in
                guard let name = candidates.first(where: { $0.value.url == url })?.key else { throw LibraryError("Unrecognized simulator download.") }
                let data = try InstallJournal.boundedRead(folder.appendingPathComponent(name + ".zip"), limit: 1_048_576)
                for i in 1...20 {
                    try token.check(); progress(Int64(data.count * i / 20), Int64(data.count)); Thread.sleep(forTimeInterval: 0.1)
                }
                try token.check(); try data.write(to: target)
            })
        } catch {
            return DependencyInstaller(library: library, pins: [], indexProvider: { _ in throw error })
        }
    }
}
#endif
