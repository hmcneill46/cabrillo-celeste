#if canImport(UIKit)
import SwiftUI

struct ProfileBackupView: View {
    let state: [String: Any]
    let locked: Bool
    let action: (String, [String: Any]) -> Void
    @State private var confirm: String?
    @State private var removeID = ""
    private var review: [String: Any] { state["review"] as? [String: Any] ?? [:] }
    private var backups: [[String: Any]] { state["backups"] as? [[String: Any]] ?? [] }
    private var slots: [[String: Any]] { state["slots"] as? [[String: Any]] ?? [] }
    private var active: Bool { state["active"] as? Bool == true }
    private var unavailable: Bool { locked || active || state["ready"] as? Bool != true || state["restartRequired"] as? Bool == true }
    private func send(_ name: String, _ values: [String: Any] = [:]) { action("profile." + name, values) }
    private func date(_ text: String) -> String {
        guard let date = ISO8601DateFormatter().date(from: text) else { return text }
        return date.formatted(date: .abbreviated, time: .shortened)
    }
    private func summary(_ row: [String: Any]) -> String {
        let size = ByteCountFormatter.string(fromByteCount: (row["bytes"] as? NSNumber)?.int64Value ?? 0, countStyle: .file)
        return "\(row["slots"] as? Int ?? 0) saves · \(row["files"] as? Int ?? 0) files · \(size)"
    }
    var body: some View {
        List {
            Section {
                Text("Keep your whole climb").font(.title2.bold())
                Text("Back up every save slot, game and mod settings, and other persistent profile files.").foregroundStyle(.secondary)
                Text("Game files and mod ZIPs stay out of the backup. Restoring requires the same installed mod archives; their identities and enabled choices are recorded.").font(.footnote).foregroundStyle(.secondary)
                Text("Files a mod stores outside this profile are not included.").font(.footnote).foregroundStyle(.secondary)
            }
            if active || state["message"] != nil {
                Section {
                    if active { ProgressView("Working with your profile…").accessibilityIdentifier("profile.working") }
                    if let message = state["message"] as? String { Text(message).textSelection(.enabled).accessibilityIdentifier("profile.message") }
                    if state["restartRequired"] as? Bool == true {
                        Label("Close Cabrillo in the app switcher and relaunch before playing.", systemImage: "arrow.clockwise").accessibilityIdentifier("profile.restart")
                    }
                    if state["error"] as? Bool == true { Button("Export diagnostics…") { action("export", [:]) }.accessibilityIdentifier("profile.exportDiagnostics") }
                }
            }
            if locked && !active {
                Section { Text("Close and relaunch after playing to back up or restore. Profile changes are available before the game starts.").font(.footnote) }
            }
            Section("Backups") {
                Button("Create whole-profile backup") { send("create") }.disabled(unavailable || !review.isEmpty).accessibilityIdentifier("profile.create")
                Button("Import backup from Files…") { send("import") }.disabled(unavailable || !review.isEmpty || state["retained"] as? Bool == true).accessibilityIdentifier("profile.import")
                ForEach(backups.indices, id: \.self) { i in
                    let row = backups[i], id = row["id"] as? String ?? ""
                    VStack(alignment: .leading, spacing: 8) {
                        Text(date(row["created"] as? String ?? "Backup")).font(.headline)
                        if let error = row["error"] as? String { Text(error).font(.caption).foregroundStyle(.orange) }
                        else {
                            Text(summary(row)).font(.caption).foregroundStyle(.secondary)
                            HStack {
                                Button("Export…") { send("export", ["id": id]) }.disabled(locked || active || state["ready"] as? Bool != true).accessibilityIdentifier("profile.export.\(i)")
                                Spacer()
                                Button("Review restore…") { send("review", ["id": id]) }.disabled(unavailable || !review.isEmpty || state["retained"] as? Bool == true).accessibilityIdentifier("profile.review.\(i)")
                            }.buttonStyle(.borderless)
                            Button("Remove backup…", role: .destructive) { removeID = id; confirm = "remove" }.font(.caption).disabled(unavailable || !review.isEmpty)
                        }
                    }.padding(.vertical, 5)
                }
            }
            if !review.isEmpty {
                Section("Review restore") {
                    Text(date(review["created"] as? String ?? "" )).font(.headline)
                    Text(summary(review))
                    Text("This replaces the complete profile. Saves created after this backup will leave the active profile. The current profile is retained locally so you can roll back.").font(.subheadline)
                    let issues = review["issues"] as? [String] ?? []
                    if issues.isEmpty { Label("Installed mod archives match", systemImage: "checkmark.circle").foregroundStyle(.green) }
                    else {
                        Text("Restore needs attention").font(.headline).foregroundStyle(.orange)
                        ForEach(issues, id: \.self) { Text($0).font(.caption).textSelection(.enabled) }
                        Text("Cancel this review and resolve the archive differences in Mods, then import the backup again.").font(.footnote)
                    }
                    DisclosureGroup("Recorded mod choices") {
                        let mods = review["mods"] as? [[String: Any]] ?? []
                        ForEach(mods.indices, id: \.self) { i in
                            let mod = mods[i]
                            VStack(alignment: .leading) {
                                Text(mod["filename"] as? String ?? "Archive")
                                Text(mod["enabled"] as? Bool == true ? "Enabled" : "Disabled").font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                    Button("Restore this backup…", role: .destructive) { confirm = "restore" }.disabled(unavailable || !issues.isEmpty).accessibilityIdentifier("profile.restore")
                    Button("Cancel review") { send("cancel") }.disabled(active).accessibilityIdentifier("profile.cancel")
                }
            }
            if state["retained"] as? Bool == true {
                Section("Retained profile") {
                    Text("A complete profile is retained on this device. Keep it until you have checked your restored saves.").font(.subheadline)
                    if state["canRollback"] as? Bool == true {
                        Button("Roll back to previous profile…") { confirm = "rollback" }.disabled(unavailable).accessibilityIdentifier("profile.rollback")
                    }
                    Button("Discard retained profile…", role: .destructive) { confirm = "discard" }.disabled(unavailable).accessibilityIdentifier("profile.discard")
                    Text("Discarding frees the retained copy and allows another restore. Export a backup first if you want to keep that profile.").font(.footnote).foregroundStyle(.secondary)
                }
            }
            Section("Your save slots · \(slots.count)") {
                if slots.isEmpty { Text("No save slots yet. Everest adds an empty slot as existing slots fill.").foregroundStyle(.secondary) }
                ForEach(slots.indices, id: \.self) { i in
                    let row = slots[i]
                    VStack(alignment: .leading, spacing: 5) {
                        Text("Slot \(row["slot"] as? Int ?? 0)" + ((row["name"] as? String).map { " · " + $0 } ?? "")).font(.headline)
                        Text(row["summary"] as? String ?? "Summary unavailable").font(.subheadline).foregroundStyle(.secondary)
                        if let modified = row["modified"] as? String { Text("Saved " + date(modified)).font(.caption).foregroundStyle(.secondary) }
                        Text("\(row["files"] as? Int ?? 0) save and mod files").font(.caption).foregroundStyle(.secondary)
                    }.accessibilityIdentifier("profile.slot.\(row["id"] as? Int ?? 0)")
                }
            }
        }.navigationTitle("Saves")
            .alert(confirmTitle, isPresented: Binding(get: { confirm != nil }, set: { if !$0 { confirm = nil } })) {
                Button("Cancel", role: .cancel) { confirm = nil }
                Button(confirmTitle, role: .destructive) {
                    let command = confirm ?? ""; confirm = nil
                    send(command, ["id": command == "remove" ? removeID : review["id"] as? String ?? ""])
                }.accessibilityIdentifier("profile.confirm")
            } message: { Text(confirmMessage) }
    }
    private var confirmTitle: String { ["restore": "Replace profile", "rollback": "Restore previous profile", "discard": "Discard retained copy", "remove": "Remove backup"][confirm ?? ""] ?? "Confirm" }
    private var confirmMessage: String {
        switch confirm {
        case "restore": return "The reviewed backup will replace every persistent profile file. Your current profile will be retained for rollback. Relaunch afterward."
        case "rollback": return "Your current saves and settings will be replaced by the complete profile retained before restoring. Relaunch afterward."
        case "discard": return "This permanently removes the retained copy. Your active profile and saved backup ZIPs stay available."
        default: return "This removes this local backup ZIP. Any copy you exported to Files remains available."
        }
    }
}
#endif
