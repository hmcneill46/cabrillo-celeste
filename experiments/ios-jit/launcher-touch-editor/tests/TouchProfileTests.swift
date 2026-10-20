import Foundation

@main enum TouchProfileTests {
    static var checks = 0
    static func check(_ value: Bool, _ name: String) { precondition(value,name);checks += 1;print("SWIFT_TOUCH_CHECK \(name)") }
    static func main() throws {
        var fixtures = [[String:Any]]()
        for (w,h,safe,pad) in [(960.0,540.0,[0.0,0,0,0],false),(932,430,[0,59,21,59],false),(852,393,[0,59,21,59],false),(1180,820,[0,0,20,0],true)] {
            let profile = TouchProfile.factory(width:w,height:h,top:safe[0],left:safe[1],bottom:safe[2],right:safe[3],pad:pad)
            check(profile.validation() == nil,"factory valid \(w)")
            var edge = profile; edge.controls[2].shape = "rectangle"; edge.controls[2].x = 0; edge.controls[2].y = 0
            check(edge.validation() == nil && edge.controls[2].contains(1,1,width:w,height:h),"edge outside safe area and game image remains usable")
            edge.controls[2].x = 1-edge.controls[2].width;edge.controls[2].y = 1-edge.controls[2].height
            edge.mirror();check(edge.validation() == nil,"mirror preserves a flush edge")
            check(try TouchProfile.decode(profile.encoded()) == profile,"JSON preserves all options")
            var mirror = profile;mirror.mirror();mirror.mirror()
            check(zip(mirror.controls,profile.controls).allSatisfy {abs($0.x-$1.x)<1e-12 && $0.kind == $1.kind},"mirror is reversible")
            var split = profile;split.preset("split");check(split.validation() == nil,"split preset valid")
            var swipe = profile;swipe.preset("swipe");check(swipe.validation() == nil && swipe.swipe,"swipe preset valid")
            var invalid = profile;invalid.controls[0].x = .nan;check(invalid.validation() != nil,"nonfinite dimensions rejected")
            invalid = profile;invalid.controls.removeAll {$0.kind == "pause"};check(invalid.validation() != nil,"cannot remove last pause")
            invalid = profile;invalid.controls[0].id = invalid.controls[1].id;check(invalid.validation() != nil,"duplicate identifiers rejected")
            var samples = [[String:Any]]()
            for orientation in 0...3 {for swap in [false,true] {for shape in ["circle","rectangle"] {
                let item = TouchItem(id:"split",kind:"split",shape:shape,x:0.2,y:0.2,width:0.4,height:0.6,split:orientation,swap:swap)
                for x in [0.21,0.3,0.4,0.59,0.7] {for y in [0.21,0.35,0.5,0.79] {
                    samples.append(["control":try JSONSerialization.jsonObject(with:JSONEncoder().encode(item)),"x":x*w,"y":y*h,
                        "hit":item.contains(x*w,y*h,width:w,height:h),"action":item.splitAction(x*w,y*h,width:w,height:h)])
                }}
            }}}
            for rightEdge in [false,true] {for bottomEdge in [false,true] {
                let item = TouchItem(id:"edge",kind:"jump",shape:"rectangle",x:rightEdge ? 0.92 : 0,y:bottomEdge ? 0.88 : 0,width:0.08,height:0.12)
                let px = rightEdge ? w-0.5 : 0.5, py = bottomEdge ? h-0.5 : 0.5
                samples.append(["control":try JSONSerialization.jsonObject(with:JSONEncoder().encode(item)),"x":px,"y":py,"hit":true,"action":"jump"])
            }}
            fixtures.append(["width":w,"height":h,"safe":safe,"pad":pad,"profile":try JSONSerialization.jsonObject(with:profile.encoded()),"splitSamples":samples])
        }
        let morro:[String:Any] = ["format":"Celeste Touch Layout","version":1,"phoneProfile":"D3|2|0|1|1|2|1|1|0.02,0.5,0.2,0.4|0,0.3,0.45,0.7|0.8,0.7,0.15,0.25|0.6,0.5,0.15,0.25|0.6,0.3,0.38,0.68|0.6,0.04,0.3,0.15|0.46,0.04,0.07,0.1|0.02,0.04,0.07,0.1|100,100,80,90,60,70,100,100|1|1,5,1,100,0.4,0.4,0.08,0.15|1,6,0,100,0.4,0.65,0.08,0.15|0,2,1,100,0.44,0.44,0.12,0.12|0,2,1,100,0.44,0.44,0.12,0.12"]
        let imported = try TouchProfile.imported(JSONSerialization.data(withJSONObject:morro),pad:false,width:932,height:430)
        check(imported.controls.contains {$0.kind == "crouchDash"} && imported.controls.contains {$0.kind == "quickRestart"},"Morro extra actions import")
        check(imported.controls.first {$0.kind == "split"}?.split == 2 && imported.controls.first {$0.kind == "split"}?.swap == false,"Morro split settings import")
        for bad in [Data(),Data("{}".utf8),Data(repeating:32,count:32769)] {
            var rejected = false;do {_ = try TouchProfile.imported(bad,pad:false,width:932,height:430)} catch {rejected = true};check(rejected,"invalid import rejected")
        }
        let output = URL(fileURLWithPath:CommandLine.arguments[1]);try JSONSerialization.data(withJSONObject:fixtures,options:[.sortedKeys]).write(to:output)
        print("PASS_SWIFT_TOUCH_PROFILE checks=\(checks)")
    }
}
