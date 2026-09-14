#if canImport(UIKit)
import SwiftUI
import UIKit

private final class LauncherModel: ObservableObject {
    @Published var state: [String: Any] = [:]
    let action: (String, [String: Any]) -> Void
    init(action: @escaping (String, [String: Any]) -> Void) { self.action = action }
    var mods: [[String: Any]] { state["mods"] as? [[String: Any]] ?? [] }
    var userMods: [[String: Any]] { mods.filter { !($0["internal"] as? Bool ?? false) } }
    var issues: [String] { state["issues"] as? [String] ?? [] }
    func flag(_ key: String) -> Bool { state[key] as? Bool ?? false }
    func text(_ key: String) -> String { state[key] as? String ?? "" }
    var locked: Bool { flag("busy") || flag("used") }
    func send(_ name: String, _ fields: [String: Any] = [:]) { action(name, fields) }
}
private struct LauncherView: View {
    @ObservedObject var model: LauncherModel
    @State private var search = ""
    @State private var tab = 0
    @AppStorage("launcher.metrics") private var metrics = true
    @AppStorage("launcher.sjRegression") private var regression = false
    private let rose = Color(red: 0.96, green: 0.36, blue: 0.47)
    var body: some View {
        TabView(selection: $tab) {
            NavigationStack { play }.tabItem { Label("Play", systemImage: "mountain.2.fill") }.tag(0)
            NavigationStack { mods }.tabItem { Label("Mods", systemImage: "shippingbox.fill") }.tag(1)
            NavigationStack { settings }.tabItem { Label("Settings", systemImage: "slider.horizontal.3") }.tag(2)
        }
        .tint(rose).preferredColorScheme(.dark)
    }
    private func statusRow(_ title: String, _ detail: String, ready: Bool) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: ready ? "checkmark.circle.fill" : "circle.dashed").foregroundStyle(ready ? Color.green : Color.secondary)
            VStack(alignment: .leading, spacing: 3) { Text(title).font(.headline); Text(detail).font(.subheadline).foregroundStyle(.secondary) }
            Spacer(minLength: 0)
        }.padding(.vertical, 4)
    }
    private var play: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 14) {
                    Image(systemName: "mountain.2.fill").font(.system(size: 42, weight: .light)).foregroundStyle(rose)
                    Text("Your next climb").font(.largeTitle.bold())
                    Text("Celeste, with the mods you choose.").font(.title3).foregroundStyle(.secondary)
                    Label("Strawberry Jam profile", systemImage: "person.crop.square").font(.subheadline).foregroundStyle(.secondary)
                }.padding(.vertical, 18).listRowBackground(Color.clear)
            }
            Section("Ready to play") {
                statusRow("Game files", model.flag("contentStaged") ? "Game ZIP selected. Verified before the game starts." : model.flag("hasContent") ? "Your imported Celeste files are retained." : "Import the original Celeste FNA game ZIP once.", ready: model.flag("hasContent"))
                Button(model.flag("hasContent") ? "Choose game ZIP…" : "Import game ZIP…") { model.send("content") }.disabled(model.locked).accessibilityIdentifier("launcher.importGame")
                statusRow("Mods", model.flag("scanning") ? "Reading your mod library…" : "\(model.userMods.filter { $0["enabled"] as? Bool ?? false }.count) enabled · \(model.userMods.count) installed", ready: model.issues.isEmpty && !model.flag("scanning"))
                Button("Manage mods") { tab = 1 }
                statusRow("JIT", model.flag("jitReady") ? "Ready for this running app." : "Enable for each fresh launch using StikDebug in LiveContainer 2.", ready: model.flag("jitReady"))
                Button("Enable via LiveContainer 2") { model.send("jit") }.disabled(model.locked || !model.flag("jitAvailable")).accessibilityIdentifier("launcher.enableJIT")
            }
            if !model.issues.isEmpty {
                Section("Resolve before playing") { ForEach(model.issues.prefix(8), id: \.self) { Text($0).font(.subheadline).foregroundStyle(.orange) }; Button("Open mod library") { tab = 1 } }
            }
            Section {
                Button { model.send("run") } label: { Label("Run Celeste", systemImage: "play.fill").font(.headline).frame(maxWidth: .infinity).padding(.vertical, 9) }
                    .buttonStyle(.borderedProminent).disabled(!model.flag("canRun")).accessibilityIdentifier("launcher.run")
                if model.flag("used") { Text("To play again or change code mods, close this app in the app switcher and relaunch it. Your files and choices are saved.").font(.footnote).foregroundStyle(.secondary) }
            }.listRowBackground(Color.clear)
            if model.flag("busy") || !model.text("message").isEmpty {
                Section(model.text("status")) {
                    if model.flag("busy") { ProgressView().accessibilityLabel("Working") }
                    Text(model.text("message")).font(.subheadline).textSelection(.enabled)
                    if model.flag("canCancelContent") { Button("Cancel import") { model.send("cancelContent") } }
                    if model.flag("canCancelDownload") { Button("Cancel download") { model.send("cancelDownload") } }
                }
            }
        }.listStyle(.insetGrouped).navigationTitle("Celeste").navigationBarTitleDisplayMode(.inline)
    }
    private var shownMods: [[String: Any]] { model.mods.filter { !($0["internal"] as? Bool ?? false) && (search.isEmpty || (String(describing: $0["name"] ?? "") + String(describing: $0["filename"] ?? "")).localizedCaseInsensitiveContains(search)) } }
    private var mods: some View {
        List {
            Section {
                Button { model.send("mods") } label: { Label("Import mod ZIPs…", systemImage: "square.and.arrow.down") }.disabled(model.locked).accessibilityIdentifier("launcher.importMods")
                Menu("Set all mods…") {
                    Button("Enable all") { model.send("all", ["enabled": true]) }
                    Button("Disable all") { model.send("all", ["enabled": false]) }
                }.disabled(model.locked)
                Text("Changes apply to your next launch. Importing a ZIP keeps its original contents. iOS compatibility varies by mod.").font(.footnote).foregroundStyle(.secondary)
            }
            if !model.issues.isEmpty { Section("Needs attention") { ForEach(model.issues, id: \.self) { Text($0).font(.footnote).foregroundStyle(.orange) } } }
            Section("Installed mods") {
                if shownMods.isEmpty { ContentUnavailableView(search.isEmpty ? "Your mod library" : "No matching mods", systemImage: "shippingbox", description: Text(search.isEmpty ? "Import a mod ZIP or download Strawberry Jam below." : "Try a different name.")) }
                ForEach(shownMods.indices, id: \.self) { index in
                    let row = shownMods[index]
                    // Filename is the persistent archive identity, including a content hash for imports.
                    let filename = row["filename"] as? String ?? ""
                    Toggle(isOn: Binding(get: { row["enabled"] as? Bool ?? false }, set: { model.send("toggle", ["filename": filename, "enabled": $0]) })) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text((row["name"] as? String).flatMap { $0.isEmpty ? nil : $0 } ?? filename).font(.headline)
                            Text("\(row["version"] as? String ?? "") · \(ByteCountFormatter.string(fromByteCount: (row["bytes"] as? NSNumber)?.int64Value ?? 0, countStyle: .file))").font(.caption).foregroundStyle(.secondary)
                            if let problem = row["problem"] as? String, !problem.isEmpty { Text(problem).font(.caption).foregroundStyle(.orange) }
                            if let dependencies = row["dependencies"] as? [String], !dependencies.isEmpty { Text("Requires " + dependencies.joined(separator: ", ")).font(.caption2).foregroundStyle(.secondary).lineLimit(3) }
                        }.padding(.vertical, 4)
                    }.disabled(model.locked).accessibilityIdentifier("mod." + filename)
                }
            }
            Section("Strawberry Jam") {
                Button("Download missing SJ mods") { model.send("download") }.disabled(model.locked)
                Text("Downloads the tested release and its dependencies directly over Wi-Fi: up to 1.24 GB. Completed ZIPs are retained if you cancel. Existing enable/disable choices are preserved.").font(.footnote).foregroundStyle(.secondary)
            }
            Section { Button("Rescan files") { model.send("refresh") }.disabled(model.locked) }
        }.navigationTitle("Mods").searchable(text: $search, prompt: "Find a mod")
    }
    private var settings: some View {
        Form {
            Section("While playing") {
                Toggle("Performance overlay", isOn: $metrics).accessibilityIdentifier("launcher.metrics")
                Text("Recent callback FPS, average frame callback time and a rolling 1% low. Callback timing includes game work and waits inside the call; GPU time is not measured. Loading stalls are included. Pausing resets the window.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Diagnostics") {
                Button("Export diagnostics…") { model.send("export") }.accessibilityIdentifier("launcher.export")
                Button("Record LiveContainer / StikDebug versions") { model.send("versions") }
                Button("Export current JIT script…") { model.send("script") }.disabled(!model.flag("jitAvailable") || model.locked)
                Toggle("Strawberry Jam regression test", isOn: $regression).disabled(model.locked)
                Text("Normally off. The test adds lobby/Bing shortcuts and requires both maps, music, a saved jump and background/resume. Normal play uses Celeste’s own menus.").font(.footnote).foregroundStyle(.secondary)
                Text(model.text("process")).font(.caption.monospaced()).textSelection(.enabled)
            }
            Section("About this build") {
                LabeledContent("Version", value: "0.11.0 (20)")
                LabeledContent("Everest", value: "1.6458.0")
                Text("Private development build. Your game files, original mod ZIPs and complete profile saves stay in the app between updates.").font(.footnote).foregroundStyle(.secondary)
            }
        }.navigationTitle("Settings")
    }
}

@objc public final class CJLauncherBridge: NSObject {
    private let model: LauncherModel
    @objc public let viewController: UIViewController
    @objc(initWithAction:) public init(action: @escaping (String, [String: Any]) -> Void) {
        let model = LauncherModel(action: action); self.model = model
        self.viewController = UIHostingController(rootView: LauncherView(model: model)); super.init()
    }
    @objc(update:) public func update(_ state: [String: Any]) { model.state = state }
}
#endif
