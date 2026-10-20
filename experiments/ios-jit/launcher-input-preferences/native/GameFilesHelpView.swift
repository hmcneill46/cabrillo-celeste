#if canImport(UIKit)
import SwiftUI

struct GameFilesHelpView: View {
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        CJNavigation {
            List {
                Section("Choose a copy you own") {
                    Text("Use a clean Celeste 1.4.0.0 FNA download from itch.io, Steam or Epic. Windows, macOS and Linux game files can work on your iPhone or iPad.")
                    Text("You only need one ZIP. Keep the whole game folder, including Celeste.exe, FNA.dll and Content. Cabrillo prepares Everest when you first play.")
                }
                Section("itch.io") {
                    Text("Open your owned Celeste download page. Choose the Windows OpenGL/FNA, Linux or macOS 1.4.0.0 ZIP, save it in Files, then import it here. Keep an original downloaded ZIP intact.")
                }
                Section("Steam · use a computer") {
                    Text("Sign into Steam with an account that owns Celeste. Open this address in the computer’s browser:")
                    Text("steam://open/console").font(.callout.monospaced()).textSelection(.enabled)
                    Text("In Steam’s Console tab, enter this command for the supported Linux depot. These files work in Cabrillo even if your computer is a Mac or Windows PC:")
                    Text("download_depot 504230 504233 5880027853585448535").font(.callout.monospaced()).textSelection(.enabled)
                    Text("Wait for “Depot download complete”, open the folder at the printed path, and ZIP the whole folder. Copy that ZIP to Files on this device. The usual Windows download may be XNA; use this depot instead.")
                    Text("Steam achievements and Steam Cloud are unavailable in Cabrillo. Your local game progress and manual save transfers still work.").foregroundStyle(.secondary)
                }
                Section("Epic Games Store") {
                    Text("Download a clean Windows or macOS FNA 1.4.0.0 copy from your account, then ZIP its whole game folder. The supported Epic Windows package has no Celeste.Content.dll; Cabrillo handles that automatically.")
                    Text("Legendary is an optional downloader for your computer. After installing it, run “legendary auth”, then “legendary list”. Use Celeste’s App Name from that list with “legendary install APP_NAME --platform Mac --download-only” (or --platform Windows). ZIP the completed download folder.")
                    Link("Legendary download and instructions", destination: URL(string: "https://github.com/legendary-gl/legendary")!)
                }
                Section("ZIP and import") {
                    Text("On a Mac, right-click the game folder or Celeste.app in Finder and choose Compress. On Windows, use Compress to ZIP or Send to → Compressed folder. Keep one complete game installation per ZIP.")
                    Text("Save the ZIP to Files and choose Import game ZIP in Cabrillo. Enable JIT, then Run Celeste. The first launch prepares your copy; later launches reuse it.")
                    Text("Use an unmodified FNA copy. Other game versions, XNA and folders already patched by Everest are unsupported. Do not mix files from different downloads.")
                }
                Section("Changing copies") {
                    Text("Quit Celeste normally, close and relaunch Cabrillo, then choose the new ZIP. Your saves and mod choices are kept. Importing game files does not import desktop saves; use the Saves tab to transfer them.")
                }
            }
            .navigationTitle("Game files")
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
    }
}
#endif
