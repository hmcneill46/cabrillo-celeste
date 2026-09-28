import SwiftUI

struct CabrilloShortcutSettings: View {
    let locked: Bool
    let action: (String, [String: Any]) -> Void
    @AppStorage("shortcut.mode") private var mode = "auto"
    @AppStorage("shortcut.restoreWiFi") private var restoreWiFi = true
    @AppStorage("shortcut.restoreCellular") private var restoreCellular = true
    var body: some View {
        Section("Home Screen shortcut") {
            Text("Import the supplied Cabrillo shortcut, keep that name, then add it to your Home Screen. Set up LocalDevVPN and StikDebug once before using it.").font(.footnote).foregroundStyle(.secondary)
            Picker("Networking", selection: $mode) {
                Text("Automatic").tag("auto")
                Text("Keep Wi-Fi & cellular").tag("wifi")
                Text("Travel · Airplane Mode").tag("travel")
            }.disabled(locked).accessibilityIdentifier("shortcut.mode")
            Text("Automatic keeps Wi-Fi and cellular settings when Wi-Fi has an address. Otherwise, Travel enables networking, verifies LocalDevVPN, then uses Airplane Mode while JIT is prepared.").font(.footnote).foregroundStyle(.secondary)
            Toggle("Wi-Fi after Travel", isOn: $restoreWiFi).disabled(locked)
            Toggle("Cellular data after Travel", isOn: $restoreCellular).disabled(locked)
            Text("Travel finishes with Airplane Mode off and these choices. iOS does not let this shortcut read the previous radio switches, so these are a restore preset. Bluetooth is not changed by a separate action; Airplane Mode follows your iOS settings.").font(.footnote).foregroundStyle(.secondary)
            Button("Start shortcut launch") { action("shortcut.start", [:]) }.disabled(locked)
            Text("After JIT is verified, you return here ready to choose Play. Celeste still runs once per app process; close Cabrillo before starting another game session.").font(.footnote).foregroundStyle(.secondary)
        }
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
