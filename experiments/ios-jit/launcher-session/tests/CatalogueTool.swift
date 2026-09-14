import Foundation
@main struct CatalogueTool {
    static func main() throws {
        let root=URL(fileURLWithPath:CommandLine.arguments[1]);let library=ModLibrary(profile:root)
        if CommandLine.arguments.count>2 && CommandLine.arguments[2]=="normal" {
            try library.setAllEnabled(false)
            if CommandLine.arguments.count>3 { let row=try library.importZIP(URL(fileURLWithPath:CommandLine.arguments[3]));try library.setEnabled(true,filename:row.filename) }
        } else { try library.setAllEnabled(true) }
        let result=try library.snapshot(force:true,prepare:true)
        print("PASS_CATALOGUE_PREFLIGHT \(result["enabledCount"]!) enabled / \(result["installedCount"]!) installed")
    }
}
