
import Foundation
import Darwin
public struct DDIPaths { public static func `default`(in root: URL) -> DDIPaths { DDIPaths() } }
public enum StikJITError: Error {
 case pairingFile(String), ddiDownload(String), ddiFilesMissing(String), ddiNotMounted
 case customScript(String), scriptExecution(String), scriptUnavailable, deviceNotReady(String)
 case device(Int32, Int32, String), debugProxyUnavailable, txmDetectionUnavailable
}
public enum StikJIT {
 public enum Script { case customBase64(String) }
 public struct DeviceSecurityState { public let isTXMPresent: Bool? }
 public enum JITReadiness { case ready(DeviceSecurityState), unreachable(reason: String), preparationFailed(reason: String) }
 public enum PreparationStage { case checkingReachability, checkingDDI, downloadingDDI(fraction: Double,status: String), mountingDDI(fraction: Double), verifyingDDI, ready }
 public static var isTXMPresent: Bool? { false }
 public static func resetCachedDDI(at paths: DDIPaths) throws {}
 public static func prepareDevice(pairingFile: URL, paths: DDIPaths, progress: (PreparationStage)->Void) -> JITReadiness {
  let record: [String:Any] = ["helper_pid":getpid(),"prepare_stub_called":true,"jit_attempted":false]
  let url=FileManager.default.urls(for:.libraryDirectory,in:.userDomainMask)[0].appendingPathComponent("fixture-no-jit.json")
  try? JSONSerialization.data(withJSONObject:record).write(to:url,options:.atomic)
  NSLog("FIXTURE_STIKJIT_PREPARE pid=%d NO_JIT",getpid())
  for stage in [PreparationStage.checkingReachability,.checkingDDI,.ready] { progress(stage);Thread.sleep(forTimeInterval:0.3) }
  return .ready(DeviceSecurityState(isTXMPresent:false))
 }
 public static func enableJIT(targetPID: Int32,pairingFile: URL,ddiPaths: DDIPaths,script: Script,forceScript: Bool,preparationProgress: (PreparationStage)->Void,progress: (String)->Void) throws {
  fatalError("Fixture must never call JIT enablement")
 }
}
