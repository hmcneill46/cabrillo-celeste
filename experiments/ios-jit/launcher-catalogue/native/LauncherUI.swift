#if canImport(UIKit)
import SwiftUI
import UIKit

private final class LauncherModel: ObservableObject {
    let browser = CatalogueBrowserModel()
    @Published var state: [String: Any] = [:]
    let action: (String, [String: Any]) -> Void
    init(action: @escaping (String, [String: Any]) -> Void) { self.action = action }
    var mods: [[String: Any]] { state["mods"] as? [[String: Any]] ?? [] }
    var userMods: [[String: Any]] { mods.filter { !($0["internal"] as? Bool ?? false) && !($0["retainedPrevious"] as? Bool ?? false) } }
    var previousMods: [[String: Any]] { mods.filter { $0["retainedPrevious"] as? Bool == true } }
    var issues: [String] { state["issues"] as? [String] ?? [] }
    var install: [String: Any] { state["installation"] as? [String: Any] ?? [:] }
    var plan: [String: Any] { install["plan"] as? [String: Any] ?? [:] }
    var updates: [[String: Any]] { state["updates"] as? [[String: Any]] ?? [] }
    func flag(_ key: String) -> Bool { state[key] as? Bool ?? false }
    func text(_ key: String) -> String { state[key] as? String ?? "" }
    var locked: Bool { flag("busy") || flag("used") }
    func send(_ name: String, _ fields: [String: Any] = [:]) { action(name, fields) }
}
private struct LauncherView: View {
    @ObservedObject var model: LauncherModel
    @State private var search = ""
    @State private var tab = 0
    @State private var modPage = 0
    @State private var showPrevious = false
    @AppStorage("launcher.metrics") private var metrics = true
    @AppStorage("launcher.cellularDownloads") private var cellular = false
    @AppStorage("launcher.autoUpdateChecks") private var autoUpdateChecks = true
    private let rose = Color(red: 0.96, green: 0.36, blue: 0.47)
    private func bytes(_ value: Any?) -> String { ByteCountFormatter.string(fromByteCount: (value as? NSNumber)?.int64Value ?? 0, countStyle: .file) }
    var body: some View {
        Group { if model.flag("closing") { closing } else { tabs } }
            .tint(rose).preferredColorScheme(.dark)
            .sheet(isPresented: Binding(get: { model.flag("showInstallation") }, set: { if !$0 { model.send("closeInstallation") } })) { installation }
    }
    private var closing: some View {
        VStack(spacing: 22) {
            Image(systemName: "mountain.2.fill").font(.system(size: 48, weight: .light)).foregroundStyle(rose)
            Text("Returning to camp").font(.largeTitle.bold())
            ProgressView().controlSize(.large)
            Text(model.text("shutdownDetail")).font(.title3).accessibilityIdentifier("session.stage")
            Text("Finishing your session. Please keep the app open.").foregroundStyle(.secondary)
            Text("Saving is checked before the game closes.").font(.footnote).foregroundStyle(.secondary)
        }.multilineTextAlignment(.center).padding(28).frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(red: 0.055, green: 0.063, blue: 0.09))
    }
    private var tabs: some View {
        TabView(selection: $tab) {
            NavigationStack { play }.tabItem { Label("Play", systemImage: "mountain.2.fill") }.tag(0)
            NavigationStack { mods }.tabItem { Label("Mods", systemImage: "shippingbox.fill") }.tag(1)
            NavigationStack { settings }.tabItem { Label("Settings", systemImage: "slider.horizontal.3") }.tag(2)
        }
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
                    Label("My Celeste", systemImage: "person.crop.square").font(.subheadline).foregroundStyle(.secondary)
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
                Section {
                    Label("Your mod selection needs attention", systemImage: "exclamationmark.circle").foregroundStyle(.orange)
                    Text("Review missing dependencies or incompatible versions before playing.").font(.subheadline).foregroundStyle(.secondary)
                    Button("Resolve dependencies…") { model.send("resolve") }.disabled(model.locked).accessibilityIdentifier("launcher.resolve")
                }
            }
            Section {
                Button { model.send("run") } label: { Label("Run Celeste", systemImage: "play.fill").font(.headline).frame(maxWidth: .infinity).padding(.vertical, 9) }
                    .buttonStyle(.borderedProminent).disabled(model.locked || model.flag("scanning")).accessibilityIdentifier("launcher.run")
                if model.flag("used") { Text("To play again or change code mods, close this app in the app switcher and relaunch it. Your files and choices are saved.").font(.footnote).foregroundStyle(.secondary) }
            }.listRowBackground(Color.clear)
            if model.flag("busy") || !model.text("message").isEmpty {
                Section(model.text("status")) {
                    if model.flag("busy") { ProgressView().accessibilityLabel("Working") }
                    Text(model.text("message")).font(.subheadline).textSelection(.enabled)
                    if model.flag("canCancelContent") { Button("Cancel import") { model.send("cancelContent") } }
                }
            }
        }.listStyle(.insetGrouped).navigationTitle("Celeste").navigationBarTitleDisplayMode(.inline)
    }
    private var shownMods: [[String: Any]] { (model.userMods + (showPrevious ? model.previousMods : [])).filter { search.isEmpty || (String(describing: $0["name"] ?? "") + String(describing: $0["filename"] ?? "")).localizedCaseInsensitiveContains(search) } }
    private var mods: some View {
        VStack(spacing: 0) {
            Picker("Mod library", selection: $modPage) { Text("Installed").tag(0); Text("Browse").tag(2); Text("Updates").tag(1) }.pickerStyle(.segmented).accessibilityIdentifier("mods.pages").padding(.horizontal, 20).padding(.vertical, 9)
            if modPage == 2 {
                if model.flag("used") || model.browser.suspended { ContentUnavailableView("Browsing paused", systemImage: "moon.zzz", description: Text("Close and relaunch the app to browse or change mods for your next game session.")) }
                else { CatalogueBrowserView(model: model.browser, locked: model.locked, review: { selection in model.send("planCatalogue", ["pageURL": selection.pageURL, "fileIDs": selection.fileIDs]) }, log: model.send) }
            }
            else { List { if modPage == 0 { installedMods } else { updateMods.onAppear { model.send("checkUpdatesIfDue") } } } }
        }.navigationTitle("Mods").searchable(text: Binding(get: { modPage == 2 ? model.browser.search : search }, set: { if modPage == 2 { model.browser.search = $0 } else { search = $0 } }), prompt: modPage == 2 ? "Search Celeste mods" : "Find an installed mod")
    }
    @ViewBuilder private var installedMods: some View {
        Section {
            Button { model.send("mods") } label: { Label("Import mod ZIPs…", systemImage: "square.and.arrow.down") }.disabled(model.locked).accessibilityIdentifier("launcher.importMods")
            Button { model.send("resolve") } label: { Label("Resolve dependencies…", systemImage: "puzzlepiece.extension") }.disabled(model.locked).accessibilityIdentifier("mods.resolve")
            Button { model.send("installationReport") } label: { Label("Last installation report", systemImage: "list.bullet.rectangle") }.disabled(model.flag("busy")).accessibilityIdentifier("mods.lastReport")
            Menu("Set all mods…") {
                Button("Enable all") { model.send("all", ["enabled": true]) }
                Button("Disable all") { model.send("all", ["enabled": false]) }
            }.disabled(model.locked)
            Text("Original ZIPs and your choices are kept between app updates. Changes apply to the next game session.").font(.footnote).foregroundStyle(.secondary)
            if !model.previousMods.isEmpty { Toggle("Show retained previous archives (\(model.previousMods.count))", isOn: $showPrevious).font(.subheadline) }
        }
        if !model.issues.isEmpty {
            Section("Needs attention") { ForEach(model.issues.prefix(12), id: \.self) { Text($0).font(.subheadline).foregroundStyle(.orange) }
                if model.issues.count > 12 { Text("\(model.issues.count - 12) more issues. Resolve dependencies to review the complete plan.").font(.footnote) }
            }
        }
        Section("Installed mods") {
            if shownMods.isEmpty { ContentUnavailableView(search.isEmpty ? "Your mod library" : "No matching mods", systemImage: "shippingbox", description: Text(search.isEmpty ? "Import a mod ZIP to begin. Its dependencies can be downloaded here." : "Try a different name.")) }
            ForEach(shownMods.indices, id: \.self) { index in
                let row = shownMods[index], filename = row["filename"] as? String ?? ""
                Toggle(isOn: Binding(get: { row["enabled"] as? Bool ?? false }, set: { model.send("toggle", ["filename": filename, "enabled": $0]) })) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text((row["name"] as? String).flatMap { $0.isEmpty ? nil : $0 } ?? filename).font(.headline)
                        Text("\(row["version"] as? String ?? "") · \(bytes(row["bytes"]))").font(.caption).foregroundStyle(.secondary)
                        if row["retainedPrevious"] as? Bool == true { Text("Previous archive kept for recovery. Disable its replacement before enabling this version.").font(.caption).foregroundStyle(.orange) }
                        if let problem = row["problem"] as? String, !problem.isEmpty { Text(problem).font(.caption).foregroundStyle(.orange) }
                        if let deps = row["dependencies"] as? [String], !deps.isEmpty { Text("Requires " + deps.joined(separator: ", ")).font(.caption2).foregroundStyle(.secondary).lineLimit(2) }
                    }.padding(.vertical, 4)
                }.disabled(model.locked).accessibilityIdentifier("mod." + filename)
            }
        }
        Section { Button("Rescan files") { model.send("refresh") }.disabled(model.locked) }
    }
    @ViewBuilder private var updateMods: some View {
        Section {
            Button { model.send("checkUpdates") } label: { Label("Check for updates", systemImage: "arrow.clockwise") }.disabled(model.locked).accessibilityIdentifier("mods.checkUpdates")
            Button("Last installation report") { model.send("installationReport") }.disabled(model.flag("busy")).accessibilityIdentifier("mods.lastReport")
            let available = model.updates.filter { $0["canUpdate"] as? Bool == true }
            if !available.isEmpty { Button("Update all compatible (\(available.count))…") { model.send("planUpdates", ["filenames": available.compactMap { $0["filename"] as? String }]) }.disabled(model.locked).accessibilityIdentifier("mods.updateAll") }
            Text("Review version changes and any new dependencies before downloading. Disabled mods stay disabled; compatible dependencies are kept.").font(.footnote).foregroundStyle(.secondary)
            if model.flag("checkingUpdates") { ProgressView(model.install["message"] as? String ?? "Checking updates…") }
            else if !model.text("updateMessage").isEmpty { Text(model.text("updateMessage")).font(.footnote).foregroundStyle(.secondary) }
        }
        Section("Compatible updates") {
            let rows = model.updates.filter { $0["canUpdate"] as? Bool == true && (search.isEmpty || ($0["name"] as? String ?? "").localizedCaseInsensitiveContains(search)) }
            if rows.isEmpty && model.flag("updatesChecked") { Label("No available updates in this index", systemImage: "checkmark.circle").foregroundStyle(.secondary) }
            ForEach(rows.indices, id: \.self) { i in
                let row = rows[i], filename = row["filename"] as? String ?? ""
                VStack(alignment: .leading, spacing: 9) {
                    Text(row["name"] as? String ?? filename).font(.headline)
                    Text("\(row["current"] as? String ?? "") → \(row["latest"] as? String ?? "") · \(bytes(row["bytes"]))").font(.subheadline).foregroundStyle(.secondary)
                    if row["enabled"] as? Bool == false { Label("Stays disabled", systemImage: "pause.circle").font(.caption).foregroundStyle(.secondary) }
                    if let reason = row["reason"] as? String, !reason.isEmpty { Text(reason).font(.caption).foregroundStyle(.orange) }
                    Button("Update…") { model.send("planUpdates", ["filenames": [filename]]) }.disabled(model.locked || row["canUpdate"] as? Bool != true).accessibilityIdentifier("update." + filename)
                }.padding(.vertical, 5)
            }
        }
        let blocked = model.updates.filter { $0["canUpdate"] as? Bool != true && (search.isEmpty || ($0["name"] as? String ?? "").localizedCaseInsensitiveContains(search)) }
        if !blocked.isEmpty {
            Section("Requires an app update") {
                ForEach(blocked.indices, id: \.self) { i in
                    let row = blocked[i]
                    VStack(alignment: .leading, spacing: 9) {
                        Label(row["name"] as? String ?? "Mod", systemImage: "lock.fill").font(.headline)
                        Text("Installed \(row["current"] as? String ?? "") · Latest \(row["latest"] as? String ?? "")").font(.subheadline).foregroundStyle(.secondary)
                        Text(row["reason"] as? String ?? "This release cannot be installed by this app version.").font(.caption).foregroundStyle(.orange)
                        Text("Current version kept").font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                    }.padding(.vertical, 5).accessibilityIdentifier("blockedUpdate." + (row["filename"] as? String ?? ""))
                }
            }
        }
    }
    private var installation: some View {
        let active = model.install["active"] as? Bool ?? false
        let phase = model.install["phase"] as? String ?? "checking"
        let issues = model.plan["issues"] as? [String] ?? []
        return NavigationStack {
            List {
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        Image(systemName: phase == "complete" ? "checkmark.seal.fill" : "shippingbox.fill").font(.system(size: 36)).foregroundStyle(phase == "complete" ? .green : rose)
                        Text(phase == "complete" ? "Ready for your next climb" : phase == "report" ? "Installation report" : phase == "review" && !issues.isEmpty ? "Installation blocked" : "Prepare your mods").font(.title.bold())
                        Text(model.install["message"] as? String ?? "Checking dependencies…").foregroundStyle(.secondary).accessibilityIdentifier("install.message")
                        if active {
                            if let total = model.install["totalBytes"] as? NSNumber, total.doubleValue > 0, let done = model.install["receivedBytes"] as? NSNumber {
                                ProgressView(value: min(done.doubleValue, total.doubleValue), total: total.doubleValue)
                                Text("\(bytes(done)) of \(bytes(total)) · \(model.install["completedFiles"] as? Int ?? 0)/\(model.install["totalFiles"] as? Int ?? 0) files").font(.caption).monospacedDigit()
                            } else { ProgressView() }
                        }
                    }.padding(.vertical, 10)
                }
                if !active, let report = model.install["report"] as? [String: Any] {
                    installationReport(report)
                }
                if phase == "review" {
                    if !issues.isEmpty {
                        Section("Cannot install this selection") {
                            Text("Nothing has been installed. These requirements must be resolved before any changes can be applied.").font(.subheadline).accessibilityIdentifier("install.blocked")
                            ForEach(issues, id: \.self) { Text($0).foregroundStyle(.orange) }
                            Text("Keep a compatible installed version, import an earlier compatible release, or use a future app version with the required runtime. Mod ZIPs cannot replace the app's runtime.").font(.footnote).foregroundStyle(.secondary)
                        }
                    }
                    let choices = model.plan["compatibilityChoices"] as? [String] ?? []
                    if !choices.isEmpty { Section("Compatible earlier releases") { ForEach(choices, id: \.self) { Text($0).font(.subheadline) } } }
                    let downloads = model.plan["downloads"] as? [[String: Any]] ?? []
                    if !downloads.isEmpty {
                        Section(issues.isEmpty ? "Download · \(bytes(model.plan["totalBytes"]))" : "Proposed downloads · blocked") {
                            ForEach(downloads.indices, id: \.self) { i in
                                let row = downloads[i]
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(row["name"] as? String ?? "Mod").font(.headline)
                                    Text(bytes(row["bytes"])).font(.caption).foregroundStyle(.secondary)
                                    if row["staysDisabled"] as? Bool == true { Text("Stays disabled").font(.caption).foregroundStyle(.secondary) }
                                    if row["pinned"] as? Bool == true { Text("Verified original release").font(.caption).foregroundStyle(.secondary) }
                                }
                            }
                        }
                    }
                    let enable = model.plan["enable"] as? [String] ?? [], disable = model.plan["disable"] as? [String] ?? []
                    if !enable.isEmpty { Section("Enable existing") { ForEach(enable, id: \.self) { Text($0).font(.subheadline) } } }
                    if !disable.isEmpty { Section("Keep previous archives disabled") { ForEach(disable, id: \.self) { Text($0).font(.subheadline) }; Text("Original files are retained for recovery.").font(.footnote).foregroundStyle(.secondary) } }
                    Section {
                        if model.plan["canApply"] as? Bool == true {
                            Button(downloads.isEmpty ? "Apply changes" : "Download and install") { model.send("applyInstallation", ["planID": model.plan["id"] as? String ?? ""]) }.buttonStyle(.borderedProminent).accessibilityIdentifier("install.apply")
                        } else if issues.isEmpty { Label("All required dependencies are ready", systemImage: "checkmark.circle").foregroundStyle(.green) }
                        if issues.isEmpty { Text(cellular ? "Keep the app open while downloading. Cellular downloads are enabled." : "Keep the app open on Wi-Fi. Completed, verified downloads survive cancellation.").font(.footnote).foregroundStyle(.secondary) }
                    }
                }
                if phase == "failed" || phase == "cancelled" {
                    Section { Button("Review dependencies again") { model.send("resolve") }.accessibilityIdentifier("install.retry"); Text("Existing mods and saves are retained. Updates can be checked again from the Updates page.").font(.footnote).foregroundStyle(.secondary) }
                }
            }.navigationTitle("Review installation").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button(active ? "Cancel" : "Done") { model.send(active ? "cancelInstallation" : "closeInstallation") }.disabled(phase == "installing").accessibilityIdentifier("install.close") } }
        }.interactiveDismissDisabled(active).preferredColorScheme(.dark).tint(rose)
    }
    @ViewBuilder private func installationReport(_ report: [String: Any]) -> some View {
        let applied = report["applicationState"] as? String == "applied"
        let changes = report["changes"] as? [[String: Any]] ?? []
        Section("Result") {
            if let started = report["started"] as? NSNumber { Text(Date(timeIntervalSinceReferenceDate: started.doubleValue), format: .dateTime.day().month().hour().minute()).font(.caption).foregroundStyle(.secondary) }
            Label(applied ? "Changes applied" : report["applicationState"] as? String == "unconfirmed" ? "Changes need verification" : "No mod changes applied", systemImage: applied ? "checkmark.circle.fill" : "info.circle").accessibilityIdentifier("install.reportResult")
            Text(report["message"] as? String ?? "").font(.subheadline)
            if let error = model.install["reportPersistenceError"] as? String { Text("Report could not be saved: " + error).font(.footnote).foregroundStyle(.orange) }
        }
        if applied {
            ForEach(["updated", "refreshed", "installed", "enabled", "disabled"], id: \.self) { action in
                let rows = changes.filter { $0["action"] as? String == action }
                if !rows.isEmpty {
                    Section(["updated": "Updated mods", "refreshed": "Refreshed archives", "installed": "Installed mods", "enabled": "Enabled existing mods", "disabled": "Disabled mods"][action]!) {
                        ForEach(rows.indices, id: \.self) { i in
                            let row = rows[i]
                            VStack(alignment: .leading, spacing: 4) {
                                Text(row["name"] as? String ?? "Mod").font(.headline)
                                if action == "updated" { Text("\(row["beforeVersion"] as? String ?? "") → \(row["afterVersion"] as? String ?? "")").font(.subheadline).accessibilityIdentifier("change." + (row["name"] as? String ?? "")) }
                                else { Text(row["afterVersion"] as? String ?? "").font(.subheadline) }
                                if action == "enabled" { Text("Off → On").font(.caption).foregroundStyle(.secondary) }
                                else if action == "disabled" { Text("On → Off").font(.caption).foregroundStyle(.secondary) }
                                else if row["enabled"] as? Bool == false { Text("Kept disabled").font(.caption).foregroundStyle(.secondary) }
                                else if action == "installed" { Text("Downloaded, verified and enabled").font(.caption).foregroundStyle(.secondary) }
                            }
                        }
                    }
                }
            }
        }
        let downloads = report["downloads"] as? [[String: Any]] ?? []
        if !applied && !downloads.isEmpty {
            Section("Downloads") {
                ForEach(downloads.indices, id: \.self) { i in
                    let row = downloads[i], status = row["status"] as? String ?? "notAttempted"
                    VStack(alignment: .leading, spacing: 4) {
                        Text(row["name"] as? String ?? "Mod").font(.headline)
                        Text(["verified": "Downloaded and verified · kept for retry", "failed": "Failed", "cancelled": "Cancelled", "notAttempted": "Not attempted", "verificationRecorded": "Verified before interruption", "interrupted": "Result not recorded"][status] ?? status).font(.caption).foregroundStyle(status == "failed" ? .orange : .secondary)
                        if let detail = row["detail"] as? String { Text(detail).font(.caption).foregroundStyle(.secondary) }
                    }
                }
            }
        }
    }
    private var settings: some View {
        Form {
            Section("While playing") {
                Toggle("Performance overlay", isOn: $metrics).accessibilityIdentifier("launcher.metrics")
                Text("Callback FPS, average callback time and a rolling 1% low. Includes game work and waits; GPU time is not measured.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Downloads") {
                Toggle("Automatically check for mod updates", isOn: $autoUpdateChecks).disabled(model.locked)
                Text("Checks when you visit Updates if the last successful check is over 24 hours old. Nothing is downloaded or installed without your review.").font(.footnote).foregroundStyle(.secondary)
                Toggle("Allow cellular downloads", isOn: $cellular).disabled(model.locked)
                Text("Mod archives can be large. Every installation shows its download size before you begin.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Diagnostics") {
                Button("Export diagnostics…") { model.send("export") }.accessibilityIdentifier("launcher.export")
                Button("Record LiveContainer / StikDebug versions") { model.send("versions") }
                Button("Export current JIT script…") { model.send("script") }.disabled(!model.flag("jitAvailable") || model.locked)
                Text(model.text("process")).font(.caption.monospaced()).textSelection(.enabled)
            }
            Section("About this build") {
                LabeledContent("Version", value: (Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "Unknown") + " (" + (Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "?") + ")")
                LabeledContent("Everest", value: RuntimeIdentity.builtins["Everest"] ?? "Unknown")
                LabeledContent("iOS support · required", value: "1.0.0 (ABI 1)")
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
    @objc(update:) public func update(_ state: [String: Any]) {
        // The host polls twice per second. Republishing identical state can
        // continuously replace an open UIKit menu and restart its animation.
        if !NSDictionary(dictionary: model.state).isEqual(to: state) { model.state = state }
    }
    @MainActor @objc(prepareForGameWithCompletion:) public func prepareForGame(completion: @escaping ([String: Any]) -> Void) {
        Task {
            await model.browser.suspendForGame()
            completion(await model.browser.provider.diagnostics())
        }
    }
}
#endif
