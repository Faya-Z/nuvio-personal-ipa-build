package com.nuvio.app.features.player

import com.nuvio.app.isIos
import kotlin.time.TimeSource
import com.nuvio.app.features.streams.epochMs

/** Source-local monitor, fed by the existing engine snapshot callback; no extra timer/network probe. */
internal class PlayerRecoveryRuntime(private val profileId: Int) {
    val gate = StallRecoveryGate()
    val reliability by lazy {
        SourceReliability(
            persisted = if (isIos) runCatching { SourceReliabilityStorage.load(profileId) }.getOrNull() else null,
            nowMs = ::epochMs,
            persist = { value -> if (isIos) runCatching { SourceReliabilityStorage.save(profileId, value) } },
        )
    }
    private var key: PlaybackKey? = null
    var watchdogAttempted = false
        private set
    private var started = false
    private var failed = false
    private var origin = TimeSource.Monotonic.markNow()

    fun observeKey(next: PlaybackKey) {
        if (key == next) return
        key = next
        watchdogAttempted = false
        started = false
        failed = false
        origin = TimeSource.Monotonic.markNow()
        gate.reset()
    }
    fun recordStarted(provider: String?) {
        if (!started) { started = true; reliability.record(provider, true) }
    }
    fun recordFailure(provider: String?) {
        if (!failed) { failed = true; reliability.record(provider, false) }
    }
    fun markWatchdogAttempted() { watchdogAttempted = true }
    fun nowMs(): Long = origin.elapsedNow().inWholeMilliseconds
}

internal fun PlayerScreenRuntime.canProactivelyRecover(): Boolean {
    val snapshot = playbackSnapshot
    val hash = activeStream?.behaviorHints?.videoHash
    val size = activeStream?.behaviorHints?.videoSize?.toLong()
    return isIos && playerSettingsUiState.streamAutoPlayFallbackActive &&
        activeSourceUrl == autoSelectedSourceUrl && activeSourceUrl.isNotBlank() &&
        activeVideoId != null && initialLoadCompleted && initialSeekApplied &&
        playbackSnapshotKey == activePlaybackKey && playerControllerSourceUrl == activeSourceUrl &&
        shouldPlay && !isPartySynced && !partyAppInBackground && !isScrubbingTimeline &&
        scrubbingPositionMs == null && (pendingSeekTarget?.second?.elapsedNow()?.inWholeMilliseconds ?: Long.MAX_VALUE) >= 3_000L &&
        !snapshot.isEnded && snapshot.positionMs > 0 && snapshot.durationMs - snapshot.positionMs > 15_000L &&
        errorMessage == null && !isNetworkOffline() && credentialRefreshJob?.isActive != true &&
        activeTorrentInfoHash == null && samePlaybackFile(hash, size, hash, size)
}

internal fun PlayerScreenRuntime.observeRecoverySnapshot(snapshot: PlayerPlaybackSnapshot) {
    recoveryRuntime.observeKey(activePlaybackKey)
    if (isIos && initialLoadCompleted && initialSeekApplied && snapshot.isPlaying && !snapshot.isLoading &&
        shouldPlay && !snapshot.isEnded) recoveryRuntime.recordStarted(activeProviderAddonId)
    val eligible = !recoveryRuntime.watchdogAttempted && canProactivelyRecover() && sourceFallbackJob?.isActive != true &&
        sourceFallbackAttempts < playerSettingsUiState.streamAutoPlayFallbackMaxSources
    if (recoveryRuntime.gate.observe(eligible, snapshot.isLoading, snapshot.positionMs, recoveryRuntime.nowMs())) {
        recoveryRuntime.markWatchdogAttempted()
        tryFallbackToNextSourceAfterError(null, proactivePositionMs = snapshot.positionMs)
    }
}
