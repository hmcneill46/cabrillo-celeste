#if !targetEnvironment(simulator)
#error("This synthetic launcher presentation fixture is simulator-only")
#endif
import SwiftUI
import UIKit

@main final class UnifiedLauncherPreviewDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, configurationForConnecting session: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let config = UISceneConfiguration(name: "UnifiedLauncherPreview", sessionRole: session.role)
        config.delegateClass = UnifiedLauncherPreviewScene.self
        return config
    }
}
final class UnifiedLauncherPreviewScene: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    var launcher: CJLauncherBridge?
    var state: [String: Any] = [:]
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let scene = scene as? UIWindowScene else { return }
        let args = ProcessInfo.processInfo.arguments
        if !args.contains("--preserve") {
            UserDefaults.standard.removeObject(forKey: "cabrillo.featherTouch")
            UserDefaults.standard.removeObject(forKey: CJTouchStore.key(false))
            UserDefaults.standard.removeObject(forKey: CJTouchStore.key(true))
        }
        let selected = args.first(where: { $0.hasPrefix("--state=") }).map { String($0.dropFirst(8)) } ?? "ready"
        let provider = args.first(where: { $0.hasPrefix("--provider=") }).map { String($0.dropFirst(11)) } ?? (selected.hasPrefix("integrated") ? "integrated" : "manual")
        state = ["hasContent": true, "jitReady": true, "jitAvailable": true, "mods": [], "issues": [], "shortcut": [:],
            "platform": ["provider": provider, "providerAvailable": true, "providerError": "", "screenFPS": 120,
                "providers": ["integrated", "stikdebug", "livecontainer2", "trollstore", "manual"],
                "labels": ["integrated":"Built-in StikJIT", "stikdebug":"Standalone StikDebug", "livecontainer2":"StikDebug in LiveContainer 2", "trollstore":"TrollStore", "manual":"Already enabled / another tool"],
                "help": "Synthetic presentation state", "button": "Existing JIT method"]]
        var integrated: [String: Any] = ["phase":"idle", "message":"", "active":false, "acquiring":false,
            "pairingImported":true, "ddiReady":true, "serviceReady":true, "serviceChecked":true,
            "serviceCheckAgeSeconds":4, "serviceFresh":true, "needsTXM":true, "forceScript":false]
        switch selected {
        case "empty": state["hasContent"] = false; state["jitReady"] = false
        case "jitPending": state["jitReady"] = false
        case "issues": state["issues"] = ["Synthetic dependency issue"]
        case "busy", "used", "profileBlocked", "shortcutBlocked", "scanning": state[selected] = true
        case "integratedMissing":
            state["jitReady"] = false; integrated["pairingImported"] = false; integrated["ddiReady"] = false
            integrated["serviceReady"] = false; integrated["serviceChecked"] = false; integrated["needsTXM"] = NSNull()
        case "integratedService": state["jitReady"] = false
        case "integratedOldCheck":
            state["jitReady"] = false; integrated["serviceCheckAgeSeconds"] = 150
            integrated["serviceReady"] = false; integrated["serviceFresh"] = false
        case "integratedProgress":
            state["jitReady"] = false; state["busy"] = true; integrated["active"] = true
            integrated["phase"] = "enabling"; integrated["message"] = "Preparing executable memory for this running app. Keep Cabrillo open."
        case "integratedVerifying":
            state["jitReady"] = false; state["busy"] = true; integrated["acquiring"] = true
            integrated["message"] = "Debugger detached"; integrated["requestConsumed"] = true
        case "integratedFailure":
            state["jitReady"] = false; integrated["phase"] = "failed"; integrated["serviceReady"] = false
            integrated["error"] = "The pairing file was rejected. Import a fresh pairing file for this device."
        case "integratedRestart":
            state["jitReady"] = false; integrated["phase"] = "failed"; integrated["requestConsumed"] = true
            integrated["restartRequired"] = true; integrated["error"] = "JIT could not be verified. Reopen Cabrillo before trying again."
        case "integratedUnavailable":
            state["jitReady"] = false
            var platform = state["platform"] as! [String: Any]
            platform["providerAvailable"] = false
            platform["providerError"] = "Built-in StikJIT cannot run inside LiveContainer. Choose another JIT method in Settings."
            state["platform"] = platform
        default: break
        }
        state["integratedJIT"] = integrated
        let window = UIWindow(windowScene: scene)
        if args.contains("--system-light") { window.overrideUserInterfaceStyle = .light }
        if args.contains("--large-type") { window.traitOverrides.preferredContentSizeCategory = .accessibilityExtraLarge }
        let bridge = CJLauncherBridge { [weak self] action, fields in
            guard let self = self else { return }
            if action == "integrated.forceScript" {
                var value = self.state["integratedJIT"] as! [String: Any]
                value["forceScript"] = fields["enabled"] as? Bool == true
                self.state["integratedJIT"] = value
                self.launcher?.update(self.state)
            }
            let message = action == "integrated.forceScript" ? action + ":" + String(fields["enabled"] as? Bool == true) : action
            let alert = UIAlertController(title: "Fixture action", message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            window.rootViewController?.present(alert, animated: false)
        }
        bridge.update(state)
        window.rootViewController = bridge.viewController
        self.launcher = bridge; self.window = window
        window.makeKeyAndVisible()
    }
}
