package com.nuvio.app.features.player

import kotlin.math.max
import kotlin.math.min

/** Reissued metadata can shift a chapter boundary. Treat substantially overlapping
 * intervals of the same category as the same segment; separate recaps remain separate. */
internal fun personalSameSkipSegment(
    category: String?, start: Double, end: Double,
    previousCategory: String?, previousStart: Double, previousEnd: Double,
): Boolean {
    if (category == null || category != previousCategory ||
        !start.isFinite() || !end.isFinite() || !previousStart.isFinite() || !previousEnd.isFinite() ||
        start < 0.0 || previousStart < 0.0 || end <= start || previousEnd <= previousStart) return false
    val overlap = min(end, previousEnd) - max(start, previousStart)
    return overlap > 0 && overlap >= 0.5 * max(end - start, previousEnd - previousStart)
}

/** Never auto-seek backward, into the past, or outside the known timeline. */
internal fun personalForwardSkipTarget(positionMs: Long, requestedMs: Long, durationMs: Long): Long? {
    if (positionMs < 0 || requestedMs <= positionMs || durationMs <= 0 || positionMs >= durationMs) return null
    val bounded = min(requestedMs, durationMs - 1)
    return bounded.takeIf { it > positionMs }
}

/** The next episode can change after metadata/shuffle updates without changing
 * the current source. An old preload must not suppress preparation for the new one. */
internal fun personalShouldResetPreload(previous: Triple<String, Int?, Int?>?, next: Triple<String, Int?, Int?>?, triggered: Boolean): Boolean =
    triggered && previous != next
