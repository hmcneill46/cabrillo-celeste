#if !targetEnvironment(simulator)
#error("The touch editor preview is a simulator-only synthetic fixture")
#endif
import UIKit

// Isolated simulator app hosting the complete production launcher.
@main final class TouchEditorPreviewDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, configurationForConnecting session: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let config = UISceneConfiguration(name: "TouchEditorPreview", sessionRole: session.role)
        config.delegateClass = TouchEditorPreviewScene.self
        return config
    }
}
final class TouchEditorPreviewScene: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    var bridge: CJLauncherBridge?
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let scene = scene as? UIWindowScene else { return }
        let arguments = ProcessInfo.processInfo.arguments
        if !arguments.contains("--preserve") {
            UserDefaults.standard.removeObject(forKey: "cabrillo.featherTouch")
            UserDefaults.standard.removeObject(forKey: CJTouchStore.key(false))
            UserDefaults.standard.removeObject(forKey: CJTouchStore.key(true))
        }
        let bridge = CJLauncherBridge(action: { _, _ in })
        bridge.update(["used": arguments.contains("--used"), "platform": ["screenFPS": 120]])
        let window = UIWindow(windowScene: scene)
        window.rootViewController = bridge.viewController
        self.bridge = bridge; self.window = window; window.makeKeyAndVisible()
        if arguments.contains("--pause-editor") {
            let button = UIButton(type:.system);button.setTitle("Open in-game editor",for:.normal);button.accessibilityIdentifier = "test.pauseEditor"
            button.addAction(UIAction { _ in
                if let requested = arguments.first(where: { $0.hasPrefix("--resize-edge=") }) {
                    // Seed only this isolated simulator container. The chosen
                    // widths are valid in real layout imports.
                    let edge = String(requested.dropFirst("--resize-edge=".count))
                    let surface = TouchSurface.current
                    var profile = surface.factory
                    if let i = profile.controls.firstIndex(where: { $0.kind == "jump" }) {
                        let small = 24.0, large = 64.0
                        let width = edge == "bottom" ? large : small
                        let height = edge == "right" ? large : small
                        profile.controls[i].shape = edge == "circle" ? "circle" : "rectangle"
                        profile.controls[i].box = TouchBox(
                            x: edge == "bottom" ? 0.65 : 1-width/surface.width,
                            y: edge == "right" ? 0.60 : 1-height/surface.height,
                            width: width/surface.width, height: height/surface.height)
                        try! CJTouchStore.save(profile,pad:surface.pad)
                    }
                }
                CJTouchEditorBridge.present(from:bridge.viewController)
            },for:.touchUpInside)
            button.translatesAutoresizingMaskIntoConstraints = false;bridge.viewController.view.addSubview(button)
            NSLayoutConstraint.activate([button.topAnchor.constraint(equalTo:bridge.viewController.view.safeAreaLayoutGuide.topAnchor,constant:55),button.leadingAnchor.constraint(equalTo:bridge.viewController.view.leadingAnchor,constant:20),button.widthAnchor.constraint(equalToConstant:250),button.heightAnchor.constraint(equalToConstant:48)])
        }
    }
}
