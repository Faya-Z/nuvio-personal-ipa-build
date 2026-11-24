package com.nuvio.app.features.player

fun main() {
    val d = PlaybackDiagnostics()
    fun s(t: Long, loading: Boolean = false, playing: Boolean = false, expected: Boolean = true, ended: Boolean = false) =
        d.observe(loading, playing, ended, expected, t)
    check(s(0, loading = true) == null)
    check(s(900, playing = true) == "startup_completed elapsed_ms=900")
    check(s(1000, playing = true) == null)
    check(s(1200, loading = true) == "rebuffer_started")
    check(s(1400, loading = true) == null)
    check(s(1500) == null)
    check(s(1800, playing = true) == "rebuffer_completed elapsed_ms=600 count=1 total_ms=600")
    check(s(2000, loading = true, expected = false) == null)
    check(s(2200, playing = true) == null)
    check(s(2300, loading = true) == "rebuffer_started")
    check(s(2400, expected = false) == null)
    check(s(2500, playing = true) == null)
    check(s(2600, loading = true) == "rebuffer_started")
    check(s(2800, playing = true) == "rebuffer_completed elapsed_ms=200 count=2 total_ms=800")
    check(s(3000, ended = true) == null)
    d.reset()
    check(s(50, expected = false) == null)
    check(s(100, playing = true) == "startup_completed timing_excluded=true")
    d.reset()
    check(s(75, playing = true) == "startup_completed elapsed_ms=75")
    println("PASS: 18 playback diagnostic assertions")
}
