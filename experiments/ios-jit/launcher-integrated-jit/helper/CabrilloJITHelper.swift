import Foundation
import Darwin
import CoreFoundation
import StikJIT

// Credential bytes travel only in the extension request and a protected,
// extension-local temporary plist. No App Group, log stream, or shared file IPC.
private struct HelperRequest: Decodable {
    let schema: Int
    let operation: String
    let requestID: String
    let targetPID: Int32
    let pairingBase64: String
    let scriptBase64: String
    let requiresScript: Bool
    let progressToken: String
}

private struct HelperResponse: Encodable {
    let schema = 1
    let requestID: String
    let success: Bool
    let code: String
    let txmPresent: Bool?
    var deviceCode: Int? = nil
    var deviceSubCode: Int? = nil
}

private enum HelperWorker {
    static let queue = DispatchQueue(label: "org.cabrillo.integrated-jit.worker")
    static let pairingLimit = 1024 * 1024

    static func pairingIsValid(_ data: Data) -> Bool {
        guard !data.isEmpty, data.count <= pairingLimit,
              let object = try? PropertyListSerialization.propertyList(from: data, options: [], format: nil),
              let row = object as? [String: Any],
              let publicKey = row["public_key"] as? Data, publicKey.count == 32,
              let privateKey = row["private_key"] as? Data, privateKey.count == 32,
              let identifier = row["identifier"] as? String, !identifier.isEmpty, identifier.count <= 4096 else { return false }
        return true
    }

    static func perform(_ request: HelperRequest) -> HelperResponse {
        func response(_ success: Bool, _ code: String, deviceReason: String? = nil) -> HelperResponse {
            var result = HelperResponse(requestID: request.requestID, success: success, code: code, txmPresent: StikJIT.isTXMPresent)
            if let text = deviceReason,
               let expression = try? NSRegularExpression(pattern: #"\(idevice code (-?[0-9]{1,10})/(-?[0-9]{1,10})\)"#),
               let match = expression.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)),
               let first = Range(match.range(at: 1), in: text), let second = Range(match.range(at: 2), in: text) {
                result.deviceCode = Int(text[first]); result.deviceSubCode = Int(text[second])
            }
            return result
        }
        guard request.schema == 1, !request.requestID.isEmpty, request.requestID.count <= 128,
              ["prepare", "enable", "reset"].contains(request.operation), UUID(uuidString: request.progressToken) != nil else {
            return response(false, "request")
        }
        // Notifications contain only a fixed stage and an unlogged random token.
        // They never decide readiness; the authenticated extension result does.
        var stagesSent = Set<String>()
        func stage(_ name: String) {
            guard stagesSent.insert(name).inserted else { return }
            let name = "org.cabrillo.jit.\(request.progressToken).\(name)"
            CFNotificationCenterPostNotification(CFNotificationCenterGetDarwinNotifyCenter(),
                CFNotificationName(rawValue: name as CFString), nil, nil, true)
        }
        var preparationStage = ""
        func preparation(_ value: StikJIT.PreparationStage) {
            switch value {
            case .checkingReachability: preparationStage = "reachability"
            case .checkingDDI: preparationStage = "ddi"
            case .downloadingDDI: preparationStage = "download"
            case .mountingDDI: preparationStage = "mount"
            case .verifyingDDI: preparationStage = "verify"
            case .ready: preparationStage = "prepared"
            @unknown default: break
            }
            if !preparationStage.isEmpty { stage(preparationStage) }
        }
        func preparationFailure(_ reason: String) -> HelperResponse {
            let lower = reason.lowercased()
            let code: String
            if lower.hasPrefix("pairing file error:") { code = "pairing" }
            else if lower.hasPrefix("failed to download developer disk image:") || preparationStage == "download" { code = "ddi-download" }
            else if preparationStage == "mount" || preparationStage == "verify" || lower.hasPrefix("developer disk image files missing:") { code = "ddi-mount" }
            else if lower.contains("failed to create rsd tunnel") || lower.contains("failed to read pairing file") { code = "pairing-connection" }
            else { code = "preparation" }
            return response(false, code, deviceReason: reason)
        }
        let manager = FileManager.default
        let root = manager.urls(for: .libraryDirectory, in: .userDomainMask)[0].appendingPathComponent("StikJIT", isDirectory: true)
        let paths = DDIPaths.default(in: root)
        do {
            try manager.createDirectory(at: root, withIntermediateDirectories: true,
                                        attributes: [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication])
            var excluded = URLResourceValues(); excluded.isExcludedFromBackup = true
            var protectedRoot = root; try protectedRoot.setResourceValues(excluded)
            // Remove only credential remnants from interrupted older requests.
            let leftovers = try manager.contentsOfDirectory(at: root, includingPropertiesForKeys: nil)
            for item in leftovers.prefix(128) where item.lastPathComponent.hasPrefix("session-") && item.pathExtension == "plist" {
                try? manager.removeItem(at: item)
            }
            if request.operation == "reset" {
                try StikJIT.resetCachedDDI(at: paths)
                return response(true, "reset")
            }
            guard let pairing = Data(base64Encoded: request.pairingBase64), pairingIsValid(pairing) else { return response(false, "pairing") }
            let temporary = root.appendingPathComponent("session-\(UUID().uuidString).plist")
            try pairing.write(to: temporary, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
            defer { try? manager.removeItem(at: temporary) }
            if request.operation == "prepare" {
                switch StikJIT.prepareDevice(pairingFile: temporary, paths: paths, progress: preparation) {
                case .ready: return response(true, "ready")
                case .unreachable: return response(false, "unreachable")
                case .preparationFailed(let reason): return preparationFailure(reason)
                @unknown default: return response(false, "preparation")
                }
            }
            // The exact Cabrillo mailbox script is mandatory on26+, even if TXM
            // detection fails or reports false. Never substitute universal.js.
            let force: Bool
            if #available(iOS 26.0, *) { force = true } else { force = request.requiresScript }
            guard request.targetPID > 0, request.targetPID != getpid(),
                  let script = Data(base64Encoded: request.scriptBase64), script.count <= 262144,
                  (!force || (!script.isEmpty && String(data: script, encoding: .utf8) != nil)) else { return response(false, "request") }
            try StikJIT.enableJIT(targetPID: request.targetPID, pairingFile: temporary, ddiPaths: paths,
                                 script: .customBase64(request.scriptBase64), forceScript: force,
                                 preparationProgress: preparation, progress: { _ in stage("debugging") })
            // The host must independently pass its native memory tests and prove
            // known debugger detach; this result alone never authorizes gameplay.
            return response(true, "enabled")
        } catch let error as StikJITError {
            switch error {
            case .pairingFile: return response(false, "pairing")
            case .ddiDownload: return response(false, "ddi-download")
            case .ddiFilesMissing, .ddiNotMounted: return response(false, "ddi-mount")
            case .customScript, .scriptExecution, .scriptUnavailable: return response(false, "script")
            case .deviceNotReady(let reason): return preparationFailure(reason)
            case .device(let code, let subCode, _):
                var result = response(false, "debugger"); result.deviceCode = Int(code); result.deviceSubCode = Int(subCode); return result
            case .debugProxyUnavailable: return response(false, "debugger")
            case .txmDetectionUnavailable: return response(false, "txm")
            @unknown default: return response(false, "helper")
            }
        } catch { return response(false, "storage") }
    }
}

@objc(CabrilloJITHelperHandler)
final class CabrilloJITHelperHandler: NSObject, NSExtensionRequestHandling {
    func beginRequest(with context: NSExtensionContext) {
        let data = (context.inputItems.first as? NSExtensionItem)?.userInfo?["org.cabrillo.integrated-jit.request.v1"] as? Data
        HelperWorker.queue.async {
            let result: HelperResponse
            if let data, data.count <= 2 * 1024 * 1024, let request = try? JSONDecoder().decode(HelperRequest.self, from: data) {
                result = HelperWorker.perform(request)
            } else { result = HelperResponse(requestID: "", success: false, code: "request", txmPresent: nil) }
            let item = NSExtensionItem()
            item.userInfo = ["org.cabrillo.integrated-jit.response.v1": (try? JSONEncoder().encode(result)) ?? Data()]
            context.completeRequest(returningItems: [item], completionHandler: nil)
        }
    }
}
