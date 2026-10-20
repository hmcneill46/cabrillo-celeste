import Foundation

enum CatalogueSort: String, CaseIterable, Identifiable, Codable {
    case downloads, latest, updated, likes, views
    var id: String { rawValue }
    var title: String {
        switch self { case .downloads: return "Most downloaded"; case .latest: return "Newest"; case .updated: return "Recently updated"; case .likes: return "Most liked"; case .views: return "Most viewed" }
    }
}

struct CatalogueQuery: Hashable {
    var search = ""
    var sort = CatalogueSort.downloads
    var category: String?
    var subcategory: String?
    var term: String { String(search.trimmingCharacters(in: .whitespacesAndNewlines).prefix(100)) }
    func url(page: Int) throws -> URL {
        guard (1...500).contains(page) else { throw LibraryError("Choose a category to narrow this list.") }
        var c = URLComponents(string: "https://maddie480.ovh/celeste/" + (term.isEmpty ? "gamebanana-list" : "gamebanana-search"))!
        if !term.isEmpty { c.queryItems = [URLQueryItem(name: "q", value: term)] }
        else {
            c.queryItems = [URLQueryItem(name: "page", value: String(page)), URLQueryItem(name: "sort", value: sort.rawValue)]
            for (name, value) in [("category", category), ("subcategory", subcategory)] {
                if let value { guard CatalogueSafety.categoryID(value) else { throw LibraryError("The category is not valid. Reset filters and try again.") }; c.queryItems!.append(URLQueryItem(name: name, value: value)) }
            }
        }
        return c.url!
    }
}

enum CatalogueSafety {
    static func categoryID(_ s: String) -> Bool { s.range(of: "^GameBanana_(Mod|Tool|Wip)_([0-9]+|Root)$", options: .regularExpression) != nil }
    static func page(_ text: String) -> URL? {
        guard let u = validDownloadURL(text), u.host == "gamebanana.com", u.query == nil,
              u.path.range(of: "^/(mods|tools|wips)/[1-9][0-9]*$", options: .regularExpression) != nil else { return nil }; return u
    }
    static func fileID(_ text: String) -> String? {
        guard let u = validDownloadURL(text), u.host == "gamebanana.com", u.query == nil,
              u.path.range(of: "^/(mmdl|dl)/[1-9][0-9]*$", options: .regularExpression) != nil,
              let n = UInt32(u.lastPathComponent), n > 0 else { return nil }; return String(n)
    }
    static func media(_ text: String) -> URL? {
        guard let u = validDownloadURL(text), ["images.gamebanana.com", "banana-mirror-images.celestemods.com", "celestemodupdater.0x0a.de"].contains(u.host ?? ""), u.query == nil else { return nil }
        if u.host == "celestemodupdater.0x0a.de" && !u.path.hasPrefix("/banana-mirror-images/") { return nil }
        guard ["jpg", "jpeg", "png", "webp"].contains(u.pathExtension.lowercased()) else { return nil }; return u
    }
    static func transport(_ u: URL) -> Bool {
        guard validDownloadURL(u.absoluteString) != nil else { return false }
        return ["maddie480.ovh", "gamebanana.com", "everestapi.github.io"].contains(u.host ?? "") || media(u.absoluteString) != nil
    }
    // Inert text only. No HTML/WebKit renderer, scripts, external style or attachment loading.
    static func text(_ value: Any?, limit: Int = 600) -> String {
        var s = String((value as? String ?? "").prefix(200_000))
        s = s.replacingOccurrences(of: "(?is)<(script|style|iframe)\\b[^>]*>.*?</\\1\\s*>", with: "", options: .regularExpression)
        s = s.replacingOccurrences(of: "(?i)<\\s*(br\\s*/?|/p|/div|/li|/h[1-6])\\s*>", with: "\n", options: .regularExpression)
        s = s.replacingOccurrences(of: "<[^>]*>", with: "", options: .regularExpression)
        for (a,b) in [("&nbsp;", " "), ("&quot;", "\""), ("&#39;", "'"), ("&apos;", "'"), ("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&")] { s = s.replacingOccurrences(of: a, with: b) }
        let regex = try! NSRegularExpression(pattern: "&#(x[0-9a-fA-F]+|[0-9]+);")
        for m in regex.matches(in: s, range: NSRange(s.startIndex..., in: s)).reversed() {
            guard let r = Range(m.range(at: 1), in: s), let whole = Range(m.range, in: s) else { continue }
            let v = String(s[r]), n = v.hasPrefix("x") ? UInt32(v.dropFirst(), radix: 16) : UInt32(v)
            if let n, let scalar = UnicodeScalar(n), n >= 32 { s.replaceSubrange(whole, with: String(scalar)) }
        }
        s = s.replacingOccurrences(of: "[\\t ]+", with: " ", options: .regularExpression).replacingOccurrences(of: "\\n[ \\n]*\\n", with: "\n\n", options: .regularExpression)
        return String(s.unicodeScalars.filter { $0.value >= 32 || $0.value == 10 }.prefix(limit)).trimmingCharacters(in: .whitespacesAndNewlines)
    }
    static func count(_ value: Any?) -> Int64? { guard let n = value as? NSNumber, n.doubleValue.isFinite, n.doubleValue >= 0, n.doubleValue <= 1e13 else { return nil }; return n.int64Value }
}

struct CatalogueFile: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let description: String
    let url: String
    let bytes: UInt64
    let date: Date?
    let hasMetadata: Bool
    let latest: Bool
    var selectable: Bool { hasMetadata && latest && bytes > 0 && bytes <= 4_294_967_296 && name.lowercased().hasSuffix(".zip") }
    init?(_ row: [String: Any]) {
        guard let url = row["URL"] as? String, let id = CatalogueSafety.fileID(url), let bytes = CatalogueSafety.count(row["Size"]) else { return nil }
        self.id = id; self.url = url; self.bytes = UInt64(bytes)
        name = CatalogueSafety.text(row["Name"], limit: 240); description = CatalogueSafety.text(row["Description"], limit: 2000)
        date = CatalogueSafety.count(row["CreatedDate"]).map { Date(timeIntervalSince1970: Double($0)) }
        hasMetadata = row["HasEverestYaml"] as? Bool == true || row["HasEverestYaml"] as? String == "true"
        latest = row["IsLatestVersion"] as? Bool == true || row["IsLatestVersion"] as? String == "true"
    }
}

struct CatalogueEntry: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let author: String
    let summary: String
    let body: String
    let category: String
    let subcategory: String
    let images: [String]
    let files: [CatalogueFile]
    let downloads: Int64?
    let likes: Int64?
    let views: Int64?
    let created: Date?
    let updated: Date?
    var pageURL: URL { URL(string: id)! }
    // Some real helpers (including Memorial Helper) were published as Tools.
    // Archive metadata and the verified index decide installability, not taxonomy.
    var installable: Bool { files.contains(where: \.selectable) }
    init?(_ row: [String: Any]) {
        guard let raw = row["PageURL"] as? String, let page = CatalogueSafety.page(raw) else { return nil }
        id = page.absoluteString; name = CatalogueSafety.text(row["Name"], limit: 240)
        guard !name.isEmpty else { return nil }
        author = CatalogueSafety.text(row["Author"], limit: 240); summary = CatalogueSafety.text(row["Description"])
        body = CatalogueSafety.text(row["Text"], limit: 30_000)
        category = CatalogueSafety.text(row["CategoryName"], limit: 100); subcategory = CatalogueSafety.text(row["SubcategoryName"], limit: 100)
        var seen = Set<String>()
        let originals = (row["Screenshots"] as? [String] ?? []).compactMap { CatalogueSafety.media($0)?.absoluteString }
        images = (originals.isEmpty ? (row["MirroredScreenshots"] as? [String] ?? []).compactMap { CatalogueSafety.media($0)?.absoluteString } : originals).filter { seen.insert($0).inserted }.prefix(8).map { $0 }
        seen = []
        files = (row["Files"] as? [[String: Any]] ?? []).prefix(128).compactMap(CatalogueFile.init).filter { seen.insert($0.id).inserted }
        downloads = CatalogueSafety.count(row["Downloads"]); likes = CatalogueSafety.count(row["Likes"]); views = CatalogueSafety.count(row["Views"])
        created = CatalogueSafety.count(row["CreatedDate"]).map { Date(timeIntervalSince1970: Double($0)) }
        updated = CatalogueSafety.count(row["UpdatedDate"]).map { Date(timeIntervalSince1970: Double($0)) }
    }
    static func parse(_ data: Data) throws -> [Self] {
        guard data.count <= 4_194_304, let rows = try JSONSerialization.jsonObject(with: data) as? [[String: Any]], rows.count <= 100 else { throw LibraryError("The catalogue returned an unexpected page. Try refreshing later.") }
        var seen = Set<String>(); let values = rows.compactMap(Self.init).filter { seen.insert($0.id).inserted }
        guard rows.isEmpty || !values.isEmpty else { throw LibraryError("This catalogue page contains no valid Celeste entries.") }; return values
    }
}

struct CatalogueCategory: Identifiable, Hashable {
    let id: String
    let name: String
    let count: Int64?
    var children: [CatalogueCategory] = []
    static func parse(_ categories: Data, subcategories: Data) throws -> [Self] {
        guard categories.count <= 262_144, subcategories.count <= 262_144,
              let rows = try ManifestYAML().parse(categories).list, rows.count <= 100,
              let groups = try ManifestYAML().parse(subcategories).map else { throw LibraryError("Categories could not be read. You can still browse or search.") }
        let sub = groups.values.compactMap(\.map).reduce(into: [String: YAMLValue]()) { $0.merge($1) { old, _ in old } }
        var seen = Set<String>()
        return rows.compactMap { value in
            guard let row = value.map, let id = row["categoryid"]?.text, CatalogueSafety.categoryID(id), seen.insert(id).inserted else { return nil }
            var childSeen = Set<String>()
            let children: [Self] = (sub[id]?.list ?? []).prefix(100).compactMap { value in
                guard let child = value.map, let key = child["id"]?.text, CatalogueSafety.categoryID(key), childSeen.insert(key).inserted else { return nil }
                return Self(id: key, name: CatalogueSafety.text(child["name"]?.text, limit: 100), count: child["count"]?.text.flatMap(Int64.init))
            }
            return Self(id: id, name: CatalogueSafety.text(row["formatted"]?.text, limit: 100), count: row["count"]?.text.flatMap(Int64.init), children: children)
        }
    }
}

struct CatalogueSelection: Codable {
    let pageURL: String
    let fileIDs: [String]
    func candidates(in db: DependencyDatabase) throws -> [DownloadCandidate] {
        guard CatalogueSafety.page(pageURL) != nil, !fileIDs.isEmpty, fileIDs.count <= 32,
              Set(fileIDs).count == fileIDs.count, fileIDs.allSatisfy({ id in UInt32(id).map { $0 > 0 && String($0) == id } ?? false }) else { throw LibraryError("Choose the mod files you want to install.") }
        let all = Array(db.indexedByName.values) + db.earlierByName.values.flatMap { $0 }
        return try fileIDs.map { id in
            let matches = Dictionary(all.filter { CatalogueSafety.fileID($0.url) == id }.map { ($0.key, $0) }, uniquingKeysWith: { a, _ in a }).values
            guard matches.count == 1, let source = matches.first else { throw LibraryError("File \(id) is not in the verified mod index. Refresh Browse and try again, or download a compatible ZIP from GameBanana and use Import mod ZIPs. Nothing was installed.") }
            return source
        }
    }
}

struct GameBananaDetails {
    let author: String
    let studios: [String]
    let body: String
    let images: [String]
    let downloads: Int64?
    let likes: Int64?
    let views: Int64?
    let updated: Date?
    let availableFiles: Set<String>
    static func apiURL(_ entry: CatalogueEntry) -> URL {
        let type = entry.pageURL.path.hasPrefix("/tools/") ? "Tool" : entry.pageURL.path.hasPrefix("/wips/") ? "Wip" : "Mod"
        return URL(string: "https://gamebanana.com/apiv11/\(type)/\(entry.pageURL.lastPathComponent)/ProfilePage")!
    }
    init(_ data: Data, entry: CatalogueEntry) throws {
        guard data.count <= 4_194_304, let row = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              (row["_aGame"] as? [String: Any])?["_idRow"] as? Int == 6460,
              String((row["_idRow"] as? Int) ?? 0) == entry.pageURL.lastPathComponent,
              row["_bIsPrivate"] as? Bool != true, row["_bIsTrashed"] as? Bool != true, row["_bIsWithheld"] as? Bool != true else { throw LibraryError("The live mod page is unavailable.") }
        author = CatalogueSafety.text((row["_aSubmitter"] as? [String: Any])?["_sName"], limit: 240)
        studios = (row["_aContributingStudios"] as? [[String: Any]] ?? []).prefix(10).map { CatalogueSafety.text($0["_sName"], limit: 200) }.filter { !$0.isEmpty }
        body = CatalogueSafety.text(row["_sText"], limit: 30_000)
        images = (((row["_aPreviewMedia"] as? [String: Any])?["_aImages"] as? [[String: Any]]) ?? []).prefix(8).compactMap { image in
            guard image["_sType"] as? String == "screenshot", let base = image["_sBaseUrl"] as? String,
                  let file = (image["_sFile800"] ?? image["_sFile530"] ?? image["_sFile"]) as? String, !file.contains("/") else { return nil }
            return CatalogueSafety.media(base + "/" + file)?.absoluteString
        }
        downloads = CatalogueSafety.count(row["_nDownloadCount"]); likes = CatalogueSafety.count(row["_nLikeCount"]); views = CatalogueSafety.count(row["_nViewCount"])
        updated = CatalogueSafety.count(row["_tsDateUpdated"]).map { Date(timeIntervalSince1970: Double($0)) }
        availableFiles = Set((row["_aFiles"] as? [[String: Any]] ?? []).prefix(128).compactMap { file in
            guard file["_bIsArchived"] as? Bool != true, file["_sAvResult"] as? String != "infected", let id = file["_idRow"] as? Int, id > 0 else { return nil }; return String(id)
        })
    }
}
