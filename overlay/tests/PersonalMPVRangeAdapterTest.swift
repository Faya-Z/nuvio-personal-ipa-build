import Foundation
import MPVCallbackFixture
// Uses a C fixture for the public callback signatures and a mock byte source. No real MPV.
var checks = 0
func check(_ b: @autoclosure () -> Bool, _ why: String) { precondition(b(),why); checks += 1 }
let bytes = Data(0..<12)
let identity = PersonalPrefetchCache.Identity(profile: 3,resource: UUID(),etag:"\"a\"",length:12)
let cache = PersonalPrefetchCache()
check(cache.store(identity:identity,offset:0,requestedCount:4,status:206,contentRange:"bytes 0-3/12",responseETag:identity.etag,body:bytes.prefix(4),now:1),"cache seeded")
let slot = PersonalPrefetchTransport.Prepared(url:URL(string:"https://media.example/a.mp4")!,identity:identity,cache:cache,created:1)
var opens = 0
var stops = 0
private let adapter = PersonalMPVRangeAdapter(open:{ s in
    opens += 1
    return PersonalRangeReader(identity:s.identity,cache:s.cache,clock:{1},fetch:{offset,count,tag in
        .init(status:206,range:"bytes \(offset)-\(offset+Int64(count)-1)/12",etag:tag,encoding:nil,body:bytes.subdata(in:Int(offset)..<Int(offset)+count))
    },stop:{ stops += 1 })
})
let handle = fixture_create()!
defer { fixture_destroy(handle) }
let uri = adapter.url(for:slot,handle:handle)!
check(uri.hasPrefix("nuviorange://"),"opaque uri")
check(!uri.contains("media.example"),"no source URL in token")
check(fixture_registrations(handle)==1,"C registration")
var info = mpv_stream_cb_info()
check(fixture_open(handle,"nuviorange://invalid",&info)<0,"unknown token")
check(opens==0,"no opener")
check(fixture_open(handle,uri,&info)==0 && opens==1,"C invokes Swift opener")
check(info.cookie != nil && info.read_fn != nil && info.close_fn != nil && info.cancel_fn != nil,"callbacks set")
var other = mpv_stream_cb_info()
check(fixture_open(handle,uri,&other)<0,"one-use token")
check(info.size_fn!(info.cookie)==12,"size callback")
var buffer = [CChar](repeating:0,count:12)
let n = buffer.withUnsafeMutableBufferPointer { info.read_fn!(info.cookie,$0.baseAddress,6) }
check(n==4 && Array(buffer.prefix(4)) == [0,1,2,3],"cached short read")
let m = buffer.withUnsafeMutableBufferPointer { info.read_fn!(info.cookie,$0.baseAddress,6) }
check(m==6 && Array(buffer.prefix(6)) == [4,5,6,7,8,9],"subsequent read")
check(info.seek_fn!(info.cookie,2)==2,"seek callback")
check(info.seek_fn!(info.cookie,13)==(-1),"invalid seek")
check(info.seek_fn!(info.cookie,12)==12,"seek to EOF")
check(buffer.withUnsafeMutableBufferPointer { info.read_fn!(info.cookie,$0.baseAddress,1) }==0,"EOF")
info.cancel_fn!(info.cookie)
check(buffer.withUnsafeMutableBufferPointer { info.read_fn!(info.cookie,$0.baseAddress,1) }<0,"cancelled read")
info.close_fn!(info.cookie)
check(stops>=1,"close releases reader")
let second = adapter.url(for:slot,handle:handle)!
check(fixture_registrations(handle)==1,"no duplicate registration")
adapter.clear()
check(fixture_open(handle,second,&other)<0,"clear removes pending token")
print("PASS: \(checks) C-to-Swift callback fixture checks (not actual libmpv)")
