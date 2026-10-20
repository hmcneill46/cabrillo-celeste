import Foundation

// Compile this control with the frozen50 native files, not the56 overlay.
@main struct DependencyMirrorOriginalControl {
    static func main() throws {
        let payload = Data("""
        {"url":"https://gamebanana.com/mmdl/42","bytes":10,"hashes":["0123456789abcdef"],"modules":[],"mirrorName":"replacement_56"}
        """.utf8)
        let candidate = try JSONDecoder().decode(DownloadCandidate.self, from: payload)
        let original = URL(string: candidate.url)!
        let available = URL(string: "https://banana-mirror-mods.celestemods.com/replacement_56.zip")!
        let target = URL(fileURLWithPath: CommandLine.arguments[1]).appendingPathComponent("original-control.part")
        var attempts = [String]()
        do {
            try InstallDownload.fetchWithMirrors(original, destination: target, cancellation: InstallCancellation(), retry: { _, _ in }, transport: { url in
                attempts.append(url.absoluteString)
                guard url == available else { throw LibraryError("HTTP 404: this fixture serves only its published MirrorName") }
                try Data("available".utf8).write(to: target)
            })
            throw LibraryError("The original differing-MirrorName failure was not reproduced")
        } catch {
            guard attempts == [original.absoluteString, "https://banana-mirror-mods.celestemods.com/42.zip", "https://celestemodupdater.0x0a.de/banana-mirror/42.zip"],
                  !FileManager.default.fileExists(atPath: target.path) else { throw error }
        }
        let result: [String: Any] = ["status": "PASS_ORIGINAL_MIRRORNAME_404_REPRODUCED", "attempts": attempts,
            "publishedMirrorNeverRequested": !attempts.contains(available.absoluteString), "partialFileAbsent": true,
            "networkUsed": false, "gameOrAdapterExecuted": false]
        try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]).write(to: URL(fileURLWithPath: CommandLine.arguments[1]).appendingPathComponent("original-control.json"))
        print("PASS_ORIGINAL_MIRRORNAME_404_REPRODUCED")
    }
}
