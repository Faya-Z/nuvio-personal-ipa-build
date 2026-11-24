// Pure helpers; deliberately independent of UIKit and libmpv for host tests.
private enum PersonalNativePlaybackPolicy {
    static func milliseconds(_ seconds: Double) -> Int64 {
        guard seconds.isFinite, seconds > 0 else { return 0 }
        let ms = seconds * 1000
        // Double(Int64.max) rounds up; never cast at or above that boundary.
        guard ms.isFinite, ms < Double(Int64.max) else { return 0 }
        return Int64(ms)
    }

    static func bufferedPosition(position: Double, duration: Double, cacheEnd: Double) -> Int64 {
        let current = milliseconds(position)
        let end = milliseconds(duration)
        let estimate = max(current, milliseconds(cacheEnd))
        // Unknown duration is valid for live media; never report an end behind position.
        return end > 0 ? max(current, min(estimate, end)) : estimate
    }

    static func playbackRate(_ rate: Double) -> Float {
        let result = Float(rate)
        return result.isFinite && result > 0 ? result : 1
    }

    static func needsTrackRefresh(_ property: String?) -> Bool {
        // Unknown notifications retain the original full-refresh behaviour.
        switch property {
        case "pause", "paused-for-cache", "core-idle", "eof-reached", "seeking": return false
        default: return true
        }
    }
}
