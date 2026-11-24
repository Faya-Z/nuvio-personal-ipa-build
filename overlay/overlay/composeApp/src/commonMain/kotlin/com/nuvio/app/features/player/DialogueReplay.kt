package com.nuvio.app.features.player

import kotlin.time.TimeSource

internal data class DialogueReplay(
    val key: PlaybackKey,
    val controller: PlayerEngineController,
    val window: DialogueReplayWindow,
    val previousExplicit: Boolean,
    val previousPreferredApplied: Boolean,
    var seekObserved: Boolean = false,
    val requestedAt: kotlin.time.TimeMark = TimeSource.Monotonic.markNow(),
)

internal fun PlayerScreenRuntime.dialogueReplayAvailable(): Boolean {
    val controller = playerController ?: return false
    return initialLoadCompleted && initialSeekApplied && !playbackSnapshot.isLoading &&
        !playbackSnapshot.isEnded && playbackSnapshot.positionMs > 1_000L &&
        playbackSnapshotKey == activePlaybackKey && playerControllerSourceUrl == activeSourceUrl &&
        !isPartySynced && !isScrubbingTimeline && !useCustomSubtitles && selectedAddonSubtitleId == null &&
        serverSubtitleTracks.isEmpty() && !hasBurnedInServerSubtitle &&
        controller.getSubtitleTracks().any { replayEnglishLanguage(it.language) && it.isForced != true } &&
        trackPreferenceRestoreApplied && pendingEngineSwitchTrackPreference == null && errorMessage == null && dialogueReplay == null
}

internal fun PlayerScreenRuntime.replayDialogue() {
    if (!dialogueReplayAvailable()) return
    val controller = playerController ?: return
    val window = DialogueReplayWindow.from(playbackSnapshot.positionMs) ?: return
    val tracks = controller.getSubtitleTracks()
    // If subtitles are already on, simply replay without changing their selection.
    if (selectedSubtitleIndex >= 0 || tracks.any { it.isSelected }) {
        seekBy(window.startMs - window.endMs)
        showSubtitleModal = false
        return
    }
    val track = tracks.firstOrNull { replayEnglishLanguage(it.language) && it.isForced != true } ?: return
    val session = DialogueReplay(activePlaybackKey, controller, window,
        isUserExplicitSubtitleSelection, preferredSubtitleSelectionApplied)
    dialogueReplay = session
    isUserExplicitSubtitleSelection = true
    preferredSubtitleSelectionApplied = true
    controller.selectSubtitleTrack(track.index)
    selectedSubtitleIndex = track.index
    // Use the existing seek pipeline and progress reporting; never save the temporary track.
    seekBy(window.startMs - window.endMs)
    showSubtitleModal = false
}

internal fun PlayerScreenRuntime.finishDialogueReplay(restore: Boolean = true) {
    val session = dialogueReplay ?: return
    dialogueReplay = null
    if (!restore || session.key != activePlaybackKey || session.controller !== playerController) return
    session.controller.selectSubtitleTrack(-1)
    selectedSubtitleIndex = -1
    isUserExplicitSubtitleSelection = session.previousExplicit
    preferredSubtitleSelectionApplied = session.previousPreferredApplied
}

internal fun PlayerScreenRuntime.updateDialogueReplay(snapshot: PlayerPlaybackSnapshot) {
    val session = dialogueReplay ?: return
    if (session.key != activePlaybackKey || session.controller !== playerController) {
        finishDialogueReplay(restore = false)
        return
    }
    if (snapshot.isEnded) { finishDialogueReplay(); return }
    if (!session.seekObserved && session.requestedAt.elapsedNow().inWholeMilliseconds >= 8_000L) {
        finishDialogueReplay()
        return
    }
    if (snapshot.isLoading) return
    // Wait until the seek is actually observed; the first callback may still be at the old point.
    if (snapshot.positionMs < session.window.endMs - 500L) session.seekObserved = true
    if (session.seekObserved && session.window.finished(snapshot.positionMs, snapshot.isEnded)) finishDialogueReplay()
}
