import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
// No network: URLProtocol injects responses through the real URLSession delegate path.
final class FixtureProtocol: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        let range = request.value(forHTTPHeaderField: "Range") ?? ""
        let values = range.dropFirst(6).split(separator: "-").compactMap { Int($0) }
        guard values.count == 2, values[0] <= values[1], values[1] < 16 else {
            client?.urlProtocol(self, didFailWithError: URLError(.badServerResponse)); return
        }
        let n = values[1]-values[0]+1
        let response = HTTPURLResponse(url: request.url!, statusCode: values[0] == 8 ? 200 : 206, httpVersion: "HTTP/1.1", headerFields: ["Content-Range":"bytes \(values[0])-\(values[1])/16", "Content-Length": "\(n)", "ETag":"\"test\""])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Data((values[0]...values[1]).map(UInt8.init)))
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}
let finished = DispatchSemaphore(value: 0)
DispatchQueue.global().async {
    let url = URL(string:"https://media.example/a.mp4")!
    let h = PersonalRangeHTTP(protocolClasses: [FixtureProtocol.self])
    defer { h.cancel(); finished.signal() }
    let first = h.fetch(url: url, offset: 0, count: 4, etag: nil)
    precondition(first?.body == Data([0,1,2,3]), "first response")
    precondition(first?.etag == "\"test\"", "first ETag")
    let second = h.fetch(url: url, offset: 4, count: 4, etag: first?.etag)
    precondition(second?.body == Data([4,5,6,7]), "second response")
    precondition(h.sessionCreationCount == 1, "reuse session")
    precondition(h.fetch(url:url,offset:8,count:4,etag:first?.etag) == nil, "non-range rejected")
    precondition(h.fetch(url:url,offset:12,count:4,etag:first?.etag)?.body == Data([12,13,14,15]), "retry on existing session")
    precondition(h.sessionCreationCount == 1, "reuse after rejected response")
    h.cancel()
    precondition(h.fetch(url:url,offset:0,count:4,etag:nil) == nil, "cancel prevents reuse")
    print("PASS: 8 URLSession delegate and connection-reuse checks (mock responses)")
}
precondition(finished.wait(timeout: .now()+30) == .success, "test timeout")
