// Pure policy, inserted into MPVPlayerBridge.swift by the overlay.
// No changes to volume, audio processing, byte limits or startup buffering.
private struct PersonalAdaptiveCachePolicy {
    private var stableSince: Double?
    private var stallSince: Double?
    private var lastQualifiedStall: Double?
    private var armed = false
    private(set) var level = 0

    mutating func observe(now: Double, eligible: Bool, playing: Bool, buffering: Bool) -> Int {
        guard now.isFinite, eligible else {
            stableSince = nil
            stallSince = nil
            armed = false
            return level
        }
        if buffering {
            stableSince = nil
            if armed && stallSince == nil { stallSince = now }
            if let start = stallSince, now - start >= 1.0 {
                if let last = lastQualifiedStall, now - last >= 0, now - last <= 90 {
                    level = min(level + 1, 2)
                }
                lastQualifiedStall = now
                stallSince = nil
                armed = false
            }
            return level
        }
        stallSince = nil
        guard playing else {
            stableSince = nil
            armed = false
            return level
        }
        if stableSince == nil || now < stableSince! { stableSince = now }
        if let since = stableSince {
            if now - since >= 3 { armed = true }
            if now - since >= 90 {
                level = 0
                lastQualifiedStall = nil
            }
        }
        return level
    }

    func target(base: Double) -> Double? {
        guard base.isFinite, base > 0, base < 3 else { return nil }
        return min(3, base + Double(level))
    }
}
