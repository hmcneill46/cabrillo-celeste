import Foundation

@main enum TouchResizeTests {
    static var checks = 0
    static func check(_ condition: @autoclosure () -> Bool, _ message: String) {
        precondition(condition(), message); checks += 1
    }
    static func close(_ a: Double, _ b: Double) -> Bool { abs(a-b) < 1e-10 }
    static let schemaTemplate = TouchProfile.factory(width:852,height:393)
    static let schemaJumpIndex = schemaTemplate.controls.firstIndex { $0.kind == "jump" }!
    static func valid(_ box: TouchBox) -> Bool {
        var profile = schemaTemplate
        profile.controls[schemaJumpIndex].box = box
        return profile.validation() == nil
    }
    static func main() throws {
        var cases = 0
        for (width,height) in [(852.0,393.0),(932,430),(568,320),(1194,834),(1180,820),(3840,2160),(2560,1440),(7680,4320)] {
            let surface = CGSize(width:width,height:height)
            let widths = [0.015,24/width,32/width,64/width,0.4,1.0].filter { $0 >= 0.015 }
            let heights = [0.015,24/height,32/height,64/height,0.4,1.0].filter { $0 >= 0.015 }
            for w in widths { for h in heights { for x in [0.0,(1-w)/2,1-w] { for y in [0.0,(1-h)/2,1-h] {
                let start = TouchBox(x:x,y:y,width:w,height:h)
                check(valid(start),"valid matrix input")
                for circle in [false,true] { for dx in [-10000.0,-64,-1,0,1,64,10000] { for dy in [-10000.0,-64,-1,0,1,64,10000] {
                    let result = TouchResizePolicy.resized(start,translation:CGSize(width:dx,height:dy),canvas:surface,surface:surface,circle:circle)
                    cases += 1
                    check(valid(result),"resize must preserve valid bounds")
                    check(close(result.x,start.x) && close(result.y,start.y),"resize keeps origin")
                    if circle {
                        check(close(result.width/start.width,result.height/start.height),"circle bounds scale uniformly")
                        check(min(result.width*width,result.height*height) >= min(32,start.width*width,start.height*height)-1e-9,"circle retains its current small size or 32-point minimum")
                    } else {
                        check(result.width*width >= min(32,start.width*width)-1e-9 && result.height*height >= min(32,start.height*height)-1e-9,"rectangle retains its current small size or 32-point minimum")
                    }
                    if dx == 0 && dy == 0 {
                        check(close(result.width,start.width) && close(result.height,start.height),"zero translation preserves imported bounds")
                    }
                    if dx <= 0 && dy <= 0 {
                        check(result.width <= start.width+1e-10 && result.height <= start.height+1e-10,"shrinking cannot enlarge a small edge control")
                    }
                }}}
            }}}}
            // Equal-sized physical circle stays round, grows normally away from
            // edges, and stops as soon as either canvas edge is reached.
            let physicalSide = max(64,0.015*max(width,height))
            let circle = TouchBox(x:0.2,y:0.2,width:physicalSide/width,height:physicalSide/height)
            let grown = TouchResizePolicy.resized(circle,translation:CGSize(width:24,height:24),canvas:surface,surface:surface,circle:true)
            check(close(grown.width*width,physicalSide+24) && close(grown.height*height,physicalSide+24),"existing round circle growth is retained")
            let edgeSide = max(24,0.015*max(width,height))
            let edge = TouchBox(x:1-edgeSide/width,y:1-edgeSide/height,width:edgeSide/width,height:edgeSide/height)
            let unchanged = TouchResizePolicy.resized(edge,translation:CGSize(width:1,height:1),canvas:surface,surface:surface,circle:true)
            check(close(unchanged.width,edge.width) && close(unchanged.height,edge.height),"small round corner stays valid")
            // Portrait preview is scaled; its gesture delta must normalize to
            // the same full-display layout as an actual-size landscape canvas.
            let full = TouchResizePolicy.resized(circle,translation:CGSize(width:24,height:24),canvas:surface,surface:surface,circle:false)
            let preview = TouchResizePolicy.resized(circle,translation:CGSize(width:12,height:12),canvas:CGSize(width:width/2,height:height/2),surface:surface,circle:false)
            check(full == preview,"scaled preview and actual-size canvas agree")
        }
        // Validate through the actual imported schema rather than a stricter
        // test-only approximation. Existing rounded edge overflow is accepted.
        var toleranceCases = 0
        for shape in ["rectangle","circle"] {
            for box in [TouchBox(x:0.985005,y:0.4,width:0.015,height:0.12),
                        TouchBox(x:0.4,y:0.985005,width:0.12,height:0.015),
                        TouchBox(x:0.985005,y:0.985005,width:0.015,height:0.015)] {
                var imported = TouchProfile.factory(width:852,height:393)
                let i = imported.controls.firstIndex { $0.kind == "jump" }!
                imported.controls[i].box = box; imported.controls[i].shape = shape
                imported = try TouchProfile.decode(imported.encoded())
                check(imported.validation() == nil,"actual schema accepts rounded edge import")
                for dx in [-10000.0,-1,0,1,10000] { for dy in [-10000.0,-1,0,1,10000] {
                    let resized = TouchResizePolicy.resized(box,translation:CGSize(width:dx,height:dy),canvas:CGSize(width:852,height:393),surface:CGSize(width:852,height:393),circle:shape == "circle")
                    var changed = imported;changed.controls[i].box = resized
                    check(changed.validation() == nil,"resize preserves actual schema-valid rounded import")
                    _ = try TouchProfile.decode(changed.encoded())
                    check(resized.x+resized.width <= max(1,box.x+box.width)+1e-12 && resized.y+resized.height <= max(1,box.y+box.height)+1e-12,"rounding overflow never increases")
                    if dx == 0 && dy == 0 { check(resized == box,"zero drag preserves exact rounded import") }
                    toleranceCases += 1
                }}
            }
        }
        // These are valid imported profiles, not a new wide-screen factory
        // feature. Preserve schema minimums under a larger resize canvas.
        var wideSchemaCases = 0
        for (width,height) in [(3840.0,2160.0),(2560,1440),(7680,4320)] {
            for shape in ["rectangle","circle"] {
                for box in [TouchBox(x:0.4,y:0.4,width:0.03,height:0.03),
                            TouchBox(x:0.985,y:0.4,width:0.015,height:0.03),
                            TouchBox(x:0.4,y:0.985,width:0.03,height:0.015),
                            TouchBox(x:0.1,y:0.1,width:0.7480560063881185,height:0.8)] {
                    var imported = TouchProfile.factory(width:852,height:393)
                    let i = imported.controls.firstIndex { $0.kind == "jump" }!
                    imported.controls[i].box=box;imported.controls[i].shape=shape
                    imported = try TouchProfile.decode(imported.encoded())
                    for dx in [-10000.0,-1,0,1,10000] { for dy in [-10000.0,-1,0,1,10000] {
                        var changed = imported
                        changed.controls[i].box=TouchResizePolicy.resized(box,translation:CGSize(width:dx,height:dy),canvas:CGSize(width:width,height:height),surface:CGSize(width:width,height:height),circle:shape == "circle")
                        check(changed.validation() == nil,"wide canvas preserves actual schema minimums")
                        _ = try TouchProfile.decode(changed.encoded())
                        wideSchemaCases += 1
                    }}
                }
            }
        }
        print("PASS_TOUCH_RESIZE59 checks=\(checks) cases=\(cases) tolerance_cases=\(toleranceCases) wide_schema_cases=\(wideSchemaCases)")
    }
}
