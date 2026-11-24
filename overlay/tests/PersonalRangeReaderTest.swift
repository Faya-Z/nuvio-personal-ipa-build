import Foundation
var checks = 0
func check(_ b: @autoclosure () -> Bool, _ label: String) { precondition(b(), label); checks += 1 }
let id = PersonalPrefetchCache.Identity(profile: 1, resource: UUID(), etag: "\"v1\"", length: 12)
let cache = PersonalPrefetchCache()
var calls = 0
var now = 0.0
var invalid = false
let full = Data(0..<12)
func reply(_ offset: Int64, _ count: Int, _ tag: String) -> PersonalRangeReader.Reply {
    .init(status: 206, range: "bytes \(offset)-\(offset+Int64(count)-1)/12", etag: tag, encoding: nil,
          body: full.subdata(in: Int(offset)..<Int(offset)+count))
}
check(cache.store(identity: id, offset: 0, requestedCount: 4, status: 206, contentRange: "bytes 0-3/12", responseETag: id.etag, body: full.prefix(4), now: now), "prefetch")
let r = PersonalRangeReader(identity: id, cache: cache, clock: { now }, fetch: { offset, count, tag in
    calls += 1; return reply(offset, count, invalid ? "\"changed\"" : tag)
})!
check(r.read(2) == Data([0,1]), "first hit")
check(r.read(9) == Data([2,3]), "partial hit")
check(r.servedPrefetchBytes == 4 && calls == 0, "no fetch for hit")
check(r.read(3) == Data([4,5,6]) && calls == 1, "miss and read ahead")
check(r.read(2) == Data([7,8]) && calls == 1, "rolling read")
check(r.seek(5) == 5 && r.read(2) == Data([5,6]), "back seek")
check(r.seek(12) == 12 && r.read(1) == Data(), "EOF")
check(r.seek(13) == -1 && r.seek(-1) == -1, "bad seek")
check(r.seek(0) == 0 && r.read(1) == Data([0]), "prefetch again")
now = 91; invalid = true
check(r.seek(0) == 0 && r.read(1) == nil, "expiry and changed validator")
invalid = false
check(r.read(1) == Data([0]), "position unchanged on failure")
check(r.read(0) == nil, "invalid count")
r.cancel(); check(r.read(1) == nil && r.seek(0) == -1, "cancelled")
let fresh = reply(0, 4, id.etag)
check(PersonalRangeReader.identity(profile: 1, resource: id.resource, reply: fresh, requested: 4) == id, "identity discovery")
check(PersonalRangeReader.identity(profile: 1, resource: id.resource, reply: fresh, requested: 5) == nil, "partial reply rejected")
check(PersonalRangeReader.valid(fresh, identity: id, offset: 0, count: 4), "valid")
let compressed = PersonalRangeReader.Reply(status: 206, range: fresh.range, etag: fresh.etag, encoding: "gzip", body: fresh.body)
check(!PersonalRangeReader.valid(compressed, identity: id, offset: 0, count: 4), "compressed rejected")
let weak = PersonalRangeReader.Reply(status: 206, range: fresh.range, etag: "W/\"v1\"", encoding: nil, body: fresh.body)
check(PersonalRangeReader.identity(profile: 1, resource: UUID(), reply: weak, requested: 4) == nil, "weak rejected")
let ordinary = PersonalRangeReader.Reply(status: 200, range: fresh.range, etag: fresh.etag, encoding: nil, body: fresh.body)
check(PersonalRangeReader.identity(profile: 1, resource: UUID(), reply: ordinary, requested: 4) == nil, "ordinary response rejected")
for bad in ["http://media.example/a.mp4", "https://media.example/a.m3u8", "https://u:p@media.example/a.mp4", "https://media.example/a.mp4?token=x", "https://media.example/a.mp4#x", "https://127.0.0.1/a.mp4", "https://my.local/a.mp4", "https://[::1]/a.mp4", "https://media.example:8443/a.mp4"] { check(PersonalRangeReader.directFile(bad) == nil, bad) }
check(PersonalRangeReader.directFile("https://media.example/a.mp4") != nil, "eligible URL")
print("PASS: \(checks) range-reader assertions")
