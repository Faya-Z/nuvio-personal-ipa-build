import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// A bounded, cancellable HTTP range transaction. No redirects, credentials, cookies,
/// or disk caching; abort immediately if a server ignores the requested range.
final class PersonalRangeHTTP: NSObject, URLSessionDataDelegate, @unchecked Sendable {
    private let lock = NSLock()
    private var session: URLSession?
    private var task: URLSessionDataTask?
    private var cancelled = false
    private var done: DispatchSemaphore?
    private var status: HTTPURLResponse?
    private var body = Data()
    private var maxCount = 0
    private var result: PersonalRangeReader.Reply?
    private var sessionsCreated = 0
    private let protocolClasses: [AnyClass]?
    init(protocolClasses: [AnyClass]? = nil) { self.protocolClasses = protocolClasses; super.init() }
    // Diagnostics for the standalone transport test. No URL or user data logged.
    var sessionCreationCount: Int { lock.lock(); defer { lock.unlock() }; return sessionsCreated }

    static func request(url: URL, offset: Int64, count: Int, etag: String?) -> URLRequest? {
        guard offset >= 0, count > 0, count <= PersonalPrefetchCache.limit,
              offset <= Int64.max - Int64(count) else { return nil }
        if let etag, !PersonalPrefetchCache.Identity(profile: 0, resource: UUID(), etag: etag, length: 1).valid { return nil }
        var req = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 8)
        req.httpMethod = "GET"
        req.setValue("bytes=\(offset)-\(offset+Int64(count)-1)", forHTTPHeaderField: "Range")
        req.setValue("identity", forHTTPHeaderField: "Accept-Encoding")
        if let etag { req.setValue(etag, forHTTPHeaderField: "If-Match") }
        return req
    }
    func fetch(url: URL, offset: Int64, count: Int, etag: String?) -> PersonalRangeReader.Reply? {
        // Production path only permits credential-free direct HTTPS files. No blocking UI calls.
        guard !Thread.isMainThread, PersonalRangeReader.directFile(url.absoluteString) != nil,
              let request = Self.request(url: url, offset: offset, count: count, etag: etag) else { return nil }
        let semaphore = DispatchSemaphore(value: 0)
        lock.lock()
        guard !cancelled, done == nil else { lock.unlock(); return nil }
        let s: URLSession
        if let existing = session { s = existing } else {
        let config = URLSessionConfiguration.ephemeral
        config.httpCookieStorage = nil; config.httpShouldSetCookies = false; config.urlCredentialStorage = nil
        config.urlCache = nil; config.requestCachePolicy = .reloadIgnoringLocalCacheData
        config.allowsCellularAccess = false
        config.timeoutIntervalForRequest = 8; config.timeoutIntervalForResource = 10
        let queue = OperationQueue(); queue.maxConcurrentOperationCount = 1
        if let protocolClasses { config.protocolClasses = protocolClasses }
        s = URLSession(configuration: config, delegate: self, delegateQueue: queue)
        session = s; sessionsCreated += 1
        }
        let t = s.dataTask(with: request)
        session = s; task = t; done = semaphore; maxCount = count; status = nil; body = Data(); result = nil
        lock.unlock()
        t.resume()
        if semaphore.wait(timeout: .now() + 10) == .timedOut { cancel(); return nil }
        lock.lock()
        let answer = cancelled ? nil : result
        done = nil; task = nil; status = nil; body = Data(); result = nil
        lock.unlock()
        // Keep the ephemeral connection pool for subsequent sequential ranges.
        return answer
    }
    func cancel() {
        lock.lock(); cancelled = true; let s = session; let signal = done
        session = nil; task = nil; status = nil; body = Data(); result = nil; done = nil
        lock.unlock()
        s?.invalidateAndCancel(); signal?.signal()
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) { completionHandler(nil) }
    func urlSession(_ session: URLSession, task: URLSessionTask, didReceive challenge: URLAuthenticationChallenge,
                    completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        // TLS trust uses default verification; never supply credentials for HTTP auth.
        if challenge.protectionSpace.authenticationMethod == "NSURLAuthenticationMethodServerTrust" {
            completionHandler(.performDefaultHandling, nil)
        } else { completionHandler(.cancelAuthenticationChallenge, nil) }
    }
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse,
                    completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        lock.lock(); defer { lock.unlock() }
        guard self.session === session, task === dataTask, !cancelled,
              let http = response as? HTTPURLResponse, http.statusCode == 206,
              http.url == dataTask.originalRequest?.url,
              response.expectedContentLength <= Int64(maxCount),
              let range = http.value(forHTTPHeaderField: "Content-Range"), range.hasPrefix("bytes "),
              let tag = http.value(forHTTPHeaderField: "ETag"),
              PersonalPrefetchCache.Identity(profile: 0, resource: UUID(), etag: tag, length: 1).valid,
              http.value(forHTTPHeaderField: "Content-Encoding").map({ $0.lowercased() == "identity" }) ?? true else {
            completionHandler(.cancel); return
        }
        status = http; completionHandler(.allow)
    }
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        lock.lock()
        guard self.session === session, task === dataTask, !cancelled, status != nil else { lock.unlock(); dataTask.cancel(); return }
        guard data.count <= maxCount-body.count else { status = nil; body = Data(); lock.unlock(); dataTask.cancel(); return }
        body.append(data); lock.unlock()
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        lock.lock(); defer { lock.unlock() }
        guard self.session === session, self.task === task, !cancelled else { return }
        if error == nil, let http = status, let range = http.value(forHTTPHeaderField: "Content-Range"),
           let tag = http.value(forHTTPHeaderField: "ETag") {
            result = .init(status: http.statusCode, range: range, etag: tag,
                           encoding: http.value(forHTTPHeaderField: "Content-Encoding"), body: body)
        }
        done?.signal()
    }
}

/// One shared next-file slot. All URL and profile matches are exact; the MPV opener
/// consumes it once, and performs conditional revalidation before using the bytes.
final class PersonalPrefetchTransport: @unchecked Sendable {
    static let shared = PersonalPrefetchTransport()
    struct Prepared {
        let url: URL
        let identity: PersonalPrefetchCache.Identity
        let cache: PersonalPrefetchCache
        let created: Double
    }
    private let lock = NSLock()
    private var generation: UInt64 = 0
    private var pending: PersonalRangeHTTP?
    private var prepared: Prepared?
    func clear() {
        lock.lock(); generation &+= 1; let old = pending; pending = nil; prepared = nil; lock.unlock(); old?.cancel()
    }
    func prepare(url raw: String, profile: Int) {
        guard let url = PersonalRangeReader.directFile(raw) else { return }
        let http = PersonalRangeHTTP()
        lock.lock(); generation &+= 1; let token = generation; let old = pending
        pending = http; prepared = nil; lock.unlock(); old?.cancel()
        DispatchQueue.global(qos: .utility).async { [weak self] in
            guard let self else { return }
            let count = 1024 * 1024 // deliberately modest; not a whole-file download
            defer { http.cancel() } // close the speculative session even if superseded
            let reply = http.fetch(url: url, offset: 0, count: count, etag: nil)
            let now = ProcessInfo.processInfo.systemUptime
            var slot: Prepared?
            if let reply, let id = PersonalRangeReader.identity(profile: profile, resource: UUID(), reply: reply, requested: count) {
                let cache = PersonalPrefetchCache()
                if cache.store(identity: id, offset: 0, requestedCount: count, status: reply.status,
                               contentRange: reply.range, responseETag: reply.etag, body: reply.body, now: now) {
                    slot = Prepared(url: url, identity: id, cache: cache, created: now)
                }
            }
            self.lock.lock(); defer { self.lock.unlock() }
            if self.generation == token { self.prepared = slot; self.pending = nil }
        }
    }
    func take(url raw: String, profile: Int) -> Prepared? {
        lock.lock(); generation &+= 1
        let slot = prepared, old = pending
        prepared = nil; pending = nil; lock.unlock()
        // Playback has started. An unfinished speculative request must not keep running.
        old?.cancel()
        let now = ProcessInfo.processInfo.systemUptime
        guard let slot, slot.identity.profile == profile, slot.url.absoluteString == raw,
              now >= slot.created, now-slot.created <= PersonalPrefetchCache.lifetime else { return nil }
        return slot
    }
    static func open(_ slot: Prepared) -> PersonalRangeReader? {
        let http = PersonalRangeHTTP()
        // Check the resource is still the same before serving even the first cached byte.
        guard let probe = http.fetch(url: slot.url, offset: 0, count: 1, etag: slot.identity.etag),
              PersonalRangeReader.valid(probe, identity: slot.identity, offset: 0, count: 1) else { http.cancel(); return nil }
        let reader = PersonalRangeReader(identity: slot.identity, cache: slot.cache,
            clock: { ProcessInfo.processInfo.systemUptime },
            fetch: { http.fetch(url: slot.url, offset: $0, count: $1, etag: $2) }, stop: { http.cancel() })
        if reader == nil { http.cancel() }
        return reader
    }
}
