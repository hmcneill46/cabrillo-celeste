// Presentation fixture only. This executable never contains a game or JIT runtime.
#if !targetEnvironment(simulator)
#error("LoadingPreview is simulator-only")
#endif
import SwiftUI
@main final class LoadingPreview: UIResponder, UIApplicationDelegate {
    func application(_ application:UIApplication,configurationForConnecting session:UISceneSession,options:UIScene.ConnectionOptions)->UISceneConfiguration {
        let configuration=UISceneConfiguration(name:nil,sessionRole:session.role);configuration.delegateClass=PreviewScene.self;return configuration
    }
}
final class PreviewScene:UIResponder,UIWindowSceneDelegate {
    var window:UIWindow?
    func scene(_ scene:UIScene,willConnectTo session:UISceneSession,options:UIScene.ConnectionOptions) {
        guard let scene=scene as? UIWindowScene else {return}
        let window=CJLoadingWindow(windowScene:scene);window.rootViewController=UIHostingController(rootView:PreviewScreen());self.window=window;window.makeKeyAndVisible()
    }
}
private struct PreviewScreen: View {
    @State private var processed=14
    @State private var exported=false
    @State private var expanded=false
    @StateObject private var cover=WindowCover()
    private let started=ProcessInfo.processInfo.systemUptime-24
    private var failure: Bool { ProcessInfo.processInfo.arguments.contains("--failure") }
    private var files: Bool { ProcessInfo.processInfo.arguments.contains("--files") }
    var body: some View {
        CabrilloLoadingView(state: ["active":true,"failed":failure,"phase":files ? "files" : "mods",
            "detail":"Strawberry Jam 2021 — Example of a long archive and module name 1.0.0",
            "completed":processed,"total":60,"archives_processed":processed,"archives_total":60,
            "modules_loaded":processed+3,"load_failures":failure ? 1 : 0,"delayed":4,"skipped":1,
            "started_uptime":started,"failure":"An example mod stopped while loading. The diagnostics include the module name and original exception."],
            canCancelFiles:files,cancelFiles:{exported=true},exportDiagnostics:{exported=true},detailsChanged:{expanded=$0})
        .overlay(alignment:.bottomTrailing) {
            VStack {
                if expanded { Text("Details opened").font(.caption2).accessibilityIdentifier("preview.expanded") }
                if ProcessInfo.processInfo.arguments.contains("--window-cover") {
                    Text(cover.focused ? "Game keeps focus" : "Game lost focus").accessibilityIdentifier("preview.focus")
                    Button("Show test game") { cover.handoff() }.accessibilityIdentifier("preview.handoff")
                }
            }
        }
        .alert("Fixture action received",isPresented:$exported) { Button("OK"){} }
        .onAppear { if ProcessInfo.processInfo.arguments.contains("--window-cover") { DispatchQueue.main.async { cover.begin() } } }
        .onReceive(Timer.publish(every:1,on:.main,in:.common).autoconnect()) { _ in
            if processed<59 { processed+=1 };cover.checkFocus()
        }
    }
}
private final class WindowCover: ObservableObject {
    @Published var focused=false
    private var launcher:UIWindow?,game:UIWindow?
    func begin() {
        guard let scene=UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let launcher=scene.windows.first(where:{$0.isKeyWindow}) else { return }
        self.launcher=launcher;launcher.windowLevel = .normal+10
        (launcher as? CJLoadingWindow)?.preservesGameFocus=true
        let game=UIWindow(windowScene:scene);self.game=game
        let controller=UIViewController();controller.view.backgroundColor = .systemBlue
        let label=UILabel();label.text="Test game view";label.textColor = .white;label.accessibilityIdentifier="preview.gameReady"
        label.translatesAutoresizingMaskIntoConstraints=false;controller.view.addSubview(label)
        NSLayoutConstraint.activate([label.centerXAnchor.constraint(equalTo:controller.view.centerXAnchor),label.centerYAnchor.constraint(equalTo:controller.view.centerYAnchor)])
        game.rootViewController=controller;game.makeKeyAndVisible();checkFocus()
    }
    func checkFocus(){if let game { focused=game.isKeyWindow } }
    func handoff(){(launcher as? CJLoadingWindow)?.preservesGameFocus=false;launcher?.windowLevel = .normal;launcher?.isHidden=true;game?.makeKeyAndVisible()}
}
