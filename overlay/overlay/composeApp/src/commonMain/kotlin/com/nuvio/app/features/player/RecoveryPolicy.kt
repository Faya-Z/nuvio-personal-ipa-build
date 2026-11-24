package com.nuvio.app.features.player

/** One attempt per uninterrupted loading interval; no inference from a moving playback clock. */
internal class StallRecoveryGate(private val timeoutMs: Long = 15_000L) {
    private var since: Long? = null
    private var position: Long = 0L
    private var attempted = false

    fun reset() { since = null; attempted = false; position = 0L }

    fun observe(eligible: Boolean, loading: Boolean, positionMs: Long, nowMs: Long): Boolean {
        if (!eligible || !loading) { reset(); return false }
        val start = since
        if (start == null || nowMs < start || positionMs != position) {
            since = nowMs; position = positionMs; attempted = false
            return false
        }
        if (attempted || nowMs - start < timeoutMs) return false
        attempted = true
        return true
    }
}

/** Local bounded observations, with optional persistence of opaque provider identifiers. */
internal class SourceReliability(
    private val limit: Int = 32,
    persisted: String? = null,
    private val nowMs: () -> Long = { 0L },
    private val persist: (String) -> Unit = {},
) {
    private data class Counts(val successes: Int = 0, val failures: Int = 0, val timeMs: Long = 0)
    private val entries = linkedMapOf<String, Counts>()
    private val maxAgeMs = 14L * 24 * 60 * 60 * 1000
    init {
        require(limit in 1..128)
        if (persisted != null && persisted.length <= 20_000 && persisted.startsWith("v1\n")) {
            for (line in persisted.lineSequence().drop(1)) {
                val parts = line.split('|')
                if (parts.size != 4 || !parts[0].matches(Regex("[0-9a-f]{16}"))) continue
                val success = parts[1].toIntOrNull() ?: continue
                val failure = parts[2].toIntOrNull() ?: continue
                val time = parts[3].toLongOrNull() ?: continue
                if (success !in 0..24 || failure !in 0..24 || success + failure !in 1..24) continue
                if (!fresh(time)) continue
                entries.remove(parts[0])
                entries[parts[0]] = Counts(success, failure, time)
                trim()
            }
        }
    }
    private fun fresh(time: Long): Boolean {
        val now = nowMs()
        return time >= 0 && now >= time && now - time <= maxAgeMs
    }
    private fun trim() {
        while (entries.size > limit) entries.remove(entries.keys.first())
    }
    // FNV-1a pseudonym, not cryptographic protection. Never persist the original ID.
    private fun key(provider: String?): String? {
        if (provider.isNullOrBlank() || provider.length > 2048) return null
        var hash = 14695981039346656037UL
        for (byte in provider.encodeToByteArray()) {
            hash = (hash xor byte.toUByte().toULong()) * 1099511628211UL
        }
        return hash.toString(16).padStart(16, '0')
    }
    fun record(provider: String?, success: Boolean) {
        val id = key(provider) ?: return
        val now = nowMs().coerceAtLeast(0)
        entries.entries.removeAll { !fresh(it.value.timeMs) }
        val old = entries.remove(id) ?: Counts()
        val c = if (old.successes + old.failures >= 24) Counts(old.successes / 2, old.failures / 2) else old
        entries[id] = if (success) c.copy(successes = c.successes + 1, timeMs = now)
            else c.copy(failures = c.failures + 1, timeMs = now)
        trim()
        persist(snapshot())
    }
    fun snapshot(): String = buildString {
        append("v1\n")
        for ((id, c) in entries) if (fresh(c.timeMs)) {
            append(id).append('|').append(c.successes).append('|').append(c.failures).append('|').append(c.timeMs).append('\n')
        }
    }
    fun observations(provider: String?): Int {
        val c = entries[key(provider)]?.takeIf { fresh(it.timeMs) } ?: return 0
        return c.successes + c.failures
    }
    fun score(provider: String?): Double {
        val c = entries[key(provider)]?.takeIf { fresh(it.timeMs) } ?: return 0.5
        return (c.successes + 2.0) / (c.successes + c.failures + 4.0)
    }
    fun <T> best(candidates: List<T>, provider: (T) -> String?): T? =
        candidates.maxByOrNull { score(provider(it)) }
}
