import SwiftUI

struct CabrilloShortcutSettings: View {
    let locked: Bool
    let setup: [String: Any]
    let providerLocked: Bool
    let action: (String, [String: Any]) -> Void
    @State private var showSetup = false
    @AppStorage("shortcut.mode") private var mode = "auto"
    @AppStorage("shortcut.restoreWiFi") private var restoreWiFi = true
    @AppStorage("shortcut.restoreCellular") private var restoreCellular = true
    var body: some View {
        Section("Home Screen shortcut") {
            Button { showSetup = true } label: { Label("Add Home Screen shortcut…", systemImage: "plus.app") }
                .disabled(locked).accessibilityIdentifier("shortcut.setup")
                .sheet(isPresented: $showSetup) { CabrilloShortcutSetup(locked: locked, providerLocked: providerLocked, state: setup, action: action) }
            Text("Create a shortcut for this installation. Set up LocalDevVPN and your chosen StikDebug app once; Cabrillo uses the current Enable with setting at each launch.").font(.footnote).foregroundStyle(.secondary)
            Picker("Networking", selection: $mode) {
                Text("Automatic").tag("auto")
                Text("Keep Wi-Fi & cellular").tag("wifi")
                Text("Travel · Airplane Mode").tag("travel")
            }.disabled(locked).accessibilityIdentifier("shortcut.mode")
            Text("Automatic keeps Wi-Fi and cellular settings when Wi-Fi has an address. Otherwise, Travel enables networking, verifies LocalDevVPN, then uses Airplane Mode while JIT is prepared.").font(.footnote).foregroundStyle(.secondary)
            Toggle("Wi-Fi after Travel", isOn: $restoreWiFi).disabled(locked)
            Toggle("Cellular data after Travel", isOn: $restoreCellular).disabled(locked)
            Text("Travel finishes with Airplane Mode off and these choices. iOS does not let this shortcut read the previous radio switches, so these are a restore preset. Bluetooth is not changed by a separate action; Airplane Mode follows your iOS settings.").font(.footnote).foregroundStyle(.secondary)
            Button("Test installed shortcut") { action("shortcut.install.test", [:]) }.disabled(locked)
            Text("After JIT is verified, you return here ready to choose Play. Celeste still runs once per app process; close Cabrillo before starting another game session.").font(.footnote).foregroundStyle(.secondary)
        }
    }
}

struct CabrilloShortcutSetup: View {
    let locked: Bool
    let providerLocked: Bool
    let state: [String: Any]
    let action: (String, [String: Any]) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var helperLink = ""
    @FocusState private var helperFocused: Bool
    private var needsLink: Bool { state["needsLaunchLink"] as? Bool == true }
    private var blocked: Bool { locked || state["error"] != nil }
    var body: some View {
        NavigationView {
            Form {
                Section("This installation") {
                    Text(state["location"] as? String ?? "Identifying Cabrillo…").font(.headline)
                    Text(state["provider"] as? String ?? "Choose a JIT provider in Settings")
                    Text("The shortcut uses your current JIT and networking choices. LocalDevVPN and StikDebug must already be set up. First use may ask permission to open them.").font(.footnote).foregroundStyle(.secondary)
                    if let error = state["error"] as? String { Text(error).foregroundStyle(.orange).accessibilityIdentifier("shortcut.setup.error") }
                }
                if state["helperLinkRequired"] as? Bool == true {
                    Section("StikDebug in LiveContainer 2") {
                        Text("Standalone Cabrillo cannot read LiveContainer’s apps. In LiveContainer, hold StikDebug → Add to Home Screen → Copy Launch URL, then paste it here. Share that StikDebug installation with LiveContainer 2.").font(.footnote)
                        TextField("StikDebug launch link", text: $helperLink).textInputAutocapitalization(.never).disableAutocorrection(true).keyboardType(.URL).focused($helperFocused).submitLabel(.done).onSubmit { helperFocused = false }.disabled(locked || providerLocked).accessibilityIdentifier("shortcut.helperLink")
                        Button("Save helper link") { action("shortcut.install.helper", ["link": helperLink]) }.disabled(locked || providerLocked || helperLink.isEmpty)
                        if providerLocked { Text("Restart Cabrillo before changing the helper after a JIT request.").font(.footnote).foregroundStyle(.secondary) }
                    }
                }
                Section("1 · Save and import") {
                    Button(needsLink ? "Copy launch link & save shortcut…" : "Save shortcut…") { action("shortcut.install.export", [:]) }.disabled(blocked).accessibilityIdentifier("shortcut.install.export")
                    Text("Save Cabrillo.shortcut to Files, then tap that file to open it in Shortcuts. Review it and add it with the exact name Cabrillo. If an older Cabrillo shortcut exists, replace it; avoid leaving a second copy named Cabrillo 1.").font(.footnote)
                    if needsLink {
                        Text("When Shortcuts asks for the launch link, paste the link copied by the button above. It selects this Cabrillo app and its current data container, even if another guest was used last.").font(.footnote)
                        Button("Copy launch link again") { action("shortcut.install.copy", [:]) }.disabled(blocked)
                    }
                }
                Section("2 · Add the Home Screen icon") {
                    Button("Open Cabrillo in Shortcuts") { action("shortcut.install.open", [:]) }.disabled(blocked)
                    Text("Open the shortcut’s details or share menu, choose Add to Home Screen, then tap Add. Apple requires these import and Home Screen steps; saving the file does not install the shortcut.").font(.footnote)
                }
                Section("3 · Try a fresh launch") {
                    Text("Finish any current game with its normal Quit. Close Cabrillo and the StikDebug host, then tap your new Home Screen icon. Allow first-use prompts. Cabrillo confirms readiness only after JIT works and the debugger detaches.").font(.footnote)
                    Text("If you move Cabrillo to another LiveContainer host or switch its data container, repeat setup there. Keep just one shortcut named Cabrillo for these launch callbacks.").font(.footnote).foregroundStyle(.secondary)
                }
            }.navigationTitle("Home Screen shortcut").navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
                    ToolbarItemGroup(placement: .keyboard) { Spacer(); Button("Done typing") { helperFocused = false }.accessibilityIdentifier("shortcut.helperDone") }
                }
        }.navigationViewStyle(.stack)
            .onAppear { helperLink = state["helperLink"] as? String ?? "" }
    }
}

struct CabrilloShortcutStatus: View {
    let state: [String: Any]
    let action: (String, [String: Any]) -> Void
    var body: some View {
        if let phase = state["phase"] as? String, phase != "idle" {
            Section("Home Screen launch") {
                HStack(alignment: .top) {
                    if state["active"] as? Bool == true { ProgressView().accessibilityLabel("Preparing launch").accessibilityIdentifier("shortcut.progress") }
                    else { Image(systemName: phase == "ready" ? "checkmark.circle.fill" : "info.circle").foregroundStyle(phase == "ready" ? Color.green : Color.orange) }
                    Text(state["message"] as? String ?? "").accessibilityIdentifier("shortcut.status")
                }.accessibilityElement(children: .contain)
                if state["active"] as? Bool == true {
                    Button("Cancel launch") { action("shortcut.cancel", [:]) }.disabled(phase == "restore" || phase == "waiting-detach")
                } else if state["recoveryRequired"] as? Bool == true {
                    Button("Restore networking") { action("shortcut.recover", [:]) }.accessibilityIdentifier("shortcut.recover")
                }
                if phase == "waiting-detach" { Text("If StikDebug is stuck, stop its debugging session and return here. Networking stays in place while the debugger may still need it.").font(.footnote).foregroundStyle(.secondary) }
            }
        }
    }
}
