#if canImport(UIKit)
import SwiftUI
import UIKit

struct CabrilloLoadingView: View {
    let state: [String: Any]
    let canCancelFiles: Bool
    let cancelFiles: () -> Void
    let exportDiagnostics: () -> Void
    private let rose = Color(red: 0.96, green: 0.36, blue: 0.47)
    private var failed: Bool { state["failed"] as? Bool ?? false }
    private var phase: String { state["phase"] as? String ?? "selection" }
    private func number(_ key: String, _ fallback: Int = 0) -> Int { (state[key] as? NSNumber)?.intValue ?? fallback }
    private var fraction: Double? {
        guard phase == "mods", number("total", -1) > 0 else { return nil }
        return Double(number("completed")) / Double(number("total"))
    }
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
    private var extraCounts: String {
        var values: [String] = []
        if number("delayed") > 0 { values.append("\(number("delayed")) waiting for dependencies") }
        if number("skipped") > 0 { values.append("Duplicate entries skipped: \(number("skipped"))") }
        if number("load_failures") > 0 { values.append("Failed mod loads: \(number("load_failures"))") }
        return values.joined(separator: " · ")
    }
    var body: some View {
        GeometryReader { geometry in
            let compact = geometry.size.height < 500
            Group {
                // Errors retain scrolling, text selection and Export. Normal
                // startup has no disclosure controls, gestures or scroll view.
                if failed { ScrollView { content(compact: compact).padding(24) } }
                else {
                    content(compact: compact)
                        .padding(.horizontal, geometry.size.width < 500 ? 24 : 44)
                        .padding(.vertical, compact ? 14 : 32)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(red: 0.055, green: 0.063, blue: 0.09))
        }
        .tint(rose).preferredColorScheme(.dark)
    }
    private func content(compact: Bool) -> some View {
        VStack(alignment: .leading, spacing: compact ? 12 : 26) {
            VStack(alignment: .leading, spacing: compact ? 4 : 12) {
                if !compact {
                    Image(systemName: "mountain.2.fill").font(.system(size: 48, weight: .light))
                        .foregroundStyle(rose).accessibilityHidden(true)
                }
                Text("CABRILLO").font(.caption.weight(.semibold)).tracking(3).foregroundStyle(.secondary)
                Text(failed ? "Celeste couldn’t start" : "Starting Celeste")
                    .font(compact ? .title2.bold() : .largeTitle.bold()).accessibilityAddTraits(.isHeader)
            }
            VStack(alignment: .leading, spacing: compact ? 8 : 14) {
                Text(title).font(.headline).accessibilityIdentifier("loading.stage")
                if let detail = state["detail"] as? String, !detail.isEmpty {
                    Text(detail).font(.subheadline).foregroundStyle(.secondary)
                        .lineLimit(compact ? 2 : 4).fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("loading.detail")
                }
                if !failed {
                    CabrilloLoadingTrack(fraction: fraction)
                        .frame(height: 5).padding(.vertical, 3)
                        .accessibilityElement().accessibilityLabel(fraction == nil ? "Loading" : "Archives and folders processed")
                        .accessibilityValue(fraction == nil ? "In progress" : "\(number("completed")) of \(number("total"))")
                        .accessibilityIdentifier("loading.progress")
                }
                if number("archives_total", -1) >= 0 {
                    Text("Archives and folders: \(number("archives_processed")) / \(number("archives_total")) · Mod loads completed: \(number("modules_loaded"))")
                        .font(.footnote.monospacedDigit()).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("loading.counts")
                    if !extraCounts.isEmpty {
                        Text(extraCounts).font(.footnote).foregroundStyle(number("load_failures") > 0 ? Color.orange : Color.secondary)
                            .fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("loading.extraCounts")
                    }
                }
                if failed {
                    Text(state["failure"] as? String ?? "Startup stopped before the game was ready.")
                        .font(.subheadline).textSelection(.enabled).accessibilityIdentifier("loading.failure")
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
            .padding(compact ? 14 : 22).frame(maxWidth: .infinity, alignment: .leading)
            .background(.white.opacity(0.045), in: RoundedRectangle(cornerRadius: 18))
            if failed {
                Button("Export diagnostics…", action: exportDiagnostics)
                    .buttonStyle(.borderedProminent).accessibilityIdentifier("loading.export")
                Text("Close this app in the app switcher, then relaunch before trying again.")
                    .font(.footnote).foregroundStyle(.secondary)
            } else {
                Text("Large mods can take a while. Celeste’s loading screen will take over when it’s ready.")
                    .font(.footnote).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
                if canCancelFiles {
                    Button("Cancel file preparation", action: cancelFiles)
                        .font(.subheadline).accessibilityIdentifier("loading.cancelFiles")
                }
            }
        }
        .frame(maxWidth: 540, alignment: .leading)
    }
}

// The moving segment is an indeterminate activity indicator, never a synthetic
// percentage. Core Animation owns its motion; there is no per-frame SwiftUI work
// or extra startup scheduling delay. Counts only change on actual reports.
private struct CabrilloLoadingTrack: UIViewRepresentable {
    let fraction: Double?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    func makeUIView(context: Context) -> LoadingTrackView { LoadingTrackView() }
    func updateUIView(_ view: LoadingTrackView, context: Context) { view.update(fraction: fraction, reduceMotion: reduceMotion) }
}
final class LoadingTrackView: UIView {
    private let fill = CALayer()
    private var fraction: Double?
    private var reduceMotion = false
    private var lastWidth: CGFloat = -1
    override init(frame: CGRect) {
        super.init(frame: frame)
        isUserInteractionEnabled = false
        backgroundColor = UIColor.white.withAlphaComponent(0.10)
        layer.cornerRadius = 2.5; layer.masksToBounds = true
        fill.backgroundColor = UIColor(red: 0.96, green: 0.36, blue: 0.47, alpha: 1).cgColor
        fill.cornerRadius = 2.5; layer.addSublayer(fill)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    func update(fraction: Double?, reduceMotion: Bool) {
        guard fraction != self.fraction || reduceMotion != self.reduceMotion || lastWidth < 0 else { return }
        self.fraction = fraction; self.reduceMotion = reduceMotion; lastWidth = -1
        setNeedsLayout()
    }
    override func layoutSubviews() {
        super.layoutSubviews()
        guard lastWidth != bounds.width else { return }; lastWidth = bounds.width
        CATransaction.begin(); CATransaction.setDisableActions(true)
        fill.removeAnimation(forKey: "activity"); fill.transform = CATransform3DIdentity
        if let fraction {
            fill.frame = CGRect(x: 0, y: 0, width: bounds.width * min(1, max(0, fraction)), height: bounds.height)
        } else {
            let width = bounds.width * 0.24
            fill.frame = CGRect(x: reduceMotion ? (bounds.width - width) / 2 : -width, y: 0, width: width, height: bounds.height)
            if !reduceMotion, bounds.width > 0 {
                let motion = CABasicAnimation(keyPath: "transform.translation.x")
                motion.fromValue = 0; motion.toValue = bounds.width + width
                motion.duration = 1.6; motion.repeatCount = .infinity
                fill.add(motion, forKey: "activity")
            }
        }
        CATransaction.commit()
    }
}
#endif
