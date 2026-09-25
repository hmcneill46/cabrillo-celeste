#if canImport(UIKit)
import SwiftUI

struct ProfileBackupView: View {
    let state: [String: Any]
    let locked: Bool
    let action: (String, [String: Any]) -> Void
    @State private var confirm: String?
    @State private var removeID = ""
    @State private var details: [String: Any] = [:]
    @State private var showingDetails = false
    private var slotReview: [String: Any] { state["slotReview"] as? [String: Any] ?? [:] }
    private var reviewing: Bool { !review.isEmpty || !slotReview.isEmpty }
    private var cannotImport: Bool { unavailable || reviewing || state["retained"] as? Bool == true }
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
                Text("Your saves, wherever you play").font(.title2.bold())
                Text("Hold a slot or tap its ••• menu to export, replace or duplicate it. Use Files to move a save between your devices.").foregroundStyle(.secondary)
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
            Section("Your save slots") {
                ForEach(slots.indices, id: \.self) { i in
                    let row = slots[i], id = row["id"] as? Int ?? 0
                    HStack(alignment: .top) {
                        slotSummary(row).accessibilityIdentifier("profile.slot.\(id)")
                        Spacer(minLength: 8)
                        Menu { slotActions(row) } label: {
                            Image(systemName: "ellipsis.circle").font(.title3).frame(minWidth: 44, minHeight: 44)
                        }.accessibilityLabel("Actions for slot \(id + 1)").accessibilityIdentifier("profile.slotMenu.\(id)")
                    }.contextMenu { slotActions(row) }
                }
                Button { send("slotImport", ["target": -1]) } label: {
                    Label("Import another save…", systemImage: "plus.circle")
                }.disabled(cannotImport).accessibilityIdentifier("profile.slotNew")
                Text("Slots 1–3 work in vanilla. Everest offers more slots as you fill them. To start a new save, choose an empty slot in the game; importing here uses the first available empty slot.").font(.footnote).foregroundStyle(.secondary)
            }
            if !slotReview.isEmpty {
                SlotTransferReviewView(review: slotReview, unavailable: unavailable, active: active, action: action)
                    .id(slotReview["id"] as? String ?? "")
            }
            Section("Backups") {
                Text("A whole-profile backup also includes game and mod settings and unknown persistent files. It requires the same installed mod archives when restoring. Game files, mod ZIPs and files stored outside this profile are not included.").font(.footnote).foregroundStyle(.secondary)

                Button("Create whole-profile backup") { send("create") }.disabled(unavailable || reviewing).accessibilityIdentifier("profile.create")
                Button("Import backup from Files…") { send("import") }.disabled(unavailable || reviewing || state["retained"] as? Bool == true).accessibilityIdentifier("profile.import")
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
                                Button("Review restore…") { send("review", ["id": id]) }.disabled(unavailable || reviewing || state["retained"] as? Bool == true).accessibilityIdentifier("profile.review.\(i)")
                            }.buttonStyle(.borderless)
                            Button("Remove backup…", role: .destructive) { removeID = id; confirm = "remove" }.font(.caption).disabled(unavailable || reviewing)
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

        }.navigationTitle("Saves")
            .sheet(isPresented: $showingDetails) {
                CJNavigation {
                    List {
                        Section { slotSummary(details) }
                        Section("Files in this slot") {
                            ForEach(details["filenames"] as? [String] ?? [], id: \.self) { Text($0).font(.caption).textSelection(.enabled) }
                        }
                        Section {
                            Text("Slot 1 is 0.celeste on disk; slots 2 and 3 are 1.celeste and 2.celeste. Keep a slot’s numbered mod files together for Everest.")
                            Text("Transfers preserve file contents. Compatible game and mod versions are needed; a copied file’s date alone does not prove it has the latest progress.")
                        }.font(.footnote)
                    }.navigationTitle("Save details").toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { showingDetails = false } } }
                }
            }
            .alert(confirmTitle, isPresented: Binding(get: { confirm != nil }, set: { if !$0 { confirm = nil } })) {
                Button("Cancel", role: .cancel) { confirm = nil }
                Button(confirmTitle, role: .destructive) {
                    let command = confirm ?? ""; confirm = nil
                    send(command, ["id": command == "remove" ? removeID : review["id"] as? String ?? ""])
                }.accessibilityIdentifier("profile.confirm")
            } message: { Text(confirmMessage) }
    }
    private func slotSummary(_ row: [String: Any]) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text("Slot \(row["slot"] as? Int ?? 0)" + ((row["name"] as? String).map { " · " + $0 } ?? "")).font(.headline)
            Text(row["summary"] as? String ?? "Summary unavailable").font(.subheadline).foregroundStyle(.secondary)
            if let modified = row["modified"] as? String { Text("Saved " + date(modified)).font(.caption).foregroundStyle(.secondary) }
            if row["empty"] as? Bool != true { Text("\(row["files"] as? Int ?? 0) save and mod files").font(.caption).foregroundStyle(.secondary) }
            if let version = row["version"] as? String { Text("Celeste " + version).font(.caption).foregroundStyle(.secondary) }
        }
    }
    @ViewBuilder private func slotActions(_ row: [String: Any]) -> some View {
        let id = row["id"] as? Int ?? 0, empty = row["empty"] as? Bool == true
        if !empty {
            Button("Export save + mod data…", systemImage: "square.and.arrow.up") { send("slotExport", ["slot": id, "mainOnly": false]) }.disabled(unavailable || reviewing).accessibilityIdentifier("profile.slotExport")
            if row["hasMain"] as? Bool == true {
                Button("Export main .celeste file…", systemImage: "doc") { send("slotExport", ["slot": id, "mainOnly": true]) }.disabled(unavailable || reviewing).accessibilityIdentifier("profile.slotExportMain")
                Button("Duplicate into empty slot…", systemImage: "doc.on.doc") { send("slotDuplicate", ["slot": id]) }.disabled(cannotImport).accessibilityIdentifier("profile.slotDuplicate")
            }
        }
        Button(empty ? "Import from Files…" : "Replace from Files…", systemImage: "square.and.arrow.down") { send("slotImport", ["target": id]) }.disabled(cannotImport).accessibilityIdentifier("profile.slotReplace")
        Button("Save details", systemImage: "info.circle") { details = row; showingDetails = true }.accessibilityIdentifier("profile.slotDetails")
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

#if canImport(UIKit)
private struct SlotTransferReviewView: View {
    let review: [String: Any]
    let unavailable: Bool
    let active: Bool
    let action: (String, [String: Any]) -> Void
    @State private var keepModData = true
    @State private var confirming = false
    private var target: Int { (review["target"] as? Int ?? 0) + 1 }
    private var mainOnly: Bool { review["mainOnly"] as? Bool == true }
    private var existing: [String: Any] { review["existing"] as? [String: Any] ?? [:] }
    var body: some View {
        Section("Review import · slot \(target)") {
            comparison("Incoming save", review["incoming"] as? [String: Any] ?? [:])
            comparison("Currently in slot \(target)", existing)
            if mainOnly {
                Toggle("Keep this slot’s existing mod files", isOn: $keepModData).disabled(unavailable).accessibilityIdentifier("profile.keepModData")
                Text(keepModData ? "Only the main save is replaced. Existing mod files stay available—use this when bringing the same climb back from vanilla." : "The main save is replaced and this slot’s old mod files are removed from the active profile. Use this for a different climb.").font(.footnote).foregroundStyle(.secondary)
            } else {
                Text("This replaces the slot’s main save and mod files together. Old mod files for this slot are removed from the active profile to avoid mixing two different saves.").font(.footnote)
            }
            Text("Other slots and settings stay as they are. Your complete current profile is retained for rollback. Close and relaunch after importing.").font(.footnote)
            Text("Modded progress needs compatible Everest, maps and mods on the destination. No mods are installed by this transfer. Dates alone cannot tell which copy is newest; compare progress before replacing.").font(.footnote).foregroundStyle(.secondary)
            DisclosureGroup("Files to import") {
                ForEach(review["files"] as? [String] ?? [], id: \.self) { Text($0).font(.caption).textSelection(.enabled) }
            }
            Button("Import into slot \(target)…") { confirming = true }.disabled(unavailable).accessibilityIdentifier("profile.slotCommit")
            Button("Cancel import") { action("profile.cancel", [:]) }.disabled(active).accessibilityIdentifier("profile.slotCancel")
        }
            .alert("Import into slot \(target)?", isPresented: $confirming) {
                Button("Cancel", role: .cancel) {}
                Button("Import save", role: .destructive) { action("profile.slotCommit", ["id": review["id"] as? String ?? "", "keepModData": mainOnly && keepModData]) }.accessibilityIdentifier("profile.slotConfirm")
            } message: { Text("The reviewed files will replace this slot. The complete current profile will be retained for rollback. Relaunch before playing.") }
    }
    private func comparison(_ title: String, _ row: [String: Any]) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title).font(.headline)
            if let name = row["name"] as? String { Text(name) }
            Text(row["summary"] as? String ?? "Empty slot").foregroundStyle(.secondary)
            if let stamp = row["modified"] as? String, let date = ISO8601DateFormatter().date(from: stamp) { Text("Saved " + date.formatted(date: .abbreviated, time: .shortened)).font(.caption) }
            if let version = row["version"] as? String { Text("Celeste " + version).font(.caption) }
        }.padding(.vertical, 4)
    }
}
#endif
