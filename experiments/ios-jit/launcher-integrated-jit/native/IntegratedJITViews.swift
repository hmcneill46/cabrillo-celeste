import SwiftUI

// A List's automatic Label style can give its symbol the list accent color.
// Keep one foreground for the whole centered button label in every state.
struct CabrilloRunButtonLabel: View {
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "play.fill").symbolRenderingMode(.monochrome).accessibilityHidden(true)
            Text("Run Celeste")
        }
        .font(.headline)
        .foregroundStyle(Color.white)
        .frame(maxWidth: .infinity, alignment: .center)
        .padding(.vertical, 9)
    }
}

private struct IntegratedJITPresentation {
    let state: [String: Any]
    func flag(_ key: String) -> Bool { state[key] as? Bool == true }
    func text(_ key: String) -> String { state[key] as? String ?? "" }
    var phase: String { text("phase") }
    var active: Bool { flag("active") || flag("acquiring") }
    var pairingImported: Bool { flag("pairingImported") }
    var serviceReady: Bool {
        guard flag("serviceChecked"), flag("serviceReady"),
              let age = (state["serviceCheckAgeSeconds"] as? NSNumber)?.doubleValue else { return false }
        return age.isFinite && age >= 0 && age <= 45 && state["serviceFresh"] as? Bool != false
    }
    var serviceStale: Bool {
        guard flag("serviceChecked"), let age = (state["serviceCheckAgeSeconds"] as? NSNumber)?.doubleValue else { return false }
        return age.isFinite && age > 45
    }
    var serviceAge: String {
        guard let seconds = (state["serviceCheckAgeSeconds"] as? NSNumber)?.doubleValue,
              seconds.isFinite, seconds >= 0 else { return "" }
        if seconds < 2 { return "Checked just now." }
        if seconds < 60 { return "Checked \(Int(seconds)) seconds ago." }
        if seconds < 120 { return "Checked 1 minute ago." }
        if seconds < 3600 { return "Checked \(Int(seconds / 60)) minutes ago." }
        return "Checked over an hour ago. Check the connection again before starting."
    }
    var progressMessage: String {
        if flag("acquiring") && !flag("active") { return "Verifying JIT for this running app…" }
        return text("message").isEmpty ? "Preparing JIT for this running app…" : text("message")
    }
    var error: String { text("error") }
    var failure: Bool { phase == "failed" || !error.isEmpty }
}

struct CabrilloIntegratedJITReadiness: View {
    let state: [String: Any]
    let jitReady: Bool
    let available: Bool
    let unavailableReason: String
    let locked: Bool
    let action: (String, [String: Any]) -> Void
    private var status: IntegratedJITPresentation { IntegratedJITPresentation(state: state) }
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("LocalDevVPN", systemImage: status.serviceReady ? "checkmark.circle.fill" : "network")
                .font(.headline).foregroundStyle(status.serviceReady ? Color.green : Color.primary)
            Text(status.serviceReady ? "The device service responded to the last connection check." : status.serviceStale ? "The connection check is out of date. Check the connection again." : status.flag("serviceChecked") ? "The device service did not respond to the last connection check. Reconnect LocalDevVPN and try again." : "Connect LocalDevVPN, then check the connection.")
                .font(.subheadline).foregroundStyle(.secondary).accessibilityIdentifier("integrated.serviceStatus")
            if !status.serviceAge.isEmpty { Text(status.serviceAge).font(.footnote).foregroundStyle(.secondary).accessibilityIdentifier("integrated.serviceAge") }
            if !status.text("serviceMessage").isEmpty {
                Text(status.text("serviceMessage")).font(.footnote).foregroundStyle(.secondary)
            }
            Label(jitReady ? "JIT verified for this running app" : "Built-in StikJIT", systemImage: jitReady ? "checkmark.circle.fill" : "bolt")
                .font(.headline).foregroundStyle(jitReady ? Color.green : Color.primary)
                .accessibilityIdentifier("integrated.jitStatus")
            if !available {
                Text(unavailableReason.isEmpty ? "Built-in StikJIT is unavailable in this installation. Choose another JIT method in Settings." : unavailableReason)
                    .font(.subheadline).foregroundStyle(.orange).accessibilityIdentifier("integrated.unavailable")
            } else if !status.pairingImported {
                Text("Import your pairing file in Settings, then use Run Celeste. JIT is verified before the game starts.")
                    .font(.subheadline).foregroundStyle(.secondary)
            } else if !jitReady {
                Text("Run Celeste checks the connection, enables JIT and verifies this process before starting the game.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }
            if status.active {
                HStack(alignment: .top, spacing: 10) {
                    ProgressView().accessibilityLabel("Preparing JIT")
                    Text(status.progressMessage)
                        .fixedSize(horizontal: false, vertical: true)
                }.font(.subheadline).accessibilityIdentifier("integrated.progress")
            } else if status.failure {
                Text(status.error.isEmpty ? status.text("message") : status.error)
                    .font(.subheadline).foregroundStyle(.orange).accessibilityIdentifier("integrated.error")
            } else if !status.text("message").isEmpty {
                Text(status.text("message")).font(.subheadline).foregroundStyle(.secondary)
            }
            if status.flag("restartRequired") {
                Text("Close and relaunch Cabrillo before trying JIT again.")
                    .font(.subheadline).foregroundStyle(.orange).accessibilityIdentifier("integrated.playRestartRequired")
            }
        }.padding(.vertical, 4)
        Button("Check connection") { action("integrated.refresh", [:]) }
            .disabled(locked || !available || status.active).accessibilityIdentifier("integrated.refresh")
    }
}

struct CabrilloIntegratedJITSettings: View {
    let state: [String: Any]
    let available: Bool
    let unavailableReason: String
    let locked: Bool
    let action: (String, [String: Any]) -> Void
    private var status: IntegratedJITPresentation { IntegratedJITPresentation(state: state) }
    private var controlsLocked: Bool { locked || !available || status.active || status.flag("requestConsumed") || status.flag("restartRequired") }
    var body: some View {
        Section("Built-in StikJIT") {
            if !available {
                Text(unavailableReason.isEmpty ? "Choose another JIT method for this installation." : unavailableReason)
                    .font(.subheadline).foregroundStyle(.orange)
            }
            CJLabeledContent("Pairing file", value: status.pairingImported ? "Imported" : "Not imported")
                .accessibilityIdentifier("integrated.pairingStatus")
            Button("Import pairing file…") { action("integrated.importPairing", [:]) }
                .disabled(controlsLocked).accessibilityIdentifier("integrated.importPairing")
            Text("Import a pairing file exported by iLoader or another pairing tool. Files placed at Cabrillo/pairingFile.plist are detected automatically.")
                .font(.footnote).foregroundStyle(.secondary)
            CJLabeledContent("Developer image", value: status.flag("ddiReady") ? "Prepared" : "Not prepared")
                .accessibilityIdentifier("integrated.ddiStatus")
            Text("A prepared developer image and a reachable device service do not enable JIT by themselves. Cabrillo checks JIT for this running app before starting Celeste.")
                .font(.footnote).foregroundStyle(.secondary)
            Button("Prepare developer image") { action("integrated.prepare", [:]) }
                .disabled(controlsLocked || !status.pairingImported).accessibilityIdentifier("integrated.prepare")
            Button("Reset developer image") { action("integrated.resetDDI", [:]) }
                .disabled(controlsLocked).accessibilityIdentifier("integrated.resetDDI")
            CJLabeledContent("TXM", value: (state["needsTXM"] as? Bool).map { $0 ? "Present" : "Not present" } ?? "Unknown")
                .accessibilityIdentifier("integrated.txmStatus")
            Toggle("Force JIT script", isOn: Binding(get: { status.flag("forceScript") }, set: { action("integrated.forceScript", ["enabled": $0]) }))
                .disabled(controlsLocked).accessibilityIdentifier("integrated.forceScript")
            Text("Use the debugger script even when this iOS version normally prepares JIT memory directly.")
                .font(.footnote).foregroundStyle(.secondary)
            if status.flag("requestConsumed") || status.flag("restartRequired") {
                Text("Close and relaunch Cabrillo before changing JIT setup or trying a new request.")
                    .font(.footnote).foregroundStyle(.secondary).accessibilityIdentifier("integrated.restartRequired")
            }
            if status.active {
                HStack(alignment: .top, spacing: 10) {
                    ProgressView()
                    Text(status.progressMessage).fixedSize(horizontal: false, vertical: true)
                }.font(.subheadline)
            } else if status.failure {
                Text(status.error.isEmpty ? status.text("message") : status.error)
                    .font(.subheadline).foregroundStyle(.orange)
            }
        }
    }
}
