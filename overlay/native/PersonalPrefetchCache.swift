import Foundation

/// Experimental transport-independent, bounded cache; no network requests or credentials.
/// Caller must establish authorized resource identity and a fresh strong validator.
final class PersonalPrefetchCache {
    struct Identity: Equatable {
        let profile: Int
        let resource: UUID
        let etag: String
        let length: Int64
        var valid: Bool {
            length > 0 && etag.count >= 2 && etag.count <= 256 && etag.hasPrefix("\"") && etag.hasSuffix("\"") &&
            !etag.dropFirst().dropLast().contains("\"") && !etag.contains("\r") && !etag.contains("\n")
        }
    }
    private struct Entry { let identity: Identity; let offset: Int64; let data: Data; let stored: Double }
    private let lock = NSLock()
    private var entry: Entry?
    static let limit = 4 * 1024 * 1024
    static let lifetime = 90.0
    @discardableResult
    func store(identity: Identity, offset: Int64, requestedCount: Int, status: Int,
               contentRange: String, responseETag: String, body: Data, now: Double) -> Bool {
        lock.lock(); defer { lock.unlock() }
        guard identity.valid, now.isFinite, now >= 0, status == 206, responseETag == identity.etag,
              offset >= 0, offset < identity.length, requestedCount > 0, requestedCount <= Self.limit else { return false }
        let expected = Int(min(Int64(requestedCount), identity.length-offset))
        guard body.count == expected, contentRange == "bytes \(offset)-\(offset+Int64(expected)-1)/\(identity.length)" else { return false }
        entry = Entry(identity: identity, offset: offset, data: body, stored: now)
        return true
    }
    /// Partial hits are allowed; reader must fetch remainder normally.
    func read(identity: Identity, offset: Int64, count: Int, now: Double) -> Data? {
        lock.lock(); defer { lock.unlock() }
        guard let e = entry else { return nil }
        guard now.isFinite, now >= e.stored, now-e.stored <= Self.lifetime else { entry = nil; return nil }
        guard identity.valid, e.identity == identity, offset >= e.offset, count > 0, count <= Self.limit,
              offset-e.offset < Int64(e.data.count) else { return nil }
        let start = Int(offset-e.offset), end = min(start+count,e.data.count)
        return e.data.subdata(in: start..<end)
    }
    func clear() { lock.lock(); entry = nil; lock.unlock() }
}
