import Foundation

struct TouchBox: Codable, Equatable {
    var x: Double; var y: Double; var width: Double; var height: Double
}
struct TouchItem: Codable, Equatable, Identifiable {
    var id: String
    var kind: String
    var shape = "circle"
    var x: Double; var y: Double; var width: Double; var height: Double
    var opacity = 100
    var enabled = true
    var split = 0
    var swap = false
    var box: TouchBox {
        get { TouchBox(x: x, y: y, width: width, height: height) }
        set { x = newValue.x; y = newValue.y; width = newValue.width; height = newValue.height }
    }
    var name: String { Self.names[kind] ?? kind }
    static let names = ["movement": "Movement", "floating": "Movement region", "jump": "Jump", "dash": "Dash", "grab": "Grab", "pause": "Pause", "journal": "Journal", "crouchDash": "Crouch dash", "quickRestart": "Quick restart", "split": "Jump / Dash", "gesture": "Tap / Swipe"]
    var isRegion: Bool { ["floating", "gesture"].contains(kind) }
    func contains(_ px: Double, _ py: Double, width w: Double, height h: Double) -> Bool {
        if shape == "rectangle" { return px >= x*w && px <= (x+width)*w && py >= y*h && py <= (y+height)*h }
        let dx = px-(x+width/2)*w, dy = py-(y+height/2)*h, radius = min(width*w, height*h)/2
        return dx*dx+dy*dy <= radius*radius
    }
    func splitAction(_ px: Double, _ py: Double, width w: Double, height h: Double, previous: String = "") -> String {
        let rw = width*w, rh = height*h, dx = px-x*w, dy = py-y*h
        let side: Double
        switch split {
        case 0: side = (dy*rw-dx*rh)/hypot(rw, rh)
        case 1: side = (dy*rw+dx*rh-rw*rh)/hypot(rw, rh)
        case 2: side = dx-rw/2
        default: side = dy-rh/2
        }
        if abs(side) < 4 && ["jump", "dash"].contains(previous) { return previous }
        return ((side <= 0) != swap) ? "jump" : "dash"
    }
}

struct TouchProfile: Codable, Equatable {
    var schema = 1
    var movement = "fixed"
    var grab = "toggle"
    var controllerGrab = "game"
    var keyboardGrab = "game"
    var featherTouch = false
    var toggleBehavior = "default"
    var controllerPrompts = "automatic"
    var visibility = "automatic"
    var sliding = true
    var haptics = true
    var directionalHaptics = false
    var opacity = 100
    var swipe = false
    var swipeDistance = 24.0
    var controls: [TouchItem]
    func active(_ item: TouchItem) -> Bool {
        item.enabled && (item.kind != "floating" || movement == "floating") && (item.kind != "gesture" || swipe) && (!swipe || !["jump", "dash", "split"].contains(item.kind))
    }
    static func factory(width w: Double, height h: Double, top: Double = 0, left: Double = 0, bottom: Double = 0, right: Double = 0, pad: Bool = false) -> Self {
        let scale = pad ? 1.18 : 1.0
        func rect(_ kind: String, _ x: Double, _ y: Double, _ width: Double, _ height: Double, _ shape: String = "rectangle") -> TouchItem {
            TouchItem(id: kind, kind: kind, shape: shape, x: x/w, y: y/h, width: width/w, height: height/h)
        }
        func circle(_ kind: String, _ x: Double, _ y: Double, _ radius: Double) -> TouchItem {
            rect(kind, x-radius*scale, y-radius*scale, radius*2*scale, radius*2*scale, "circle")
        }
        let jx = w-right-72*scale, jy = h-bottom-69*scale
        return Self(controls: [circle("movement", left+106*scale, h-bottom-104*scale, 94),
            rect("floating", left, top+78*scale, max(1,w*0.48-left), max(1,h-bottom-top-78*scale)),
            circle("jump", jx, jy, 58), circle("dash", jx-87*scale, jy-91*scale, 51), circle("grab", jx-157*scale, jy-8*scale, 45),
            rect("pause", w*0.5-29*scale, top+15*scale, 58*scale, 40*scale),
            rect("journal", left+15*scale, top+15*scale, 50*scale, 40*scale),
            TouchItem(id: "gesture", kind: "gesture", shape: "rectangle", x: 0.53, y: 0.30, width: 0.46, height: 0.69, opacity: 20)])
    }
    func validation() -> String? {
        guard ["default","persistent"].contains(toggleBehavior), ["automatic","xbox","playstation","switch","stadia"].contains(controllerPrompts), schema == 1, ["fixed", "floating"].contains(movement), ["hold", "invert", "toggle"].contains(grab),
              ["game", "hold", "invert", "toggle"].contains(controllerGrab), ["game", "hold", "invert", "toggle"].contains(keyboardGrab),
              ["automatic", "always", "off"].contains(visibility), (0...100).contains(opacity), swipeDistance.isFinite,
              (12...80).contains(swipeDistance), (3...24).contains(controls.count) else { return "This layout contains unsupported settings." }
        var ids = Set<String>()
        for c in controls {
            guard !c.id.isEmpty, c.id.count <= 64, ids.insert(c.id).inserted, TouchItem.names[c.kind] != nil,
                  ["circle", "rectangle"].contains(c.shape), (0...3).contains(c.split), (0...100).contains(c.opacity),
                  (c.x+c.y+c.width+c.height).isFinite, c.x >= 0, c.y >= 0, c.width >= 0.015, c.height >= 0.015,
                  c.x+c.width <= 1.00001, c.y+c.height <= 1.00001 else { return "A control lies outside the screen or has invalid dimensions." }
        }
        for kind in ["movement", "floating", "gesture"] where controls.filter({ $0.kind == kind }).count != 1 { return "Keep one movement control, floating region and gesture region." }
        guard controls.contains(where: { $0.kind == "movement" && $0.enabled }), controls.contains(where: { $0.kind == "pause" && $0.enabled && $0.opacity >= 20 }) else { return "Keep movement and a visible Pause button available." }
        if swipe && !controls.contains(where: { $0.kind == "gesture" && $0.enabled }) { return "Enable the gesture region for tap and swipe." }
        if movement == "floating" && !controls.contains(where: { $0.kind == "floating" && $0.enabled }) { return "Enable the floating movement region." }
        if !swipe && (!controls.contains(where: { $0.enabled && ["jump", "split"].contains($0.kind) }) || !controls.contains(where: { $0.enabled && ["dash", "split"].contains($0.kind) })) { return "Keep both Jump and Dash available." }
        return nil
    }
    func geometryWarning(width: Double, height: Double) -> String? {
        for item in controls where active(item) && !item.isRegion {
            if min(item.width*width, item.height*height) < 32 { return "\(item.name) is smaller than 32 points. It may be difficult to press." }
        }
        // Overlap is allowed for shoulder/background regions. Explain the exact
        // priority instead of silently moving or deleting the user's controls.
        let items = controls.filter { active($0) && !$0.isRegion }
        for (i, a) in items.enumerated() { for b in items.dropFirst(i+1) {
            let ax = (a.x+a.width/2)*width, ay = (a.y+a.height/2)*height
            let bx = (b.x+b.width/2)*width, by = (b.y+b.height/2)*height
            if a.contains(bx,by,width:width,height:height) || b.contains(ax,ay,width:width,height:height) {
                return "\(a.name) and \(b.name) overlap. The first button in the list receives the touch; buttons take priority over movement and gesture regions."
            }
        }}
        return nil
    }
    mutating func mirror() {
        for i in controls.indices {
            controls[i].x = max(0,1-controls[i].x-controls[i].width)
            if controls[i].kind == "split" {
                if controls[i].split < 2 { controls[i].split = 1-controls[i].split }
                else if controls[i].split == 2 { controls[i].swap.toggle() }
            }
        }
    }
    mutating func preset(_ name: String) {
        swipe = name == "swipe"
        for i in controls.indices {
            if ["jump", "dash"].contains(controls[i].kind) { controls[i].enabled = name == "buttons" }
            if controls[i].kind == "split" { controls[i].enabled = name == "split" }
        }
        if name != "buttons", let i = controls.firstIndex(where: { $0.kind == "grab" }) {
            controls[i].shape = "rectangle"; controls[i].box = TouchBox(x: 0.65, y: 0.06, width: 0.32, height: 0.14)
        }
        if name == "split" && !controls.contains(where: { $0.kind == "split" }) {
            controls.append(TouchItem(id: UUID().uuidString, kind: "split", shape: "rectangle", x: 0.60, y: 0.32, width: 0.38, height: 0.66))
        }
    }
    static func decode(_ data: Data) throws -> Self {
        guard data.count <= 32768 else { throw TouchProfileError.message("Choose a layout smaller than 32 KB.") }
        guard var object = try JSONSerialization.jsonObject(with:data) as? [String:Any] else { throw TouchProfileError.message("Choose a Cabrillo layout.") }
        if object["featherTouch"] == nil || object["featherTouch"] is NSNull { object["featherTouch"] = false }
        if object["toggleBehavior"] == nil { object["toggleBehavior"] = "default" }
        if object["controllerPrompts"] == nil { object["controllerPrompts"] = "automatic" }
        let result = try JSONDecoder().decode(Self.self, from: JSONSerialization.data(withJSONObject:object))
        if let error = result.validation() { throw TouchProfileError.message(error) }
        return result
    }
    func encoded() throws -> Data {
        if let error = validation() { throw TouchProfileError.message(error) }
        let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return try encoder.encode(self)
    }
}
enum TouchProfileError: LocalizedError {
    case message(String)
    var errorDescription: String? { if case .message(let value) = self { return value }; return nil }
}

// Morro's public D3 v2 document can be previewed and converted. Cabrillo exports
// its own versioned schema because it also supports swipe regions and more extras.
extension TouchProfile {
    static func imported(_ data: Data, pad: Bool, width: Double, height: Double) throws -> Self {
        guard data.count <= 32768 else { throw TouchProfileError.message("Choose a layout smaller than 32 KB.") }
        if let own = try? decode(data) { return own }
        guard let doc = try JSONSerialization.jsonObject(with: data) as? [String: Any], doc["format"] as? String == "Celeste Touch Layout",
              doc["version"] as? Int == 1, let encoded = (doc[pad ? "tabletProfile" : "phoneProfile"] ?? doc["phoneProfile"] ?? doc["tabletProfile"]) as? String else {
            throw TouchProfileError.message("Choose a Cabrillo layout or a Morro D3 version 2 layout.")
        }
        let parts = encoded.components(separatedBy: "|")
        guard parts.count == 22, parts[0] == "D3", parts[1] == "2" else { throw TouchProfileError.message("This Morro layout version is not supported.") }
        let p = Array(parts.dropFirst(2))
        func integer(_ index: Int, _ range: ClosedRange<Int>) throws -> Int {
            guard let n = Int(p[index]), range.contains(n) else { throw TouchProfileError.message("Invalid Morro layout option.") }; return n
        }
        func numbers(_ text: String, _ count: Int) throws -> [Double] {
            let fields = text.components(separatedBy: ","); let values = fields.compactMap(Double.init)
            guard fields.count == count, values.count == count, values.allSatisfy({ $0.isFinite }) else { throw TouchProfileError.message("Invalid Morro control dimensions.") }; return values
        }
        var result = factory(width: width, height: height, pad: pad)
        result.movement = try integer(0,0...1) == 1 ? "floating" : "fixed"
        let split = try integer(1,0...1) == 1; result.sliding = try integer(2,0...1) == 1
        let orientation = try integer(3,0...3), swap = try integer(4,0...1) == 0, grabShape = try integer(5,0...1)
        let opacities = try numbers(p[14],8), journal = try integer(15,0...1) == 1
        guard opacities.allSatisfy({ (0...100).contains($0) && $0.rounded() == $0 }) else { throw TouchProfileError.message("Invalid Morro opacity.") }
        let kinds = ["movement","floating","jump","dash","split","grab","pause","journal"]
        result.controls = try kinds.enumerated().map { index, kind in
            let r = try numbers(p[index+6],4)
            let circle = ["movement","jump","dash"].contains(kind) || (kind == "grab" && grabShape == 0)
            return TouchItem(id: kind, kind: kind, shape: circle ? "circle" : "rectangle", x: r[0], y: r[1], width: r[2], height: r[3], opacity: Int(opacities[index]),
                enabled: kind == "journal" ? journal : kind == "split" ? split : ["jump","dash"].contains(kind) ? !split : true, split: orientation, swap: swap)
        }
        for index in 16..<20 {
            let n = try numbers(p[index],8)
            guard [0.0,1].contains(n[0]), (0...6).contains(n[1]), n[1].rounded() == n[1], [0.0,1].contains(n[2]), (0...100).contains(n[3]), n[3].rounded() == n[3] else { throw TouchProfileError.message("Invalid Morro extra button.") }
            if n[0] == 1 { result.controls.append(TouchItem(id: "extra\(index)", kind: ["jump","dash","grab","pause","journal","crouchDash","quickRestart"][Int(n[1])], shape: n[2] == 0 ? "circle" : "rectangle", x:n[4],y:n[5],width:n[6],height:n[7],opacity:Int(n[3]))) }
        }
        result.controls.append(TouchItem(id:"gesture",kind:"gesture",shape:"rectangle",x:0.53,y:0.30,width:0.46,height:0.69,opacity:20))
        if let error = result.validation() { throw TouchProfileError.message(error) }
        return result
    }
}
