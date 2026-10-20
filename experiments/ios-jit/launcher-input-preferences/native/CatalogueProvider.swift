import Foundation

struct CatalogueResponse: Codable {
    let data: Data
    let date: Date
    let total: Int?
    var cached = false
    var stale = false
}

// Four small transfers at most, shared by pages, details and thumbnails.
actor CatalogueSlots {
    private var available: Int
    init(limit: Int = 4) { available = limit }
    private var queue: [(UUID, CheckedContinuation<Void, Error>)] = []
    func acquire() async throws {
        let id = UUID()
        try await withTaskCancellationHandler {
            try Task.checkCancellation()
            if available > 0 { available -= 1; return }
            try await withCheckedThrowingContinuation { continuation in queue.append((id, continuation)) }
        } onCancel: { Task { await self.cancel(id) } }
    }
    private func cancel(_ id: UUID) { if let i = queue.firstIndex(where: { $0.0 == id }) { queue.remove(at: i).1.resume(throwing: CancellationError()) } }
    func release() { if !queue.isEmpty { queue.removeFirst().1.resume() } else { available += 1 } }
}

final class CatalogueTransfer: NSObject, URLSessionDataDelegate, @unchecked Sendable {
    static let slots = CatalogueSlots()
    private let lock = NSLock()
    private var cancelled = false
    private var task: URLSessionDataTask?
    private var continuation: CheckedContinuation<CatalogueResponse, Error>?
    private var data = Data()
    private var response: HTTPURLResponse?
    private let limit: Int
    private let image: Bool
    init(limit: Int, image: Bool) { self.limit = limit; self.image = image }
    static func get(_ url: URL, limit: Int, image: Bool = false) async throws -> CatalogueResponse {
        try await slots.acquire()
        do {
            try Task.checkCancellation()
            let result = try await CatalogueTransfer(limit: limit, image: image).perform(url)
            await slots.release(); return result
        } catch { await slots.release(); throw error }
    }
    private func cancel() { lock.lock(); cancelled = true; let task = task; lock.unlock(); task?.cancel() }
    private func perform(_ url: URL) async throws -> CatalogueResponse {
        guard CatalogueSafety.transport(url) else { throw LibraryError("This catalogue address is not supported.") }
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                lock.lock()
                guard !cancelled else { lock.unlock(); continuation.resume(throwing: CancellationError()); return }
                self.continuation = continuation
                let c = URLSessionConfiguration.ephemeral
                c.urlCache = nil; c.httpShouldSetCookies = false; c.httpCookieStorage = nil
                c.timeoutIntervalForRequest = 15; c.timeoutIntervalForResource = 30; c.waitsForConnectivity = false
                c.allowsConstrainedNetworkAccess = !image
                let q = OperationQueue(); q.maxConcurrentOperationCount = 1
                let session = URLSession(configuration: c, delegate: self, delegateQueue: q)
                var request = URLRequest(url: url); request.setValue("CelesteIOS/0.15.0", forHTTPHeaderField: "User-Agent")
                let task = session.dataTask(with: request); self.task = task; lock.unlock(); task.resume()
            }
        } onCancel: { self.cancel() }
    }
    private func finish(_ session: URLSession, result: Result<CatalogueResponse, Error>) {
        lock.lock(); let done = continuation; continuation = nil; task = nil; lock.unlock()
        done?.resume(with: result); session.invalidateAndCancel()
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        guard let u = request.url, CatalogueSafety.transport(u) else { completionHandler(nil); finish(session, result: .failure(LibraryError("The catalogue redirected to an unsupported address."))); return }; completionHandler(request)
    }
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            completionHandler(.cancel); finish(session, result: .failure(LibraryError("The catalogue is unavailable (HTTP \((response as? HTTPURLResponse)?.statusCode ?? 0)). Try again shortly."))); return
        }
        guard response.expectedContentLength <= limit else { completionHandler(.cancel); finish(session, result: .failure(LibraryError("This catalogue response exceeds the size limit."))); return }
        self.response = http; completionHandler(.allow)
    }
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive chunk: Data) {
        guard data.count <= limit - chunk.count else { finish(session, result: .failure(LibraryError("This catalogue response exceeds the size limit."))); return }; data.append(chunk)
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error { finish(session, result: .failure(error)); return }
        guard response != nil, !data.isEmpty else { finish(session, result: .failure(LibraryError("The catalogue returned an empty response."))); return }
        let total = response?.value(forHTTPHeaderField: "X-Total-Count").flatMap(Int.init).flatMap { (0...100_000).contains($0) ? $0 : nil }
        finish(session, result: .success(CatalogueResponse(data: data, date: Date(), total: total)))
    }
}

actor CatalogueProvider {
    struct Cached: Codable { let schema: Int; let url: String; let hash: String; let response: CatalogueResponse }
    struct Flight { let id: UUID; let task: Task<CatalogueResponse, Error>; var users: Set<UUID> }
    let root: URL
    private let transport: (URL, Int, Bool) async throws -> CatalogueResponse
    private var flights: [String: Flight] = [:]
    private var backoff: [String: Date] = [:]
    private var suspended = false
    private var lastFailure: [String: Any] = [:]
    private(set) var counters: [String: Int] = [:]
    init(root: URL, transport: @escaping (URL, Int, Bool) async throws -> CatalogueResponse = { try await CatalogueTransfer.get($0, limit: $1, image: $2) }) { self.root = root; self.transport = transport }
    private func record(_ key: String) { counters[key, default: 0] += 1 }
    private func file(_ url: URL, image: Bool) -> URL { root.appendingPathComponent(image ? "images" : "pages").appendingPathComponent(digestData(Data(url.absoluteString.utf8)) + ".json") }
    private func cached(_ url: URL, image: Bool) -> CatalogueResponse? {
        guard let data = try? InstallJournal.boundedRead(file(url, image: image), limit: 6_000_000),
              let value = try? JSONDecoder().decode(Cached.self, from: data), value.schema == 1, value.url == url.absoluteString,
              digestData(value.response.data) == value.hash else { return nil }
        var r = value.response; r.cached = true; return r
    }
    private func store(_ response: CatalogueResponse, url: URL, image: Bool) throws {
        let path = file(url, image: image), folder = path.deletingLastPathComponent()
        try InstallJournal.directory(folder)
        try InstallJournal.atomicWrite(try canonicalData(Cached(schema: 1, url: url.absoluteString, hash: digestData(response.data), response: response)), to: path)
        // Own cache only, no profile files. Bound both bytes and entry count.
        let files = try FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: [.fileSizeKey, .contentModificationDateKey, .isRegularFileKey]).filter { $0.pathExtension == "json" }
        let rows = files.compactMap { u -> (URL, Int, Date)? in guard let v = try? u.resourceValues(forKeys: [.fileSizeKey, .contentModificationDateKey, .isRegularFileKey]), v.isRegularFile == true else { return nil }; return (u, v.fileSize ?? 0, v.contentModificationDate ?? .distantPast) }.sorted { $0.2 < $1.2 }
        var bytes = rows.reduce(0) { $0 + $1.1 }, count = rows.count
        for row in rows where bytes > (image ? 33_554_432 : 25_165_824) || count > (image ? 96 : 64) { try FileManager.default.removeItem(at: row.0); bytes -= row.1; count -= 1 }
    }
    private func release(_ key: String, flight: UUID, user: UUID) {
        guard var f = flights[key], f.id == flight, f.users.remove(user) != nil else { return }
        if f.users.isEmpty { f.task.cancel(); flights.removeValue(forKey: key) } else { flights[key] = f }
    }
    func fetch(_ url: URL, refresh: Bool = false, image: Bool = false, ttl: TimeInterval = 900, validate: (Data) throws -> Void = { _ in }) async throws -> CatalogueResponse {
        try Task.checkCancellation()
        guard !suspended else { throw CancellationError() }
        guard CatalogueSafety.transport(url) else { throw LibraryError("This catalogue URL is not supported.") }
        let key = url.absoluteString, candidate = cached(url, image: image), now = Date()
        let old = candidate.flatMap { value -> CatalogueResponse? in do { try validate(value.data); return value } catch { return nil } }
        if let old, !refresh, now.timeIntervalSince(old.date) >= 0, now.timeIntervalSince(old.date) < ttl { record("cacheHits"); return old }
        if let until = backoff[key], until > now {
            if var old { old.stale = true; record("staleCacheHits"); return old }
            throw LibraryError("This request failed recently. Please retry in a minute.")
        }
        let user = UUID(), flight: Flight
        if var existing = flights[key] { existing.users.insert(user); flights[key] = existing; flight = existing; record("coalesced") }
        else {
            let transport = transport
            flight = Flight(id: UUID(), task: Task { try await transport(url, 4_194_304, image) }, users: [user]); flights[key] = flight; record(image ? "imageRequests" : "metadataRequests")
        }
        defer { release(key, flight: flight.id, user: user) }
        do {
            let response = try await withTaskCancellationHandler { try await flight.task.value } onCancel: { Task { await self.release(key, flight: flight.id, user: user) } }
            try Task.checkCancellation()
            guard !suspended else { throw CancellationError() }
            guard !response.data.isEmpty, response.data.count <= 4_194_304 else { throw LibraryError("The catalogue response exceeded its limit.") }
            try validate(response.data)
            do { try store(response, url: url, image: image) } catch { record("cacheWriteFailures") }
            backoff.removeValue(forKey: key); return response
        } catch {
            if Task.isCancelled || error is CancellationError || (error as? URLError)?.code == .cancelled { record("cancelled"); throw CancellationError() }
            record("failed"); backoff[key] = now.addingTimeInterval(60)
            let detail = error as NSError
            lastFailure = ["endpoint": (url.host ?? "") + url.path, "domain": detail.domain, "code": detail.code]
            if backoff.count > 128 { backoff = backoff.filter { $0.value > now }; if backoff.count > 128 { backoff = [:] } }
            if var old { old.stale = true; record("staleCacheHits"); return old }
            if error is LibraryError { throw error }
            throw LibraryError(Self.connectionMessage(error))
        }
    }
    private static func connectionMessage(_ error: Error) -> String {
        switch (error as? URLError)?.code {
        case .notConnectedToInternet, .networkConnectionLost:
            return "You're offline. Reconnect to Wi-Fi or mobile data, then try again. Your installed mods are still available."
        case .timedOut:
            return "The catalogue is taking too long to respond. Please try again shortly."
        case .cannotFindHost, .cannotConnectToHost, .dnsLookupFailed:
            return "Couldn't reach the catalogue. Check your connection and try again shortly."
        case .secureConnectionFailed, .serverCertificateUntrusted, .serverCertificateHasBadDate, .serverCertificateHasUnknownRoot, .serverCertificateNotYetValid:
            return "Couldn't connect securely to the catalogue. Please try again later."
        default:
            return "Couldn't load this catalogue page. Please check your connection and try again."
        }
    }
    func page(_ query: CatalogueQuery, page: Int, refresh: Bool = false) async throws -> (entries: [CatalogueEntry], response: CatalogueResponse) {
        let response = try await fetch(query.url(page: page), refresh: refresh, validate: { _ = try CatalogueEntry.parse($0) })
        return (try CatalogueEntry.parse(response.data), response)
    }
    func categories(refresh: Bool = false) async throws -> [CatalogueCategory] {
        async let a = fetch(URL(string: "https://maddie480.ovh/celeste/gamebanana-categories")!, refresh: refresh, ttl: 86400, validate: { guard $0.count <= 262_144, try ManifestYAML().parse($0).list != nil else { throw LibraryError("Invalid categories.") } })
        async let b = fetch(URL(string: "https://maddie480.ovh/celeste/gamebanana-subcategories")!, refresh: refresh, ttl: 86400, validate: { guard $0.count <= 262_144, try ManifestYAML().parse($0).map != nil else { throw LibraryError("Invalid subcategories.") } })
        return try await CatalogueCategory.parse(a.data, subcategories: b.data)
    }
    func details(_ entry: CatalogueEntry) async throws -> GameBananaDetails {
        let response = try await fetch(GameBananaDetails.apiURL(entry), ttl: 600, validate: { _ = try GameBananaDetails($0, entry: entry) })
        return try GameBananaDetails(response.data, entry: entry)
    }
    func cancelAll() {
        for f in flights.values { f.task.cancel() }; flights = [:]
    }
    func suspendForGame() async {
        suspended = true
        let pending = Array(flights.values)
        cancelAll()
        for flight in pending { _ = await flight.task.result }
    }
    func diagnostics() -> [String: Any] { ["schema": 1, "counts": counters, "lastFailure": lastFailure, "activeRequests": flights.count, "suspendedForGame": suspended, "metadataDiskLimit": 25_165_824, "imageDiskLimit": 33_554_432, "decodedImageLimit": 16_777_216, "pageSize": 20, "maximumRetainedRows": 200] }
}
