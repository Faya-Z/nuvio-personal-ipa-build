from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
patches = {
    base/'PlayerNextEpisodeAutoPlay.kt': [
        ('        val preloadLeadMs = maxOf(playerSettingsUiState.streamAutoPlayTimeoutSeconds.toLong() * 1_000L, 10_000L)\n            .coerceAtMost(30_000L)\n',
         '        val preloadLeadMs = nextEpisodePreparationLeadMs(\n'
         '            timeoutSeconds = playerSettingsUiState.streamAutoPlayTimeoutSeconds,\n'
         '            positionMs = playbackSnapshot.positionMs,\n'
         '            durationMs = playbackSnapshot.durationMs,\n'
         '            bufferedPositionMs = playbackSnapshot.bufferedPositionMs,\n'
         '            isPlaying = playbackSnapshot.isPlaying && shouldPlay,\n'
         '            hasRecentStall = playbackDiagnostics.hasRecentStall(),\n'
         '            allowEarlyPreparation = com.nuvio.app.isIos && !isPartySynced && !partyAppInBackground &&\n'
         '                activeTorrentInfoHash == null && sourceFallbackJob?.isActive != true &&\n'
         '                credentialRefreshJob?.isActive != true && !showEpisodesPanel &&\n'
         '                (pendingSeekTarget?.second?.elapsedNow()?.inWholeMilliseconds ?: Long.MAX_VALUE) >= 3_000L,\n'
         '        )\n'),
        ('    val type = contentType ?: return\n    // Offline: preloading streams', '    val type = contentType ?: parentMetaType\n    // Offline: preloading streams'),
    ],
    base/'PlayerScreenRuntimeEffects.kt': [
        ('        controller.seekTo(targetPositionMs)\n        initialSeekApplied = true\n',
         '        controller.seekTo(boundedResumeTargetMs(targetPositionMs, playbackSnapshot.durationMs))\n        initialSeekApplied = true\n'),
    ],
    base/'PlayerScreenRuntimeUi.kt': [
        ('        addonSubtitle = selectedAddonSubtitle.takeIf { useCustomSubtitles },\n        onDismiss = { showStreamInfo = false },\n',
         '        addonSubtitle = selectedAddonSubtitle.takeIf { useCustomSubtitles },\n'
         '        diagnostics = if (showStreamInfo && com.nuvio.app.isIos) playbackDiagnostics.summary() else null,\n'
         '        bufferAheadMs = if (showStreamInfo && com.nuvio.app.isIos && playbackSnapshot.bufferedPositionMs > 0L)\n'
         '            (playbackSnapshot.bufferedPositionMs - playbackSnapshot.positionMs).coerceAtLeast(0L) else null,\n'
         '        onDismiss = { showStreamInfo = false },\n'),
    ],
    base/'StreamInfoOverlay.kt': [
        ('    onDismiss: () -> Unit,\n    modifier: Modifier = Modifier,\n) {\n    PlayerOverlayScaffold(',
         '    onDismiss: () -> Unit,\n    modifier: Modifier = Modifier,\n    diagnostics: PlaybackDiagnosticSummary? = null,\n    bufferAheadMs: Long? = null,\n) {\n    PlayerOverlayScaffold('),
        ('            if (mediaInfo.videoCodec != null || mediaInfo.videoWidth != null || mediaInfo.videoFrameRate != null) {\n',
         '            if (diagnostics != null) {\n'
         '                StreamInfoSection("Playback diagnostics (current source)") {\n'
         '                    StreamInfoRow {\n'
         '                        StreamInfoItem("Startup", diagnostics.startupMs?.let { "${it} ms" } ?: "Not measured")\n'
         '                        StreamInfoItem("Completed stalls", diagnostics.completedStalls.toString())\n'
         '                        StreamInfoItem("Total stall time", "${diagnostics.totalStallMs} ms")\n'
         '                        StreamInfoItem("Buffer ahead", bufferAheadMs?.let { "${it / 1000L} s" })\n'
         '                        StreamInfoItem("Status", if (diagnostics.buffering) "Buffering" else "No active stall")\n'
         '                    }\n'
         '                }\n'
         '            }\n\n'
         '            if (mediaInfo.videoCodec != null || mediaInfo.videoWidth != null || mediaInfo.videoFrameRate != null) {\n'),
    ],
}
