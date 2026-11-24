from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
patches = {
    base/'PlayerScreenRuntimeEffects.kt': [
        ('''            current !in autoSkippedIntervals
        ) {
            val durationMs = playbackSnapshot.durationMs
            val rawMs = current.internalSkipAction(skipIntervals, durationMs)?.targetMs ?: return@LaunchedEffect
            val seekPositionMs = if (durationMs > 0L) rawMs.coerceAtMost(durationMs - 1) else rawMs
''', '''            current !in autoSkippedIntervals &&
            !skipIntervalDismissed && playbackSnapshotKey == activePlaybackKey &&
            !playbackSnapshot.isLoading && !playbackSnapshot.isOpening && shouldPlay &&
            autoSkippedIntervals.none { previous ->
                personalSameSkipSegment(segmentCategory(current.type), current.startTime, current.endTime,
                    segmentCategory(previous.type), previous.startTime, previous.endTime)
            }
        ) {
            val durationMs = playbackSnapshot.durationMs
            val rawMs = current.internalSkipAction(skipIntervals, durationMs)?.targetMs ?: return@LaunchedEffect
            val seekPositionMs = personalForwardSkipTarget(playbackSnapshot.positionMs, rawMs, durationMs)
                ?: return@LaunchedEffect
'''),
        ('''    LaunchedEffect(playbackSnapshot.isLoading, playerController, playerControllerSourceUrl, activeSourceUrl) {
        if (!playbackSnapshot.isLoading) loadChaptersIfNeeded()
    }
''', '''    LaunchedEffect(playbackSnapshot.isLoading, playbackSnapshot.isOpening, playbackSnapshotKey,
        activePlaybackKey, playerController, playerControllerSourceUrl, activeSourceUrl) {
        if (!playbackSnapshot.isLoading && !playbackSnapshot.isOpening &&
            playbackSnapshotKey == activePlaybackKey) loadChaptersIfNeeded()
    }
'''),
    ],
    base/'PlayerScreenRuntimeUi.kt': [
        ('''                if (seekMs != null) {
                    playerController?.seekTo(seekMs)
                    scheduleProgressSyncAfterSeek()
                    publishPartyPlayback(positionMs = seekMs)
                    skipIntervalDismissed = true
''', '''                if (seekMs != null && playerControllerSourceUrl == activeSourceUrl &&
                    playbackSnapshotKey == activePlaybackKey && playerController != null) {
                    autoSkippedIntervals.add(interval)
                    playerController?.seekTo(seekMs)
                    scheduleProgressSyncAfterSeek()
                    publishPartyPlayback(positionMs = seekMs)
                    skipIntervalDismissed = true
'''),
        ('''        onDismissSkipInterval = { skipIntervalDismissed = true },''', '''        onDismissSkipInterval = {
            activeSkipInterval?.let(autoSkippedIntervals::add)
            skipIntervalDismissed = true
        },'''),
    ],
    base/'PlayerScreenRuntimeChapters.kt': [
        ('''    val sourceUrl = activeSourceUrl
    if (playerControllerSourceUrl != sourceUrl || chaptersLoadedForSourceUrl == sourceUrl) return
    val loaded = PlayerChapters.normalize(controller.getChapters())
    if (activeSourceUrl != sourceUrl || playerController !== controller) return
''', '''    val sourceUrl = activeSourceUrl
    val expectedKey = activePlaybackKey
    if (playerControllerSourceUrl != sourceUrl || chaptersLoadedForSourceUrl == sourceUrl ||
        playbackSnapshotKey != expectedKey || playbackSnapshot.isOpening) return
    val loaded = PlayerChapters.normalize(controller.getChapters())
    if (activeSourceUrl != sourceUrl || playerController !== controller || activePlaybackKey != expectedKey) return
'''),
    ],
}
patches[base/'PlayerScreenRuntimeState.kt'] = [
    ('    var nextEpisodePreloadTriggered by mutableStateOf(false)\n',
     '    var nextEpisodePreloadTriggered by mutableStateOf(false)\n'
     '    var personalPreloadedEpisodeKey: Triple<String, Int?, Int?>? = null\n'),
]
patches[base/'PlayerNextEpisodeAutoPlay.kt'] = [
    ('    // Preload: trigger source fetch before the button appears\n',
     '    val nextPreloadKey = nextEpisodeInfo?.let { Triple(it.videoId, it.season, it.episode) }\n'
     '    if (personalShouldResetPreload(personalPreloadedEpisodeKey, nextPreloadKey, nextEpisodePreloadTriggered)) {\n'
     '        cancelNextEpisodePreload()\n'
     '    }\n'
     '    // Preload: trigger source fetch before the button appears\n'),
    ('    if (playerSettingsUiState.preloadNextEpisodeSources && !nextEpisodePreloadTriggered && nextEpisodeInfo != null && !isNetworkOffline()) {\n',
     '    if (playerSettingsUiState.preloadNextEpisodeSources && !nextEpisodePreloadTriggered && nextEpisodeInfo != null &&\n'
     '        !isNetworkOffline() && !showEpisodesPanel && !nextEpisodeAutoPlaySearching) {\n'),
    ('    nextEpisodePreloadTriggered = true\n    nextEpisodePreloadJob?.cancel()\n',
     '    nextEpisodePreloadTriggered = true\n'
     '    personalPreloadedEpisodeKey = Triple(nextEp.videoId, nextEp.season, nextEp.episode)\n'
     '    if (DownloadsRepository.findPlayableDownload(parentMetaId = parentMetaId, seasonNumber = nextEp.season,\n'
     '            episodeNumber = nextEp.episode, videoId = nextEp.videoId) != null) return\n'
     '    nextEpisodePreloadJob?.cancel()\n'),
    ('    nextEpisodePreloadTriggered = false\n}',
     '    nextEpisodePreloadTriggered = false\n    personalPreloadedEpisodeKey = null\n}'),
]
