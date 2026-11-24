from pathlib import Path

base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')

patches = {
    base/'PlayerScreenRuntimeState.kt': [
        ('    var playbackSnapshot by mutableStateOf(PlayerPlaybackSnapshot())',
         '    var dialogueReplay by mutableStateOf<DialogueReplay?>(null)\n    var playbackSnapshot by mutableStateOf(PlayerPlaybackSnapshot())'),
    ],
    base/'PlayerScreenRuntimePlaybackActions.kt': [
        ('    playbackSnapshotKey = playbackKey\n',
         '    playbackSnapshotKey = playbackKey\n    updateDialogueReplay(snapshot)\n'),
    ],
    base/'PlayerScreenRuntimeEffects.kt': [
        ('    LaunchedEffect(activePlaybackKey, activeSourceUrl, activeSourceAudioUrl, activeSourceHeaders, activeSourceResponseHeaders) {\n',
         '    LaunchedEffect(activePlaybackKey, activeSourceUrl, activeSourceAudioUrl, activeSourceHeaders, activeSourceResponseHeaders) {\n        finishDialogueReplay(restore = false)\n'),
    ],
    base/'PlayerScreenRuntimeSourceFallback.kt': [
        ('    if (initialLoadCompleted) return false\n',
         '    // Midstream recovery is conservative: only matching file fingerprints, no party or manual pause.\n'
         '    val midstream = initialLoadCompleted\n'
         '    val previousHash = activeStream?.behaviorHints?.videoHash\n'
         '    val previousSize = activeStream?.behaviorHints?.videoSize?.toLong()\n'
         '    if (midstream && (!shouldPlay || isPartySynced || isScrubbingTimeline || !initialSeekApplied ||\n'
         '        playbackSnapshotKey != activePlaybackKey || playbackSnapshot.isEnded ||\n'
         '        playbackSnapshot.positionMs <= 0L || playbackSnapshot.durationMs <= playbackSnapshot.positionMs ||\n'
         '        !samePlaybackFile(previousHash, previousSize, previousHash, previousSize))) return false\n'),
        ('                    streams = state.groups.flatMap { it.streams },\n',
         '                    streams = state.groups.flatMap { it.streams }.filter { candidate ->\n'
         '                        !midstream || (candidate.playableDirectUrl != null &&\n'
         '                            samePlaybackFile(previousHash, previousSize, candidate.behaviorHints.videoHash,\n'
         '                                candidate.behaviorHints.videoSize?.toLong()))\n'
         '                    },\n'),
        ('                val url = playable?.playableDirectUrl\n',
         '                if (midstream && (!shouldPlay || isPartySynced || isScrubbingTimeline)) return@launch\n'
         '                val url = playable?.playableDirectUrl\n'),
        ('                log.i { "Source failed to start, falling back to ${playable.streamLabel} from ${playable.addonName}" }\n',
         '                if (midstream && !samePlaybackFile(previousHash, previousSize, playable.behaviorHints.videoHash,\n'
         '                        playable.behaviorHints.videoSize?.toLong())) continue\n'
         '                finishDialogueReplay()\n'
         '                log.i { if (midstream) "Matched-file recovery started" else "Startup source fallback started" }\n'),
    ],
    base/'PlayerScreenRuntimeUi.kt': [
        ('        onBuiltInSubtitleTrackSelected = { index ->\n',
         '        onDialogueReplay = if (dialogueReplayAvailable()) ({ replayDialogue() }) else null,\n'
         '        onBuiltInSubtitleTrackSelected = { index ->\n            finishDialogueReplay(restore = false)\n'),
        ('        onAddonSubtitleSelected = { addon ->\n',
         '        onAddonSubtitleSelected = { addon ->\n            finishDialogueReplay(restore = false)\n'),
    ],
    base/'PlayerScreenModalHosts.kt': [
        ('    onSubmitIntroSuccess: () -> Unit,\n', '    onSubmitIntroSuccess: () -> Unit,\n    onDialogueReplay: (() -> Unit)? = null,\n'),
        ('        onDismiss = onSubtitleModalDismissed,\n', '        onDismiss = onSubtitleModalDismissed,\n        onDialogueReplay = onDialogueReplay,\n'),
    ],
    base/'SubtitleModal.kt': [
        ('    modifier: Modifier = Modifier,\n) {\n    val effectiveSelectedAddonSubtitle',
         '    modifier: Modifier = Modifier,\n    onDialogueReplay: (() -> Unit)? = null,\n) {\n    val effectiveSelectedAddonSubtitle'),
        ('                Row(\n                    modifier = Modifier.horizontalScroll(rememberScrollState()),\n',
         '                if (onDialogueReplay != null) {\n'
         '                    androidx.compose.material3.TextButton(onClick = onDialogueReplay) {\n'
         '                        Text("Replay 10s with subtitles", color = Color.White)\n'
         '                    }\n                }\n\n'
         '                Row(\n                    modifier = Modifier.horizontalScroll(rememberScrollState()),\n'),
    ],
}
