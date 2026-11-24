import Foundation

// A single-reader, seekable transport. Fetch closure must supply an exact conditional
// range or nil; a validator change is an error, never a silent splice of two files.
final class PersonalRangeReader {
    struct Reply {
        let status: Int
        let range: String
        let etag: String
        let encoding: String?
        let body: Data
    }
    typealias Fetch = (Int64, Int, String) -> Reply?
    let identity: PersonalPrefetchCache.Identity
    private let cache: PersonalPrefetchCache
    private let fetch: Fetch
    private let clock: () -> Double
    private let state = NSLock()
    private var cancelled = false
    private var position: Int64 = 0
    private var generation: UInt64 = 0
    private var chunkOffset: Int64 = 0
    private var chunk = Data()
    private let stop: () -> Void
    private(set) var servedPrefetchBytes = 0
    static let chunkSize = 1024 * 1024

    init?(identity: PersonalPrefetchCache.Identity, cache: PersonalPrefetchCache,
          clock: @escaping () -> Double, fetch: @escaping Fetch, stop: @escaping () -> Void = {}) {
        guard identity.valid else { return nil }
        self.identity = identity; self.cache = cache; self.clock = clock; self.fetch = fetch; self.stop = stop
    }
    deinit { cancel() }
    func seek(_ offset: Int64) -> Int64 {
        state.lock(); defer { state.unlock() }
        guard !cancelled, offset >= 0, offset <= identity.length else { return -1 }
        generation &+= 1; position = offset; return offset
    }
    func cancel() {
        state.lock()
        guard !cancelled else { state.unlock(); return }
        cancelled = true; generation &+= 1; chunk = Data(); state.unlock()
        stop()
    }
    // nil means read error; empty data means EOF. Callbacks are serialized by MPV except cancel.
    func read(_ requested: Int) -> Data? {
        state.lock()
        guard !cancelled, requested > 0 else { state.unlock(); return nil }
        let offset = position, token = generation
        let count = Int(min(Int64(min(requested, Self.chunkSize)), identity.length-offset))
        if count == 0 { state.unlock(); return Data() }
        if let hit = cache.read(identity: identity, offset: offset, count: count, now: clock()) {
            position += Int64(hit.count); servedPrefetchBytes += hit.count; state.unlock(); return hit
        }
        if offset >= chunkOffset, offset-chunkOffset < Int64(chunk.count) {
            let start = Int(offset-chunkOffset), end = min(start+count, chunk.count)
            let hit = chunk.subdata(in: start..<end); position += Int64(hit.count); state.unlock(); return hit
        }
        state.unlock()
        let fetchCount = Int(min(Int64(Self.chunkSize), identity.length-offset))
        guard let reply = fetch(offset, fetchCount, identity.etag),
              Self.valid(reply, identity: identity, offset: offset, count: fetchCount) else { return nil }
        state.lock(); defer { state.unlock() }
        guard !cancelled, generation == token, position == offset else { return nil }
        chunkOffset = offset; chunk = reply.body
        let output = chunk.prefix(count)
        position += Int64(output.count)
        return Data(output)
    }
    static func valid(_ r: Reply, identity: PersonalPrefetchCache.Identity, offset: Int64, count: Int) -> Bool {
        guard identity.valid, offset >= 0, offset < identity.length, count > 0,
              Int64(count) <= identity.length-offset, r.status == 206,
              r.etag == identity.etag, r.body.count == count,
              r.encoding == nil || r.encoding?.lowercased() == "identity" else { return false }
        return r.range == "bytes \(offset)-\(offset+Int64(count)-1)/\(identity.length)"
    }
    static func directFile(_ raw: String) -> URL? {
        guard let c = URLComponents(string: raw), c.scheme?.lowercased() == "https", let host = c.host,
              !host.isEmpty, !host.contains(":"), host.contains("."),
              !host.lowercased().hasSuffix(".local"), !host.lowercased().hasSuffix(".localhost"),
              !host.allSatisfy({ $0.isNumber || $0 == "." }),
              c.user == nil, c.password == nil, c.query == nil, c.fragment == nil,
              c.port == nil || c.port == 443, let u = c.url,
              ["mp4", "mkv", "webm", "mov", "m4v"].contains(u.pathExtension.lowercased()) else { return nil }
        return u
    }
    // Parse only exact, bounded, complete first-range replies with strong identity.
    static func identity(profile: Int, resource: UUID, reply: Reply, requested: Int) -> PersonalPrefetchCache.Identity? {
        guard requested > 0, requested <= PersonalPrefetchCache.limit,
              reply.range.hasPrefix("bytes 0-"), let slash = reply.range.lastIndex(of: "/"),
              let length = Int64(reply.range[reply.range.index(after: slash)...]), length > 0 else { return nil }
        let id = PersonalPrefetchCache.Identity(profile: profile, resource: resource, etag: reply.etag, length: length)
        return valid(reply, identity: id, offset: 0, count: Int(min(length, Int64(requested)))) ? id : nil
    }
}
