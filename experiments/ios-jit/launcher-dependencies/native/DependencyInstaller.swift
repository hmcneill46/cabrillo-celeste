import Foundation

final class InstallCancellation {
    private let lock = NSLock()
    private var value = false
    var cancelled: Bool { lock.lock(); defer { lock.unlock() }; return value }
    func cancel() { lock.lock(); value = true; lock.unlock() }
    func check() throws { if cancelled { throw LibraryError("Download cancelled. Completed, verified files are kept for your next attempt.") } }
}

// A separate delegate queue streams to disk while the install worker waits.
// Neither large ZIP bytes nor metadata parsing run on UIKit's main thread.
final class InstallDownload: NSObject, URLSessionDownloadDelegate {
    private let semaphore = DispatchSemaphore(value: 0)
    private let destination: URL
    private let limit: Int64
    private let expected: Int64?
    private let cancellation: InstallCancellation
    private let progress: (Int64, Int64) -> Void
    private var failure: Error?
    private var saved = false
    private var lastReport = Date.distantPast
    private var session: URLSession?
    private var task: URLSessionDownloadTask?
    init(destination: URL, limit: Int64, expected: Int64?, cancellation: InstallCancellation, progress: @escaping (Int64, Int64) -> Void) {
        self.destination = destination; self.limit = limit; self.expected = expected; self.cancellation = cancellation; self.progress = progress
    }
    func fetch(_ url: URL) throws {
        try cancellation.check()
        guard validDownloadURL(url.absoluteString) != nil else { throw LibraryError("The download URL is not supported HTTPS.") }
        let config = URLSessionConfiguration.ephemeral
        config.allowsCellularAccess = UserDefaults.standard.bool(forKey: "launcher.cellularDownloads")
        config.timeoutIntervalForRequest = 45; config.timeoutIntervalForResource = 900; config.waitsForConnectivity = false
        let queue = OperationQueue(); queue.maxConcurrentOperationCount = 1
        let session = URLSession(configuration: config, delegate: self, delegateQueue: queue); self.session = session
        var request = URLRequest(url: url); request.setValue("CelesteIOS/0.13.0", forHTTPHeaderField: "User-Agent")
        request.setValue("identity", forHTTPHeaderField: "Accept-Encoding")
        let task = session.downloadTask(with: request); self.task = task; task.resume()
        while semaphore.wait(timeout: .now() + 0.2) == .timedOut {
            if cancellation.cancelled { task.cancel() }
        }
        session.finishTasksAndInvalidate(); self.task = nil; self.session = nil
        try cancellation.check()
        if let failure { throw failure }
        guard saved else { throw LibraryError("The server did not provide a complete download.") }
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        guard let url = request.url, validDownloadURL(url.absoluteString) != nil else {
            failure = LibraryError("The server redirected to an unsupported download address."); completionHandler(nil); return
        }
        completionHandler(request)
    }
    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didWriteData bytesWritten: Int64, totalBytesWritten received: Int64, totalBytesExpectedToWrite serverExpected: Int64) {
        if received > limit || serverExpected > limit || (expected != nil && serverExpected > 0 && serverExpected != expected!) {
            failure = LibraryError("The download size differs from the reviewed mod index."); downloadTask.cancel(); return
        }
        if cancellation.cancelled { downloadTask.cancel(); return }
        if Date().timeIntervalSince(lastReport) >= 0.1 { lastReport = Date(); progress(received, expected ?? max(0, serverExpected)) }
    }
    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didFinishDownloadingTo location: URL) {
        guard !cancellation.cancelled else { return }
        do {
            guard let response = downloadTask.response as? HTTPURLResponse, response.statusCode == 200 else { throw LibraryError("The mod server returned an error. Try again later.") }
            let size = (try FileManager.default.attributesOfItem(atPath: location.path)[.size] as? NSNumber)?.int64Value ?? -1
            guard size > 0, size <= limit, expected == nil || size == expected! else { throw LibraryError("The downloaded file is truncated or has an unexpected size.") }
            guard !FileManager.default.fileExists(atPath: destination.path) else { throw LibraryError("The download staging path is already occupied.") }
            try FileManager.default.moveItem(at: location, to: destination)
            let f = try FileHandle(forWritingTo: destination); try f.synchronize(); try f.close(); saved = true
        } catch { failure = error }
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if failure == nil { failure = error }; semaphore.signal()
    }
}

final class DependencyInstaller {
    let library: ModLibrary
    let pins: [DownloadCandidate]
    private let worker = DispatchQueue(label: "Celeste.mod-installs", qos: .userInitiated)
    private let control = NSLock()
    private var token = InstallCancellation()
    private var running = false
    private var plan: DependencyPlan?
    private var inventory: LibraryInventory?
    private var database: DependencyDatabase?
    private var verified: [String: VerifiedDownload] = [:]
    private var offeredUpdates: [ModUpdate] = []
    private var requestedUpdates: [String: DownloadCandidate] = [:]
    // Internal transport seams allow real filesystem/recovery tests without
    // publishing test mods. The app's ObjC entry point always uses HTTPS.
    private let indexProvider: ((InstallCancellation) throws -> DependencyDatabase)?
    private let downloadProvider: ((String, URL, Int64, Int64?, InstallCancellation, @escaping (Int64, Int64) -> Void) throws -> Void)?
    var update: (([String: Any]) -> Void)?
    init(library: ModLibrary, pins: [DownloadCandidate], indexProvider: ((InstallCancellation) throws -> DependencyDatabase)? = nil,
         downloadProvider: ((String, URL, Int64, Int64?, InstallCancellation, @escaping (Int64, Int64) -> Void) throws -> Void)? = nil) {
        self.library = library; self.pins = pins; self.indexProvider = indexProvider; self.downloadProvider = downloadProvider
    }
    private func emit(_ phase: String, _ message: String, active: Bool, extra: [String: Any] = [:]) {
        var state: [String: Any] = ["phase": phase, "message": message, "active": active, "plan": plan?.json ?? [:]]
        state.merge(extra) { _, new in new }
        DispatchQueue.main.async { self.update?(state) }
    }
    private func start(_ body: @escaping (InstallCancellation) throws -> Void) {
        control.lock(); guard !running else { control.unlock(); return }; running = true; token = InstallCancellation(); let token = self.token; control.unlock()
        worker.async {
            do {
                let cache = InstallJournal.cache(self.library.profile)
                if FileManager.default.fileExists(atPath: cache.path) {
                    // A killed process can leave a URLSession staging file.
                    // Only our UUID-named incomplete downloads are disposable.
                    for file in try FileManager.default.contentsOfDirectory(at: cache, includingPropertiesForKeys: nil) where file.pathExtension == "part" && UUID(uuidString: file.deletingPathExtension().lastPathComponent) != nil {
                        try FileManager.default.removeItem(at: file)
                    }
                }
                try body(token)
            }
            catch { self.emit(token.cancelled ? "cancelled" : "failed", error.localizedDescription, active: false) }
            self.control.lock(); self.running = false; self.control.unlock()
        }
    }
    func cancel() { control.lock(); token.cancel(); control.unlock() }
    private func pinDatabase() throws -> DependencyDatabase {
        // A tiny non-network catalogue lets complete profiles and enable-only
        // plans resolve offline. App compatibility pins include actual metadata.
        var db = try DependencyDatabase(updates: Data("{}".utf8), graph: Data("{}".utf8), pins: pins, allowEmpty: true)
        for pin in pins { for m in pin.modules { db.byName[m.name] = pin } }
        return db
    }
    private func fetch(_ url: String, to file: URL, limit: Int64, expected: Int64? = nil, token: InstallCancellation, progress: @escaping (Int64, Int64) -> Void = { _, _ in }) throws {
        if let downloadProvider { return try downloadProvider(url, file, limit, expected, token, progress) }
        guard let url = validDownloadURL(url) else { throw LibraryError("Invalid HTTPS download source.") }
        try InstallDownload(destination: file, limit: limit, expected: expected, cancellation: token, progress: progress).fetch(url)
    }
    private func loadDatabase(_ token: InstallCancellation) throws -> DependencyDatabase {
        if let indexProvider { return try indexProvider(token) }
        let fm = FileManager.default, root = library.profile.appendingPathComponent("LauncherIndex")
        try InstallJournal.directory(root)
        let generation = UUID().uuidString, folder = root.appendingPathComponent(generation)
        try InstallJournal.directory(folder)
        do {
            var provenance = ["fetched": ISO8601DateFormatter().string(from: Date()), "generation": generation]
            for (kind, pointer) in [("updates", "https://everestapi.github.io/modupdater.txt"), ("graph", "https://everestapi.github.io/modgraph.txt")] {
                try token.check(); emit("index", kind == "updates" ? "Fetching the community mod index…" : "Reading dependency information…", active: true)
                let pointerFile = folder.appendingPathComponent(kind + ".txt")
                try fetch(pointer, to: pointerFile, limit: 4096, token: token)
                let urls = try String(contentsOf: pointerFile, encoding: .utf8).components(separatedBy: .newlines).map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty && !$0.hasPrefix("#") }
                guard !urls.isEmpty, urls.count <= 16, urls.allSatisfy({ validDownloadURL($0) != nil }) else { throw LibraryError("Everest's index location is invalid.") }
                let file = folder.appendingPathComponent(kind + ".yaml")
                var last: Error?
                for url in urls {
                    do { try fetch(url, to: file, limit: 33_554_432, token: token); provenance[kind + "URL"] = url; last = nil; break }
                    catch { last = error; try? fm.removeItem(at: file); try token.check() }
                }
                if let last { throw last }
                provenance[kind + "SHA256"] = digestData(try Data(contentsOf: file))
            }
            let db = try DependencyDatabase(updates: Data(contentsOf: folder.appendingPathComponent("updates.yaml")), graph: Data(contentsOf: folder.appendingPathComponent("graph.yaml")), provenance: provenance, pins: pins)
            try InstallJournal.atomicWrite(try canonicalData(provenance), to: folder.appendingPathComponent("receipt.json"))
            try InstallJournal.atomicWrite(Data(generation.utf8), to: root.appendingPathComponent("current.txt"))
            // Keep the current and preceding successful snapshot; these are
            // disposable launcher-owned metadata, never mod or save files.
            let old = try fm.contentsOfDirectory(at: root, includingPropertiesForKeys: [.creationDateKey]).filter { UUID(uuidString: $0.lastPathComponent) != nil && $0.lastPathComponent != generation }.sorted { ((try? $0.resourceValues(forKeys: [.creationDateKey]).creationDate) ?? .distantPast) < ((try? $1.resourceValues(forKeys: [.creationDateKey]).creationDate) ?? .distantPast) }
            for item in old.dropLast() { try? fm.removeItem(at: item) }
            return db
        } catch {
            try? fm.removeItem(at: folder); try token.check()
            guard let pointer = try? InstallJournal.boundedRead(root.appendingPathComponent("current.txt"), limit: 128), let generation = String(data: pointer, encoding: .utf8), UUID(uuidString: generation) != nil else { throw error }
            let cached = root.appendingPathComponent(generation)
            guard let receipt = try? JSONDecoder().decode([String: String].self, from: InstallJournal.boundedRead(cached.appendingPathComponent("receipt.json"), limit: 65536)),
                  let updates = try? InstallJournal.boundedRead(cached.appendingPathComponent("updates.yaml"), limit: 33_554_432),
                  let graph = try? InstallJournal.boundedRead(cached.appendingPathComponent("graph.yaml"), limit: 33_554_432),
                  digestData(updates) == receipt["updatesSHA256"], digestData(graph) == receipt["graphSHA256"] else { throw error }
            var provenance = receipt; provenance["cached"] = "true"
            return try DependencyDatabase(updates: updates, graph: graph, provenance: provenance, pins: pins)
        }
    }
    private func cachedDatabase() throws -> DependencyDatabase {
        let root = library.profile.appendingPathComponent("LauncherIndex")
        let pointer = try InstallJournal.boundedRead(root.appendingPathComponent("current.txt"), limit: 128)
        guard let generation = String(data: pointer, encoding: .utf8), UUID(uuidString: generation) != nil else { throw LibraryError("Check for updates to load the mod index.") }
        let folder = root.appendingPathComponent(generation)
        var receipt = try JSONDecoder().decode([String: String].self, from: InstallJournal.boundedRead(folder.appendingPathComponent("receipt.json"), limit: 65536))
        let updates = try InstallJournal.boundedRead(folder.appendingPathComponent("updates.yaml"), limit: 33_554_432), graph = try InstallJournal.boundedRead(folder.appendingPathComponent("graph.yaml"), limit: 33_554_432)
        guard digestData(updates) == receipt["updatesSHA256"], digestData(graph) == receipt["graphSHA256"] else { throw LibraryError("The cached index changed. Check for updates again.") }
        receipt["cached"] = "true"
        return try DependencyDatabase(updates: updates, graph: graph, provenance: receipt, pins: pins)
    }
    private func verify(_ source: DownloadCandidate, at file: URL) throws -> VerifiedDownload {
        let identity = try DownloadIdentity.read(file)
        guard source.accepts(identity) else { throw LibraryError("\(source.title) did not match its published integrity hash. Nothing was installed; refresh the index and retry.") }
        let originalName = (source.modules.first?.name ?? "mod") + ".zip"
        guard InstallJournal.safeFile(originalName) else { throw LibraryError("This archive needs a manual filename choice. Download it from its mod page and import the ZIP.") }
        let inspected = try ModLibrary.inspect(file, filename: originalName, digest: identity.sha256, bytes: identity.bytes)
        for expected in source.modules {
            guard inspected.modules.contains(where: { $0.name == expected.name && $0.version.parts == expected.version.parts }) else { throw LibraryError("The downloaded ZIP's identity or version differs from the mod index. It remains staged; refresh the index before retrying.") }
        }
        for module in inspected.modules {
            if DependencyPlanner.builtins[module.name] != nil { throw LibraryError("A downloaded ZIP cannot replace built-in app support.") }
            if let pin = library.specialPins[module.name], pin != identity.sha256 { throw LibraryError("This download does not match the app-compatible release of \(module.name).") }
        }
        var source = source
        source.modules = inspected.modules.map { m in ModMetadata(name: m.name, version: m.version, dll: nil, dependencies: m.dependencies.sorted { $0.name < $1.name }, optionalDependencies: m.optionalDependencies.sorted { $0.name < $1.name }) }.sorted { $0.name < $1.name }
        let metadataFree = inspected.modules.count == 1 && inspected.modules[0].version.text == "0.0.0-dummy"
        let stem = String((inspected.modules.first?.name ?? "mod").unicodeScalars.map { CharacterSet.alphanumerics.contains($0) || "-_".unicodeScalars.contains($0) ? String($0) : "_" }.joined().prefix(80))
        let filename = metadataFree ? originalName : stem + "-" + identity.sha256.prefix(12) + ".zip"
        let archive = ModArchive(filename: filename, digest: identity.sha256, bytes: identity.bytes, modules: inspected.modules, problem: nil)
        return VerifiedDownload(source: source, identity: identity, archive: archive)
    }
    private func cached(_ source: DownloadCandidate) throws -> VerifiedDownload? {
        let file = InstallJournal.cache(library.profile).appendingPathComponent(source.key + ".zip")
        guard FileManager.default.fileExists(atPath: file.path) else { return nil }
        do { return try verify(source, at: file) }
        catch {
            // Only this disposable cache entry is removed. Installed ZIPs are
            // never repaired or deleted by a failed download verification.
            try FileManager.default.removeItem(at: file)
            emit("checking", "A cached download failed verification and will be downloaded again.", active: true, extra: ["cacheRejected": source.key, "cacheError": error.localizedDescription])
            return nil
        }
    }
    private func replan(_ inventory: LibraryInventory, _ db: DependencyDatabase) throws -> DependencyPlan {
        let updates = requestedUpdates.mapValues { source in verified[source.key]?.source ?? source }
        return try DependencyPlanner.resolve(inventory, database: db, pins: library.specialPins, updates: updates)
    }
    private func prepare(_ inventory: LibraryInventory, database initial: DependencyDatabase, token: InstallCancellation) throws {
        self.inventory = inventory; var db = initial
        var plan = try replan(inventory, db)
        try InstallJournal.directory(InstallJournal.cache(library.profile))
        var checked = Set<String>()
        for _ in 0..<1024 {
            let pending = plan.downloads.filter { !checked.contains($0.key) }
            if pending.isEmpty { break }
            for source in pending {
                try token.check(); checked.insert(source.key)
                if let value = try cached(source) { verified[source.key] = value; db.replaceWithVerified(value.source) }
            }
            plan = try replan(inventory, db)
        }
        self.database = db; self.plan = plan
        emit("review", db.provenance["cached"] == "true" ? "Using the verified cached index from \(db.provenance["fetched"] ?? "an earlier visit"). Review these changes." : requestedUpdates.isEmpty ? "Review the dependencies needed by your enabled mods." : "Review these updates and their dependencies. Disabled mods stay disabled.", active: false, extra: ["index": db.provenance, "verifiedFiles": verified.count])
    }
    func checkUpdates(automatic: Bool = false) {
        start { token in
            self.plan = nil; self.requestedUpdates = [:]; self.verified = [:]; self.offeredUpdates = []
            let inventory = try LibraryInventory.read(self.library, force: !automatic)
            let cached = ModUpdates.readCache(self.library.profile)
            if automatic {
                let settings = UserDefaults.standard, lastAttempt = settings.double(forKey: "launcher.lastAutomaticUpdateAttempt"), elapsed = Date().timeIntervalSince1970 - lastAttempt
                let allowed = settings.object(forKey: "launcher.autoUpdateChecks") == nil || settings.bool(forKey: "launcher.autoUpdateChecks")
                if cached?.fresh(for: inventory.revision) == true || !allowed || (elapsed >= 0 && elapsed < 3600) {
                    if let cached, cached.revision == inventory.revision, let db = try? self.cachedDatabase(), db.provenance["updatesSHA256"] == cached.index["updatesSHA256"], db.provenance["graphSHA256"] == cached.index["graphSHA256"] {
                        self.inventory = inventory; self.database = db; self.offeredUpdates = cached.updates
                        self.emit("updates", "Last checked \(cached.checked.formatted(date: .abbreviated, time: .shortened)). Tap Check for updates to refresh now.", active: false, extra: ["updates": cached.updates.map(\.json), "cachedAvailability": true]); return
                    }
                    self.emit("updatesIdle", allowed ? "Tap Check for updates to refresh availability." : "Automatic checks are off. Tap Check for updates when you want to check.", active: false); return
                }
                settings.set(Date().timeIntervalSince1970, forKey: "launcher.lastAutomaticUpdateAttempt")
            }
            self.emit("checkingUpdates", "Checking the latest published mod archives…", active: true)
            let db = try self.loadDatabase(token)
            let updates = try ModUpdates.check(inventory, library: self.library, database: db, cancellation: token) { name in
                self.emit("checkingUpdates", "Checking \(name)…", active: true)
            }
            self.inventory = inventory; self.database = db; self.offeredUpdates = updates
            let record = ModUpdates.CheckCache(schema: 1, checked: db.provenance["cached"] == "true" ? (cached?.checked ?? .distantPast) : Date(), revision: inventory.revision, updates: updates, index: db.provenance)
            let file = ModUpdates.cacheFile(self.library.profile); try InstallJournal.directory(file.deletingLastPathComponent())
            let data = try canonicalData(record)
            if data.count <= 2_097_152 { try InstallJournal.atomicWrite(data, to: file) }
            self.emit("updates", db.provenance["cached"] == "true" ? "Using the cached index from \(db.provenance["fetched"] ?? "an earlier visit")." : "Checked the community mod index just now.", active: false, extra: ["updates": updates.map(\.json), "index": db.provenance])
        }
    }
    func planUpdates(_ filenames: [String]) {
        start { token in
            guard !filenames.isEmpty, Set(filenames).count == filenames.count, filenames.count <= 1024,
                  let inventory = self.inventory, let db = self.database,
                  try LibraryInventory.read(self.library).revision == inventory.revision else { throw LibraryError("The library changed. Check for updates again before choosing an update.") }
            var selected: [String: DownloadCandidate] = [:]
            for name in filenames {
                guard let update = self.offeredUpdates.first(where: { $0.archive.filename == name }), update.canUpdate else { throw LibraryError("That update is unavailable or app-managed. Check for updates again.") }
                selected[name] = update.candidate
            }
            self.requestedUpdates = selected; self.verified = [:]; self.plan = nil
            self.emit("checking", "Checking the selected updates together…", active: true)
            try self.prepare(inventory, database: db, token: token)
        }
    }
    func resolve() {
        start { token in
            self.plan = nil; self.verified = [:]; self.requestedUpdates = [:]; self.emit("checking", "Checking your installed mod versions…", active: true)
            let inventory = try LibraryInventory.read(self.library); self.inventory = inventory
            var db = try self.pinDatabase()
            var plan = try DependencyPlanner.resolve(inventory, database: db, pins: self.library.specialPins)
            if !plan.issues.isEmpty { db = try self.loadDatabase(token); plan = try DependencyPlanner.resolve(inventory, database: db, pins: self.library.specialPins) }
            try self.prepare(inventory, database: db, token: token)
        }
    }
    func apply(planID: String) {
        start { token in
            guard let plan = self.plan, plan.id == planID, plan.issues.isEmpty, let inventory = self.inventory, var db = self.database else { throw LibraryError("Review a dependency plan before installing.") }
            self.emit("checking", "Checking that your mod choices still match this plan…", active: true)
            guard try LibraryInventory.read(self.library).revision == plan.revision else { throw LibraryError("Your mod choices changed. Tap Review dependencies to create a new plan.") }
            let folder = InstallJournal.cache(self.library.profile); try InstallJournal.directory(folder)
            var completed: UInt64 = 0, count = 0
            for source in plan.downloads {
                try token.check()
                let file = folder.appendingPathComponent(source.key + ".zip")
                if let cached = try self.cached(source) { self.verified[source.key] = cached }
                else {
                    let temporary = folder.appendingPathComponent(UUID().uuidString + ".part")
                    defer { try? FileManager.default.removeItem(at: temporary) }
                    self.emit("downloading", source.title, active: true, extra: ["receivedBytes": completed, "totalBytes": plan.totalBytes, "completedFiles": count, "totalFiles": plan.downloads.count])
                    let base = completed, done = count
                    try self.fetch(source.url, to: temporary, limit: Int64(source.bytes), expected: Int64(source.bytes), token: token) { received, _ in
                        self.emit("downloading", source.title, active: true, extra: ["receivedBytes": base + UInt64(max(0, received)), "totalBytes": plan.totalBytes, "completedFiles": done, "totalFiles": plan.downloads.count])
                    }
                    self.emit("verifying", "Verifying \(source.title)…", active: true, extra: ["receivedBytes": completed + source.bytes, "totalBytes": plan.totalBytes, "completedFiles": count, "totalFiles": plan.downloads.count])
                    let value = try self.verify(source, at: temporary)
                    try FileManager.default.moveItem(at: temporary, to: file)
                    self.verified[source.key] = value
                }
                let value = self.verified[source.key]!
                try InstallJournal.atomicWrite(try canonicalData(value), to: folder.appendingPathComponent(source.key + ".json"))
                db.replaceWithVerified(value.source); completed += source.bytes; count += 1
                self.emit("verified", source.title, active: true, extra: ["verifiedSHA256": value.identity.sha256, "verifiedXXHash": value.identity.xxHash, "sourceURL": source.url, "receivedBytes": completed, "totalBytes": plan.totalBytes, "completedFiles": count, "totalFiles": plan.downloads.count])
            }
            try token.check(); self.database = db
            let revised = try self.replan(inventory, db)
            if revised.signature != plan.signature {
                self.plan = revised; self.emit("review", "The ZIPs contain different requirements from the online graph. Review the updated plan; verified downloads are kept.", active: false, extra: ["revised": true]); return
            }
            var disabled = Set(inventory.disabled); disabled.formUnion(plan.disable); disabled.subtract(plan.enable)
            for source in plan.downloads {
                let name = self.verified[source.key]!.archive.filename
                if plan.disabledDownloads.contains(where: { $0.key == source.key }) { disabled.insert(name) }
                else { disabled.remove(name) }
            }
            let actual = LibraryInventory(archives: (inventory.archives + plan.downloads.map { self.verified[$0.key]!.archive }).sorted { $0.filename < $1.filename }, disabled: disabled.sorted())
            let final = try DependencyPlanner.resolve(actual, database: db, pins: self.library.specialPins)
            guard final.issues.isEmpty, final.downloads.isEmpty, final.enable.isEmpty, final.disable.isEmpty else { throw LibraryError("The verified ZIPs do not form a complete compatible selection. Nothing was installed. " + final.issues.joined(separator: "\n")) }
            self.emit("installing", "Applying the verified mod selection…", active: true)
            let receipt = try InstallJournal.commit(library: self.library, inventory: inventory, plan: plan, verified: self.verified)
            self.plan = nil; self.inventory = nil; self.offeredUpdates = []; self.requestedUpdates = [:]
            self.emit("complete", "Mod changes installed. Your original archives and saves are retained.", active: false,
                      extra: ["receipt": (try JSONSerialization.jsonObject(with: canonicalData(receipt)))])
        }
    }
}

@objc public final class CJDependencyInstaller: NSObject {
    private let installer: DependencyInstaller
    @objc public var onUpdate: ((NSDictionary) -> Void)?
    @objc(initWithLibrary:) public init(library: CJModLibrary) {
        let url = Bundle.main.url(forResource: "CompatibilityDownloads", withExtension: "json")
        let pins = url.flatMap { try? Data(contentsOf: $0) }.flatMap { try? JSONDecoder().decode([DownloadCandidate].self, from: $0) } ?? []
        #if targetEnvironment(simulator)
        installer = SimulatorInstallFixture.make(library.library) ?? DependencyInstaller(library: library.library, pins: pins)
        #else
        installer = DependencyInstaller(library: library.library, pins: pins)
        #endif
        super.init()
        installer.update = { [weak self] state in self?.onUpdate?(state as NSDictionary) }
    }
    @objc public func resolve() { installer.resolve() }
    @objc public func checkUpdates() { installer.checkUpdates() }
    @objc public func checkUpdatesIfDue() { installer.checkUpdates(automatic: true) }
    @objc(planUpdates:) public func planUpdates(_ filenames: [String]) { installer.planUpdates(filenames) }
    @objc(applyPlan:) public func apply(plan: String) { installer.apply(planID: plan) }
    @objc public func cancel() { installer.cancel() }
    @objc(diagnosticsForProfile:) public static func diagnostics(profile: URL) -> NSDictionary { InstallJournal.diagnostics(profile: profile) as NSDictionary }
}
