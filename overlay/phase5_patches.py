from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
bridge = Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
policy = (Path(__file__).parent / 'native/AdaptiveCachePolicy.swift').read_text()
patches = {
    base/'PlayerScreenRuntimeState.kt': [
        ('    val recoveryRuntime = PlayerRecoveryRuntime()\n', '    val recoveryRuntime = PlayerRecoveryRuntime(profileId)\n'),
    ],
    bridge: [
        ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)', policy + '\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
        ('    private var mpv: OpaquePointer?\n',
         '    private var mpv: OpaquePointer?\n'
         '    private var personalCachePolicy = PersonalAdaptiveCachePolicy()\n'
         '    private var personalCacheBaseline: Double?\n'
         '    private var personalCacheApplied: Double?\n'
         '    private var personalCacheRemote = false\n'
         '    private var personalLoadGeneration: UInt64 = 0\n'),
        ('    private func queueLoad(_ request: PendingLoadRequest) {\n        pendingLoadRequest = request\n',
         '    private func queueLoad(_ request: PendingLoadRequest) {\n'
         '        personalLoadGeneration &+= 1\n'
         '        personalCacheRemote = false\n'
         '        pendingLoadRequest = request\n'),
        ('        startupSubtitles = request.subtitles\n        command("loadfile", args: [request.urlString, "replace"])\n',
         '        startupSubtitles = request.subtitles\n'
         '        resetPersonalCachePolicy(url: request.urlString)\n'
         '        let loadGeneration = personalLoadGeneration\n'
         '        command("loadfile", args: [request.urlString, "replace"])\n'),
        ('                self?.command("audio-add", args: [audioUrl, "select"], checkForErrors: false)\n',
         '                guard let self, self.personalLoadGeneration == loadGeneration, self.mpv != nil else { return }\n'
         '                self.command("audio-add", args: [audioUrl, "select"], checkForErrors: false)\n'),
        ('            let pos = getDouble("time-pos")\n            isFileLoaded = false\n',
         '            let pos = getDouble("time-pos")\n'
         '            personalLoadGeneration &+= 1\n'
         '            let retryGeneration = personalLoadGeneration\n'
         '            resetPersonalCachePolicy(url: path)\n'
         '            isFileLoaded = false\n'),
        ('                self?.command("seek", args: [String(format: "%.3f", pos), "absolute"])\n',
         '                guard let self, self.personalLoadGeneration == retryGeneration, self.mpv != nil else { return }\n'
         '                self.command("seek", args: [String(format: "%.3f", pos), "absolute"])\n'),
        ('    // MARK: - State Update\n',
         '''    // MARK: - Personal buffering policy

    private func resetPersonalCachePolicy(url: String) {
        // Restore the original option before each new media load, including local playback.
        let name = "options/cache-pause-wait"
        if let baseline = personalCacheBaseline, personalCacheApplied != baseline {
            guard mpv_set_property_string(mpv, name, String(baseline)) >= 0 else {
                personalCacheRemote = false
                return
            }
        }
        personalCachePolicy = PersonalAdaptiveCachePolicy()
        personalCacheBaseline = getString(name).flatMap { Double($0) }
        personalCacheApplied = personalCacheBaseline
        // Do not change local media, loopback/P2P streams or startup cache thresholds.
        let parsed = URL(string: url)
        let scheme = parsed?.scheme?.lowercased()
        let host = parsed?.host?.lowercased()
        personalCacheRemote = (scheme == "https" || scheme == "http") && host != nil &&
            host != "localhost" && host != "127.0.0.1" && host != "::1" && host != "[::1]" &&
            host?.hasPrefix("127.") != true
    }

    private func updatePersonalCachePolicy(position: Double, duration: Double, paused: Bool,
                                           seeking: Bool, ended: Bool, idle: Bool, buffering: Bool) {
        guard Thread.isMainThread, let mpv, personalCacheRemote,
              let base = personalCacheBaseline else { return }
        let eligible = isFileLoaded && !paused && !seeking && !ended && position >= 5 &&
            duration - position > 15 && UIApplication.shared.applicationState == .active
        _ = personalCachePolicy.observe(now: ProcessInfo.processInfo.systemUptime,
            eligible: eligible, playing: !idle && !paused, buffering: buffering)
        guard let target = personalCachePolicy.target(base: base), target != personalCacheApplied else { return }
        if mpv_set_property_string(mpv, "options/cache-pause-wait", String(target)) >= 0 {
            personalCacheApplied = target
        } else {
            // Unsupported runtime setting: do not repeatedly attempt a change.
            personalCacheRemote = false
        }
    }

    // MARK: - State Update
'''),
        ('        let bufferingCache = getFlag("paused-for-cache")\n',
         '        let bufferingCache = getFlag("paused-for-cache")\n'
         '        updatePersonalCachePolicy(position: position, duration: duration, paused: paused,\n'
         '                                  seeking: seeking, ended: eofReached, idle: idle, buffering: bufferingCache)\n'),
    ],
}
