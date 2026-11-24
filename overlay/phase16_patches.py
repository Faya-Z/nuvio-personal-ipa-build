from pathlib import Path
base=Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
ios=Path('composeApp/src/iosMain/kotlin/com/nuvio/app/features/player')
bridge=Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
root=Path(__file__).parent/'native'
# Keep the experimental native stream transport behind an explicit build condition.
transport='\n'.join((root/name).read_text() for name in ['PersonalPrefetchCache.swift','PersonalRangeReader.swift','PersonalRangeHTTP.swift','PersonalMPVRangeAdapter.swift'])
patches={
 base/'PlayerEngine.kt': [('    fun setPlaybackSpeed(speed: Float)\n','    fun preparePersonalNextFile(url: String, profileId: Int) {}\n    fun cancelPersonalNextFile() {}\n    fun setPlaybackSpeed(speed: Float)\n')],
 ios/'PlayerBridge.kt': [('    fun play()\n','    fun preparePersonalNextFile(url: String, profileId: Int)\n    fun cancelPersonalNextFile()\n    fun setPersonalPrefetchProfile(profileId: Int)\n    fun play()\n')],
 ios/'PlayerEngine.ios.kt': [
 ('            override fun getAudioTracks(): List<AudioTrack> {\n','''            override fun preparePersonalNextFile(url: String, profileId: Int) = bridge.preparePersonalNextFile(url, profileId)
            override fun cancelPersonalNextFile() = bridge.cancelPersonalNextFile()
            override fun getAudioTracks(): List<AudioTrack> {
'''),
 ('        bridge.loadFileWithAudioAtPosition(\n','        bridge.setPersonalPrefetchProfile(com.nuvio.app.features.profiles.ProfileRepository.activeProfileId)\n        bridge.loadFileWithAudioAtPosition(\n')],
 base/'PlayerNextEpisodeAutoPlay.kt': [
 ('    onNextEpisodeCardVisibleChanged: (Boolean) -> Unit,\n): Job? {','''    onNextEpisodeCardVisibleChanged: (Boolean) -> Unit,
    onPreparePersonalNextFile: (StreamItem) -> Unit = {},
    onCancelPersonalNextFile: () -> Unit = {},
): Job? {'''),
 ('''            for (i in 3 downTo 1) {
                onCountdownChanged(i)
                delay(1000)
            }
            onEpisodeStreamSelected(selected, nextVideo, resolveRun.tried)
''','''            var handedOff = false
            try {
                if (settings.preloadNextEpisodeSources) onPreparePersonalNextFile(selected)
                for (i in 3 downTo 1) {
                    onCountdownChanged(i)
                    delay(1000)
                }
                onEpisodeStreamSelected(selected, nextVideo, resolveRun.tried)
                handedOff = true
            } finally {
                if (!handedOff) onCancelPersonalNextFile()
            }
''')],
 base/'PlayerScreenRuntimeSourceActions.kt': [
 ('        currentStreamBingeGroup = currentStreamBingeGroup,\n        onDownloadedEpisodeSelected =','''        currentStreamBingeGroup = currentStreamBingeGroup,
        onPreparePersonalNextFile = { stream ->
            if (isCurrentRequest() && com.nuvio.app.isIos && !isPartySynced && !partyAppInBackground &&
                stream.serverTarget == null && stream.p2pInfoHash == null && stream.clientResolve == null &&
                stream.behaviorHints.proxyHeaders == null &&
                (playbackSnapshot.isEnded || (!playbackSnapshot.isLoading &&
                    playbackSnapshot.bufferedPositionMs - playbackSnapshot.positionMs >= 15_000L))) {
                stream.playableDirectUrl?.let { playerController?.preparePersonalNextFile(it, profileId) }
            }
        },
        onCancelPersonalNextFile = { playerController?.cancelPersonalNextFile() },
        onDownloadedEpisodeSelected =''')],
 bridge: [
 ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)', '#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT\n'+transport+'\n#endif\n\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
 ('    private func parseSubtitles(_ json: String?) -> [PluginSubtitle] {\n','''    func preparePersonalNextFile(url: String, profileId: Int32) {
#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
        guard !ProcessInfo.processInfo.isLowPowerModeEnabled, UIApplication.shared.applicationState == .active else { return }
        PersonalPrefetchTransport.shared.prepare(url: url, profile: Int(profileId))
#endif
    }
    func cancelPersonalNextFile() {
#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
        PersonalPrefetchTransport.shared.clear()
#endif
    }
    func setPersonalPrefetchProfile(profileId: Int32) {
#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
        ensurePlayerViewController().personalPrefetchProfile = Int(profileId)
#endif
    }

    private func parseSubtitles(_ json: String?) -> [PluginSubtitle] {
'''),
 ('    private var personalBarPolicy = PersonalEncodedBarPolicy()\n','''#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
    var personalPrefetchProfile: Int?
    private let personalRangeAdapter = PersonalMPVRangeAdapter()
    private var personalRangeOriginal: String?
    private var personalRangeURI: String?
#endif
    private var personalBarPolicy = PersonalEncodedBarPolicy()
'''),
 ('        let args = PersonalNativeResumePolicy.loadArguments(url: request.urlString, positionMs: request.initialPositionMs)\n','''        var selectedURL = request.urlString
#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
        personalRangeOriginal = nil
        personalRangeURI = nil
        personalRangeAdapter.clear()
        if let handle = mpv, let profile = personalPrefetchProfile, request.initialPositionMs == 0,
           sanitizedHeaders.isEmpty, request.audioUrl == nil, request.subtitles.isEmpty,
           !ProcessInfo.processInfo.isLowPowerModeEnabled, UIApplication.shared.applicationState == .active,
           let slot = PersonalPrefetchTransport.shared.take(url: request.urlString, profile: profile),
           let uri = personalRangeAdapter.url(for: slot, handle: handle) {
            personalRangeOriginal = request.urlString
            personalRangeURI = uri
            selectedURL = uri
        }
#endif
        let args = PersonalNativeResumePolicy.loadArguments(url: selectedURL, positionMs: request.initialPositionMs)
'''),
 ('        } else {\n            command("loadfile", args: args)\n        }\n        if let audioUrl = request.audioUrl,','''        } else {
            if commandResult("loadfile", args: args, checkForErrors: false) < 0 {
#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
                personalRangeAdapter.clear()
                personalRangeOriginal = nil
                personalRangeURI = nil
#endif
                command("loadfile", args: [request.urlString, "replace"])
            }
        }
        if let audioUrl = request.audioUrl,'''),
 # Retry the ordinary URL, not the one-use custom protocol token. Asynchronous read errors
 # use the existing playback error/recovery path; retry can restore the original source.
 ('        if let path = getString("path") {\n            clearPlaybackError()','''        if var path = getString("path") {
#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
            if path == personalRangeURI, let original = personalRangeOriginal {
                path = original
                personalRangeAdapter.clear()
                personalRangeOriginal = nil
                personalRangeURI = nil
            }
#endif
            clearPlaybackError()'''),
 ('        super.didReceiveMemoryWarning()\n','''        super.didReceiveMemoryWarning()
#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
        PersonalPrefetchTransport.shared.clear()
#endif
'''),
 ]}
