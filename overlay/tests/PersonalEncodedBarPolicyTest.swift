var count = 0
func check(_ v: Bool) { precondition(v); count += 1 }
let w = 640, h = 360, stride = w*4
func frame(top: Int = 40, bottom: Int = 40, middle: UInt8 = 120, logo: Bool = false) -> [UInt8] {
    var a = [UInt8](repeating: 0, count: h*stride)
    for y in top..<(h-bottom) { for x in 0..<w { let p = y*stride+x*4; a[p]=middle; a[p+1]=middle; a[p+2]=middle } }
    if logo { let p = (w/33)*4; a[p]=255 }
    return a
}
func detect(_ a: [UInt8], width: Int = w, height: Int = h, rowStride: Int = stride) -> PersonalEncodedBarPolicy.Bars? {
    a.withUnsafeBytes { PersonalEncodedBarPolicy.detect(width: width,height: height,stride: rowStride,bytes: $0) }
}
let b = detect(frame())!
check(b.top == 36); check(b.bottom == 36); check(b.crop == "640x288+0+36")
check(detect(frame(top: 0,bottom: 0)) == nil)
check(detect(frame(top: 40,bottom: 0)) == nil)
check(detect(frame(top: 50,bottom: 30)) == nil)
check(detect(frame(middle: 10)) == nil)
check(detect(frame(logo: true)) == nil)
check(detect(frame(top: 80,bottom: 80)) == nil)
check(detect(frame(top: 5,bottom: 5)) == nil)
check(detect([], width: 640) == nil)
check(detect(frame(), rowStride: 0) == nil)
check(detect(frame(), rowStride: -1) == nil)
check(detect(frame(), width: Int.max) == nil)
var p = PersonalEncodedBarPolicy()
check(p.observe(b) == nil); check(p.observe(b) == nil); check(p.observe(b) == b)
check(p.attempts == 3)
p = PersonalEncodedBarPolicy()
check(p.observe(b) == nil); check(p.observe(nil) == nil); check(p.observe(b) == nil); check(p.observe(b) == nil); check(p.observe(b) == b)
p = PersonalEncodedBarPolicy(); check(p.observe(b) == nil)
let b2 = detect(frame(top: 56,bottom: 56))!
check(p.observe(b2) == nil); check(p.observe(b2) == nil); check(p.observe(b2) == b2)
print("PASS: \(count) encoded-bar assertions")
