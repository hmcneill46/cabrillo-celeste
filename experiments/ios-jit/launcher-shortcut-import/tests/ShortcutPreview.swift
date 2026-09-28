#if !targetEnvironment(simulator)
#error("This presentation fixture must not be bundled on a device")
#endif
import SwiftUI
@main struct ShortcutPreview: App {
    init() {
        UserDefaults.standard.set("auto",forKey:"shortcut.mode")
        UserDefaults.standard.set(true,forKey:"shortcut.restoreWiFi")
        UserDefaults.standard.set(true,forKey:"shortcut.restoreCellular")
    }
    var body: some Scene { WindowGroup { PreviewScreen() } }
}
private struct PreviewScreen: View {
    @State private var received = ""
    private let args = ProcessInfo.processInfo.arguments
    var body: some View {
        let recovery=args.contains("--recovery"), active=args.contains("--active"), waiting=args.contains("--waiting")
        let state:[String:Any] = ["phase":recovery ? "recovery" : waiting ? "waiting-detach" : active ? "jit" : "ready",
            "message":recovery ? "An earlier launch was interrupted. Restore its networking preset before trying again." : waiting ? "Waiting for StikDebug to finish and detach before restoring networking…" : active ? "Enabling JIT for this running app…" : "JIT is ready. Your networking preset is restored.",
            "active":active || waiting,"recoveryRequired":recovery || active || waiting]
        NavigationView {
            Form {
                CabrilloShortcutStatus(state:state,action:record)
                CabrilloShortcutSettings(locked:active || waiting || recovery,setup:[
                    "location":args.contains("--standalone") ? "Standalone Cabrillo" : "LiveContainer",
                    "provider":args.contains("--standalone") ? "StikDebug in LiveContainer 2" : "Standalone StikDebug",
                    "needsLaunchLink":!args.contains("--standalone"),
                    "helperLinkRequired":args.contains("--standalone"),
                    "error":args.contains("--standalone") ? "Save StikDebug’s LiveContainer launch link below before exporting the shortcut." : nil
                ].compactMapValues { $0 },providerLocked:false,action:record)
            }.navigationTitle("Cabrillo")
        }.navigationViewStyle(.stack).preferredColorScheme(.dark)
            .dynamicTypeSize(args.contains("--large-type") ? .xxLarge : .large)
            .alert("Fixture action received",isPresented:Binding(get:{!received.isEmpty},set:{if !$0 {received=""}})) {
                Button("OK"){received=""}
            } message: { Text(received) }
    }
    private func record(_ action:String,_ fields:[String:Any]) { received=action }
}
