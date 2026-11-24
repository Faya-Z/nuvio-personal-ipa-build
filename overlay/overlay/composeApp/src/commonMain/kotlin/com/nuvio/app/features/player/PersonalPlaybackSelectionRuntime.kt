package com.nuvio.app.features.player

import com.nuvio.app.isIos
import com.nuvio.app.features.streams.StreamAutoPlayEvaluation
import com.nuvio.app.features.streams.epochMs
import kotlin.time.TimeSource

/** Initial selection uses a fresh profile-local score snapshot and never triggers a network probe. */
internal fun rankPersonalInitialSources(evaluation: StreamAutoPlayEvaluation, profileId: Int, enabled: Boolean): StreamAutoPlayEvaluation {
    if (!isIos || !enabled || evaluation.stream == null || evaluation.readyStreams.firstOrNull() != evaluation.stream) return evaluation
    val stored = runCatching { SourceReliabilityStorage.load(profileId) }.getOrNull() ?: return evaluation
    val reliability = SourceReliability(persisted = stored, nowMs = ::epochMs)
    val ranked = rankInitialSources(evaluation.readyStreams,
        score = { reliability.score(it.addonId) }, observations = { reliability.observations(it.addonId) },
        isDirect = { it.playableDirectUrl != null && it.serverTarget == null && it.clientResolve == null && it.p2pInfoHash == null })
    return if (ranked == evaluation.readyStreams) evaluation else evaluation.copy(stream = ranked.firstOrNull(), readyStreams = ranked)
}

internal class PersonalEnglishCorrection {
    private var key: PlaybackKey? = null
    private var controller: PlayerEngineController? = null
    private var attempted = false
    fun allow(key: PlaybackKey, controller: PlayerEngineController): Boolean {
        if (this.key != key || this.controller !== controller) {
            this.key = key; this.controller = controller; attempted = false
        }
        if (attempted) return false
        attempted = true
        return true
    }
}

internal fun PlayerScreenRuntime.verifyPreferredEnglishAudio() {
    if (!isIos || playbackSnapshot.isLoading || !trackPreferenceRestoreApplied || !preferredAudioSelectionApplied ||
        isUserExplicitAudioSelection || pendingEngineSwitchTrackPreference != null ||
        serverAudioTracks.isNotEmpty() || isPartySynced || playerControllerSourceUrl != activeSourceUrl ||
        audioLanguageStatus(playerSettingsUiState.preferredAudioLanguage) != EnglishAudioStatus.English) return
    val ctrl = playerController ?: return
    val track = preferredVerifiedEnglishTrack(ctrl.getAudioTracks().map {
        EnglishTrackCandidate(it.index, it.language, it.label, it.isSelected)
    }) ?: return
    if (personalEnglishCorrection.allow(activePlaybackKey, ctrl)) ctrl.selectAudioTrack(track)
}

internal fun PlayerScreenRuntime.selectedAudioMetadataStatus(): String =
    (audioTracks.firstOrNull { it.isSelected }?.let { audioLanguageStatus(it.language) }
        ?: EnglishAudioStatus.NoSelection).display

/** Current-item session with periodic, profile-local history checkpoints. */
internal class PersonalSessionHistory(private val profileId: Int) {
    private val clock = TimeSource.Monotonic.markNow()
    private var item: Triple<String?, Int?, Int?>? = null
    private var playbackKey: PlaybackKey? = null
    private var mediaId: String? = null
    private var savedMs = 0L
    private var lastSaveMs = 0L
    private var savedSession = false
    private var persisted: HistoryEntry? = null
    fun flush() {
        val id = mediaId ?: return
        val delta = history.watchedMediaMs - savedMs
        if (delta <= 0L) return
        runCatching {
            val ledger = PersonalHistoryLedger(PersonalHistoryStorage.load(profileId))
            if (ledger.record(id, delta, !savedSession, epochMs())) {
                PersonalHistoryStorage.save(profileId, ledger.encode())
                savedMs = history.watchedMediaMs
                savedSession = true
                persisted = ledger.get(id)
            }
        }
    }
    fun totalForCurrentItem(): HistoryEntry? {
        val pending = history.watchedMediaMs - savedMs
        val prior = persisted
        if (prior == null && pending <= 0L) return null
        return HistoryEntry((prior?.playedMs ?: 0L) + pending, (prior?.sessions ?: 0) + if (pending > 0 && !savedSession) 1 else 0, prior?.updatedMs ?: 0L)
    }
    var history = PlaybackSessionHistory(); private set
    fun observe(key: PlaybackKey, item: Triple<String?, Int?, Int?>, mediaId: String, snapshot: PlayerPlaybackSnapshot, playing: Boolean) {
        if (this.item != item || this.mediaId != mediaId) {
            flush(); this.item = item; this.mediaId = mediaId; history = PlaybackSessionHistory()
            savedMs = 0; savedSession = false; lastSaveMs = clock.elapsedNow().inWholeMilliseconds
            persisted = runCatching { PersonalHistoryLedger(PersonalHistoryStorage.load(profileId)).get(mediaId) }.getOrNull()
        }
        if (playbackKey != key) { playbackKey = key; history.resetContinuity() }
        val now = clock.elapsedNow().inWholeMilliseconds
        history.observe(snapshot.positionMs, now, playing, snapshot.playbackSpeed)
        if (now - lastSaveMs >= 30_000L) { flush(); lastSaveMs = now }
    }
}

internal fun PlayerScreenRuntime.observePersonalSessionHistory(snapshot: PlayerPlaybackSnapshot) {
    if (!isIos) return
    personalSessionHistory.observe(activePlaybackKey, Triple(activeVideoId, activeSeasonNumber, activeEpisodeNumber), playbackSession.videoId, snapshot,
        initialLoadCompleted && initialSeekApplied && shouldPlay && snapshot.isPlaying && !snapshot.isLoading &&
        !snapshot.isEnded && !isScrubbingTimeline && scrubbingPositionMs == null &&
        (pendingSeekTarget?.second?.elapsedNow()?.inWholeMilliseconds ?: Long.MAX_VALUE) >= 3_000L)
}
