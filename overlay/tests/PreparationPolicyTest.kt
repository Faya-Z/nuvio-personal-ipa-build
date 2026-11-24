package com.nuvio.app.features.player

fun main() {
    fun lead(timeout: Int = 15, pos: Long = 60_000, duration: Long = 120_000,
        buffered: Long = 90_000, playing: Boolean = true, stall: Boolean = false, allowed: Boolean = true) =
        nextEpisodePreparationLeadMs(timeout, pos, duration, buffered, playing, stall, allowed)
    check(lead() == 45_000L)
    check(lead(timeout = 1) == 40_000L)
    check(lead(timeout = 60) == 60_000L)
    check(lead(timeout = Int.MIN_VALUE) == 40_000L)
    check(lead(timeout = Int.MAX_VALUE) == 60_000L)
    check(lead(buffered = 79_999) == 15_000L)
    check(lead(buffered = 80_000) == 45_000L)
    check(lead(buffered = 0) == 15_000L)
    check(lead(buffered = Long.MAX_VALUE, duration = 70_000) == 15_000L)
    check(lead(pos = 29_999) == 15_000L)
    check(lead(pos = 30_000) == 45_000L)
    check(lead(playing = false) == 15_000L)
    check(lead(stall = true) == 15_000L)
    check(lead(allowed = false) == 15_000L)
    check(lead(duration = 0) == 15_000L)
    check(lead(duration = 60_000) == 15_000L)
    check(boundedResumeTargetMs(12_000, 60_000) == 12_000L)
    check(boundedResumeTargetMs(99_000, 60_000) == 60_000L)
    check(boundedResumeTargetMs(12_000, 0) == 12_000L)
    check(boundedResumeTargetMs(-5, 60_000) == 0L)
    check(boundedResumeTargetMs(-5, 0) == 0L)
    println("PASS: 21 preparation and resume assertions")
}
