import Foundation
private var assertions = 0
private func check(_ value: @autoclosure () -> Bool, _ label: String) {
    assertions += 1
    precondition(value(), label)
}
private func runTests() {
    var b = PersonalNativeEventBatch()
    check(b.take() == .none, "empty")
    check(b.count == 0, "empty count")
    b.add("sub-text"); b.add("sub-text")
    check(b.count == 2, "subtitle count")
    check(b.take() == .subtitleOnly, "subtitle burst")
    check(b.take() == .none, "reset")
    for name in ["pause", "paused-for-cache", "core-idle", "eof-reached", "seeking"] {
        b.add(name); check(b.take() == .playback, name)
    }
    for name in ["track-list", "aid", "sid", "future-property"] {
        b.add(name); check(b.take() == .tracks, name)
    }
    b.add(nil); check(b.take() == .tracks, "unknown name")
    b.add("pause"); b.add("sub-text")
    check(b.take() == .playback, "playback includes subtitle refresh")
    b.add("sub-text"); b.add("track-list"); b.add("pause")
    check(b.take() == .tracks, "tracks includes all refreshes")
    b.add("sid"); b.add("sub-text"); b.add("seeking")
    check(b.take() == .tracks, "order independence")
    for _ in 0..<63 { b.add("pause") }
    check(!b.shouldFlush, "under bound")
    b.add("aid")
    check(b.shouldFlush, "batch limit")
    check(b.take() == .tracks, "limit preserves track refresh")
    check(!b.shouldFlush && b.count == 0, "bound resets")
    b.add("sub-text")
    check(b.take() == .subtitleOnly, "new batch independent")
    b.add("pause"); let beforeBoundary = b.take()
    b.add("aid"); let afterBoundary = b.take()
    check(beforeBoundary == .playback && afterBoundary == .tracks, "lifecycle boundary")
    print("PASS: \(assertions) native event batch assertions")
}
runTests()
