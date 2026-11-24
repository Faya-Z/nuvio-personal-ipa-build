// Optional, conservative letterbox detector; uses sparse RGB samples, no persisted frames.
struct PersonalEncodedBarPolicy {
    struct Bars: Equatable { let width: Int; let height: Int; let top: Int; let bottom: Int
        var crop: String { "\(width)x\(height-top-bottom)+0+\(top)" }
    }
    static func detect(width: Int, height: Int, stride: Int, bytes: UnsafeRawBufferPointer) -> Bars? {
        guard (320...4096).contains(width), (180...2160).contains(height), width >= height,
              stride >= width * 4, stride <= 65536, bytes.count >= stride * height else { return nil }
        // Sample 32 columns away from corners; use the brightest RGB component so colored
        // edge content cannot be mistaken for a black bar. Reject subtitles/logos in bars.
        func darkRow(_ y: Int) -> Bool {
            (0..<32).allSatisfy { i in
                let x = (i+1) * width / 33, p = y * stride + x * 4
                return max(bytes[p], max(bytes[p+1], bytes[p+2])) <= 20
            }
        }
        var bright = 0
        for j in 1...8 { for i in 1...16 {
            let p = ((height/4 + j*height/18) * stride) + (i*width/17)*4
            if max(bytes[p], max(bytes[p+1], bytes[p+2])) >= 60 { bright += 1 }
        } }
        guard bright >= 48 else { return nil } // fades / dark scenes
        let limit = height / 5
        var top = 0, bottom = 0
        while top < limit && darkRow(top) { top += 1 }
        while bottom < limit && darkRow(height-1-bottom) { bottom += 1 }
        guard top >= height/40, bottom >= height/40, top < limit, bottom < limit,
              abs(top-bottom) <= max(2,height/100) else { return nil }
        // Leave a margin rather than cutting into picture content. Keep even offsets.
        let margin = max(2, height/100)
        let t = (max(0,top-margin)/2)*2, b = (max(0,bottom-margin)/2)*2
        guard t > 0, b > 0 else { return nil }
        return Bars(width: width, height: height, top: t, bottom: b)
    }
    private(set) var attempts = 0
    private var previous: Bars?
    private var consecutive = 0
    mutating func observe(_ bars: Bars?) -> Bars? {
        attempts += 1
        guard let bars else { previous = nil; consecutive = 0; return nil }
        if let p = previous, p.width == bars.width, p.height == bars.height,
           abs(p.top-bars.top) <= 4, abs(p.bottom-bars.bottom) <= 4 {
            consecutive += 1
            previous = Bars(width: bars.width,height: bars.height,top: min(p.top,bars.top),bottom: min(p.bottom,bars.bottom))
        } else { previous = bars; consecutive = 1 }
        return consecutive >= 3 ? previous : nil
    }
}
