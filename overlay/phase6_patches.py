from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
streams = base.parent/'streams'
patches = {
    streams/'StreamsRepository.kt': [
        ('            var autoSelectTriggered = false\n            var timeoutElapsed = false\n',
         '            val personalSelectionProfile = ProfileRepository.activeProfileId\n            var autoSelectTriggered = false\n            var timeoutElapsed = false\n'),
        ('                    activeResolverProviderId = debridSettings.activeResolverProviderId,\n                )\n\n            fun settleAutoPlay',
         '                    activeResolverProviderId = debridSettings.activeResolverProviderId,\n                ).let { evaluation ->\n'
         '                    com.nuvio.app.features.player.rankPersonalInitialSources(evaluation, personalSelectionProfile,\n'
         '                        playerSettings.streamAutoPlayFallbackActive && autoPlayMode == StreamAutoPlayMode.REGEX_MATCH &&\n'
         '                            persistedBingeGroup == null && !bingeGroupOnly &&\n'
         '                            personalSelectionProfile == ProfileRepository.activeProfileId)\n'
         '                }\n\n            fun settleAutoPlay'),
    ],
    base/'PlayerScreenRuntimeState.kt': [
        ('    val recoveryRuntime = PlayerRecoveryRuntime(profileId)\n',
         '    val recoveryRuntime = PlayerRecoveryRuntime(profileId)\n'
         '    val personalEnglishCorrection = PersonalEnglishCorrection()\n'
         '    val personalSessionHistory = PersonalSessionHistory()\n'),
    ],
    base/'PlayerScreenRuntimePlaybackActions.kt': [
        ('    observeRecoverySnapshot(snapshot)\n', '    observeRecoverySnapshot(snapshot)\n    observePersonalSessionHistory(snapshot)\n'),
    ],
    base/'PlayerScreenRuntimeTrackActions.kt': [
        ('    applyPendingEngineSwitchTrackPreference()\n}', '    applyPendingEngineSwitchTrackPreference()\n    verifyPreferredEnglishAudio()\n}'),
    ],
    base/'PlayerScreenRuntimeUi.kt': [
        ('        diagnostics = if (showStreamInfo && com.nuvio.app.isIos) playbackDiagnostics.summary() else null,\n',
         '        diagnostics = if (showStreamInfo && com.nuvio.app.isIos) playbackDiagnostics.summary() else null,\n'
         '        audioMetadataStatus = if (showStreamInfo && com.nuvio.app.isIos) selectedAudioMetadataStatus() else null,\n'
         '        watchedMediaMs = if (showStreamInfo && com.nuvio.app.isIos) personalSessionHistory.history.watchedMediaMs else null,\n'),
    ],
    base/'StreamInfoOverlay.kt': [
        ('    bufferAheadMs: Long? = null,\n', '    bufferAheadMs: Long? = null,\n    audioMetadataStatus: String? = null,\n    watchedMediaMs: Long? = null,\n'),
        ('                        StreamInfoItem("Buffer ahead", bufferAheadMs?.let { "${it / 1000L} s" })\n',
         '                        StreamInfoItem("Buffer ahead", bufferAheadMs?.let { "${it / 1000L} s" })\n'
         '                        StreamInfoItem("Audio language", audioMetadataStatus)\n'
         '                        StreamInfoItem("Media played this session", watchedMediaMs?.let { "${it / 60000L}m ${(it / 1000L) % 60L}s" })\n'),
    ],
}
