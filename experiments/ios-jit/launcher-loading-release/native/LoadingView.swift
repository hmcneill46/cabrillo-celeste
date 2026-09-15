#if canImport(UIKit)
import SwiftUI

struct CabrilloLoadingView: View {
    let state: [String: Any]
    let canCancelFiles: Bool
    let cancelFiles: () -> Void
    let exportDiagnostics: () -> Void
    let detailsChanged: (Bool) -> Void
    @State private var details = false
    private let rose = Color(red: 0.96, green: 0.36, blue: 0.47)
    private var failed: Bool { state["failed"] as? Bool ?? false }
    private var phase: String { state["phase"] as? String ?? "selection" }
    private func number(_ key: String, _ fallback: Int = 0) -> Int { (state[key] as? NSNumber)?.intValue ?? fallback }
    private var title: String {
        switch phase {
        case "selection": return "Checking your selected mods"
        case "catalogue": return "Finishing browsing activity"
        case "runtime", "platform": return "Preparing Celeste"
        case "files": return "Checking game files"
        case "settings": return "Preparing your settings"
        case "hooks": return "Preparing mod hooks"
        case "orientation", "window": return "Preparing the game view"
        case "everest": return "Preparing Everest"
        case "mod_index": return "Reading your mod library"
        case "mods": return "Loading mods"
        case "dependencies": return "Resolving mod dependencies"
        case "maps", "content_index": return "Indexing content"
        case "mod_options": return "Applying mod options"
        case "verify_mods": return "Checking loaded mods"
        case "game_content": return "Loading game content"
        case "ready": return "Ready to climb"
        default: return "Preparing Celeste"
        }
    }
    var body: some View {
        GeometryReader { geometry in
            let compact = geometry.size.height < 500
            ScrollView {
                VStack(alignment: .leading, spacing: compact ? 16 : 30) {
                    VStack(alignment: .leading, spacing: 12) {
                        if !compact { Image(systemName: "mountain.2.fill")
                            .font(.system(size: 48, weight: .light)).foregroundStyle(rose)
                            .accessibilityHidden(true) }
                        Text("CABRILLO").font(.caption.weight(.semibold)).tracking(3).foregroundStyle(.secondary)
                        Text(failed ? "Celeste couldn’t start" : "Starting Celeste")
                            .font(compact ? .title2.bold() : .largeTitle.bold()).accessibilityAddTraits(.isHeader)
                        if !compact { Text(failed ? "Export details to help find the problem." : "Getting your game and mods ready for the climb.")
                            .font(.body).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
                        }
                    }
                    VStack(alignment: .leading, spacing: compact ? 10 : 16) {
                        HStack(spacing: 12) {
                            if failed { Image(systemName: "exclamationmark.circle.fill").foregroundStyle(.orange) }
                            else { ProgressView().tint(rose).accessibilityLabel("Loading") }
                            Text(title).font(.title3.weight(.semibold)).accessibilityIdentifier("loading.stage")
                        }
                        if let detail = state["detail"] as? String, !detail.isEmpty {
                            Text(detail).font(.subheadline).foregroundStyle(.secondary)
                                .lineLimit(compact ? 2 : 4).fixedSize(horizontal: false, vertical: true)
                                .accessibilityIdentifier("loading.detail")
                        }
                        if phase == "mods", number("total", -1) > 0, !failed {
                            ProgressView(value: Double(number("completed")), total: Double(number("total"))).tint(rose)
                            Text("\(number("completed")) of \(number("total")) archives and folders processed")
                                .font(.footnote.monospacedDigit()).foregroundStyle(.secondary)
                        }
                        if failed {
                            Text(state["failure"] as? String ?? "Startup stopped before the game was ready.")
                                .font(.subheadline).textSelection(.enabled)
                                .accessibilityIdentifier("loading.failure")
                        } else {
                            TimelineView(.periodic(from: .now, by: 1)) { _ in
                                let started = (state["started_uptime"] as? NSNumber)?.doubleValue ?? ProcessInfo.processInfo.systemUptime
                                let elapsed = max(0, Int(ProcessInfo.processInfo.systemUptime - started))
                                Text("\(elapsed / 60):\(String(format: "%02d", elapsed % 60)) elapsed")
                                    .font(.footnote.monospacedDigit()).foregroundStyle(.secondary)
                                    .accessibilityIdentifier("loading.elapsed")
                            }
                        }
                    }
                    .padding(compact ? 16 : 22).frame(maxWidth: .infinity, alignment: .leading)
                    .background(.white.opacity(0.045), in: RoundedRectangle(cornerRadius: 18))
                    DisclosureGroup(isExpanded: Binding(get: { details }, set: { details = $0; detailsChanged($0) })) {
                        VStack(alignment: .leading, spacing: 8) {
                            if number("archives_total", -1) >= 0 {
                                Text("Archives and folders: \(number("archives_processed")) / \(number("archives_total"))")
                                Text("Mod loads completed: \(number("modules_loaded"))")
                                if number("delayed") > 0 { Text("Waiting for dependencies: \(number("delayed"))") }
                                if number("skipped") > 0 { Text("Duplicate entries skipped: \(number("skipped"))") }
                                if number("load_failures") > 0 { Text("Mod loads that failed: \(number("load_failures"))").foregroundStyle(.orange) }
                            }
                            Text("Some mods take longer than others. Counts describe the current work, rather than time remaining.")
                            Text("The game opens when its main menu is ready.")
                        }.font(.footnote).foregroundStyle(.secondary).padding(.top, 10)
                    } label: { Text("Loading details").font(.subheadline.weight(.medium)) }
                    .accessibilityIdentifier("loading.details")
                    if failed {
                        VStack(alignment: .leading, spacing: 14) {
                            Button("Export diagnostics…", action: exportDiagnostics)
                                .buttonStyle(.borderedProminent).accessibilityIdentifier("loading.export")
                            Text("Close this app in the app switcher, then relaunch before trying again.")
                                .font(.footnote).foregroundStyle(.secondary)
                        }
                    } else if canCancelFiles {
                        Button("Cancel file preparation", action: cancelFiles)
                            .font(.subheadline).accessibilityIdentifier("loading.cancelFiles")
                    }
                }
                .frame(maxWidth: 540, alignment: .leading)
                .padding(.horizontal, geometry.size.width < 500 ? 24 : 44).padding(.vertical, compact ? 24 : 32)
                .frame(maxWidth: .infinity, minHeight: geometry.size.height, alignment: .center)
            }
            .background(Color(red: 0.055, green: 0.063, blue: 0.09))
        }
        .tint(rose).preferredColorScheme(.dark)
    }
}
#endif
