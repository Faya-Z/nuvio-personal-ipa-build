from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
patches = {
    base/'PlayerScreenRuntimeState.kt': [
        ('    val playbackDiagnostics = PlaybackDiagnostics()\n', '    val playbackDiagnostics = PlaybackDiagnostics()\n    val recoveryRuntime = PlayerRecoveryRuntime()\n'),
        ('    var sourceFallbackJob: Job? = null\n', '    var sourceFallbackJob: Job? = null\n    var sourceFallbackIsProactive = false\n'),
        ('    val targetEngine: AndroidPlaybackEngine,\n', '    val targetEngine: AndroidPlaybackEngine?,\n'),
    ],
    base/'PlayerScreenRuntimePlaybackActions.kt': [
        ('    updateDialogueReplay(snapshot)\n', '    updateDialogueReplay(snapshot)\n    observeRecoverySnapshot(snapshot)\n'),
        ('pendingSeekTarget == null,\n', '(pendingSeekTarget?.second?.elapsedNow()?.inWholeMilliseconds ?: Long.MAX_VALUE) >= 1_500L,\n'),
    ],
    base/'PlayerScreenRuntimeSourceFallback.kt': [
        ('internal fun PlayerScreenRuntime.tryFallbackToNextSourceAfterError(message: String?): Boolean {\n    if (sourceFallbackJob?.isActive == true) return true\n',
         'internal fun PlayerScreenRuntime.tryFallbackToNextSourceAfterError(message: String?, proactivePositionMs: Long? = null): Boolean {\n'
         '    if (sourceFallbackJob?.isActive == true) return proactivePositionMs == null && !sourceFallbackIsProactive\n'
         '    if (proactivePositionMs != null && !canProactivelyRecover()) return false\n'),
        ('    errorMessage = null\n\n    sourceFallbackJob = scope.launch {\n',
         '    errorMessage = null\n    sourceFallbackIsProactive = proactivePositionMs != null\n'
         '    recoveryRuntime.observeKey(activePlaybackKey)\n'
         '    if (isIos && proactivePositionMs == null) recoveryRuntime.recordFailure(activeProviderAddonId)\n'
         '    fun stillApplicable(): Boolean = activePlaybackKey == failedPlaybackKey && activeSourceUrl == autoSelectedSourceUrl &&\n'
         '        (proactivePositionMs == null || (canProactivelyRecover() && playbackSnapshot.isLoading &&\n'
         '            playbackSnapshot.positionMs == proactivePositionMs))\n\n'
         '    val localTriedKeys = sourceFallbackTriedKeys.toMutableSet()\n'
         '    var localAttempts = sourceFallbackAttempts\n'
         '    sourceFallbackJob = scope.launch {\n'),
        ('if (sourcePlaybackKey != failedPlaybackKey) return@launch', 'if (!stillApplicable()) return@launch'), # multiple occurrences handled separately below
        ('            while (sourceFallbackAttempts < playerSettingsUiState.streamAutoPlayFallbackMaxSources) {\n',
         '            while (localAttempts < playerSettingsUiState.streamAutoPlayFallbackMaxSources) {\n'),
        ('                    triedKeys = sourceFallbackTriedKeys,\n',
         '                    triedKeys = localTriedKeys,\n'),
        ('                next.playerSourceIdentityKey()?.let(sourceFallbackTriedKeys::add)\n                sourceFallbackAttempts++\n',
         '                next.playerSourceIdentityKey()?.let(localTriedKeys::add)\n                localAttempts++\n'
         '                if (proactivePositionMs == null) {\n'
         '                    sourceFallbackTriedKeys += localTriedKeys\n                    sourceFallbackAttempts = localAttempts\n                }\n'),
        ('                    failedInfoHash = failedInfoHash,\n',
         '                    failedInfoHash = failedInfoHash,\n'
         '                    reliability = recoveryRuntime.reliability.takeIf { isIos && midstream },\n'),
        ('                finishDialogueReplay()\n',
         '                finishDialogueReplay()\n'
         '                if (midstream && isIos) {\n'
         '                    if (proactivePositionMs != null) {\n'
         '                        recoveryRuntime.recordFailure(activeProviderAddonId)\n'
         '                        sourceFallbackTriedKeys += localTriedKeys\n                        sourceFallbackAttempts = localAttempts\n                    }\n'
         '                    rememberCurrentTrackPreferenceForEngineSwitch(null, url)\n'
         '                }\n'),
        ('                playReplacementSource(playable, url, videoId)\n',
         '                PlayerStreamsRepository.stopSourcesLoading()\n                playReplacementSource(playable, url, videoId)\n'),
        ('        } finally {\n            PlayerStreamsRepository.stopSourcesLoading()\n',
         '        } catch (cancelled: kotlinx.coroutines.CancellationException) {\n            throw cancelled\n'
         '        } catch (error: Exception) {\n            if (proactivePositionMs == null) throw error\n'
         '            log.d { "Proactive recovery lookup failed" }\n'
         '        } finally {\n            if (activePlaybackKey == failedPlaybackKey) PlayerStreamsRepository.stopSourcesLoading()\n'),
        ('        // The last source that failed may have been saved for reuse.\n',
         '        // A watchdog probe is not an engine error. Leave normal playback untouched if no match exists.\n'
         '        if (proactivePositionMs != null) return@launch\n'
         '        // The last source that failed may have been saved for reuse.\n'),
        ('    activeResolverProviderId: String? = DebridSettingsRepository.snapshot().activeResolverProviderId,\n',
         '    activeResolverProviderId: String? = DebridSettingsRepository.snapshot().activeResolverProviderId,\n'
         '    reliability: SourceReliability? = null,\n'),
        ('    return StreamAutoPlaySelector.evaluateAutoPlayStream(\n', '    val ready = StreamAutoPlaySelector.evaluateAutoPlayStream(\n'),
        ('    ).readyStreams.firstOrNull()\n', '    ).readyStreams\n    return reliability?.best(ready) { it.addonId } ?: ready.firstOrNull()\n'),
    ],
    base/'PlayerScreenRuntimeEngineSwitchTrackPreference.kt': [
        ('    targetEngine: AndroidPlaybackEngine,\n', '    targetEngine: AndroidPlaybackEngine?,\n    targetSourceIdentity: String = activePlaybackIdentity,\n'),
        ('        sourceIdentity = activePlaybackIdentity,\n', '        sourceIdentity = targetSourceIdentity,\n'),
        ('    if (engine != null && engine != pending.targetEngine) {\n', '    if (engine != null && pending.targetEngine != null && engine != pending.targetEngine) {\n'),
        ('    val controller = playerController ?: return\n    if (controller === pending.capturedController)', '    val controller = playerController ?: return\n    if (playerControllerSourceUrl != activeSourceUrl) return\n    if (controller === pending.capturedController)'),
    ],
    base/'PlayerScreenRuntimeEffects.kt': [
        ('        if (playerController?.playbackEngine == pending.targetEngine) {\n', '        if (pending.targetEngine == null || playerController?.playbackEngine == pending.targetEngine) {\n'),
    ],
}
# The four guards have distinct indentation/context; no broad substitution in application.
p = patches[base/'PlayerScreenRuntimeSourceFallback.kt']
p.pop(2)
p[2:2] = [
    ('            if (sourcePlaybackKey != failedPlaybackKey) return@launch\n            var polls', '            if (!stillApplicable()) return@launch\n            var polls'),
    ('                if (sourcePlaybackKey != failedPlaybackKey) return@launch\n                val state', '                if (!stillApplicable()) return@launch\n                val state'),
    ('                if (sourcePlaybackKey != failedPlaybackKey) return@launch\n                if (midstream', '                if (!stillApplicable()) return@launch\n                if (midstream'),
    ('        if (sourcePlaybackKey != failedPlaybackKey) return@launch\n        // The last', '        if (!stillApplicable()) return@launch\n        // The last'),
]

# Bind recovery to the engine as well as the media/source identity.
p.append(('    val failedPlaybackKey = sourcePlaybackKey\n', '    val failedPlaybackKey = activePlaybackKey\n'))
