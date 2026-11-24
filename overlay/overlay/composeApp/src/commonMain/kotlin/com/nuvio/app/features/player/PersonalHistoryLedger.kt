package com.nuvio.app.features.player

internal data class HistoryEntry(val playedMs: Long, val sessions: Int, val updatedMs: Long)

/** Local, bounded, versioned per-profile history. Keys are encoded media IDs, never source URLs. */
internal class PersonalHistoryLedger(raw: String?) {
    private val entries = linkedMapOf<String, HistoryEntry>()
    init {
        raw?.takeIf { it.length <= 150_000 && it.startsWith("v1\n") }?.lineSequence()?.drop(1)?.take(200)?.forEach { line ->
            val parts = line.split('|')
            if (parts.size == 4 && parts[0].length in 2..1024 && parts[0].length % 2 == 0 && parts[0].all { it in "0123456789abcdef" }) {
                val played = parts[1].toLongOrNull()
                val sessions = parts[2].toIntOrNull()
                val updated = parts[3].toLongOrNull()
                if (played != null && played in 1..MAX_PLAYED && sessions != null && sessions in 1..MAX_SESSIONS && updated != null && updated >= 0) {
                    entries[parts[0]] = HistoryEntry(played, sessions, updated)
                }
            }
        }
        trim()
    }
    fun get(mediaId: String): HistoryEntry? = key(mediaId)?.let(entries::get)
    fun record(mediaId: String, deltaMs: Long, newSession: Boolean, nowMs: Long): Boolean {
        val key = key(mediaId) ?: return false
        if (deltaMs !in 1..MAX_PLAYED || nowMs < 0) return false
        val prior = entries[key]
        entries[key] = HistoryEntry(((prior?.playedMs ?: 0) + deltaMs).coerceAtMost(MAX_PLAYED),
            ((prior?.sessions ?: 0) + if (newSession || prior == null) 1 else 0).coerceAtMost(MAX_SESSIONS), nowMs)
        trim()
        return true
    }
    fun encode(): String = "v1\n" + entries.entries.joinToString("\n") { (k,v) -> "$k|${v.playedMs}|${v.sessions}|${v.updatedMs}" }
    private fun trim() { while (entries.size > 100) { val oldest = entries.minByOrNull { it.value.updatedMs } ?: break; entries.remove(oldest.key) } }
    private fun key(id: String): String? {
        if (id.isBlank() || id.contains("://") || id.length > 256) return null
        val bytes = id.encodeToByteArray()
        if (bytes.size > 512) return null
        val digits = "0123456789abcdef"
        return buildString { for (b in bytes) { val n = b.toInt() and 255; append(digits[n shr 4]); append(digits[n and 15]) } }
    }
    private companion object { const val MAX_PLAYED = 365L * 24 * 60 * 60 * 1000; const val MAX_SESSIONS = 100_000 }
}

internal class PersonalSleepTimer {
    private var deadlineMs: Long? = null
    fun set(minutes: Int, nowMs: Long) {
        deadlineMs = if (minutes in setOf(15, 30, 60) && nowMs >= 0 && nowMs <= Long.MAX_VALUE - 3_600_000L) nowMs + minutes * 60_000L else null
    }
    fun remainingMs(nowMs: Long): Long? = deadlineMs?.let { (it - nowMs).coerceAtLeast(0L) }
    fun consumeIfDue(nowMs: Long): Boolean {
        if (remainingMs(nowMs) != 0L) return false
        deadlineMs = null
        return true
    }
}
