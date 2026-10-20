import Foundation

// A resize keeps the existing top-left corner and stays within the full-display
// canvas. Valid small layouts remain editable without being forced above 32 pt.
// Circle controls scale uniformly, preserving both round controls and imported
// non-square bounds used to position their inscribed circle.
enum TouchResizePolicy {
    static func resized(_ start: TouchBox, translation: CGSize, canvas: CGSize, surface: CGSize, circle: Bool) -> TouchBox {
        guard canvas.width > 0, canvas.height > 0, surface.width > 0, surface.height > 0 else { return start }
        let dx = Double(translation.width / canvas.width), dy = Double(translation.height / canvas.height)
        // Schema1 accepts a 0.00001 rounding tolerance at the right/bottom
        // edge. Preserve accepted imported bounds instead of clipping a minimum
        // sized control below the schema minimum; never increase that overflow.
        let availableWidth = max(start.width, 1 - start.x), availableHeight = max(start.height, 1 - start.y)
        var result = start
        if circle {
            let minimumSide = min(32, start.width * surface.width, start.height * surface.height)
            let minimumScale = max(minimumSide / min(start.width * surface.width, start.height * surface.height),
                0.015 / start.width, 0.015 / start.height)
            let requestedScale = min((start.width + dx) / start.width, (start.height + dy) / start.height)
            let maximumScale = min(availableWidth / start.width, availableHeight / start.height)
            var scale = min(maximumScale, max(minimumScale, requestedScale))
            // Division followed by multiplication can round just below 0.015.
            // Advance only that boundary result; valid starts always permit 1.
            while (start.width * scale < 0.015 || start.height * scale < 0.015) && scale < 1 {
                scale = min(1, scale.nextUp)
            }
            result.width = start.width * scale; result.height = start.height * scale
        } else {
            let minimumWidth = min(start.width, max(0.015, 32 / surface.width)), minimumHeight = min(start.height, max(0.015, 32 / surface.height))
            result.width = min(availableWidth, max(minimumWidth, start.width + dx))
            result.height = min(availableHeight, max(minimumHeight, start.height + dy))
        }
        return result
    }
}

#if canImport(UIKit)
import SwiftUI
import UIKit
import UniformTypeIdentifiers

struct TouchSurface {
    var width: Double; var height: Double; var top: Double; var left: Double; var bottom: Double; var right: Double; var pad: Bool
    var factory: TouchProfile { .factory(width:width,height:height,top:top,left:left,bottom:bottom,right:right,pad:pad) }
    static var current: Self {
        let window = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.flatMap(\.windows).first { $0.isKeyWindow }
        let size = window?.bounds.size ?? UIScreen.main.bounds.size, inset = window?.safeAreaInsets ?? .zero
        let pad = UIDevice.current.userInterfaceIdiom == .pad, landscape = size.width > size.height
        let edge = pad ? 0 : max(0,Double(inset.top)>24 ? Double(inset.top) : 0)
        return Self(width:Double(max(size.width,size.height)),height:Double(min(size.width,size.height)),
            top:landscape ? Double(inset.top) : 0,left:landscape ? Double(inset.left) : edge,
            bottom:landscape || pad ? Double(inset.bottom) : min(21,Double(inset.bottom)),right:landscape ? Double(inset.right) : edge,pad:pad)
    }
}

@objc public final class CJTouchStore: NSObject {
    @objc public static var revision: Int32 = 1
    @objc public static var editorActive = false
    // The host supplies the same signing-aware Files preparation used by game,
    // mod and save imports. Keeping this as a callback also isolates UI fixtures.
    @objc public static var prepareDocumentPicker: (() -> Void)?
    static func key(_ pad: Bool) -> String { pad ? "cabrillo.touch.tablet.v1" : "cabrillo.touch.phone.v1" }
    @objc public static func runtimeJSON() -> String {
        let value = load(TouchSurface.current)
        guard let data = try? value.encoded() else { return "" }
        return String(data:data,encoding:.utf8) ?? ""
    }
    static func load(_ surface: TouchSurface) -> TouchProfile {
        let data = UserDefaults.standard.data(forKey:key(surface.pad))
        var value = data.flatMap {try? TouchProfile.decode($0)} ?? surface.factory
        // Existing launcher preference remains the single source of truth.
        value.featherTouch = UserDefaults.standard.bool(forKey:"cabrillo.featherTouch")
        return value
    }
    @objc public static func setGrabMode(_ source: Int32, mode: Int32) {
        guard Thread.isMainThread, (0...2).contains(source), (0...2).contains(mode) else { return }
        let surface = TouchSurface.current
        var profile = load(surface)
        let value = ["hold","invert","toggle"][Int(mode)]
        switch source { case 1: profile.keyboardGrab = value; case 2: profile.controllerGrab = value; default: profile.grab = value }
        do { try save(profile,pad:surface.pad) } catch { NSLog("Cabrillo could not save grab mode: %@",error.localizedDescription) }
    }
    @objc public static func preferenceChanged() { revision = revision == Int32.max ? 1 : revision+1 }
    static func save(_ profile: TouchProfile, pad: Bool) throws {
        let data = try profile.encoded()
        UserDefaults.standard.set(data,forKey:key(pad))
        guard UserDefaults.standard.data(forKey:key(pad)) == data else { throw TouchProfileError.message("The layout could not be saved. Please try again.") }
        UserDefaults.standard.set(profile.featherTouch,forKey:"cabrillo.featherTouch")
        preferenceChanged()
    }
}

@objc public final class CJTouchEditorBridge: NSObject {
    @objc(presentFrom:) public static func present(from: UIViewController) {
        guard Thread.isMainThread, !CJTouchStore.editorActive else { return }
        var parent = from
        while let presented = parent.presentedViewController { parent = presented }
        CJTouchStore.editorActive = true
        weak var presentedEditor: UIViewController?
        let controller = CJTouchHostingController(rootView: TouchEditorView {
            // Let SwiftUI finish dismissing its confirmation dialog first.
            DispatchQueue.main.async { presentedEditor?.dismiss(animated:true) { CJTouchStore.editorActive = false } }
        })
        presentedEditor = controller
        controller.modalPresentationStyle = .fullScreen
        controller.overrideUserInterfaceStyle = .dark
        parent.present(controller,animated:true)
    }
}

private final class CJTouchHostingController: UIHostingController<TouchEditorView> {
    override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        if isBeingDismissed || presentingViewController == nil { CJTouchStore.editorActive = false }
    }
}

private final class TouchDraft: ObservableObject {
    @Published var value: TouchProfile
    @Published var selected = "movement"
    @Published var history: [TouchProfile] = []
    @Published var message = ""
    let original: TouchProfile
    let surface: TouchSurface
    var gestureStart: TouchProfile?
    init() { let s = TouchSurface.current; surface = s; let p = CJTouchStore.load(s); original = p; value = p }
    var dirty: Bool { value != original }
    func change(_ action: (inout TouchProfile) -> Void) { let old = value; action(&value); if value != old { history.append(old); if history.count > 60 { history.removeFirst() } } }
    func begin() { if gestureStart == nil { gestureStart = value } }
    func end() { if let old = gestureStart, old != value { history.append(old); if history.count > 60 {history.removeFirst()} }; gestureStart = nil }
    func undo() {
        if let last = history.popLast() {
            let kind = value.controls.first { $0.id == selected }?.kind
            value = last
            if !value.controls.contains(where: { $0.id == selected }) { selected = value.controls.first { $0.kind == kind }?.id ?? "movement" }
            message = ""
        }
    }
    func update(_ id: String, _ action: (inout TouchItem) -> Void) {
        change { p in if let index = p.controls.firstIndex(where: { $0.id == id }) { action(&p.controls[index]) } }
    }
    func add(_ kind: String, copy: TouchItem? = nil) {
        guard value.controls.count < 24 else { message = "This layout has reached 24 controls."; return }
        var item = copy ?? TouchItem(id:UUID().uuidString,kind:kind,x:0.42,y:0.43,width:64/surface.width,height:64/surface.height)
        item.id = UUID().uuidString
        if kind == "split" { item.shape = "rectangle" }
        if copy != nil { item.x = min(1-item.width,item.x+0.06); item.y = max(0,item.y-0.06) }
        item.enabled = true; change { $0.controls.append(item) }; selected = item.id
    }
    func drag(_ id: String, translation: CGSize, canvas: CGSize, resize: Bool) {
        begin(); guard let start = gestureStart?.controls.first(where: { $0.id == id }), let i = value.controls.firstIndex(where: { $0.id == id }) else { return }
        var box = start.box
        if resize {
            box = TouchResizePolicy.resized(start.box, translation: translation, canvas: canvas,
                surface: CGSize(width: surface.width, height: surface.height), circle: start.shape == "circle")
        } else {
            box.x = max(0,min(1-box.width,start.x+Double(translation.width/canvas.width)))
            box.y = max(0,min(1-box.height,start.y+Double(translation.height/canvas.height)))
            if abs(box.x+box.width/2-0.5) < 0.008 { box.x = 0.5-box.width/2 }
            if abs(box.y+box.height/2-0.5) < 0.012 { box.y = 0.5-box.height/2 }
        }
        value.controls[i].box = box
    }
}

struct TouchLayoutDocument: FileDocument {
    static var readableContentTypes: [UTType] { [.json,.data] }
    var data: Data
    init(data: Data) { self.data = data }
    init(configuration: ReadConfiguration) throws { data = configuration.file.regularFileContents ?? Data() }
    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper { FileWrapper(regularFileWithContents:data) }
}

private struct TouchLayoutImportPicker: UIViewControllerRepresentable {
    let completion: (URL?) -> Void
    func makeCoordinator() -> Coordinator { Coordinator(completion: completion) }
    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        CJTouchStore.prepareDocumentPicker?()
        // Copy mode also supports Development-signed installs whose original
        // bundle identifier differs from the signed Files host identifier.
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.json, .data], asCopy: true)
        picker.allowsMultipleSelection = false
        picker.delegate = context.coordinator
        return picker
    }
    func updateUIViewController(_ controller: UIDocumentPickerViewController, context: Context) {}
    final class Coordinator: NSObject, UIDocumentPickerDelegate {
        let completion: (URL?) -> Void
        init(completion: @escaping (URL?) -> Void) { self.completion = completion }
        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) { completion(urls.first) }
        func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) { completion(nil) }
    }
}

struct TouchEditorView: View {
    @StateObject private var draft = TouchDraft()
    @State private var page = 0
    @State private var importing = false
    @State private var exporting = false
    @State private var exportDocument = TouchLayoutDocument(data:Data())
    @State private var discard = false
    @State private var resetting = false
    @State private var importPreview: TouchProfile?
    @State private var importName = ""
    @State private var importedURL: URL?
    @State private var details = false
    @State private var toolsHidden = false
    @State private var toolOffset = CGSize.zero
    @State private var toolDragStart = CGSize.zero
    let close: () -> Void
    private let accent = Color(red:0.96,green:0.36,blue:0.47)
    var body: some View {
        GeometryReader { geometry in
            Group {
                if geometry.size.width > geometry.size.height && !details {
                    fullScreenCanvas(size:geometry.size)
                } else { detailedEditor }
            }.onChange(of:geometry.size) {_ in details = false}
        }.ignoresSafeArea(.container)
        .preferredColorScheme(.dark).tint(accent).statusBar(hidden:true)
        .confirmationDialog("Discard your layout changes?",isPresented:$discard,titleVisibility:.visible) { Button("Discard changes",role:.destructive,action:close) }
        .confirmationDialog("Reset this device’s layout and touch behavior?",isPresented:$resetting,titleVisibility:.visible) { Button("Reset to defaults",role:.destructive) { draft.change { $0 = draft.surface.factory }; draft.selected = "movement" } }
        .sheet(isPresented:$importing,onDismiss:readImportedLayout) {
            TouchLayoutImportPicker { url in importedURL = url; importing = false }
        }
        .fileExporter(isPresented:$exporting,document:exportDocument,contentType:.json,defaultFilename:"Cabrillo-touch-layout") { result in
            if case .failure(let error) = result { draft.message = error.localizedDescription }
        }
        .sheet(isPresented:Binding(get:{importPreview != nil},set:{if !$0 {importPreview = nil}})) {
            if let imported = importPreview {
                CJNavigation {
                    VStack(spacing:18) {
                        Text(importName).font(.headline)
                        Text("Preview on this device. Your saved layout stays in place until you tap Save.").foregroundStyle(.secondary)
                        TouchCanvas(profile:imported,selected:"",surface:draft.surface,select:{_ in},drag:{_,_,_,_ in},end:{}).aspectRatio(draft.surface.width/draft.surface.height,contentMode:.fit)
                        Button("Use this draft") { draft.change { $0 = imported }; draft.selected = "movement"; importPreview = nil }.buttonStyle(.borderedProminent).accessibilityIdentifier("touch.import.apply")
                        Button("Cancel import") { importPreview = nil }
                    }.padding().navigationTitle("Import preview")
                }
            }
        }
    }
    private func readImportedLayout() {
        guard let url = importedURL else { return }
        importedURL = nil
        do {
            let scoped = url.startAccessingSecurityScopedResource()
            defer { if scoped { url.stopAccessingSecurityScopedResource() } }
            let size = try url.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0
            guard size <= 32768 else { throw TouchProfileError.message("Choose a layout smaller than 32 KB.") }
            let data = try Data(contentsOf:url,options:.mappedIfSafe)
            importPreview = try TouchProfile.imported(data,pad:draft.surface.pad,width:draft.surface.width,height:draft.surface.height)
            importName = url.lastPathComponent
        } catch { draft.message = error.localizedDescription }
    }
    private var detailedEditor: some View {
        NavigationView {
            GeometryReader { geometry in
                VStack(spacing:0) {
                    Picker("Editor page",selection:$page) { Text("Layout").tag(0); Text("Behavior").tag(1) }.pickerStyle(.segmented).padding(.horizontal).padding(.bottom,8)
                    if page == 0 {
                        if geometry.size.width > 750 && geometry.size.height < 650 {
                            HStack(spacing:0) { canvas.padding(12); inspector.frame(width:285) }
                        } else { canvas.padding(.horizontal,12).padding(.bottom,8); inspector }
                    } else { behavior }
                    if !draft.message.isEmpty { Text(draft.message).font(.footnote).foregroundStyle(.orange).padding(8).accessibilityIdentifier("touch.message") }
                    tools.padding(.horizontal).padding(.vertical,10).background(Color(UIColor.secondarySystemBackground))
                }
            }
            .navigationTitle("Touch controls").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement:.principal) {
                    if details { Button("Full screen") {details = false}.accessibilityIdentifier("touch.fullScreen.back") }
                    else { Text("Touch controls").font(.headline) }
                }
                ToolbarItem(placement:.cancellationAction) { Button("Cancel") { if draft.dirty { discard = true } else { close() } }.accessibilityIdentifier("touch.cancel") }
                ToolbarItem(placement:.confirmationAction) { Button("Save") { save() }.font(.headline).disabled(draft.value.validation() != nil).accessibilityIdentifier("touch.save") }
            }
        }.navigationViewStyle(.stack).preferredColorScheme(.dark).tint(accent)
    }
    private func fullScreenCanvas(size: CGSize) -> some View {
        let toolbarWidth = toolsHidden ? 92.0 : min(520.0,Double(size.width)-32)
        let baseY = max(72.0,draft.surface.top+32)
        return ZStack(alignment:.topLeading) {
            TouchCanvas(profile:draft.value,selected:draft.selected,surface:draft.surface,select:{draft.selected = $0},drag:draft.drag,end:draft.end)
                .frame(width:size.width,height:size.height)
            HStack(spacing:14) {
                Image(systemName:"line.3.horizontal").frame(width:28,height:36).contentShape(Rectangle()).accessibilityLabel("Move toolbar")
                    .gesture(DragGesture(minimumDistance:0,coordinateSpace:.named("touch.editor.coordinates")).onChanged { value in
                        toolOffset = CGSize(width:max(toolbarWidth/2-Double(size.width)/2,min(Double(size.width)/2-toolbarWidth/2,Double(toolDragStart.width+value.translation.width))),
                            height:max(26-baseY,min(Double(size.height)-26-baseY,Double(toolDragStart.height+value.translation.height))))
                    }.onEnded {_ in toolDragStart = toolOffset})
                if toolsHidden {
                    Button { toolsHidden = false } label:{Image(systemName:"pencil")}.accessibilityLabel("Show editing tools")
                } else {
                    Button {draft.undo()} label:{Image(systemName:"arrow.uturn.backward")}.disabled(draft.history.isEmpty).accessibilityLabel("Undo").accessibilityIdentifier("touch.undo")
                    Menu {
                        ForEach(draft.value.controls) { item in Button(item.name) {draft.selected = item.id} }
                    } label:{Text(draft.value.controls.first {$0.id == draft.selected}?.name ?? "Select").lineLimit(1).frame(maxWidth:.infinity)}
                    Button {toolsHidden = true} label:{Image(systemName:"eye.slash")}.accessibilityLabel("Hide editing tools")
                    Button {details = true} label:{Image(systemName:"slider.horizontal.3")}.accessibilityLabel("Details").accessibilityIdentifier("touch.details")
                    Button("Save",action:save).font(.headline).disabled(draft.value.validation() != nil).accessibilityIdentifier("touch.save")
                }
            }.font(.body).padding(.horizontal,12).frame(width:toolbarWidth,height:48)
                .background(.ultraThinMaterial,in:Capsule()).overlay(Capsule().stroke(.white.opacity(0.18)))
                .position(x:Double(size.width)/2+toolOffset.width,y:baseY+toolOffset.height)
        }.coordinateSpace(name:"touch.editor.coordinates").accessibilityElement(children:.contain).accessibilityIdentifier("touch.fullScreen")
    }
    private var canvas: some View {
        VStack(alignment:.leading,spacing:6) {
            HStack { Text(draft.surface.pad ? "iPad layout" : "iPhone layout").font(.caption.bold()); Spacer(); Text("Drag to move · corner to resize").font(.caption).foregroundStyle(.secondary) }
            TouchCanvas(profile:draft.value,selected:draft.selected,surface:draft.surface,select:{draft.selected = $0},drag:draft.drag,end:draft.end)
                .aspectRatio(draft.surface.width/draft.surface.height,contentMode:.fit)
            Text("Rotate to landscape to place controls at actual size. The outline shows the 16:9 game image; controls can use the whole screen, edge to edge. Camera cutouts and system gestures may cover the edges.").font(.caption2).foregroundStyle(.secondary)
        }
    }
    private var inspector: some View {
        Form {
            Section {
                Picker("Selected control",selection:$draft.selected) {
                    ForEach(Array(draft.value.controls.enumerated()),id:\.element.id) { index,item in Text("\(index+1). \(item.name)\(draft.value.active(item) ? "" : " · hidden")").tag(item.id) }
                }.accessibilityIdentifier("touch.selection")
                if let item = draft.value.controls.first(where: { $0.id == draft.selected }) { itemInspector(item) }
            }
            if let error = draft.value.validation() { Section { Label(error,systemImage:"exclamationmark.triangle").foregroundStyle(.orange) } }
            else if let warning = draft.value.geometryWarning(width:draft.surface.width,height:draft.surface.height) { Section { Text(warning).font(.footnote).foregroundStyle(.secondary) } }
            Section("Layout files") {
                Button("Import layout…") { importing = true }.accessibilityIdentifier("touch.import")
                Button("Export draft…") { do { exportDocument = TouchLayoutDocument(data:try draft.value.encoded()); CJTouchStore.prepareDocumentPicker?(); exporting = true } catch { draft.message = error.localizedDescription } }.disabled(draft.value.validation() != nil)
                Text("Use Files or iCloud to keep and share layouts. Morro D3 version 2 layouts can also be imported. iPhone and iPad keep separate saved layouts.").font(.footnote).foregroundStyle(.secondary)
            }
        }
    }
    @ViewBuilder private func itemInspector(_ item: TouchItem) -> some View {
        if !["movement","floating","gesture"].contains(item.kind) {
            HStack { Button("Duplicate") { draft.add(item.kind,copy:item) }.disabled(draft.value.controls.count >= 24).accessibilityIdentifier("touch.duplicate")
                Spacer(); Button("Delete",role:.destructive) { draft.change {$0.controls.removeAll {$0.id == item.id}}; draft.selected = "movement" }.accessibilityIdentifier("touch.delete") }.buttonStyle(.borderless)
        }
        Toggle("Enabled",isOn:Binding(get:{item.enabled},set:{value in draft.update(item.id){$0.enabled = value}})).accessibilityIdentifier("touch.enabled")
        if !["movement","floating","gesture","split"].contains(item.kind) {
            Picker("Action",selection:Binding(get:{item.kind},set:{value in draft.update(item.id){$0.kind = value}})) { ForEach(["jump","dash","grab","pause","journal","crouchDash","quickRestart"],id:\.self) { Text(TouchItem.names[$0]!).tag($0) } }.accessibilityIdentifier("touch.action")
        }
        if !["movement","floating","gesture","split"].contains(item.kind) {
            Picker("Shape",selection:Binding(get:{item.shape},set:{value in draft.update(item.id){$0.shape = value}})) { Text("Circle").tag("circle");Text("Rectangle").tag("rectangle") }.pickerStyle(.segmented).accessibilityIdentifier("touch.shape")
        }
        if item.kind == "split" {
            Picker("Split direction",selection:Binding(get:{item.split},set:{value in draft.update(item.id){$0.split = value}})) {
                Text("Diagonal ↘").tag(0);Text("Diagonal ↙").tag(1);Text("Left / right").tag(2);Text("Top / bottom").tag(3)
            }.accessibilityIdentifier("touch.split")
            Toggle("Swap Jump and Dash",isOn:Binding(get:{item.swap},set:{value in draft.update(item.id){$0.swap = value}}))
        }
        itemSlider("Width",item:item,key:\.width,range:0.03...1,multiplier:draft.surface.width)
        itemSlider("Height",item:item,key:\.height,range:0.03...1,multiplier:draft.surface.height)
        itemSlider("Horizontal position",item:item,key:\.x,range:0...max(0.001,1-item.width),multiplier:100)
        itemSlider("Vertical position",item:item,key:\.y,range:0...max(0.001,1-item.height),multiplier:100)
        VStack(alignment:.leading) { Text("Opacity · \(item.opacity)%"); Slider(value:Binding(get:{Double(item.opacity)},set:{v in draft.update(item.id){$0.opacity = Int(v)}}),in:0...100,step:10) }.accessibilityIdentifier("touch.opacity")
        Button("Reset this control") {
            let original = draft.surface.factory.controls.first(where:{$0.kind == item.kind}) ?? TouchItem(id:item.id,kind:item.kind,shape:item.kind == "split" ? "rectangle" : "circle",x:0.42,y:0.43,width:64/draft.surface.width,height:64/draft.surface.height)
            draft.update(item.id) {let id = $0.id; $0 = original; $0.id = id}
        }
        if item.kind == "quickRestart" { Text("Uses Celeste’s normal Quick Restart input and confirmation behavior.").font(.footnote).foregroundStyle(.secondary) }
    }
    private func itemSlider(_ name: String,item: TouchItem,key: WritableKeyPath<TouchItem,Double>,range: ClosedRange<Double>,multiplier: Double) -> some View {
        VStack(alignment:.leading,spacing:4) {
            Text("\(name) · \(Int(item[keyPath:key]*multiplier))\(multiplier == 100 ? "%" : " pt")").font(.subheadline)
            Slider(value:Binding(get:{item[keyPath:key]},set:{value in
                draft.update(item.id) { c in c[keyPath:key] = value; c.x = max(0,min(c.x,1-c.width)); c.y = max(0,min(c.y,1-c.height)) }
            }),in:range)
        }.accessibilityIdentifier("touch.\(name)")
    }
    private func option<T: Equatable>(_ key: WritableKeyPath<TouchProfile,T>) -> Binding<T> { Binding(get:{draft.value[keyPath:key]},set:{value in draft.change {$0[keyPath:key] = value}}) }
    private var behavior: some View {
        Form {
            Section("Choose a starting point") {
                HStack { Button("Buttons") { draft.change {$0.preset("buttons")}; draft.selected = "jump" }; Button("Split region") { draft.change {$0.preset("split")}; draft.selected = draft.value.controls.first{$0.kind == "split"}?.id ?? "movement" }; Button("Tap / Swipe") { draft.change {$0.preset("swipe")}; draft.selected = "gesture" } }.buttonStyle(.borderless).accessibilityIdentifier("touch.presets")
                Text("Presets change the draft. Undo returns to your previous layout. Mirror swaps the movement and action sides.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Movement and actions") {
                Picker("Movement",selection:option(\.movement)) { Text("Fixed joystick").tag("fixed");Text("Floating joystick").tag("floating") }.accessibilityIdentifier("touch.movement")
                Text("Floating movement starts where your thumb lands inside its region. Both modes keep the same eight directions and dead zone.").font(.footnote).foregroundStyle(.secondary)
                Toggle("Slide between Jump and Dash",isOn:option(\.sliding)).accessibilityIdentifier("touch.sliding")
                Text("Slide a held finger between the two actions without lifting. Split regions use a small boundary margin to prevent accidental switching.").font(.footnote).foregroundStyle(.secondary)
                Picker("Touch grab mode",selection:option(\.grab)) { Text("Hold").tag("hold");Text("Toggle").tag("toggle");Text("Inverse").tag("invert") }.accessibilityIdentifier("touch.grab")
                Text("Hold: press to grab. Toggle: tap to grab, tap again to release. Inverse: grab until you press. Controller and keyboard can use separate modes below. Change these during play using Pause → Touch controls.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Grab preferences") {
                Picker("Controller grab mode",selection:option(\.controllerGrab)) {
                    if draft.value.controllerGrab == "game" { Text("Celeste default on first run").tag("game") }
                    Text("Hold").tag("hold");Text("Toggle").tag("toggle");Text("Inverse").tag("invert")
                }.accessibilityIdentifier("touch.controllerGrab")
                Picker("Keyboard grab mode",selection:option(\.keyboardGrab)) {
                    if draft.value.keyboardGrab == "game" { Text("Celeste default on first run").tag("game") }
                    Text("Hold").tag("hold");Text("Toggle").tag("toggle");Text("Inverse").tag("invert")
                }.accessibilityIdentifier("touch.keyboardGrab")
                Text("All modes use Celeste’s own grab setting. Each input method remembers its choice. Changing Grab mode in Celeste Options updates the method currently in use. An idle controller does not take over from touch.").font(.footnote).foregroundStyle(.secondary)
                Picker("Toggle behaviour",selection:option(\.toggleBehavior)) {
                    Text("Default · reset with Celeste").tag("default");Text("Until untoggled").tag("persistent")
                }.accessibilityIdentifier("touch.toggleBehavior")
                Text("Default clears toggled grab when Celeste normally resets it, including after death. Until untoggled keeps each input method’s toggle through deaths, map changes and switching methods for this game session. Changing its grab mode, changing this option or quitting clears it.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Controller prompts") {
                Picker("Button symbols",selection:option(\.controllerPrompts)) {
                    Text("Automatic").tag("automatic");Text("Xbox").tag("xbox");Text("PlayStation").tag("playstation");Text("Nintendo Switch").tag("switch");Text("Stadia").tag("stadia")
                }.accessibilityIdentifier("touch.controllerPrompts")
                Text("Automatic follows the controller Celeste is using, including DualSense. Changing symbols keeps your bindings and the controller’s light colour.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Experimental feather steering") {
                Toggle("Feather follows finger",isOn:option(\.featherTouch)).accessibilityIdentifier("touch.featherTouch")
                Text("Steer toward a finger during feather flight. Lift or move close to Madeline for Celeste’s neutral input. Speeds and turning stay original. Save applies this immediately; start a fresh touch after closing the editor.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Experimental tap and swipe") {
                Toggle("Tap to jump · swipe to dash",isOn:option(\.swipe)).accessibilityIdentifier("touch.swipe")
                Text("In the gesture region, touch and hold to jump. Swipe in one of eight directions to dash once, independently of the movement joystick. Lift before the next swipe. A swipe begins with a jump; use ordinary buttons when you need a dash without jumping. In menus, tap and release to confirm, or swipe to go back. Grab, Pause and Journal keep their buttons. During feather flight, Feather follows finger takes priority.").font(.footnote).foregroundStyle(.secondary)
                VStack(alignment:.leading) { Text("Swipe distance · \(Int(draft.value.swipeDistance)) pt");Slider(value:option(\.swipeDistance),in:12...80,step:2) }.disabled(!draft.value.swipe)
            }
            Section("Appearance and feedback") {
                Picker("Show controls",selection:option(\.visibility)) {Text("When using touch").tag("automatic");Text("Always").tag("always");Text("Off").tag("off")}.accessibilityIdentifier("touch.visibility")
                if draft.value.visibility == "off" { Text("Touch input is disabled. Use a controller or keyboard, or return to Cabrillo Settings to restore it.").font(.footnote).foregroundStyle(.orange) }
                VStack(alignment:.leading) {Text("Overall opacity · \(draft.value.opacity)%");Slider(value:Binding(get:{Double(draft.value.opacity)},set:{v in draft.change {$0.opacity = Int(v)}}),in:0...100,step:10)}
                Toggle("Action haptics",isOn:option(\.haptics))
                Toggle("Direction-change haptics",isOn:option(\.directionalHaptics))
                Text("Haptics depend on the device. Touch preferences do not change game physics or controller bindings.").font(.footnote).foregroundStyle(.secondary)
            }
        }
    }
    private var tools: some View {
        HStack {
            Button { draft.undo() } label:{Label("Undo",systemImage:"arrow.uturn.backward")}.disabled(draft.history.isEmpty).accessibilityIdentifier("touch.undo")
            Spacer();Button { draft.change {$0.mirror()} } label:{Label("Mirror",systemImage:"arrow.left.and.right.righttriangle.left.righttriangle.right")}.accessibilityIdentifier("touch.mirror")
            Spacer();Menu { ForEach(["jump","dash","grab","pause","journal","crouchDash","quickRestart","split"],id:\.self) {kind in Button(TouchItem.names[kind]!) {draft.add(kind)} } } label:{Label("Add",systemImage:"plus")}.disabled(draft.value.controls.count >= 24).accessibilityIdentifier("touch.add")
            Spacer();Button { resetting = true } label:{Label("Reset",systemImage:"arrow.counterclockwise")}.accessibilityIdentifier("touch.reset")
        }.font(.subheadline)
    }
    private func save() {
        do { try CJTouchStore.save(draft.value,pad:draft.surface.pad);close() } catch {draft.message = error.localizedDescription}
    }
}

private struct TouchCanvas: View {
    var profile: TouchProfile; var selected: String; var surface: TouchSurface
    var select: (String) -> Void; var drag: (String,CGSize,CGSize,Bool) -> Void; var end: () -> Void
    var body: some View {
        GeometryReader { geo in
            ZStack(alignment:.topLeading) {
                Color(red:0.07,green:0.11,blue:0.17)
                Canvas {context,size in
                    var lines = Path();lines.move(to:CGPoint(x:size.width/2,y:0));lines.addLine(to:CGPoint(x:size.width/2,y:size.height));lines.move(to:CGPoint(x:0,y:size.height/2));lines.addLine(to:CGPoint(x:size.width,y:size.height/2))
                    context.stroke(lines,with:.color(.white.opacity(0.13)),style:StrokeStyle(lineWidth:1,dash:[4,5]))
                }
                let gameWidth = min(geo.size.width,geo.size.height*16/9)
                let gameHeight = gameWidth*9/16
                Rectangle().fill(.white.opacity(0.025)).overlay(Rectangle().stroke(.white.opacity(0.35),style:StrokeStyle(lineWidth:1,dash:[7,5])))
                    .frame(width:gameWidth,height:gameHeight).position(x:geo.size.width/2,y:geo.size.height/2).allowsHitTesting(false).accessibilityLabel("16:9 game image").accessibilityIdentifier("touch.gameGuide")
                Text("16:9 GAME IMAGE").font(.system(size:11,weight:.medium,design:.rounded)).tracking(2).foregroundStyle(.white.opacity(0.32)).position(x:geo.size.width/2,y:geo.size.height/2).allowsHitTesting(false)
                ForEach(profile.controls.sorted { a,b in a.isRegion && !b.isRegion }) {item in
                    if profile.active(item) || selected == item.id {
                        let box = CGRect(x:item.x*geo.size.width,y:item.y*geo.size.height,width:item.width*geo.size.width,height:item.height*geo.size.height)
                        TouchItemPreview(item:item,selected:selected == item.id,muted:!profile.active(item))
                            .frame(width:box.width,height:box.height).contentShape(Rectangle())
                            .gesture(DragGesture(minimumDistance:0,coordinateSpace:.named("touch.canvas.coordinates")).onChanged {value in if selected != item.id {select(item.id)};drag(item.id,value.translation,geo.size,false)}.onEnded {_ in end()})
                            .position(x:box.midX,y:box.midY).accessibilityElement(children:.ignore).accessibilityLabel(item.name).accessibilityIdentifier("touch.canvas.\(item.id)")
                        if selected == item.id {
                            Image(systemName:"arrow.up.left.and.arrow.down.right").font(.system(size:11,weight:.bold)).frame(width:28,height:28).background(Color.accentColor,in:Circle())
                                .gesture(DragGesture(minimumDistance:0,coordinateSpace:.named("touch.canvas.coordinates")).onChanged {drag(item.id,$0.translation,geo.size,true)}.onEnded {_ in end()})
                                .position(x:min(geo.size.width-14,box.maxX),y:min(geo.size.height-14,box.maxY)).accessibilityLabel("Resize \(item.name)").accessibilityIdentifier("touch.resize.\(item.id)")
                        }
                    }
                }
            }.coordinateSpace(name:"touch.canvas.coordinates").clipped().overlay(RoundedRectangle(cornerRadius:10).stroke(.white.opacity(0.15))).clipShape(RoundedRectangle(cornerRadius:10))
        }.accessibilityElement(children:.contain).accessibilityIdentifier("touch.canvas")
    }
}
private struct TouchItemPreview: View {
    let item: TouchItem; let selected: Bool; let muted: Bool
    private var color: Color { ["jump":.cyan,"dash":.pink,"grab":.yellow,"movement":.blue,"crouchDash":.purple][item.kind] ?? .white }
    var body: some View {
        GeometryReader { geo in
            ZStack {
                if item.shape == "circle" {
                    Circle().fill(color.opacity(0.18)).overlay(Circle().stroke(selected ? Color.accentColor : color.opacity(0.55),style:StrokeStyle(lineWidth:selected ? 2 : 1,dash:[4,3])))
                        .frame(width:min(geo.size.width,geo.size.height),height:min(geo.size.width,geo.size.height))
                } else {
                    Rectangle().fill(color.opacity(0.1)).overlay(Rectangle().stroke(selected ? Color.accentColor : color.opacity(0.4),style:StrokeStyle(lineWidth:selected ? 2 : 1,dash:[4,3])))
                }
                if item.kind == "split" { SplitPreview(item:item) }
                else {
                    VStack(spacing:2) {
                        Image(systemName:icon).font(.system(size:min(25,max(12,min(geo.size.width,geo.size.height)*0.26)),weight:.semibold))
                        if geo.size.width > 38 && geo.size.height > 34 {Text(item.name).font(.system(size:min(11,max(8,geo.size.height*0.16)),weight:.medium)).lineLimit(1).minimumScaleFactor(0.5)}
                    }.foregroundStyle(color.opacity(0.85))
                }
            }.frame(maxWidth:.infinity,maxHeight:.infinity).opacity(muted ? 0.3 : max(0.18,Double(item.opacity)/100))
        }
    }
    private var icon: String { ["movement":"plus","jump":"arrow.up","dash":"bolt.fill","grab":"hand.raised.fill","pause":"pause.fill","journal":"book.closed","crouchDash":"arrow.down.forward","quickRestart":"arrow.counterclockwise","floating":"scope","gesture":"hand.draw"] [item.kind] ?? "circle" }
}
private struct SplitPreview: View {
    var item: TouchItem
    var body: some View {
        GeometryReader { geo in
            Canvas {context,size in
                var line = Path()
                let start: CGPoint, end: CGPoint, jump: CGPoint, dash: CGPoint
                switch item.split {
                case 0: start = .zero;end = CGPoint(x:size.width,y:size.height);jump = CGPoint(x:size.width*0.67,y:size.height*0.33);dash = CGPoint(x:size.width*0.33,y:size.height*0.67)
                case 1: start = CGPoint(x:size.width,y:0);end = CGPoint(x:0,y:size.height);jump = CGPoint(x:size.width*0.33,y:size.height*0.33);dash = CGPoint(x:size.width*0.67,y:size.height*0.67)
                case 2: start = CGPoint(x:size.width/2,y:0);end = CGPoint(x:size.width/2,y:size.height);jump = CGPoint(x:size.width*0.25,y:size.height/2);dash = CGPoint(x:size.width*0.75,y:size.height/2)
                default: start = CGPoint(x:0,y:size.height/2);end = CGPoint(x:size.width,y:size.height/2);jump = CGPoint(x:size.width/2,y:size.height*0.25);dash = CGPoint(x:size.width/2,y:size.height*0.75)
                }
                line.move(to:start);line.addLine(to:end);context.stroke(line,with:.color(.white.opacity(0.7)),lineWidth:1)
                context.draw(Text("Jump").font(.caption.bold()).foregroundColor(.cyan),at:item.swap ? dash : jump)
                context.draw(Text("Dash").font(.caption.bold()).foregroundColor(.pink),at:item.swap ? jump : dash)
            }
        }
    }
}
#endif
