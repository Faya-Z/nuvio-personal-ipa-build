from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
ios = Path('composeApp/src/iosMain/kotlin/com/nuvio/app/features/player')
bridge = Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
policy = (Path(__file__).parent / 'native/PersonalNativeConveniencePolicy.swift').read_text()
patches = {
    base/'PlayerEngine.kt': [
        ('    fun setPlaybackSpeed(speed: Float)\n', '    fun setPlaybackSpeed(speed: Float)\n    fun setPersonalSmartFill(enabled: Boolean) {}\n'),
    ],
    ios/'PlayerBridge.kt': [
        ('    fun play()\n', '    fun setPersonalSmartFill(enabled: Boolean)\n    fun play()\n'),
    ],
    ios/'PlayerEngine.ios.kt': [
        ('            override fun getAudioTracks(): List<AudioTrack> {\n', '            override fun setPersonalSmartFill(enabled: Boolean) {\n                bridge.setPersonalSmartFill(enabled)\n            }\n\n            override fun getAudioTracks(): List<AudioTrack> {\n'),
    ],
    base/'PlayerScreenRuntimeState.kt': [
        ('    var resizeMode by mutableStateOf(playerSettingsUiState.resizeMode)\n',
         '    var resizeMode by mutableStateOf(playerSettingsUiState.resizeMode)\n'
         '    var personalSmartFillEnabled by mutableStateOf(false)\n'
         '    var personalHandoverKey: PlaybackKey? = null\n'
         '    var personalHandoverPositionMs by mutableStateOf<Long?>(null)\n'),
    ],
    base/'PlayerScreenRuntimeGestureActions.kt': [
        ('internal fun PlayerScreenRuntime.cycleResizeMode() {\n', 'internal fun PlayerScreenRuntime.cycleResizeMode() {\n    personalSmartFillEnabled = false\n'),
    ],
    base/'PlayerScreenRuntimeUi.kt': [
        ('    BindAutoSyncRuntimeEffects() // AutoSync hook\n',
         '''    BindAutoSyncRuntimeEffects() // AutoSync hook
    LaunchedEffect(playerController, personalSmartFillEnabled, resizeMode, isInPip, partyPanelInset, isPartySynced) {
        if (isIos) playerController?.setPersonalSmartFill(personalSmartFillEnabled &&
            resizeMode == PlayerResizeMode.Fit && !isInPip && partyPanelInset <= 0.dp && !isPartySynced)
    }
'''),
        ('        onSleepTimer = if (com.nuvio.app.isIos && !isPartySynced) { minutes -> personalSleepRuntime.set(minutes) } else null,\n',
         '''        onSleepTimer = if (com.nuvio.app.isIos && !isPartySynced) { minutes -> personalSleepRuntime.set(minutes) } else null,
        smartFillEnabled = personalSmartFillEnabled && resizeMode == PlayerResizeMode.Fit,
        onSmartFillToggle = if (isIos && resizeMode == PlayerResizeMode.Fit && !isPartySynced) {
            { personalSmartFillEnabled = !personalSmartFillEnabled }
        } else null,
        onHandover = if (personalHandoverTarget() != null) { { savePersonalHandover() } } else null,
        handoverMessage = personalHandoverMessage(),
'''),
    ],
    base/'StreamInfoOverlay.kt': [
        ('    onSleepTimer: ((Int) -> Unit)? = null,\n',
         '''    onSleepTimer: ((Int) -> Unit)? = null,
    smartFillEnabled: Boolean = false,
    onSmartFillToggle: (() -> Unit)? = null,
    onHandover: (() -> Unit)? = null,
    handoverMessage: String? = null,
'''),
        ('            if (onSleepTimer != null) {\n',
         '''            if (onSmartFillToggle != null) {
                StreamInfoSection("Smart fill") {
                    Text("Automatically crops up to 10% for near-matching screen proportions. Does not detect encoded black bars.", color = Color.White, style = MaterialTheme.typography.bodySmall)
                    androidx.compose.material3.TextButton(onClick = onSmartFillToggle) {
                        Text(if (smartFillEnabled) "On — turn off" else "Off — turn on", color = Color.White)
                    }
                }
            }
            if (onHandover != null || handoverMessage != null) {
                StreamInfoSection("Continue on another device") {
                    handoverMessage?.let { Text(it, color = Color.White, style = MaterialTheme.typography.bodySmall) }
                    if (onHandover != null) {
                        androidx.compose.material3.TextButton(onClick = onHandover) {
                            Text("Save progress and pause", color = Color.White)
                        }
                    }
                    Text("Use the same synced profile on the other device. Remote delivery is not confirmed here.", color = Color.White, style = MaterialTheme.typography.bodySmall)
                }
            }
            if (onSleepTimer != null) {
'''),
    ],
    base/'PlayerRuntimeAutoSync.kt': [
        ('    controller.setAutoSyncSubtitleCandidates(currentAutoSyncCandidates())\n    controller.setAutoSyncAppliedListener { subtitleUrl, delayMs ->\n',
         '''    val expectedKey = activePlaybackKey
    val expectedSource = activeSourceUrl
    controller.setAutoSyncSubtitleCandidates(currentAutoSyncCandidates())
    controller.setAutoSyncAppliedListener { subtitleUrl, delayMs ->
        if (playerController !== controller || activePlaybackKey != expectedKey ||
            activeSourceUrl != expectedSource || playerControllerSourceUrl != expectedSource ||
            (isUserExplicitSubtitleSelection && selectedSubtitleIndex < 0 && !useCustomSubtitles)) {
            return@setAutoSyncAppliedListener
        }
'''),
        ('    DisposableEffect(activeController) {\n', '    DisposableEffect(activeController, activePlaybackKey, activeSourceUrl) {\n'),
        ('    LaunchedEffect(playerController, externalSubtitles) {\n        val controller = playerController ?: return@LaunchedEffect\n        SubtitleRepository.addonSubtitles.collect { repositorySubtitles ->\n',
         '''    LaunchedEffect(playerController, externalSubtitles, activePlaybackKey, activeSourceUrl) {
        val controller = playerController ?: return@LaunchedEffect
        val expectedKey = activePlaybackKey
        val expectedSource = activeSourceUrl
        SubtitleRepository.addonSubtitles.collect { repositorySubtitles ->
            if (playerController !== controller || activePlaybackKey != expectedKey ||
                activeSourceUrl != expectedSource || playerControllerSourceUrl != expectedSource) return@collect
'''),
    ],
    bridge: [
        ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)', policy + '\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
        ('    func setResizeMode(mode: Int32) { playerVC?.setResize(Int(mode)) }\n',
         '    func setResizeMode(mode: Int32) { playerVC?.setResize(Int(mode)) }\n'
         '    func setPersonalSmartFill(enabled: Bool) { ensurePlayerViewController().setPersonalSmartFill(enabled) }\n'),
        ('    private var personalLoadGeneration: UInt64 = 0\n',
         '''    private var personalLoadGeneration: UInt64 = 0
    private var personalSmartFill = false
    private var personalResizeMode = 0
    private var personalCropApplied = false
    private var personalCropCheckedAt: Double = -1
    private var personalRetrySeek: PersonalNativeRetrySeek?
'''),
        ('        personalLoadGeneration &+= 1\n        personalCacheRemote = false\n        pendingLoadRequest = request\n',
         '''        personalLoadGeneration &+= 1
        personalRetrySeek = nil
        personalCropCheckedAt = -1
        if personalResizeMode == 0 && personalCropApplied {
            setStringProperty("panscan", "0.0")
            personalCropApplied = false
        }
        personalCacheRemote = false
        pendingLoadRequest = request
'''),
        ('    func setResize(_ mode: Int) {\n        guard mpv != nil else { return }\n',
         '''    func setPersonalSmartFill(_ enabled: Bool) {
        guard Thread.isMainThread else {
            DispatchQueue.main.async { [weak self] in self?.setPersonalSmartFill(enabled) }
            return
        }
        personalSmartFill = enabled
        personalCropCheckedAt = -1
        updatePersonalSmartFill()
    }

    private func updatePersonalSmartFill() {
        guard Thread.isMainThread, mpv != nil, personalResizeMode == 0 else { return }
        if !personalSmartFill || !isFileLoaded || !isViewLoaded || view.window == nil {
            if personalCropApplied {
                setStringProperty("panscan", "0.0")
                personalCropApplied = false
            }
            return
        }
        let now = ProcessInfo.processInfo.systemUptime
        guard personalCropCheckedAt < 0 || now - personalCropCheckedAt >= 1 else { return }
        personalCropCheckedAt = now
        let size = externallyManagedViewSize ?? view.bounds.size
        let crop = PersonalNativeConveniencePolicy.smallCrop(videoWidth: getDouble("dwidth"),
            videoHeight: getDouble("dheight"), viewWidth: Double(size.width), viewHeight: Double(size.height))
        guard crop != personalCropApplied else { return }
        setStringProperty("panscan", crop ? "1.0" : "0.0")
        personalCropApplied = crop
    }

    func setResize(_ mode: Int) {
        personalResizeMode = mode
        personalCropApplied = false
        personalCropCheckedAt = -1
        guard mpv != nil else { return }
'''),
        ('    func seekToMs(_ ms: Int64) {\n        guard mpv != nil else { return }\n',
         '    func seekToMs(_ ms: Int64) {\n        personalRetrySeek = nil\n        guard mpv != nil else { return }\n'),
        ('    func seekByMs(_ ms: Int64, exact: Bool = false) {\n        guard mpv != nil else { return }\n',
         '    func seekByMs(_ ms: Int64, exact: Bool = false) {\n        personalRetrySeek = nil\n        guard mpv != nil else { return }\n'),
        ('''            let pos = getDouble("time-pos")
            personalLoadGeneration &+= 1
            let retryGeneration = personalLoadGeneration
            resetPersonalCachePolicy(url: path)
            isFileLoaded = false
            command("loadfile", args: [path, "replace"])
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
                guard let self, self.personalLoadGeneration == retryGeneration, self.mpv != nil else { return }
                self.command("seek", args: [String(format: "%.3f", pos), "absolute"])
            }
''', '''            let reported = PersonalNativePlaybackPolicy.milliseconds(getDouble("time-pos"))
            let pos = reported > 0 ? reported : positionMs
            personalLoadGeneration &+= 1
            resetPersonalCachePolicy(url: path)
            isFileLoaded = false
            personalRetrySeek = pos > 0 ? PersonalNativeRetrySeek(generation: personalLoadGeneration,
                path: path, positionMs: pos, started: ProcessInfo.processInfo.systemUptime) : nil
            let args = PersonalNativeResumePolicy.loadArguments(url: path, positionMs: pos)
            if commandResult("loadfile", args: args, checkForErrors: false) < 0 {
                command("loadfile", args: [path, "replace"])
            }
'''),
        ('    func destroyPlayer() {\n', '    func destroyPlayer() {\n        personalRetrySeek = nil\n        personalLoadGeneration &+= 1\n'),
        ('    // MARK: - State Update\n',
         '''    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        guard let mpv else { return }
        // Avoid changing forward buffering or audio processing. This cap is for the live engine only.
        let option = "options/demuxer-max-back-bytes"
        let bytes = Int64(getInt(option))
        if let cap = PersonalNativeConveniencePolicy.reducedBackCache(bytes: bytes) {
            _ = mpv_set_property_string(mpv, option, String(cap))
        }
    }

    private func verifyPersonalRetry(seeking: Bool, buffering: Bool, idle: Bool) {
        guard Thread.isMainThread, var retry = personalRetrySeek else { return }
        let now = ProcessInfo.processInfo.systemUptime
        // Until opening completes the engine may still report the previous or no path.
        if !isFileLoaded {
            if now - retry.started > 30 { personalRetrySeek = nil }
            return
        }
        switch retry.observe(generation: personalLoadGeneration, path: getString("path"), now: now,
            ready: !seeking && !buffering && !idle, positionMs: positionMs, durationMs: durationMs) {
        case .wait: personalRetrySeek = retry
        case .done: personalRetrySeek = nil
        case .seek(let target):
            personalRetrySeek = nil
            seekToMs(target)
        }
    }

    // MARK: - State Update
'''),
        ('        currentSpeed = PersonalNativePlaybackPolicy.playbackRate(speed)\n',
         '        currentSpeed = PersonalNativePlaybackPolicy.playbackRate(speed)\n'
         '        updatePersonalSmartFill()\n'
         '        verifyPersonalRetry(seeking: seeking, buffering: bufferingCache, idle: idle && !paused)\n'),
    ],
}
# Lifecycle: detach the callback, drain the serial event queue before freeing the libmpv handle.
# The existing event drain dispatches UI work asynchronously; destroyPlayer is called by UI disposal.
patches[bridge].extend([
    ('''        guard let ctx = mpv else { return }
        mpv = nil  // nil first so event loop stops reading
        mpv_terminate_destroy(ctx)
''', '''        guard let ctx = mpv else { return }
        mpv_set_wakeup_callback(ctx, nil, nil)
        eventQueue.sync {
            self.mpv = nil
            mpv_terminate_destroy(ctx)
        }
'''),
    ('''                case MPV_EVENT_FILE_LOADED:
                    DispatchQueue.main.async {
                        self.clearPlaybackError()
''', '''                case MPV_EVENT_FILE_LOADED:
                    DispatchQueue.main.async {
                        guard self.mpv != nil else { return }
                        self.clearPlaybackError()
'''),
    ('''                case MPV_EVENT_PLAYBACK_RESTART:
                    DispatchQueue.main.async {
                        self.updateState()
''', '''                case MPV_EVENT_PLAYBACK_RESTART:
                    DispatchQueue.main.async {
                        guard self.mpv != nil else { return }
                        self.updateState()
'''),
])
