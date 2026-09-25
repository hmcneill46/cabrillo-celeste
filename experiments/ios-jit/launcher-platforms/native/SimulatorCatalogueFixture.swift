#if targetEnvironment(simulator)
import Foundation

// These responses are supplied only in the simulator's Documents by XCUITest.
// The device IPA has no fixture transport or catalogue snapshots.
enum SimulatorCatalogueFixture {
    static func make(root: URL) -> CatalogueProvider? {
        let args = ProcessInfo.processInfo.arguments
        guard args.contains("--catalogue-ui-fixture") else { return nil }
        let folder = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("CatalogueFixtures")
        return CatalogueProvider(root: root.appendingPathComponent("simulator-fixture")) { url, _, image in
            if args.contains("--catalogue-ui-offline") { throw URLError(.notConnectedToInternet) }
            if image { return try await CatalogueTransfer.get(url, limit: 4_194_304, image: true) }
            let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems ?? []
            let query = items.first { $0.name == "q" }?.value ?? ""
            if query == "slow" { try await Task.sleep(for: .seconds(20)) }
            let name: String
            if url.path.hasSuffix("gamebanana-categories") { name = "categories.yaml" }
            else if url.path.hasSuffix("gamebanana-subcategories") { name = "subcategories.yaml" }
            else if url.path.contains("ProfilePage") { name = "profile.json" }
            else if query == "zzzznomatch" { return CatalogueResponse(data: Data("[]".utf8), date: Date(), total: nil) }
            else if !query.isEmpty { name = "search.json" }
            else if items.first(where: { $0.name == "page" })?.value == "2" { name = "page2.json" }
            else { name = "list.json" }
            let data = try InstallJournal.boundedRead(folder.appendingPathComponent(name), limit: 4_194_304)
            return CatalogueResponse(data: data, date: Date(), total: name == "list.json" ? 40 : name == "page2.json" ? 40 : nil)
        }
    }
}
#endif
