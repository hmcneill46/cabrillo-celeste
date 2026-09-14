import Foundation
@main struct RealUpdateTests {
    static func main() throws {
        let folder=URL(fileURLWithPath:CommandLine.arguments[1]), service=URL(fileURLWithPath:CommandLine.arguments[2]), pinFile=URL(fileURLWithPath:CommandLine.arguments[3])
        let pins=try JSONDecoder().decode([DownloadCandidate].self,from:Data(contentsOf:pinFile))
        let library=ModLibrary(profile:folder.appendingPathComponent("Profile"),specialPins:Dictionary(uniqueKeysWithValues:pins.flatMap { p in p.modules.map { ($0.name,p.pinnedSHA256!) } }))
        let before=try LibraryInventory.read(library)
        let u=try Data(contentsOf:service.appendingPathComponent("updates.yaml")),g=try Data(contentsOf:service.appendingPathComponent("graph.yaml"))
        let db=try DependencyDatabase(updates:u,graph:g,provenance:["updatesSHA256":digestData(u),"graphSHA256":digestData(g),"fetched":"2026-09-12 pinned service snapshot"],pins:pins)
        let installer=DependencyInstaller(library:library,pins:pins,indexProvider:{_ in db})
        var history:[[String:Any]]=[]
        func wait(_ action:()->Void) throws -> [String:Any] {
            var result:[String:Any]?
            installer.update={ state in
                if state["phase"] as? String != "downloading" {history.append(state)}
                if state["active"] as? Bool == false {result=state}
            }
            action();let until=Date().addingTimeInterval(240)
            while result == nil && Date()<until {RunLoop.current.run(until:Date().addingTimeInterval(0.02))}
            guard let result else {throw LibraryError("Timed out")}
            if result["phase"] as? String == "failed" {throw LibraryError(result["message"] as? String ?? "Failed")}
            return result
        }
        var state=try wait {installer.checkUpdates()}
        let updates=(state["updates"] as? [[String:Any]] ?? []).filter {$0["canUpdate"] as? Bool == true}
        guard updates.count==2 else {throw LibraryError("Expected the two runtime-compatible snapshot updates; got \(updates.count)")}
        state=try wait {installer.planUpdates(updates.compactMap {$0["filename"] as? String})}
        for _ in 0..<4 {
            guard let plan=state["plan"] as? [String:Any],plan["canApply"] as? Bool == true,let id=plan["id"] as? String else {throw LibraryError("Plan blocked: \(state)")}
            state=try wait {installer.apply(planID:id)}
            if state["phase"] as? String == "complete" {break}
        }
        guard state["phase"] as? String == "complete" else {throw LibraryError("Did not finish")}
        let after=try LibraryInventory.read(library),selection=try library.snapshot(force:true,prepare:true)
        guard selection["canRun"] as? Bool == true,after.active.count==before.active.count,after.archives.count==before.archives.count+2 else {throw LibraryError("Final selection differs")}
        for original in before.archives {guard after.archives.contains(where:{$0.filename==original.filename && $0.digest==original.digest}) else {throw LibraryError("Original archive changed")}}
        let out:[String:Any]=["status":"PASS_REAL_TWO_MOD_UPDATE_TRANSACTION","updates":updates,"index":db.provenance,"beforeRevision":before.revision,"afterRevision":after.revision,"originalArchivesPreserved":before.archives.count,"selectedArchiveCount":after.active.count,"selection":selection,"history":history,"receipts":InstallJournal.diagnostics(profile:library.profile)]
        try JSONSerialization.data(withJSONObject:out,options:[.sortedKeys,.prettyPrinted]).write(to:folder.appendingPathComponent("result.json"))
        print("PASS_REAL_TWO_MOD_UPDATE_TRANSACTION")
    }
}
