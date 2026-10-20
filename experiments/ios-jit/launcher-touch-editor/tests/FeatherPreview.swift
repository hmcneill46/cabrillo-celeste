import UIKit

// Isolated simulator app hosting the complete production launcher.
@main final class FeatherPreviewDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, configurationForConnecting session: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let config = UISceneConfiguration(name: "FeatherPreview", sessionRole: session.role)
        config.delegateClass = FeatherPreviewScene.self
        return config
    }
}
final class FeatherPreviewScene: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    var bridge: CJLauncherBridge?
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let scene = scene as? UIWindowScene else { return }
        let arguments = ProcessInfo.processInfo.arguments
        if !arguments.contains("--preserve") { UserDefaults.standard.removeObject(forKey: "cabrillo.featherTouch") }
        let bridge = CJLauncherBridge(action: { _, _ in })
        bridge.update(["used": arguments.contains("--used"), "platform": ["screenFPS": 120]])
        let window = UIWindow(windowScene: scene)
        window.rootViewController = bridge.viewController
        self.bridge = bridge; self.window = window; window.makeKeyAndVisible()
    }
}
