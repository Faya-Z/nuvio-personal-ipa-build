package com.nuvio.app.features.player

/** Keeps asynchronous cue downloads tied to the selection that requested them. */
internal class PersonalSubtitleSyncGate<K> {
    private var key: K? = null
    private var generation = 0L
    fun bind(next: K?): Boolean {
        if (next == key) return false
        key = next
        generation++
        return true
    }
    fun begin(next: K): Long {
        bind(next)
        return ++generation
    }
    fun accepts(token: Long, current: K?): Boolean =
        current != null && key == current && token == generation
    fun isBound(current: K?): Boolean = current != null && key == current
}

/** Clamp before narrowing to Int, even with malformed subtitle timestamps. */
internal fun personalSubtitleDelayMs(captured: Long, cue: Long, reaction: Long, min: Int, max: Int): Int {
    val delta = captured.coerceAtLeast(0L) - cue.coerceAtLeast(0L)
    val correction = reaction.coerceIn(0L, Int.MAX_VALUE.toLong())
    return (delta.coerceIn(min.toLong() + correction, max.toLong() + correction) - correction).toInt()
}

/** A seek is redundant only if a confirmed snapshot belongs to the current playback. */
internal fun personalNeedsResumeSeek(targetMs: Long, observedMs: Long, currentSnapshot: Boolean): Boolean {
    if (targetMs <= 0L) return false
    if (!currentSnapshot || observedMs < 0L || observedMs == 0L) return true
    return if (observedMs >= targetMs) observedMs - targetMs > 250L else targetMs - observedMs > 250L
}
