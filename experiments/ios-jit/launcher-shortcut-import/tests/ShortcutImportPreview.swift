import UIKit
let testLaunchLink="livecontainer2://livecontainer-launch?bundle-name=Example%20Guest.app&container-folder-name=00000000-1111-2222-3333-444444444444&open-url=Y2FicmlsbG86Ly9sYXVuY2g%3D"
@main final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application:UIApplication,didFinishLaunchingWithOptions options:[UIApplication.LaunchOptionsKey:Any]?) -> Bool {
        let window=UIWindow(frame:UIScreen.main.bounds);window.rootViewController=ImportScreen();window.makeKeyAndVisible();self.window=window;return true
    }
    func application(_ app:UIApplication,open url:URL,options:[UIApplication.OpenURLOptionsKey:Any]=[:])->Bool {
        (window?.rootViewController as? ImportScreen)?.receive(url.absoluteString);return true
    }
}
final class ImportScreen:UIViewController {
    var document:UIDocumentInteractionController?
    let received=UILabel()
    override func viewDidLoad(){
        super.viewDidLoad();view.backgroundColor = .systemBackground
        let stack=UIStackView();stack.axis = .vertical;stack.spacing=30;stack.translatesAutoresizingMaskIntoConstraints=false;view.addSubview(stack)
        for name in ["Original48","Candidate49"] {
            let button=UIButton(type:.system);button.setTitle(name,for:.normal);button.accessibilityIdentifier=name
            button.addAction(UIAction{[weak self] _ in self?.open(name)},for:.touchUpInside);stack.addArrangedSubview(button)
        }
        let copy=UIButton(type:.system);copy.setTitle("Copy test link",for:.normal);copy.accessibilityIdentifier="copy-link"
        copy.addAction(UIAction{_ in UIPasteboard.general.string=testLaunchLink},for:.touchUpInside);stack.addArrangedSubview(copy)
        received.accessibilityIdentifier="received-url";received.numberOfLines=0;received.text="No URL";stack.addArrangedSubview(received)
        NSLayoutConstraint.activate([stack.centerXAnchor.constraint(equalTo:view.centerXAnchor),stack.centerYAnchor.constraint(equalTo:view.centerYAnchor),stack.widthAnchor.constraint(equalTo:view.widthAnchor,constant:-48)])
    }
    func receive(_ value:String){received.text=value}
    func open(_ name:String){
        let url=Bundle.main.url(forResource:name,withExtension:"shortcut")!
        document=UIDocumentInteractionController(url:url);document?.uti="com.apple.shortcut"
        document?.presentOpenInMenu(from:CGRect(x:view.bounds.midX,y:view.bounds.midY,width:1,height:1),in:view,animated:true)
    }
}
