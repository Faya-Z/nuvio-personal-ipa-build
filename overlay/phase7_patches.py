from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
patches = {
    base/'PlayerScreenRuntimeState.kt': [
        ('    val personalSessionHistory = PersonalSessionHistory()\n',
         '    val personalSessionHistory = PersonalSessionHistory(profileId)\n    val personalSleepRuntime = PersonalSleepRuntime()\n'),
    ],
    base/'PlayerScreenRuntimePlaybackActions.kt': [
        ('    observePersonalSessionHistory(snapshot)\n', '    observePersonalSessionHistory(snapshot)\n    updatePersonalSleepTimer()\n'),
    ],
    base/'PlayerScreenRuntimeEffects.kt': [
        ('        onDispose { ServerPlayback.stop(effectSourceUrl) }', '        onDispose {\n            if (com.nuvio.app.isIos) personalSessionHistory.flush()\n            ServerPlayback.stop(effectSourceUrl)\n        }'),
    ],
    base/'PlayerScreenRuntimeUi.kt': [
        ('        watchedMediaMs = if (showStreamInfo && com.nuvio.app.isIos) personalSessionHistory.history.watchedMediaMs else null,\n',
         '        watchedMediaMs = if (showStreamInfo && com.nuvio.app.isIos) personalSessionHistory.history.watchedMediaMs else null,\n'
         '        lifetimeHistory = if (showStreamInfo && com.nuvio.app.isIos) personalSessionHistory.totalForCurrentItem() else null,\n'
         '        sleepRemainingMinutes = if (showStreamInfo && com.nuvio.app.isIos) personalSleepRuntime.remainingMinutes() else null,\n'
         '        onSleepTimer = if (com.nuvio.app.isIos && !isPartySynced) { minutes -> personalSleepRuntime.set(minutes) } else null,\n'),
    ],
    base/'StreamInfoOverlay.kt': [
        ('    watchedMediaMs: Long? = null,\n', '    watchedMediaMs: Long? = null,\n    lifetimeHistory: HistoryEntry? = null,\n    sleepRemainingMinutes: Long? = null,\n    onSleepTimer: ((Int) -> Unit)? = null,\n'),
        ('                        StreamInfoItem("Media played this session", watchedMediaMs?.let { "${it / 60000L}m ${(it / 1000L) % 60L}s" })\n',
         '                        StreamInfoItem("Media played this session", watchedMediaMs?.let { "${it / 60000L}m ${(it / 1000L) % 60L}s" })\n'
         '                        StreamInfoItem("Total media played for this item", lifetimeHistory?.let { "${it.playedMs / 60000L} min" })\n'
         '                        StreamInfoItem("Recorded viewing sessions", lifetimeHistory?.sessions?.toString())\n'),
        ('            if (mediaInfo.videoCodec != null || mediaInfo.videoWidth != null || mediaInfo.videoFrameRate != null) {\n',
         '            if (onSleepTimer != null) {\n'
         '                StreamInfoSection("Sleep timer") {\n'
         '                    StreamInfoSecondaryText(sleepRemainingMinutes?.let { "Pauses in approximately $it min" } ?: "Off")\n'
         '                    StreamInfoRow {\n'
         '                        listOf(15, 30, 60, 0).forEach { minutes ->\n'
         '                            androidx.compose.material3.TextButton(onClick = { onSleepTimer(minutes) }) {\n'
         '                                Text(if (minutes == 0) "Off" else "$minutes min", color = Color.White)\n'
         '                            }\n'
         '                        }\n'
         '                    }\n'
         '                }\n'
         '            }\n\n'
         '            if (mediaInfo.videoCodec != null || mediaInfo.videoWidth != null || mediaInfo.videoFrameRate != null) {\n'),
    ],
}
