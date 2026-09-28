import Foundation
import CryptoKit
import Darwin

// Streaming xxHash64, seed zero, following the published xxHash algorithm.
// This is the upstream download integrity check, not a publisher signature.
struct XXHash64 {
    private static let p1: UInt64 = 11400714785074694791
    private static let p2: UInt64 = 14029467366897019727
    private static let p3: UInt64 = 1609587929392839161
    private static let p4: UInt64 = 9650029242287828579
    private static let p5: UInt64 = 2870177450012600261
    private var a = p1 &+ p2, b = p2, c: UInt64 = 0, d = UInt64(0) &- p1
    private var total: UInt64 = 0
    private var tail = Data()
    private static func rotate(_ x: UInt64, _ n: UInt64) -> UInt64 { (x << n) | (x >> (64 - n)) }
    private static func round(_ x: UInt64, _ y: UInt64) -> UInt64 { rotate(x &+ y &* p2, 31) &* p1 }
    private mutating func stripe(_ bytes: UnsafeRawBufferPointer, _ offset: Int) {
        a = Self.round(a, UInt64(littleEndian: bytes.loadUnaligned(fromByteOffset: offset, as: UInt64.self)))
        b = Self.round(b, UInt64(littleEndian: bytes.loadUnaligned(fromByteOffset: offset + 8, as: UInt64.self)))
        c = Self.round(c, UInt64(littleEndian: bytes.loadUnaligned(fromByteOffset: offset + 16, as: UInt64.self)))
        d = Self.round(d, UInt64(littleEndian: bytes.loadUnaligned(fromByteOffset: offset + 24, as: UInt64.self)))
    }
    mutating func update(_ data: Data) {
        total &+= UInt64(data.count)
        var offset = 0
        if !tail.isEmpty {
            let needed = min(32 - tail.count, data.count)
            tail.append(data.prefix(needed)); offset = needed
            if tail.count == 32 {
                let block = tail; block.withUnsafeBytes { stripe($0, 0) }; tail.removeAll(keepingCapacity: true)
            }
        }
        data.withUnsafeBytes { bytes in
            while offset + 32 <= data.count { stripe(bytes, offset); offset += 32 }
        }
        if offset < data.count { tail.append(data.suffix(data.count - offset)) }
    }
    func finish() -> String {
        var h: UInt64
        if total >= 32 {
            h = Self.rotate(a, 1) &+ Self.rotate(b, 7) &+ Self.rotate(c, 12) &+ Self.rotate(d, 18)
            for v in [a, b, c, d] { h = (h ^ Self.round(0, v)) &* Self.p1 &+ Self.p4 }
        } else { h = Self.p5 }
        h &+= total
        tail.withUnsafeBytes { bytes in
            var i = 0
            while i + 8 <= bytes.count {
                h ^= Self.round(0, UInt64(littleEndian: bytes.loadUnaligned(fromByteOffset: i, as: UInt64.self)))
                h = Self.rotate(h, 27) &* Self.p1 &+ Self.p4; i += 8
            }
            if i + 4 <= bytes.count {
                h ^= UInt64(UInt32(littleEndian: bytes.loadUnaligned(fromByteOffset: i, as: UInt32.self))) &* Self.p1
                h = Self.rotate(h, 23) &* Self.p2 &+ Self.p3; i += 4
            }
            while i < bytes.count { h ^= UInt64(bytes[i]) &* Self.p5; h = Self.rotate(h, 11) &* Self.p1; i += 1 }
        }
        h ^= h >> 33; h &*= Self.p2; h ^= h >> 29; h &*= Self.p3; h ^= h >> 32
        return String(format: "%016llx", h)
    }
}

struct DownloadIdentity: Codable {
    let sha256: String
    let xxHash: String
    let bytes: UInt64
    static func read(_ url: URL) throws -> DownloadIdentity {
        let fd = open(url.path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw LibraryError("Cannot read the downloaded file.") }
        let file = FileHandle(fileDescriptor: fd, closeOnDealloc: true); defer { try? file.close() }
        var st = stat()
        guard fstat(fd, &st) == 0, (st.st_mode & S_IFMT) == S_IFREG, st.st_size > 0, st.st_size <= 4_294_967_296 else { throw LibraryError("The download is not a supported regular ZIP.") }
        var sha = SHA256(), xx = XXHash64(), count: UInt64 = 0
        while let data = try file.read(upToCount: 65_536), !data.isEmpty {
            count += UInt64(data.count); guard count <= UInt64(st.st_size) else { throw LibraryError("The download changed during verification.") }
            sha.update(data: data); xx.update(data)
        }
        guard count == UInt64(st.st_size) else { throw LibraryError("The download is incomplete.") }
        return DownloadIdentity(sha256: sha.finalize().map { String(format: "%02x", $0) }.joined(), xxHash: xx.finish(), bytes: count)
    }
}
