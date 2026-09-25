// Presentation fixture only: no game, assets or JIT runtime.
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
    @State private var trackChecks=false
    @StateObject private var cover=WindowCover()
    private let started=ProcessInfo.processInfo.systemUptime-24
    private func flag(_ name:String)->Bool { ProcessInfo.processInfo.arguments.contains(name) }
    var body: some View {
        CabrilloLoadingView(state:["active":true,"failed":flag("--failure"),"phase":flag("--files") ? "files" : flag("--indeterminate") ? "dependencies" : "mods",
            "detail":"Strawberry Jam 2021 — Example of a long archive and module name 1.0.0",
            "completed":processed,"total":60,"archives_processed":processed,"archives_total":60,
            "modules_loaded":processed+3,"load_failures":flag("--failure") ? 1 : 0,"delayed":4,"skipped":1,
            "started_uptime":started,"failure":"An example mod stopped while loading. The diagnostics include the module name and original exception."],
            canCancelFiles:flag("--files"),cancelFiles:{exported=true},exportDiagnostics:{exported=true})
        .dynamicTypeSize(flag("--large-type") ? .xxLarge : .large)
        .overlay(alignment:.bottomTrailing) {
            if flag("--window-cover") {
                Text(cover.status).font(.caption2).accessibilityIdentifier("preview.focus")
            } else if flag("--indeterminate") {
                Text(trackChecks ? "Activity checks passed" : "Activity checks failed").font(.caption2).accessibilityIdentifier("preview.track")
            }
        }
        .alert("Fixture action received",isPresented:$exported) { Button("OK"){} }
        .onAppear {
            if flag("--window-cover") { DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { cover.begin() } }
            if flag("--indeterminate") {
                let track=LoadingTrackView(frame:CGRect(x:0,y:0,width:240,height:5))
                track.update(fraction:nil,reduceMotion:false);track.layoutIfNeeded()
                let fill=track.layer.sublayers!.first!
                var passed=fill.animation(forKey:"activity") != nil
                track.update(fraction:nil,reduceMotion:true);track.layoutIfNeeded()
                passed = passed && fill.animation(forKey:"activity") == nil && fill.frame.width>0
                track.update(fraction:0.5,reduceMotion:false);track.layoutIfNeeded()
                passed = passed && fill.animation(forKey:"activity") == nil && fill.frame.width==120
                track.frame.size.width=320;track.setNeedsLayout();track.layoutIfNeeded()
                trackChecks = passed && fill.frame.width==160
            }
        }
        .onReceive(Timer.publish(every:1,on:.main,in:.common).autoconnect()) { _ in
            if processed<59 { processed+=1 };cover.checkFocus()
        }
    }
}
private final class WindowCover: NSObject,ObservableObject {
    @Published var status="Waiting"
    private var launcher:CJLoadingWindow?,game:UIWindow?,label:UILabel?
    private var touches=0
    private var guardsPassed=false
    private var backgroundRejected=false
    private let graphics:[String:Any]=["metal_layer":true,"gpu_readback_passed":true,"first_frame_drawn":true,"first_frame_readback_passed":true,"failed_checks":0]
    private let loading:[String:Any]=["active":true,"failed":false,"ready":false,"phase":"game_content"]
    func begin() {
        guard let scene=UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let launcher=scene.windows.first(where:{$0 is CJLoadingWindow}) as? CJLoadingWindow else {return}
        self.launcher=launcher;launcher.windowLevel = .normal+10;launcher.preservesGameFocus=true
        let game=UIWindow(windowScene:scene);self.game=game
        let controller=UIViewController();controller.view.backgroundColor = .systemBlue
        let target=UIButton(type:.system);target.translatesAutoresizingMaskIntoConstraints=false
        target.addTarget(self,action:#selector(touched),for:.touchUpInside);controller.view.addSubview(target)
        NSLayoutConstraint.activate([target.leadingAnchor.constraint(equalTo:controller.view.leadingAnchor),target.trailingAnchor.constraint(equalTo:controller.view.trailingAnchor),target.topAnchor.constraint(equalTo:controller.view.topAnchor),target.bottomAnchor.constraint(equalTo:controller.view.bottomAnchor)])
        let label=UILabel();self.label=label;label.textColor = .white;label.accessibilityIdentifier="preview.gameReady"
        label.translatesAutoresizingMaskIntoConstraints=false;controller.view.addSubview(label)
        NSLayoutConstraint.activate([label.centerXAnchor.constraint(equalTo:controller.view.centerXAnchor),label.centerYAnchor.constraint(equalTo:controller.view.centerYAnchor)])
        game.rootViewController=controller;game.makeKeyAndVisible()
        var rejected = !reveal(success:false)
        for key in ["metal_layer","gpu_readback_passed","first_frame_drawn","first_frame_readback_passed"] {
            var missing=graphics;missing[key]=false
            rejected = !reveal(graphics:missing) && rejected
        }
        var bad=graphics;bad["failed_checks"]=1;rejected = !reveal(graphics:bad) && rejected
        rejected = !reveal(loading:["active":false,"failed":false]) && rejected
        rejected = !reveal(loading:["active":true,"failed":true]) && rejected
        rejected = !launcher.revealGameWindow(nil,restoringLevel:.normal,frameSucceeded:true,graphics:graphics,loading:loading) && rejected
        rejected = !launcher.revealGameWindow(launcher,restoringLevel:.normal,frameSucceeded:true,graphics:graphics,loading:loading) && rejected
        guardsPassed=rejected && !launcher.isHidden;checkFocus()
        if ProcessInfo.processInfo.arguments.contains("--background-gate") {
            NotificationCenter.default.addObserver(self,selector:#selector(background),name:UIApplication.didEnterBackgroundNotification,object:nil)
            NotificationCenter.default.addObserver(self,selector:#selector(active),name:UIApplication.didBecomeActiveNotification,object:nil)
        } else {
            DispatchQueue.main.asyncAfter(deadline:.now()+12) { self.handoff() }
        }
    }
    private func reveal(success:Bool=true,graphics:[String:Any]?=nil,loading:[String:Any]?=nil)->Bool {
        launcher?.revealGameWindow(game,restoringLevel:.normal,frameSucceeded:success,graphics:graphics ?? self.graphics,loading:loading ?? self.loading) ?? false
    }
    @objc private func touched() { touches+=1;updateLabel() }
    @objc private func background() { backgroundRejected = !reveal() && launcher?.isHidden == false }
    @objc private func active() { if backgroundRejected { DispatchQueue.main.asyncAfter(deadline:.now()+1) { self.handoff() } } }
    func checkFocus() {
        if let game { status = game.isKeyWindow && guardsPassed ? "Game keeps focus; guards passed" : "Focus or guard failure" }
    }
    private func updateLabel() { label?.text="Test game view; touches=\(touches); background=\(backgroundRejected)" }
    private func handoff() {
        guard reveal() else { status="Handoff failed";return }
        updateLabel()
    }
}
