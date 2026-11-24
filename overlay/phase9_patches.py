from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
patches = {
    base/'PlayerScreenRuntimeState.kt': [
        ('    var subtitleAutoSyncState by mutableStateOf(SubtitleAutoSyncUiState())',
         '    val personalSubtitleSyncGate = PersonalSubtitleSyncGate<Triple<PlaybackKey, String, String>>()\n'
         '    var subtitleAutoSyncState by mutableStateOf(SubtitleAutoSyncUiState())'),
    ],
    base/'PlayerScreenRuntimeSubtitleActions.kt': [
        ('import kotlinx.coroutines.launch\n', 'import kotlinx.coroutines.launch\nimport kotlinx.coroutines.CancellationException\n'),
        ('    val extras = activeSubtitleExtras\n', '    val extras = activeSubtitleExtras\n    val requestedSourceKey = sourcePlaybackKey\n'),
        ('                activeSubtitleExtras = enriched\n                persistComputedVideoHash(enriched)\n',
         '                if (sourcePlaybackKey == requestedSourceKey && (p2pResolvedSourceUrl ?: activeSourceUrl) == hashableUrl) {\n'
         '                    activeSubtitleExtras = enriched\n                    persistComputedVideoHash(enriched)\n                }\n'),
        ('internal fun PlayerScreenRuntime.loadSubtitleAutoSyncCues(force: Boolean = false) {\n    val subtitle = selectedAddonSubtitle ?: return\n    if (!force && subtitleAutoSyncState.cues.isNotEmpty()) return\n',
         'internal fun PlayerScreenRuntime.personalSubtitleSyncIdentity(): Triple<PlaybackKey, String, String>? =\n'
         '    selectedAddonSubtitle?.takeIf { useCustomSubtitles }?.let { Triple(activePlaybackKey, it.selectionKey, it.url) }\n\n'
         'internal fun PlayerScreenRuntime.bindPersonalSubtitleSync() {\n'
         '    if (personalSubtitleSyncGate.bind(personalSubtitleSyncIdentity())) subtitleAutoSyncState = SubtitleAutoSyncUiState()\n'
         '}\n\n'
         'internal fun PlayerScreenRuntime.loadSubtitleAutoSyncCues(force: Boolean = false) {\n'
         '    val subtitle = selectedAddonSubtitle ?: return\n'
         '    val identity = personalSubtitleSyncIdentity() ?: return\n'
         '    bindPersonalSubtitleSync()\n'
         '    if (!force && (subtitleAutoSyncState.cues.isNotEmpty() || subtitleAutoSyncState.isLoading)) return\n'),
        ('    subtitleAutoSyncState = subtitleAutoSyncState.copy(isLoading = true, errorMessage = null)\n    scope.launch {\n',
         '    val requestToken = personalSubtitleSyncGate.begin(identity)\n'
         '    val requestHeaders = sanitizePlaybackHeaders(activeSourceHeaders)\n'
         '    subtitleAutoSyncState = subtitleAutoSyncState.copy(isLoading = true, errorMessage = null)\n    scope.launch {\n'),
        ('                headers = sanitizePlaybackHeaders(activeSourceHeaders),\n', '                headers = requestHeaders,\n'),
        ('        result.fold(\n            onSuccess = { cues ->\n',
         '        result.exceptionOrNull()?.let { if (it is CancellationException) throw it }\n'
         '        if (!personalSubtitleSyncGate.accepts(requestToken, personalSubtitleSyncIdentity())) return@launch\n'
         '        result.fold(\n            onSuccess = { cues ->\n'),
        ('                    errorMessage = error.message ?: localizedSubtitleLinesLoadError(),\n',
         '                    errorMessage = localizedSubtitleLinesLoadError(),\n'),
        ('internal fun PlayerScreenRuntime.captureSubtitleAutoSyncTime() {\n    subtitleAutoSyncState =',
         'internal fun PlayerScreenRuntime.captureSubtitleAutoSyncTime() {\n'
         '    if (personalSubtitleSyncIdentity() == null || playbackSnapshotKey != activePlaybackKey || playbackSnapshot.isLoading) return\n'
         '    bindPersonalSubtitleSync()\n    subtitleAutoSyncState ='),
        ('    val capturedPositionMs = subtitleAutoSyncState.capturedPositionMs ?: return\n    val newDelayMs = (capturedPositionMs - cue.startTimeMs - SUBTITLE_AUTO_SYNC_REACTION_COMPENSATION_MS)\n        .toInt()\n        .coerceIn(SUBTITLE_DELAY_MIN_MS, SUBTITLE_DELAY_MAX_MS)\n',
         '    if (!personalSubtitleSyncGate.isBound(personalSubtitleSyncIdentity()) || cue !in subtitleAutoSyncState.cues || subtitleAutoSyncState.isLoading) return\n'
         '    val capturedPositionMs = subtitleAutoSyncState.capturedPositionMs ?: return\n'
         '    val newDelayMs = personalSubtitleDelayMs(capturedPositionMs, cue.startTimeMs,\n'
         '        SUBTITLE_AUTO_SYNC_REACTION_COMPENSATION_MS.toLong(), SUBTITLE_DELAY_MIN_MS, SUBTITLE_DELAY_MAX_MS)\n'),
    ],
    base/'PlayerScreenRuntimeEffects.kt': [
        ('    LaunchedEffect(selectedAddonSubtitleId, useCustomSubtitles, activeSourceUrl) {\n        subtitleAutoSyncState = SubtitleAutoSyncUiState()\n',
         '    LaunchedEffect(selectedAddonSubtitleId, useCustomSubtitles, activePlaybackKey, selectedAddonSubtitle?.url) {\n        bindPersonalSubtitleSync()\n'),
        ('        controller.seekTo(boundedResumeTargetMs(targetPositionMs, playbackSnapshot.durationMs))\n        initialSeekApplied = true\n',
         '        val boundedTargetMs = boundedResumeTargetMs(targetPositionMs, playbackSnapshot.durationMs)\n'
         '        if (personalNeedsResumeSeek(boundedTargetMs, playbackSnapshot.positionMs, playbackSnapshotKey == activePlaybackKey)) {\n'
         '            controller.seekTo(boundedTargetMs)\n        }\n        initialSeekApplied = true\n'),
    ],
}
