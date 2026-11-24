package com.nuvio.app.features.player

/** Conservative fingerprint match: never infer identical cuts from titles or resolutions. */
internal fun samePlaybackFile(hash: String?, size: Long?, candidateHash: String?, candidateSize: Long?): Boolean {
    val normalized = hash?.trim()?.lowercase() ?: return false
    return normalized.length == 16 && normalized.all { it in "0123456789abcdef" } &&
        size != null && size > 0 && size == candidateSize &&
        normalized == candidateHash?.trim()?.lowercase()
}

internal fun replayEnglishLanguage(language: String?): Boolean {
    val code = language?.trim()?.lowercase()?.replace('_', '-') ?: return false
    return code == "english" || code == "eng" || code == "en" || code.startsWith("en-")
}

internal data class DialogueReplayWindow(val startMs: Long, val endMs: Long) {
    fun finished(positionMs: Long, ended: Boolean): Boolean = ended || positionMs >= endMs
    companion object {
        fun from(positionMs: Long): DialogueReplayWindow? = if (positionMs <= 0L) null
            else DialogueReplayWindow((positionMs - 10_000L).coerceAtLeast(0L), positionMs)
    }
}
