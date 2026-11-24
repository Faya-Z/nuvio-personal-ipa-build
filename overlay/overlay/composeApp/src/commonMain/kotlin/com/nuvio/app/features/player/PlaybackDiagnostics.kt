package com.nuvio.app.features.player

import kotlin.time.TimeSource

internal data class PlaybackDiagnosticSummary(
    val startupMs: Long?,
    val completedStalls: Int,
    val totalStallMs: Long,
    val buffering: Boolean,
)

/** Local, bounded playback measurements; no titles, URLs, tokens or headers. */
internal class PlaybackDiagnostics {
    private var origin = TimeSource.Monotonic.markNow()
    private var firstPlaying = false
    private var stallStart: Long? = null
    private var stallCount = 0
    private var totalStallMs = 0L
    private var openingInterrupted = false
    private var startupMs: Long? = null
    private var lastStallAtMs: Long? = null

    fun reset() {
        origin = TimeSource.Monotonic.markNow()
        firstPlaying = false
        stallStart = null
        stallCount = 0
        totalStallMs = 0L
        openingInterrupted = false
        startupMs = null
        lastStallAtMs = null
    }

    fun summary(): PlaybackDiagnosticSummary = PlaybackDiagnosticSummary(
        startupMs, stallCount, totalStallMs, stallStart != null,
    )

    fun hasRecentStall(nowMs: Long = origin.elapsedNow().inWholeMilliseconds): Boolean =
        stallStart != null || lastStallAtMs?.let { nowMs - it in 0L..45_000L } == true

    /** Call on accepted engine snapshots. Output only transitions, not every frame. */
    fun observe(
        loading: Boolean,
        playing: Boolean,
        ended: Boolean,
        expectedToPlay: Boolean,
        nowMs: Long = origin.elapsedNow().inWholeMilliseconds,
    ): String? {
        if (!expectedToPlay || ended) {
            if (!firstPlaying) openingInterrupted = true
            stallStart = null // exclude intentional pauses/seeks from stall metrics
            return null
        }
        if (!firstPlaying) {
            if (!playing || loading) return null
            firstPlaying = true
            startupMs = nowMs.coerceAtLeast(0L).takeUnless { openingInterrupted }
            return if (openingInterrupted) "startup_completed timing_excluded=true"
            else "startup_completed elapsed_ms=${nowMs.coerceAtLeast(0L)}"
        }
        if (loading) {
            if (stallStart == null) {
                stallStart = nowMs
                lastStallAtMs = nowMs
                return "rebuffer_started"
            }
            return null
        }
        val start = stallStart ?: return null
        if (!playing) return null
        stallStart = null
        val elapsed = (nowMs - start).coerceAtLeast(0L)
        lastStallAtMs = nowMs
        stallCount++
        totalStallMs += elapsed
        return "rebuffer_completed elapsed_ms=$elapsed count=$stallCount total_ms=$totalStallMs"
    }
}
