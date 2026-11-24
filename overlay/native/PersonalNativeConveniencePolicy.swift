// Pure policies: no audio or network changes. Inserted into the existing bridge.
private enum PersonalNativeConveniencePolicy {
    // Crop only a small fraction of one dimension, using display aspect (not encoded dimensions).
    // This does not detect bars baked into the media. Unknown, portrait or mismatched sizes fit.
    static func smallCrop(videoWidth: Double, videoHeight: Double, viewWidth: Double, viewHeight: Double) -> Bool {
        let values = [videoWidth, videoHeight, viewWidth, viewHeight]
        guard values.allSatisfy({ $0.isFinite && $0 > 1 }),
              videoWidth >= videoHeight, viewWidth >= viewHeight else { return false }
        let video = videoWidth / videoHeight
        let view = viewWidth / viewHeight
        guard video.isFinite, view.isFinite else { return false }
        let lost = 1.0 - min(video, view) / max(video, view)
        return lost >= 0.005 && lost <= 0.10
    }
    // Only trim already-played data, not the forward playback buffer. Never raise the limit.
    static func reducedBackCache(bytes: Int64) -> Int64? {
        let cap: Int64 = 16 * 1024 * 1024
        guard bytes > cap else { return nil }
        return cap
    }
}

private struct PersonalNativeRetrySeek {
    let generation: UInt64
    let path: String
    let positionMs: Int64
    let started: Double
    private var readySince: Double?
    init(generation: UInt64, path: String, positionMs: Int64, started: Double) {
        self.generation = generation; self.path = path; self.positionMs = positionMs; self.started = started
    }
    enum Decision: Equatable { case wait, done, seek(Int64) }
    mutating func observe(generation: UInt64, path: String?, now: Double, ready: Bool,
                          positionMs: Int64, durationMs: Int64) -> Decision {
        guard generation == self.generation, path == self.path, now.isFinite,
              started.isFinite, now >= started, now - started <= 30 else { return .done }
        guard ready, durationMs > 0 else { readySince = nil; return .wait }
        let target = min(self.positionMs, durationMs - 1)
        guard target > 0, positionMs >= 0, positionMs <= durationMs else { return .done }
        if abs(positionMs - target) <= 1_500 { return .done }
        if readySince == nil { readySince = now; return .wait }
        guard now - readySince! >= 0.75 else { return .wait }
        return .seek(target)
    }
}
