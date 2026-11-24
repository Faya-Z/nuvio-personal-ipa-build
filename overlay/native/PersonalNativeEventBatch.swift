// Coalesce consecutive property notifications; never merge across lifecycle events.
private struct PersonalNativeEventBatch {
    enum Refresh: Equatable { case none, subtitleOnly, playback, tracks }
    private(set) var count = 0
    private var tracks = false
    private var playback = false
    private var subtitle = false
    mutating func add(_ name: String?) {
        count += 1
        switch name {
        case "track-list", "aid", "sid", nil: tracks = true
        case "sub-text": subtitle = true
        case "pause", "paused-for-cache", "core-idle", "eof-reached", "seeking": playback = true
        default: tracks = true // conservative for future observed properties
        }
    }
    var shouldFlush: Bool { count >= 64 }
    mutating func take() -> Refresh {
        let result: Refresh = tracks ? .tracks : playback ? .playback : subtitle ? .subtitleOnly : .none
        self = PersonalNativeEventBatch()
        return result
    }
}
