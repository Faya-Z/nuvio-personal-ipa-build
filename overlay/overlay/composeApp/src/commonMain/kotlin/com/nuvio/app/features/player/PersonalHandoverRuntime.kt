package com.nuvio.app.features.player

import com.nuvio.app.features.watchprogress.WatchProgressRepository
import com.nuvio.app.features.watchprogress.WatchProgressClock
import kotlinx.coroutines.launch
import com.nuvio.app.features.profiles.ProfileRepository
import com.nuvio.app.isIos

internal fun PlayerScreenRuntime.personalHandoverTarget(): Long? {
    if (!isIos || profileId != ProfileRepository.activeProfileId || !initialLoadCompleted ||
        sourceFallbackJob?.isActive == true || credentialRefreshJob?.isActive == true ||
        nextEpisodeAutoPlaySearching || nextEpisodeAutoPlayJob?.isActive == true) return null
    return personalHandoverPosition(
        playbackSnapshot.positionMs, playbackSnapshot.durationMs,
        playbackSnapshotKey == activePlaybackKey,
        playerController != null && playerControllerSourceUrl == activeSourceUrl,
        initialSeekApplied, playbackSnapshot.isLoading, playbackSnapshot.isOpening, playbackSnapshot.isEnded,
        isScrubbingTimeline || scrubbingPositionMs != null,
        pendingSeekTarget?.second?.elapsedNow()?.inWholeMilliseconds, isPartySynced, errorMessage != null,
    )
}

/** Uses only the user's existing progress source. No new account, link or stream credentials. */
internal fun PlayerScreenRuntime.savePersonalHandover() {
    val position = personalHandoverTarget() ?: return
    val key = activePlaybackKey
    val snapshot = playbackSnapshot.copy(positionMs = position, isPlaying = false)
    setPlaybackPlaying(false)
    cancelNextEpisodeAutoPlay()
    personalSessionHistory.flush()
    val session = playbackSession
    val requestedAt = WatchProgressClock.nowEpochMs()
    personalHandoverVerificationJob?.cancel()
    personalHandoverKey = key
    personalHandoverPositionMs = position
    personalHandoverConfirmation = PersonalHandoverConfirmation.CHECKING
    WatchProgressRepository.flushPlaybackProgress(session = session, snapshot = snapshot, syncRemote = true)
    personalHandoverVerificationJob = scope.launch {
        val result = WatchProgressRepository.confirmPersonalHandover(session, snapshot, requestedAt)
        if (activePlaybackKey == key && profileId == ProfileRepository.activeProfileId &&
            !shouldPlay && personalHandoverPositionMs == position && personalHandoverKey == key) {
            personalHandoverConfirmation = result
        }
    }
}

internal fun PlayerScreenRuntime.personalHandoverMessage(): String? {
    if (shouldPlay || personalHandoverKey != activePlaybackKey) return null
    val pos = personalHandoverPositionMs ?: return null
    if (kotlin.math.abs(playbackSnapshot.positionMs - pos) > 1_500L) return null
    val seconds = pos / 1_000L
    val message = when (personalHandoverConfirmation) {
        PersonalHandoverConfirmation.CHECKING -> "Checking cloud checkpoint…"
        PersonalHandoverConfirmation.CONFIRMED -> "Cloud checkpoint confirmed. Refresh Continue Watching on the other device."
        PersonalHandoverConfirmation.UNCONFIRMED -> "Sync requested; cloud checkpoint not confirmed."
        PersonalHandoverConfirmation.UNAVAILABLE -> "Cloud confirmation unavailable for this progress source."
    }
    return "Paused at ${seconds / 60}:${(seconds % 60).toString().padStart(2, '0')}. $message"
}
