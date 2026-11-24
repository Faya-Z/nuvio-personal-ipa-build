package com.nuvio.app.features.player

fun main() {
    val d = PlaybackDiagnostics()
    check(d.summary() == PlaybackDiagnosticSummary(null, 0, 0, false))
    check(!d.hasRecentStall(0))
    d.observe(false, true, false, true, 1200)
    check(d.summary().startupMs == 1200L)
    d.observe(true, false, false, true, 3000)
    check(d.summary().buffering)
    check(d.hasRecentStall(4000))
    d.observe(false, true, false, true, 5000)
    check(d.summary() == PlaybackDiagnosticSummary(1200, 1, 2000, false))
    check(d.hasRecentStall(50_000))
    check(!d.hasRecentStall(50_001))
    d.reset()
    check(!d.hasRecentStall(0))
    check(d.summary().startupMs == null)
    d.observe(false, false, false, false, 50)
    d.observe(false, true, false, true, 500)
    check(d.summary().startupMs == null)
    println("PASS: 11 diagnostic summary assertions")
}
