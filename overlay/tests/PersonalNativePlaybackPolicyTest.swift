import Foundation
var checks = 0
func expect(_ condition: @autoclosure () -> Bool, _ label: String) {
    precondition(condition(), label)
    checks += 1
}
expect(PersonalNativePlaybackPolicy.milliseconds(1.25) == 1250, "positive")
expect(PersonalNativePlaybackPolicy.milliseconds(0) == 0, "zero")
expect(PersonalNativePlaybackPolicy.milliseconds(-5) == 0, "negative")
expect(PersonalNativePlaybackPolicy.milliseconds(.nan) == 0, "nan")
expect(PersonalNativePlaybackPolicy.milliseconds(.infinity) == 0, "infinite")
expect(PersonalNativePlaybackPolicy.milliseconds(-.infinity) == 0, "negative infinite")
expect(PersonalNativePlaybackPolicy.milliseconds(Double.greatestFiniteMagnitude) == 0, "overflow")
expect(PersonalNativePlaybackPolicy.milliseconds(Double(Int64.max)/1000) == 0, "boundary")
expect(PersonalNativePlaybackPolicy.milliseconds(7200) == 7_200_000, "long film")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: 1800, duration: 3600, cacheEnd: 1820) == 1_820_000, "absolute cache end, no double count")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: 1800, duration: 3600, cacheEnd: 1801) == 1_801_000, "one second headroom")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: 1800, duration: 3600, cacheEnd: 1790) == 1_800_000, "stale cache")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: 3599, duration: 3600, cacheEnd: 3620) == 3_600_000, "end bound")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: 10, duration: 0, cacheEnd: 22) == 22_000, "unknown duration")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: 10, duration: 100, cacheEnd: .nan) == 10_000, "unknown buffer")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: 101, duration: 100, cacheEnd: 110) == 101_000, "reported position outside duration")
expect(PersonalNativePlaybackPolicy.bufferedPosition(position: .nan, duration: 100, cacheEnd: 10) == 10_000, "unknown position")
expect(PersonalNativePlaybackPolicy.playbackRate(1.5) == 1.5, "rate")
expect(PersonalNativePlaybackPolicy.playbackRate(0) == 1, "zero rate")
expect(PersonalNativePlaybackPolicy.playbackRate(-1) == 1, "negative rate")
expect(PersonalNativePlaybackPolicy.playbackRate(.nan) == 1, "invalid rate")
expect(PersonalNativePlaybackPolicy.playbackRate(.infinity) == 1, "infinite rate")
expect(PersonalNativePlaybackPolicy.playbackRate(Double.greatestFiniteMagnitude) == 1, "overflow rate")
for property in ["pause", "paused-for-cache", "core-idle", "eof-reached", "seeking"] {
    expect(!PersonalNativePlaybackPolicy.needsTrackRefresh(property), property)
}
for property in ["track-list", "aid", "sid", "future-property"] {
    expect(PersonalNativePlaybackPolicy.needsTrackRefresh(property), property)
}
expect(PersonalNativePlaybackPolicy.needsTrackRefresh(nil), "unknown event")
print("PASS: \(checks) native playback assertions")
