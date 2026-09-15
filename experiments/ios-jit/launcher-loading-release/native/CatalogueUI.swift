#if canImport(UIKit)
import SwiftUI
import UIKit
import ImageIO

final class CatalogueBrowserModel: ObservableObject {
    @Published var search = ""
    @Published var sort = CatalogueSort.downloads
    @Published var category: String?
    @Published var subcategory: String?
    @Published var entries: [CatalogueEntry] = []
    @Published var categories: [CatalogueCategory] = []
    @Published var loading = false
    @Published var loadingMore = false
    @Published var error: String?
    @Published var categoryError: String?
    @Published var notice: String?
    @Published var total: Int?
    @Published var hasMore = false
    @Published var generation = UUID()
    @Published private(set) var suspended = false
    let provider: CatalogueProvider
    private var requestID = UUID()
    private var page = 0
    private var loadedQuery: CatalogueQuery?
    var query: CatalogueQuery { CatalogueQuery(search: search, sort: sort, category: category, subcategory: subcategory) }
    var filterTitle: String {
        guard let c = categories.first(where: { $0.id == category }) else { return "All categories" }
        return c.children.first(where: { $0.id == subcategory }).map { c.name + " · " + $0.name } ?? c.name
    }
    init() {
        let root = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("CelesteCatalogue/v1")
        #if targetEnvironment(simulator)
        provider = SimulatorCatalogueFixture.make(root: root) ?? CatalogueProvider(root: root)
        #else
        provider = CatalogueProvider(root: root)
        #endif
    }
    @MainActor func load(refresh: Bool = false) async {
        let query = query
        // Returning from a mod page keeps the loaded pages and scroll position.
        if !refresh, loadedQuery == query, page > 0 { return }
        let id = UUID(); requestID = id
        loading = true; loadingMore = false; error = nil; notice = nil; hasMore = false; total = nil
        if !refresh { entries = []; generation = UUID() }
        page = 0
        do {
            // Debounce typing, not pulls to refresh or category/sort changes.
            if !query.term.isEmpty && !refresh { try await Task.sleep(for: .milliseconds(350)) }
            let value = try await provider.page(query, page: 1, refresh: refresh)
            try Task.checkCancellation(); guard requestID == id else { return }
            entries = value.entries; page = 1; loadedQuery = query; total = query.term.isEmpty ? value.response.total : nil
            hasMore = query.term.isEmpty && value.entries.count == 20 && (total.map { $0 > 20 } ?? true)
            notice = value.response.stale ? "Offline copy · last loaded \(value.response.date.formatted(date: .abbreviated, time: .shortened)). Pull to refresh when connected." : nil
            loading = false
        } catch {
            guard requestID == id else { return }; loading = false
            if !(error is CancellationError) && (error as? URLError)?.code != .cancelled { self.error = error.localizedDescription }
        }
    }
    @MainActor func more() async {
        guard !loading, !loadingMore, hasMore else { return }
        let id = requestID, query = query, next = page + 1; loadingMore = true; error = nil
        do {
            let value = try await provider.page(query, page: next)
            try Task.checkCancellation(); guard id == requestID else { return }
            let old = Set(entries.map(\.id)), fresh = value.entries.filter { !old.contains($0.id) }
            if entries.count >= 200 { entries = []; generation = UUID() }
            entries += fresh; page = next; loadingMore = false
            hasMore = value.entries.count == 20 && next < 500 && (value.response.total.map { next * 20 < $0 } ?? true)
            if value.response.stale { notice = "Showing previously loaded results. Pull to refresh when connected." }
        } catch {
            guard id == requestID else { return }; loadingMore = false
            if !(error is CancellationError) { self.error = error.localizedDescription }
        }
    }
    @MainActor func loadCategories() async {
        do { let categories = try await provider.categories(); try Task.checkCancellation(); self.categories = categories; categoryError = nil }
        catch { if !(error is CancellationError) { categoryError = "Categories are unavailable. Search and browsing still work." } }
    }
    @MainActor func suspendForGame() async {
        suspended = true; requestID = UUID(); entries = []; loading = false; loadingMore = false
        CatalogueImages.shared.clear()
        await provider.suspendForGame()
    }
    @MainActor func log(_ action: @escaping (String, [String: Any]) -> Void) {
        Task { let state = await provider.diagnostics(); action("catalogueDiagnostics", state) }
    }
}

@MainActor final class CatalogueImages {
    static let shared = CatalogueImages()
    private static let decodeSlots = CatalogueSlots(limit: 2)
    private var cache: [String: (image: UIImage, cost: Int, access: UInt64)] = [:]
    private var cost = 0
    private var tick: UInt64 = 0
    private var generation = UUID()
    private var observer: NSObjectProtocol?
    init() {
        observer = NotificationCenter.default.addObserver(forName: UIApplication.didReceiveMemoryWarningNotification, object: nil, queue: .main) { [weak self] _ in Task { @MainActor in self?.clear() } }
    }
    func clear() { cache = [:]; cost = 0; generation = UUID() }
    func image(_ url: URL, provider: CatalogueProvider) async throws -> UIImage {
        let generation = generation
        tick &+= 1
        if var value = cache[url.absoluteString] { value.access = tick; cache[url.absoluteString] = value; return value.image }
        let response = try await provider.fetch(url, image: true, ttl: 604800, validate: { data in
            guard let source = CGImageSourceCreateWithData(data as CFData, [kCGImageSourceShouldCache: false] as CFDictionary),
                  let p = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any], let w = p[kCGImagePropertyPixelWidth] as? Int, let h = p[kCGImagePropertyPixelHeight] as? Int,
                  w > 0, h > 0, w <= 8192, h <= 8192, Int64(w) * Int64(h) <= 16_777_216 else { throw LibraryError("Screenshot unavailable or too large.") }
        })
        try Task.checkCancellation()
        try await Self.decodeSlots.acquire()
        let image: UIImage
        do {
            try Task.checkCancellation()
            image = try await Task.detached(priority: .utility) {
            guard let source = CGImageSourceCreateWithData(response.data as CFData, [kCGImageSourceShouldCache: false] as CFDictionary),
                  let p = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
                  let w = p[kCGImagePropertyPixelWidth] as? Int, let h = p[kCGImagePropertyPixelHeight] as? Int,
                  w > 0, h > 0, w <= 8192, h <= 8192, Int64(w) * Int64(h) <= 16_777_216,
                  let cg = CGImageSourceCreateThumbnailAtIndex(source, 0, [kCGImageSourceCreateThumbnailFromImageAlways: true, kCGImageSourceCreateThumbnailWithTransform: true, kCGImageSourceThumbnailMaxPixelSize: 800, kCGImageSourceShouldCacheImmediately: true] as CFDictionary)
            else { throw LibraryError("Screenshot unavailable.") }
            return UIImage(cgImage: cg)
            }.value
            await Self.decodeSlots.release()
        } catch { await Self.decodeSlots.release(); throw error }
        try Task.checkCancellation()
        guard generation == self.generation else { throw CancellationError() }
        if let old = cache.removeValue(forKey: url.absoluteString) { cost -= old.cost }
        let bytes = (image.cgImage?.bytesPerRow ?? 0) * (image.cgImage?.height ?? 0)
        tick &+= 1; cache[url.absoluteString] = (image, bytes, tick); cost += bytes
        while cost > 16_777_216 || cache.count > 32 {
            guard let oldest = cache.min(by: { $0.value.access < $1.value.access }) else { break }
            cost -= oldest.value.cost; cache.removeValue(forKey: oldest.key)
        }
        return image
    }
}

private struct CataloguePicture: View {
    let url: String?
    let provider: CatalogueProvider
    var fit = false
    @State private var image: UIImage?
    @State private var failed = false
    var body: some View {
        GeometryReader { proxy in
            ZStack {
                LinearGradient(colors: [Color(red: 0.17, green: 0.20, blue: 0.29), Color(red: 0.10, green: 0.12, blue: 0.20)], startPoint: .topLeading, endPoint: .bottomTrailing)
                if let image {
                    if fit { Image(uiImage: image).resizable().scaledToFit().frame(width: proxy.size.width, height: proxy.size.height) }
                    else { Image(uiImage: image).resizable().scaledToFill().frame(width: proxy.size.width, height: proxy.size.height).clipped() }
                } else { Image(systemName: failed ? "photo" : "mountain.2").font(.system(size: 30, weight: .ultraLight)).foregroundStyle(.white.opacity(0.35)) }
            }
        }.accessibilityHidden(true)
            .task(id: url) {
                guard let url = url.flatMap(CatalogueSafety.media) else { return }
                do { let image = try await CatalogueImages.shared.image(url, provider: provider); try Task.checkCancellation(); self.image = image }
                catch { if !(error is CancellationError) { failed = true } }
            }.onDisappear { image = nil }
    }
}

struct CatalogueBrowserView: View {
    @ObservedObject var model: CatalogueBrowserModel
    let locked: Bool
    let review: (CatalogueSelection) -> Void
    let log: (String, [String: Any]) -> Void
    @Environment(\.dynamicTypeSize) private var typeSize
    @Environment(\.verticalSizeClass) private var verticalSize
    @State private var showFilters = false
    private var columns: [GridItem] { [GridItem(.adaptive(minimum: typeSize.isAccessibilitySize ? 280 : 160, maximum: 360), spacing: 14, alignment: .top)] }
    var body: some View {
        ScrollViewReader { scroll in
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header.id("catalogue.top")
                    if let notice = model.notice { Label(notice, systemImage: "wifi.slash").font(.footnote).foregroundStyle(.secondary).accessibilityIdentifier("browse.offline") }
                    if model.loading && model.entries.isEmpty {
                        HStack { Spacer(); ProgressView(model.query.term.isEmpty ? "Finding your next climb…" : "Searching Celeste mods…"); Spacer() }.padding(.vertical, 70)
                    } else if model.entries.isEmpty {
                        ContentUnavailableView {
                            Label(model.error == nil ? "No matching mods" : "Couldn't load mods", systemImage: model.error == nil ? "magnifyingglass" : "wifi.exclamationmark")
                        } description: { Text(model.error ?? "Try a shorter name, a different spelling, or explore the categories.") } actions: {
                            if model.error != nil { Button("Try again") { Task { await model.load(refresh: true) } }.buttonStyle(.borderedProminent).accessibilityIdentifier("browse.retry") }
                            else { Button("Clear search and filters") { model.search = ""; model.category = nil; model.subcategory = nil }.buttonStyle(.bordered) }
                        }.padding(.top, 28)
                    } else {
                        LazyVGrid(columns: columns, alignment: .leading, spacing: 18) {
                            ForEach(model.entries) { entry in
                                NavigationLink { CatalogueDetailView(entry: entry, provider: model.provider, locked: locked, review: review) } label: { card(entry) }
                                    .buttonStyle(.plain).accessibilityIdentifier("browse.mod." + entry.pageURL.lastPathComponent)
                            }
                        }
                        if let error = model.error { VStack(alignment: .leading, spacing: 8) { Text(error).font(.footnote).foregroundStyle(.secondary); Button("Retry next page") { Task { await model.more() } } } }
                        if model.hasMore {
                            Button { Task { await model.more() } } label: {
                                HStack { Spacer(); if model.loadingMore { ProgressView() }; Text(model.entries.count >= 200 ? "Continue browsing" : "Load more mods"); Spacer() }.padding(8)
                            }.buttonStyle(.bordered).disabled(model.loadingMore).accessibilityIdentifier("browse.more")
                        } else { Text(model.query.term.isEmpty ? "You're all caught up here." : "The closest name matches from the Celeste catalogue. Try a more specific name if your mod isn't here.").font(.footnote).foregroundStyle(.secondary).frame(maxWidth: .infinity).multilineTextAlignment(.center).padding(.vertical, 12) }
                    }
                    Label("Mod pages by GameBanana · Catalogue used by Olympus", systemImage: "globe").font(.caption2).foregroundStyle(.tertiary).frame(maxWidth: .infinity).padding(.bottom, 12)
                }.padding(.horizontal, 18).padding(.top, 14).frame(maxWidth: 1120).frame(maxWidth: .infinity)
            }.background(Color(uiColor: .systemGroupedBackground))
                .scrollDismissesKeyboard(.interactively)
                .refreshable { await model.load(refresh: true); await model.loadCategories() }
                .task(id: model.query) { await model.load() }
                .task { await model.loadCategories() }
                .onChange(of: model.generation) { _, _ in scroll.scrollTo("catalogue.top", anchor: .top) }
                .onDisappear { model.log(log) }
                .sheet(isPresented: $showFilters) { filters }
        }
    }
    private var header: some View {
        VStack(alignment: .leading, spacing: 16) {
            if model.query.term.isEmpty {
                if verticalSize == .compact && !typeSize.isAccessibilitySize {
                    HStack(spacing: 10) {
                        sortMenu; filterButton; Spacer(minLength: 0)
                        if let total = model.total { Text("\(total.formatted()) mods").font(.caption).foregroundStyle(.secondary) }
                        refreshButton
                    }
                } else {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Find your next climb").font(.title.bold())
                    Text("New worlds. Fresh ideas. Made by the community.").font(.subheadline).foregroundStyle(.secondary)
                }
                ViewThatFits(in: .horizontal) {
                    HStack(spacing: 10) { sortMenu; filterButton; Spacer(minLength: 0) }
                    VStack(alignment: .leading, spacing: 10) { sortMenu; filterButton }
                }
                HStack {
                    Text(model.filterTitle).font(.headline)
                    Spacer()
                    if let total = model.total { Text("\(total.formatted()) mods").font(.caption).foregroundStyle(.secondary) }
                    refreshButton
                }
                }
                if let error = model.categoryError { HStack { Text(error).font(.caption).foregroundStyle(.secondary); Button("Retry") { Task { await model.loadCategories() } } } }
            } else {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Search results").font(.title2.bold())
                    Text("Up to 20 best matches · all categories").font(.subheadline).foregroundStyle(.secondary)
                    Button("Clear search to browse by category or sort") { model.search = "" }.font(.footnote)
                }
            }
        }
    }
    private var refreshButton: some View {
        Button { Task { await model.load(refresh: true) } } label: { Image(systemName: "arrow.clockwise").padding(7) }.disabled(model.loading).accessibilityLabel("Refresh catalogue").accessibilityIdentifier("browse.refresh")
    }
    private var sortMenu: some View {
        Menu { Picker("Sort mods", selection: $model.sort) { ForEach(CatalogueSort.allCases) { Text($0.title).tag($0) } } } label: {
            Label(model.sort.title, systemImage: "arrow.up.arrow.down").font(.subheadline.weight(.medium)).padding(.horizontal, 13).padding(.vertical, 11).background(.quaternary, in: Capsule())
        }.accessibilityIdentifier("browse.sort")
    }
    private var filterButton: some View {
        Button { showFilters = true } label: {
            Label(model.category == nil ? "Categories" : model.filterTitle, systemImage: "line.3.horizontal.decrease").font(.subheadline.weight(.medium)).lineLimit(2).padding(.horizontal, 13).padding(.vertical, 11).background(.quaternary, in: Capsule())
        }.accessibilityIdentifier("browse.categories")
    }
    private func card(_ entry: CatalogueEntry) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            CataloguePicture(url: entry.images.first, provider: model.provider).aspectRatio(1.6, contentMode: .fit).clipped()
            VStack(alignment: .leading, spacing: 7) {
                Text(entry.category.isEmpty ? "Celeste mod" : entry.category).font(.caption2.weight(.medium)).foregroundStyle(.secondary).lineLimit(1)
                Text(entry.name).font(.headline).foregroundStyle(.primary).lineLimit(3, reservesSpace: true).fixedSize(horizontal: false, vertical: true)
                Text(entry.author.isEmpty ? "Community creator" : entry.author).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                HStack(spacing: 12) {
                    if let n = entry.downloads { Label(n.formatted(.number.notation(.compactName)), systemImage: "arrow.down").accessibilityLabel("\(n) downloads") }
                    if let n = entry.likes { Label(n.formatted(.number.notation(.compactName)), systemImage: "heart").accessibilityLabel("\(n) likes") }
                }.font(.caption2).foregroundStyle(.secondary).padding(.top, 5)
            }.padding(13).frame(maxWidth: .infinity, alignment: .leading)
        }.background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 18)).clipShape(RoundedRectangle(cornerRadius: 18))
            .accessibilityElement(children: .combine)
    }
    private var filters: some View {
        NavigationStack {
            List {
                Button { choose(nil, nil) } label: { filterRow("All categories", selected: model.category == nil, count: nil) }
                ForEach(model.categories) { category in
                    if category.children.isEmpty { Button { choose(category.id, nil) } label: { filterRow(category.name, selected: model.category == category.id, count: category.count) } }
                    else {
                        NavigationLink {
                            List {
                                Button { choose(category.id, nil) } label: { filterRow("All " + category.name.lowercased(), selected: model.category == category.id && model.subcategory == nil, count: category.count) }
                                ForEach(category.children) { child in Button { choose(category.id, child.id) } label: { filterRow(child.name, selected: model.subcategory == child.id, count: child.count) } }
                            }.navigationTitle(category.name)
                        } label: { filterRow(category.name, selected: model.category == category.id, count: category.count) }
                    }
                }
                if model.categories.isEmpty { Text(model.categoryError ?? "Loading categories…").foregroundStyle(.secondary); Button("Retry") { Task { await model.loadCategories() } } }
            }.navigationTitle("Categories").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { showFilters = false } } }
        }.presentationDetents([.medium, .large]).presentationDragIndicator(.visible)
    }
    private func filterRow(_ name: String, selected: Bool, count: Int64?) -> some View {
        HStack { Text(name).foregroundStyle(.primary); Spacer(); if let count { Text(count.formatted()).font(.caption).foregroundStyle(.secondary) }; if selected { Image(systemName: "checkmark").foregroundStyle(.tint) } }.padding(.vertical, 5)
    }
    private func choose(_ category: String?, _ subcategory: String?) { model.category = category; model.subcategory = subcategory; showFilters = false }
}

private struct CatalogueDetailView: View {
    let entry: CatalogueEntry
    let provider: CatalogueProvider
    let locked: Bool
    let review: (CatalogueSelection) -> Void
    @State private var selection = Set<String>()
    @State private var expanded = false
    @State private var details: GameBananaDetails?
    @State private var detailError: String?
    @State private var fetching = true
    @State private var showOlder = false
    private var screenshots: [String] { details?.images.isEmpty == false ? details!.images : entry.images }
    private var files: [CatalogueFile] { entry.files.filter { showOlder || $0.latest } }
    private var selectedBytes: UInt64 { entry.files.filter { selection.contains($0.id) }.reduce(0) { $0 + $1.bytes } }
    var body: some View {
        ScrollViewReader { scroll in
        ScrollView {
            VStack(alignment: .leading, spacing: 25) {
                if !screenshots.isEmpty {
                    TabView {
                        ForEach(screenshots, id: \.self) { url in CataloguePicture(url: url, provider: provider, fit: true).padding(.bottom, screenshots.count > 1 ? 24 : 0) }
                    }.tabViewStyle(.page(indexDisplayMode: screenshots.count > 1 ? .always : .never)).frame(height: 230).clipShape(RoundedRectangle(cornerRadius: 20)).accessibilityLabel("Mod screenshots. Swipe to see more.")
                }
                VStack(alignment: .leading, spacing: 9) {
                    Text(entry.subcategory.isEmpty ? entry.category : entry.category + " · " + entry.subcategory).font(.subheadline).foregroundStyle(.secondary)
                    Text(entry.name).font(.largeTitle.bold()).fixedSize(horizontal: false, vertical: true)
                    Text("By " + (details?.author ?? entry.author)).font(.headline).foregroundStyle(.secondary)
                    if let studios = details?.studios, !studios.isEmpty { Label(studios.joined(separator: ", "), systemImage: "person.2").font(.subheadline).foregroundStyle(.secondary) }
                    if !entry.summary.isEmpty { Text(entry.summary).font(.title3).padding(.top, 3) }
                }
                metrics
                VStack(alignment: .leading, spacing: 12) {
                    Text("About this mod").font(.title2.bold())
                    let body = details?.body ?? entry.body
                    Text(body.isEmpty ? "Visit the GameBanana page for more about this mod." : body).font(.body).lineSpacing(4).lineLimit(expanded ? nil : 9).textSelection(.enabled)
                    if body.count > 400 { Button(expanded ? "Show less" : "Read more") { expanded.toggle() }.font(.subheadline.weight(.semibold)) }
                    if let error = detailError { Label(error, systemImage: "info.circle").font(.caption).foregroundStyle(.secondary) }
                    if fetching { ProgressView("Refreshing page details…").font(.caption) }
                }
                fileChoices.id("mod.files")
                Link(destination: entry.pageURL) { Label("View on GameBanana", systemImage: "arrow.up.right.square").frame(maxWidth: .infinity).padding(10) }.buttonStyle(.bordered)
                Text("Files and descriptions are provided by their creators. Compatibility is checked during installation; some desktop-only mods may need iOS support.").font(.caption).foregroundStyle(.secondary)
            }.padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
        }.background(Color(uiColor: .systemGroupedBackground))
            .navigationTitle("Mod details").navigationBarTitleDisplayMode(.inline)
            .toolbar(.hidden, for: .tabBar)
            .safeAreaInset(edge: .bottom) { installBar { withAnimation { scroll.scrollTo("mod.files", anchor: .top) } } }
            .task {
                let available = entry.files.filter(\.selectable)
                if available.count == 1 { selection = [available[0].id] }
                do { let value = try await provider.details(entry); try Task.checkCancellation(); details = value; selection = selection.filter { value.availableFiles.contains($0) }; fetching = false }
                catch { if !(error is CancellationError) { detailError = "Live page details are unavailable. Showing the catalogue copy." }; fetching = false }
            }
        }
    }
    private var metrics: some View {
        VStack(alignment: .leading, spacing: 12) {
            ViewThatFits(in: .horizontal) { HStack(spacing: 22) { counts }; VStack(alignment: .leading, spacing: 10) { counts } }
            if let date = details?.updated ?? entry.updated { Text("Updated " + date.formatted(date: .abbreviated, time: .omitted)).font(.caption).foregroundStyle(.secondary) }
        }.padding(16).frame(maxWidth: .infinity, alignment: .leading).background(.quaternary, in: RoundedRectangle(cornerRadius: 16))
    }
    @ViewBuilder private var counts: some View {
        if let n = details?.downloads ?? entry.downloads { Label(n.formatted(.number.notation(.compactName)) + " downloads", systemImage: "arrow.down.circle").accessibilityLabel("\(n) downloads") }
        if let n = details?.likes ?? entry.likes { Label(n.formatted(.number.notation(.compactName)), systemImage: "heart").accessibilityLabel("\(n) likes") }
        if let n = details?.views ?? entry.views { Label(n.formatted(.number.notation(.compactName)), systemImage: "eye").accessibilityLabel("\(n) views") }
    }
    private var fileChoices: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(entry.files.count > 1 ? "Choose your files" : "Mod file").font(.title2.bold()).accessibilityIdentifier("browse.filesHeading")
            if entry.installable { Text("Some mods have separate music packs. Choose the files you want; required dependencies are added in the next review.").font(.subheadline).foregroundStyle(.secondary) }
            else { Text("This page has no current Everest mod ZIP to install here. Desktop tools and other downloads are available on GameBanana.").font(.subheadline).foregroundStyle(.secondary) }
            ForEach(files) { file in
                let removed = details.map { !$0.availableFiles.contains(file.id) } ?? false
                let allowed = entry.installable && file.selectable && !removed
                Button {
                    if selection.contains(file.id) { selection.remove(file.id) } else { selection.insert(file.id) }
                } label: {
                    HStack(alignment: .top, spacing: 12) {
                        Image(systemName: allowed ? (selection.contains(file.id) ? "checkmark.circle.fill" : "circle") : "archivebox").font(.title2).foregroundStyle(selection.contains(file.id) ? Color.accentColor : .secondary).padding(.top, 2)
                        VStack(alignment: .leading, spacing: 6) {
                            Text(file.description.isEmpty ? file.name : file.description).font(.headline).foregroundStyle(.primary).multilineTextAlignment(.leading)
                            if !file.description.isEmpty { Text(file.name).font(.caption).foregroundStyle(.secondary).multilineTextAlignment(.leading) }
                            Text(ByteCountFormatter.string(fromByteCount: Int64(file.bytes), countStyle: .file) + (file.date.map { " · " + $0.formatted(date: .abbreviated, time: .omitted) } ?? "")).font(.caption).foregroundStyle(.secondary)
                            if !allowed { Text(removed ? "No longer listed on the live page" : !file.latest ? "Previous release · available on GameBanana" : "No current Everest metadata").font(.caption).foregroundStyle(.secondary) }
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }.padding(15).background(selection.contains(file.id) ? Color.accentColor.opacity(0.10) : Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 16))
                        .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(selection.contains(file.id) ? Color.accentColor.opacity(0.6) : .clear))
                }.buttonStyle(.plain).disabled(!allowed || locked).accessibilityIdentifier("browse.file." + file.id).accessibilityAddTraits(selection.contains(file.id) ? .isSelected : [])
            }
            if entry.files.contains(where: { !$0.latest }) { Button(showOlder ? "Hide previous releases" : "Show previous releases") { showOlder.toggle() }.font(.subheadline) }
        }
    }
    private func installBar(choose: @escaping () -> Void) -> some View {
        VStack(spacing: 8) {
            if locked { Text("Finish the current operation or relaunch after your game session to install mods.").font(.footnote).foregroundStyle(.secondary).multilineTextAlignment(.center) }
            else if selection.isEmpty { Text(entry.installable ? "Select the mod files you want to install" : "This download is available on GameBanana").font(.footnote).foregroundStyle(.secondary) }
            else { Text("\(selection.count) selected · \(ByteCountFormatter.string(fromByteCount: Int64(selectedBytes), countStyle: .file)) before dependencies").font(.footnote).foregroundStyle(.secondary).monospacedDigit() }
            Button {
                if selection.isEmpty { choose() } else { review(CatalogueSelection(pageURL: entry.id, fileIDs: selection.sorted())) }
            } label: { Label(selection.isEmpty ? "Choose files" : "Review installation", systemImage: selection.isEmpty ? "checklist" : "arrow.down.circle.fill").font(.headline).frame(maxWidth: .infinity).padding(.vertical, 7) }
                .buttonStyle(.borderedProminent).disabled(locked || !entry.installable).accessibilityIdentifier("browse.review")
        }.padding(.horizontal, 20).padding(.top, 12).padding(.bottom, 8).background(.regularMaterial)
    }
}
#endif
