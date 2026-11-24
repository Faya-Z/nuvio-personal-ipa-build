// Only stable, foreground network playback in Low Power Mode.
private struct PersonalLowPowerBufferPolicy {
    private var stableSince: Double?
    private var lastObserved: Double?
    private(set) var active = false
    mutating func observe(now: Double, eligible: Bool, ahead: Double) -> Double {
        guard now.isFinite, eligible, ahead.isFinite, ahead >= 10 else {
            stableSince = nil; lastObserved = nil; active = false; return 0
        }
        if let last = lastObserved, now < last { stableSince = nil; active = false }
        lastObserved = now
        if active { return 15 }
        guard ahead >= 30 else { stableSince = nil; return 0 }
        if stableSince == nil { stableSince = now }
        if let since = stableSince, now - since >= 60 { active = true }
        return active ? 15 : 0
    }
}
