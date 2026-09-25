import SwiftUI
import UIKit
import ZIPFoundation

// Simulator-only fixture: real profile store and production view, synthetic saves.
struct ProfilePreviewRoot: View {
    @ObservedObject var model: PreviewProfile
    var body: some View {
            NavigationStack { ProfileBackupView(state: model.state, locked: model.used, action: model.action) }
                .preferredColorScheme(.dark).tint(.pink)
                .environment(\.dynamicTypeSize, ProcessInfo.processInfo.arguments.contains("--large-type") ? .accessibility2 : .large)
                .alert("Export requested", isPresented: $model.exported) { Button("OK", role: .cancel) {} }
    }
}
@main final class ProfilePreviewDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, configurationForConnecting session: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let config = UISceneConfiguration(name: "ProfilePreview", sessionRole: session.role); config.delegateClass = ProfilePreviewScene.self; return config
    }
}
final class ProfilePreviewScene: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let scene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: scene)
        window.rootViewController = UIHostingController(rootView: ProfilePreviewRoot(model: PreviewProfile()))
        self.window = window; window.makeKeyAndVisible()
    }
}
final class PreviewProfile: ObservableObject {
    @Published var state: [String: Any] = [:]
    @Published var exported = false
    var used = ProcessInfo.processInfo.arguments.contains("--used")
    var restart = false
    let store: ProfileBackups
    init() {
        let root = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("ProfileUITests")
        if !ProcessInfo.processInfo.arguments.contains("--preserve") { try? FileManager.default.removeItem(at: root) }
        store = ProfileBackups(library: ModLibrary(profile: root.appendingPathComponent("Profile")), vault: root.appendingPathComponent("Vault"))
        do {
            _ = try store.initialize(defaults: ["launcher.metrics": true, "launcher.cellularDownloads": false, "launcher.autoUpdateChecks": true])
            if !ProcessInfo.processInfo.arguments.contains("--preserve") && !ProcessInfo.processInfo.arguments.contains("--empty") {
                try ProfileIO.write(Data("<SaveData><Name>Madeline</Name><Time>36000000000</Time><TotalDeaths>42</TotalDeaths></SaveData>".utf8), to: store.profile.appendingPathComponent("Saves/0.celeste"))
                try ProfileIO.write(Data("opaque mod data".utf8), to: store.profile.appendingPathComponent("Saves/1000-modsave-Custom.celeste"))
                try ProfileIO.directory(store.profile.appendingPathComponent("Mods"))
                try ProfileIO.write(Data("unknown sidecar".utf8), to: store.profile.appendingPathComponent("Unknown/file"))
            }
            try ProfileIO.write(Data("<SaveData><Version>1.4.0.0</Version><Name>Desktop Madeline</Name><Time>72000000000</Time><TotalDeaths>84</TotalDeaths></SaveData>".utf8), to: root.appendingPathComponent("Desktop/5.celeste"))
            refresh("Ready")
            if ProcessInfo.processInfo.arguments.contains("--failure") { state["error"] = true; state["message"] = "This backup failed its checksum. Your current profile is unchanged." }
        } catch { state = ["ready": false, "error": true, "message": error.localizedDescription] }
    }
    func refresh(_ message: String) {
        do { state = try store.state(); state["ready"] = true; state["restartRequired"] = restart; state["message"] = message }
        catch { state = ["ready": false, "error": true, "message": error.localizedDescription] }
    }
    func action(_ name: String, _ fields: [String: Any]) {
        if name == "export" || name == "profile.export" { exported = true; return }
        guard !used, !restart, state["active"] as? Bool != true else { return }
        state["active"] = true
        DispatchQueue.global(qos: .userInitiated).async {
            var message = "Done", failure = false, replaced = false, exported = false
            do {
                switch name {
                case "profile.slotExport":
                    _ = try self.store.exportSlot(fields["slot"] as! Int, mainOnly: fields["mainOnly"] as? Bool == true); exported = true; message = "Save export verified"
                case "profile.slotImport":
                    _ = try self.store.prepareSlot([self.store.profile.deletingLastPathComponent().appendingPathComponent("Desktop/5.celeste")], target: fields["target"] as! Int); message = "Review incoming save"
                case "profile.slotDuplicate":
                    let zip = try self.store.exportSlot(fields["slot"] as! Int, mainOnly: false)
                    _ = try self.store.prepareSlot([zip], target: -1); message = "Review duplicate save"
                case "profile.slotCommit": try self.store.importSlot(fields["id"] as! String, keepModData: fields["keepModData"] as? Bool == true); replaced = true; message = "Save imported"
                case "profile.create":
                    _ = try self.store.create()
                    // A later save makes exact replacement visible to the UI test.
                    try ProfileIO.write(Data("<SaveData><Name>After backup</Name></SaveData>".utf8), to: self.store.profile.appendingPathComponent("Saves/0.celeste"))
                    message = "Backup verified and retained"
                case "profile.review": _ = try self.store.prepare(self.store.archive(fields["id"] as! String)); message = "Review the backup below"
                case "profile.cancel": try self.store.cancelReview(); message = "Review cancelled"
                case "profile.restore": try self.store.restore(fields["id"] as! String); replaced = true; message = "Backup restored"
                case "profile.rollback": try self.store.rollback(); replaced = true; message = "Previous profile restored"
                case "profile.discard": try self.store.discardRetainedProfile(); message = "Retained copy discarded"
                case "profile.remove": try ProfileIO.fm.removeItem(at: self.store.archive(fields["id"] as! String)); message = "Backup removed"
                default: break
                }
            } catch { message = error.localizedDescription; failure = true }
            DispatchQueue.main.async { self.restart = replaced; self.refresh(message); self.state["error"] = failure; self.exported = exported }
        }
    }
}
