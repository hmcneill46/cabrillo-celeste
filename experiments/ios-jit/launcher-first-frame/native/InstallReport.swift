import Foundation

struct InstallReport: Codable {
    struct Download: Codable {
        let key: String
        var name: String
        var status: String
        var detail: String?
    }
    let schema: Int
    let id: String
    let started: Date
    var finished: Date?
    var outcome: String
    var message: String
    var applicationState: String
    var changes: [InstallJournal.Change]
    var downloads: [Download]
    var commitStarted: Bool

    init(plan: DependencyPlan) {
        schema = 1; id = plan.id; started = Date(); outcome = "inProgress"
        message = "Preparing the reviewed changes."; applicationState = "unchanged"; changes = []
        downloads = plan.downloads.map { Download(key: $0.key, name: $0.title, status: "notAttempted", detail: nil) }
        commitStarted = false
    }
    mutating func mark(_ source: DownloadCandidate, _ status: String, detail: String? = nil) {
        guard let index = downloads.firstIndex(where: { $0.key == source.key }) else { return }
        downloads[index].name = source.title; downloads[index].status = status; downloads[index].detail = detail
    }
    mutating func end(_ outcome: String, message: String) {
        self.outcome = outcome; self.message = message; finished = Date()
        for index in downloads.indices where ["downloading", "verifying"].contains(downloads[index].status) {
            downloads[index].status = outcome == "cancelled" ? "cancelled" : "failed"
            downloads[index].detail = message
        }
    }
    var json: [String: Any] { (try? JSONSerialization.jsonObject(with: canonicalData(self)) as? [String: Any]) ?? [:] }
    static func file(_ profile: URL) -> URL { profile.appendingPathComponent("LauncherReports/last-installation.json") }
    static func read(_ profile: URL) throws -> InstallReport {
        var report = try JSONDecoder().decode(Self.self, from: InstallJournal.boundedRead(file(profile), limit: 2_097_152))
        guard report.schema == 1, report.downloads.count <= 1024, report.changes.count <= 65536 else { throw LibraryError("The saved installation report is invalid.") }
        if report.outcome == "inProgress" {
            report.outcome = "interrupted"; report.applicationState = "unconfirmed"
            report.message = "The previous installation stopped before a final result was recorded. Resolve dependencies to check the selection; export diagnostics if recovery cannot complete."
            for index in report.downloads.indices {
                if report.downloads[index].status == "verified" { report.downloads[index].status = "verificationRecorded" }
                // No saved terminal result proves whether pending work was started.
                else if ["notAttempted", "downloading", "verifying"].contains(report.downloads[index].status) { report.downloads[index].status = "interrupted" }
            }
        }
        return report
    }
    func save(_ profile: URL) throws {
        let data = try canonicalData(self)
        guard data.count <= 2_097_152 else { throw LibraryError("The installation report exceeds the saved-report limit; its transaction receipt is retained.") }
        try InstallJournal.directory(Self.file(profile).deletingLastPathComponent())
        try InstallJournal.atomicWrite(data, to: Self.file(profile))
    }
}
