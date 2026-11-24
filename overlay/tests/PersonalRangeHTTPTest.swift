import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
var checks = 0
func check(_ b: @autoclosure () -> Bool, _ label: String) { precondition(b(), label); checks += 1 }
let url = URL(string: "https://media.example/file.mp4")!
let request = PersonalRangeHTTP.request(url: url, offset: 4, count: 8, etag: "\"abc\"")!
check(request.httpMethod == "GET", "method")
check(request.value(forHTTPHeaderField: "Range") == "bytes=4-11", "range")
check(request.value(forHTTPHeaderField: "Accept-Encoding") == "identity", "no compression")
check(request.value(forHTTPHeaderField: "If-Match") == "\"abc\"", "conditional")
check(request.value(forHTTPHeaderField: "Authorization") == nil && request.value(forHTTPHeaderField: "Cookie") == nil, "no auth")
check(PersonalRangeHTTP.request(url: url, offset: -1, count: 1, etag: nil) == nil, "negative")
check(PersonalRangeHTTP.request(url: url, offset: 0, count: 0, etag: nil) == nil, "zero")
check(PersonalRangeHTTP.request(url: url, offset: 0, count: PersonalPrefetchCache.limit+1, etag: nil) == nil, "over budget")
check(PersonalRangeHTTP.request(url: url, offset: Int64.max, count: 1, etag: nil) == nil, "overflow")
check(PersonalRangeHTTP.request(url: url, offset: 0, count: 1, etag: "W/\"x\"") == nil, "weak")
check(PersonalRangeHTTP.request(url: url, offset: 0, count: 1, etag: "\"a\r\nX: 1\"") == nil, "injection")
check(PersonalRangeHTTP().fetch(url: url, offset: 0, count: 1, etag: nil) == nil, "no UI blocking")
let http = PersonalRangeHTTP(); http.cancel()
check(http.fetch(url: url, offset: 0, count: 1, etag: nil) == nil, "cancel")
let transport = PersonalPrefetchTransport(); transport.prepare(url: "http://example.com/a.mp4", profile: 1)
check(transport.take(url: url.absoluteString, profile: 1) == nil, "ineligible")
transport.clear(); check(transport.take(url: url.absoluteString, profile: 1) == nil, "clear")
print("PASS: \(checks) HTTP transport request assertions")
