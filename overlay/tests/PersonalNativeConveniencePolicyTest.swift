import Foundation
var checks = 0
func verify(_ condition: @autoclosure () -> Bool) { checks += 1; precondition(condition(), "assertion \(checks)") }
func crop(_ w: Double,_ h: Double,_ x: Double,_ y: Double) -> Bool { PersonalNativeConveniencePolicy.smallCrop(videoWidth:w,videoHeight:h,viewWidth:x,viewHeight:y) }
verify(crop(1920,1080,1800,1080)); verify(crop(1800,1080,1920,1080))
verify(!crop(1920,1080,1920,1080)); verify(!crop(1920,1080,2560,1080)); verify(!crop(1440,1080,1920,1080))
verify(!crop(1080,1920,1920,1080)); verify(!crop(1920,1080,1080,1920)); verify(!crop(0,1080,1920,1080))
verify(!crop(.nan,1080,1920,1080)); verify(!crop(1920,.infinity,1920,1080)); verify(!crop(1920,1080,-1,1080))
verify(!crop(1920,1080,1921,1080)); verify(crop(1920,1080,1900,1080)); verify(!crop(1920,1080,1600,1080))
let mb: Int64 = 1024*1024
verify(PersonalNativeConveniencePolicy.reducedBackCache(bytes: 100*mb) == 16*mb)
verify(PersonalNativeConveniencePolicy.reducedBackCache(bytes: 17*mb) == 16*mb)
verify(PersonalNativeConveniencePolicy.reducedBackCache(bytes: 16*mb) == nil)
verify(PersonalNativeConveniencePolicy.reducedBackCache(bytes: 0) == nil)
verify(PersonalNativeConveniencePolicy.reducedBackCache(bytes: -1) == nil)
verify(PersonalNativeConveniencePolicy.reducedBackCache(bytes: Int64.max) == 16*mb)
private func retry() -> PersonalNativeRetrySeek { PersonalNativeRetrySeek(generation: 1,path:"media",positionMs: 60000,started: 10) }
private var r = retry()
verify(r.observe(generation:1,path:"media",now:11,ready:false,positionMs:0,durationMs:0) == .wait)
verify(r.observe(generation:1,path:"media",now:12,ready:true,positionMs:0,durationMs:120000) == .wait)
verify(r.observe(generation:1,path:"media",now:12.5,ready:true,positionMs:0,durationMs:120000) == .wait)
verify(r.observe(generation:1,path:"media",now:12.8,ready:true,positionMs:0,durationMs:120000) == .seek(60000))
r = retry(); verify(r.observe(generation:1,path:"media",now:11,ready:true,positionMs:59000,durationMs:120000) == .done)
r = retry(); verify(r.observe(generation:2,path:"media",now:11,ready:true,positionMs:0,durationMs:120000) == .done)
r = retry(); verify(r.observe(generation:1,path:"new",now:11,ready:true,positionMs:0,durationMs:120000) == .done)
r = retry(); verify(r.observe(generation:1,path:"media",now:41,ready:true,positionMs:0,durationMs:120000) == .done)
r = retry(); verify(r.observe(generation:1,path:"media",now:9,ready:true,positionMs:0,durationMs:120000) == .done)
r = retry(); verify(r.observe(generation:1,path:"media",now:11,ready:true,positionMs:0,durationMs:30000) == .wait)
verify(r.observe(generation:1,path:"media",now:12,ready:true,positionMs:0,durationMs:30000) == .seek(29999))
r = retry(); verify(r.observe(generation:1,path:"media",now:11,ready:true,positionMs:0,durationMs:120000) == .wait)
verify(r.observe(generation:1,path:"media",now:12,ready:false,positionMs:0,durationMs:120000) == .wait)
verify(r.observe(generation:1,path:"media",now:13,ready:true,positionMs:0,durationMs:120000) == .wait)
verify(r.observe(generation:1,path:"media",now:14,ready:true,positionMs:0,durationMs:120000) == .seek(60000))
print("PASS: \(checks) native convenience assertions")
