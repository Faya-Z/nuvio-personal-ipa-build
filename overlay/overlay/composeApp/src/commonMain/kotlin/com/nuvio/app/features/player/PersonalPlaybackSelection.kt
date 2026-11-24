package com.nuvio.app.features.player

/** Only promote a source when both provider histories have useful evidence. */
internal fun <T> rankInitialSources(
    candidates: List<T>,
    score: (T) -> Double,
    observations: (T) -> Int,
    isDirect: (T) -> Boolean,
): List<T> {
    val first = candidates.firstOrNull() ?: return candidates
    // Do not reorder mixed server/peer-to-peer/resolver lists or a configured first-stream order.
    if (candidates.size < 2 || candidates.any { !isDirect(it) } || observations(first) < 3) return candidates
    val index = candidates.indices.drop(1).filter { observations(candidates[it]) >= 3 }
        .maxByOrNull { score(candidates[it]) } ?: return candidates
    if (score(candidates[index]) - score(first) < 0.15) return candidates
    return listOf(candidates[index]) + candidates.filterIndexed { i, _ -> i != index }
}

internal enum class EnglishAudioStatus(val display: String) {
    English("English (track metadata)"), Other("Other language (track metadata)"),
    Unknown("Language not identified"), NoSelection("No selected audio track")
}

internal fun audioLanguageStatus(language: String?): EnglishAudioStatus {
    val code = language?.trim()?.lowercase()?.replace('_', '-') ?: return EnglishAudioStatus.Unknown
    if (code.isBlank() || code in setOf("und", "unknown", "default", "mul", "zxx", "none", "unidentified"))
        return EnglishAudioStatus.Unknown
    if (code == "english" || code == "eng" || code == "en" ||
        code.matches(Regex("(?:en|eng)-[a-z0-9]{2,8}(?:-[a-z0-9]{2,8})*"))) return EnglishAudioStatus.English
    return if (code.matches(Regex("[a-z]{2,3}(?:-[a-z0-9]{2,8})*"))) EnglishAudioStatus.Other
        else EnglishAudioStatus.Unknown
}

internal data class EnglishTrackCandidate(val index: Int, val language: String?, val label: String, val selected: Boolean)

internal fun preferredVerifiedEnglishTrack(tracks: List<EnglishTrackCandidate>): Int? {
    val current = tracks.firstOrNull { it.selected } ?: return null
    if (audioLanguageStatus(current.language) == EnglishAudioStatus.English) return null
    val nonMain = Regex("commentary|audio[ -]?description|descriptive|director.?s|isolated[ -]?score", RegexOption.IGNORE_CASE)
    return tracks.firstOrNull { it.index >= 0 && audioLanguageStatus(it.language) == EnglishAudioStatus.English &&
        !nonMain.containsMatchIn(it.label) }?.index
}

/** Count only plausible continuous media movement, never seek jumps or loading gaps. */
internal class PlaybackSessionHistory {
    var watchedMediaMs: Long = 0; private set
    var sessions: Int = 0; private set
    var lastPositionMs: Long? = null; private set
    private var previousPosition: Long? = null
    private var previousTime: Long? = null
    private var sessionStarted = false
    fun resetContinuity() { previousPosition = null; previousTime = null }
    fun observe(positionMs: Long, nowMs: Long, playing: Boolean, speed: Float) {
        if (!playing || positionMs < 0 || !speed.isFinite() || speed <= 0f) { resetContinuity(); return }
        val oldPosition = previousPosition
        val oldTime = previousTime
        previousPosition = positionMs; previousTime = nowMs; lastPositionMs = positionMs
        if (oldPosition == null || oldTime == null) return
        val elapsed = nowMs - oldTime
        val movement = positionMs - oldPosition
        if (elapsed !in 1..2_000 || movement <= 0L || movement > (elapsed * speed + 350f).toLong()) return
        if (!sessionStarted) { sessions++; sessionStarted = true }
        watchedMediaMs = (watchedMediaMs + movement).coerceAtMost(7L * 24 * 3600 * 1000)
    }
}
