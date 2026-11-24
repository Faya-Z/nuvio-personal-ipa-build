package com.nuvio.app.features.player

/** Extend existing metadata preloading only when the current stream has enough headroom.
 * This does not fetch media bytes, open another decoder or change user settings. */
internal fun nextEpisodePreparationLeadMs(
    timeoutSeconds: Int,
    positionMs: Long,
    durationMs: Long,
    bufferedPositionMs: Long,
    isPlaying: Boolean,
    hasRecentStall: Boolean,
    allowEarlyPreparation: Boolean,
): Long {
    val normal = (timeoutSeconds.toLong() * 1_000L).coerceIn(10_000L, 30_000L)
    if (!allowEarlyPreparation || !isPlaying || hasRecentStall || positionMs < 30_000L ||
        durationMs <= positionMs || bufferedPositionMs <= positionMs) return normal
    val ahead = bufferedPositionMs.coerceAtMost(durationMs) - positionMs
    if (ahead < 20_000L) return normal
    return (normal + 30_000L).coerceAtMost(60_000L)
}

/** Never issue an initial seek past the known end of a file. A zero duration is unknown. */
internal fun boundedResumeTargetMs(requestedMs: Long, durationMs: Long): Long =
    if (durationMs > 0) requestedMs.coerceIn(0L, durationMs) else requestedMs.coerceAtLeast(0L)
