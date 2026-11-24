from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
progress = base.parent / 'watchprogress/WatchProgressRepository.kt'
patches = {
    base/'PlayerScreenRuntimeState.kt': [
        ('    var personalHandoverPositionMs by mutableStateOf<Long?>(null)\n',
         '    var personalHandoverPositionMs by mutableStateOf<Long?>(null)\n'
         '    var personalHandoverConfirmation by mutableStateOf(PersonalHandoverConfirmation.UNCONFIRMED)\n'
         '    var personalHandoverVerificationJob: Job? = null\n'),
    ],
    base/'StreamInfoOverlay.kt': [
        ('Use the same synced profile on the other device. Remote delivery is not confirmed here.',
         'Use the same synced profile on the other device. Cloud confirmation does not mean the second device has refreshed yet.'),
    ],
    progress: [
        ('    fun applyExternalProgress(entries: List<WatchProgressEntry>) {\n',
         '''    /** Read-only acknowledgement of the exact Nuvio cloud progress checkpoint.
     * Never invokes provider writes or merges the readback into local progress. */
    internal suspend fun confirmPersonalHandover(
        session: WatchProgressPlaybackSession,
        snapshot: PlayerPlaybackSnapshot,
        requestedAtMs: Long,
    ): com.nuvio.app.features.player.PersonalHandoverConfirmation {
        val profile = session.profileId
        val generation = activeOperationGeneration(profile)
            ?: return com.nuvio.app.features.player.PersonalHandoverConfirmation.UNAVAILABLE
        fun stillCurrent(): Boolean = isActiveOperation(profile, generation) &&
            activeSource == WatchProgressSource.NUVIO_SYNC
        if (!stillCurrent() || ServerItemRef.isServerId(session.parentMetaId) ||
            isWatchProgressComplete(snapshot.positionMs, snapshot.durationMs, snapshot.isEnded) ||
            !shouldStoreWatchProgress(positionMs = snapshot.positionMs, durationMs = snapshot.durationMs)) {
            return com.nuvio.app.features.player.PersonalHandoverConfirmation.UNAVAILABLE
        }
        val expected = com.nuvio.app.features.player.PersonalHandoverCheckpoint(
            session.parentMetaId, session.contentType, session.videoId, session.seasonNumber,
            session.episodeNumber, snapshot.positionMs, snapshot.durationMs, requestedAtMs,
        )
        return kotlinx.coroutines.withTimeoutOrNull(8_000L) {
            repeat(3) { attempt ->
                kotlinx.coroutines.delay(if (attempt == 0) 500L else 1_500L)
                if (!stillCurrent()) return@withTimeoutOrNull com.nuvio.app.features.player.PersonalHandoverConfirmation.UNAVAILABLE
                val records = try {
                    syncAdapter.pull(profileId = profile, sinceLastWatched = requestedAtMs - 1L, limit = 64)
                } catch (cancel: kotlinx.coroutines.CancellationException) {
                    throw cancel
                } catch (_: Exception) {
                    emptyList()
                }
                if (!stillCurrent()) return@withTimeoutOrNull com.nuvio.app.features.player.PersonalHandoverConfirmation.UNAVAILABLE
                if (records.any { record -> expected.matches(record.contentId, record.contentType,
                    record.videoId, record.season, record.episode, record.position, record.duration, record.lastWatched) }) {
                    return@withTimeoutOrNull com.nuvio.app.features.player.PersonalHandoverConfirmation.CONFIRMED
                }
            }
            com.nuvio.app.features.player.PersonalHandoverConfirmation.UNCONFIRMED
        } ?: com.nuvio.app.features.player.PersonalHandoverConfirmation.UNCONFIRMED
    }

    fun applyExternalProgress(entries: List<WatchProgressEntry>) {
'''),
    ],
}

bridge = Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
policy = (Path(__file__).parent / 'native/PersonalLowPowerBufferPolicy.swift').read_text()
patches[bridge] = [
    ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)', policy + '\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
    ('    private var personalCacheRemote = false\n',
     '    private var personalCacheRemote = false\n'
     '    private var personalLowPowerPolicy = PersonalLowPowerBufferPolicy()\n'
     '    private var personalLowPowerApplied: Double = 0\n'
     '    private var personalLowPowerSupported = false\n'),
    ('    private func resetPersonalCachePolicy(url: String) {\n',
     '    private func resetPersonalCachePolicy(url: String) {\n'
     '        resetPersonalLowPowerBuffer()\n'),
    ('    private func updatePersonalCachePolicy(position: Double, duration: Double, paused: Bool,\n',
     '''    private func resetPersonalLowPowerBuffer() {
        personalLowPowerPolicy = PersonalLowPowerBufferPolicy()
        let option = "options/demuxer-hysteresis-secs"
        if personalLowPowerApplied != 0 {
            if mpv_set_property_string(mpv, option, "0") < 0 {
                personalLowPowerSupported = false
                return
            }
            personalLowPowerApplied = 0
        }
        // Preserve nonzero original settings. Unavailable options disable this policy.
        personalLowPowerSupported = getString(option).flatMap { Double($0) } == 0
    }

    private func updatePersonalLowPowerBuffer(eligible: Bool, ahead: Double) {
        guard Thread.isMainThread, let mpv, personalLowPowerSupported else { return }
        let target = personalLowPowerPolicy.observe(now: ProcessInfo.processInfo.systemUptime,
            eligible: eligible && personalCacheRemote && ProcessInfo.processInfo.isLowPowerModeEnabled,
            ahead: ahead)
        guard target != personalLowPowerApplied else { return }
        let option = "options/demuxer-hysteresis-secs"
        if mpv_set_property_string(mpv, option, String(target)) >= 0 {
            personalLowPowerApplied = target
        } else {
            personalLowPowerSupported = false
        }
    }

    private func updatePersonalCachePolicy(position: Double, duration: Double, paused: Bool,
'''),
    ('        currentSpeed = PersonalNativePlaybackPolicy.playbackRate(speed)\n',
     '        currentSpeed = PersonalNativePlaybackPolicy.playbackRate(speed)\n'
     '        updatePersonalLowPowerBuffer(eligible: isFileLoaded && !paused && !seeking && !eofReached &&\n'
     '            !idle && !bufferingCache && durationMs > 0 && durationMs - positionMs > 45_000 &&\n'
     '            UIApplication.shared.applicationState == .active,\n'
     '            ahead: Double(max(0, bufferedMs - positionMs)) / 1000.0)\n'),
]

patches[base/'PlayerScreenRuntimeEffects.kt'] = [
    ('        playerControllerSourceUrl = null\n        playbackSnapshot = PlayerPlaybackSnapshot()\n        playbackSnapshotKey = null\n        cancelNextEpisodeAutoPlay()\n',
     '        playerControllerSourceUrl = null\n'
     '        personalHandoverVerificationJob?.cancel()\n'
     '        personalHandoverVerificationJob = null\n'
     '        personalHandoverKey = null\n'
     '        personalHandoverPositionMs = null\n'
     '        playbackSnapshot = PlayerPlaybackSnapshot()\n'
     '        playbackSnapshotKey = null\n'
     '        cancelNextEpisodeAutoPlay()\n'),
]
