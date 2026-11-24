package com.nuvio.app.features.player

/** Only checkpoint a known current media position, never a placeholder or unresolved seek. */
internal fun personalHandoverPosition(
    positionMs: Long, durationMs: Long, activeSnapshot: Boolean, controllerReady: Boolean,
    initialSeekApplied: Boolean, loading: Boolean, opening: Boolean, ended: Boolean,
    scrubbing: Boolean, pendingSeekAgeMs: Long?, inParty: Boolean, hasError: Boolean,
): Long? {
    if (!activeSnapshot || !controllerReady || !initialSeekApplied || loading || opening || ended ||
        scrubbing || inParty || hasError || (pendingSeekAgeMs != null && pendingSeekAgeMs < 1_500L)) return null
    if (durationMs < 60_000L || positionMs < 1_000L || positionMs >= durationMs) return null
    return positionMs
}

internal enum class PersonalHandoverConfirmation { CHECKING, CONFIRMED, UNCONFIRMED, UNAVAILABLE }

/** Strict readback: identical media and checkpoint, and a write no older than this request. */
internal data class PersonalHandoverCheckpoint(
    val contentId: String, val contentType: String, val videoId: String,
    val season: Int?, val episode: Int?, val positionMs: Long, val durationMs: Long, val requestedAtMs: Long,
) {
    fun matches(id: String, type: String, video: String, s: Int?, e: Int?, position: Long,
                duration: Long, lastWatched: Long): Boolean =
        contentId.isNotBlank() && videoId.isNotBlank() && requestedAtMs > 0 &&
            positionMs > 0 && positionMs < durationMs &&
            contentId == id && contentType.equals(type, ignoreCase = true) && videoId == video &&
            season == s && episode == e && position == positionMs && duration == durationMs &&
            lastWatched >= requestedAtMs
}
