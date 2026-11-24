from pathlib import Path
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
ios = Path('composeApp/src/iosMain/kotlin/com/nuvio/app/features/player')
bridge = Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
policy = (Path(__file__).parent / 'native/PersonalNativeResumePolicy.swift').read_text()
patches = {
    ios/'PlayerBridge.kt': [
        ('    fun play()\n', '    fun loadFileWithAudioAtPosition(videoUrl: String, audioUrl: String?, headersJson: String?, subtitlesJson: String?, positionMs: Long)\n    fun play()\n'),
    ],
    ios/'PlayerEngine.ios.kt': [
        ('        bridge.loadFileWithAudio(\n            videoUrl = sourceUrl,\n            audioUrl = sourceAudioUrl,\n            headersJson = encodePlaybackHeadersForBridge(sourceHeaders),\n            subtitlesJson = encodeExternalSubtitlesForBridge(externalSubtitles),\n        )\n',
         '        bridge.loadFileWithAudioAtPosition(\n            videoUrl = sourceUrl,\n            audioUrl = sourceAudioUrl,\n            headersJson = encodePlaybackHeadersForBridge(sourceHeaders),\n            subtitlesJson = encodeExternalSubtitlesForBridge(externalSubtitles),\n            positionMs = initialPositionMs ?: 0L,\n        )\n'),
    ],
    base/'PlayerScreenRuntimeUi.kt': [
        ('                    initialPositionMs = activeInitialPositionMs.takeIf { it > 0L },\n',
         '                    initialPositionMs = activeInitialPositionMs.takeIf { it > 0L && (!com.nuvio.app.isIos || (!isPartySynced && !initialSeekApplied)) },\n'),
    ],
    base/'PlayerScreenRuntimeEffects.kt': [
        ('        if (initialSeekApplied || playbackSnapshot.isLoading) return@LaunchedEffect\n',
         '        if (initialSeekApplied || playbackSnapshot.isLoading) return@LaunchedEffect\n'
         '        if (com.nuvio.app.isIos && (playbackSnapshot.isOpening || playbackSnapshotKey != activePlaybackKey)) return@LaunchedEffect\n'),
        ('        playbackSnapshot.durationMs,\n        activeInitialPositionMs,\n',
         '        playbackSnapshot.durationMs,\n        playbackSnapshot.isOpening,\n        playbackSnapshotKey,\n        activeInitialPositionMs,\n'),
    ],
    bridge: [
        ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)', policy + '\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
        ('    private func parseSubtitles(_ json: String?) -> [PluginSubtitle] {\n',
         '''    func loadFileWithAudioAtPosition(videoUrl: String, audioUrl: String?, headersJson: String?, subtitlesJson: String?, positionMs: Int64) {
        ensurePlayerViewController().loadFile(
            videoUrl, audioUrl: audioUrl,
            requestHeaders: parseRequestHeaders(headersJson),
            subtitles: parseSubtitles(subtitlesJson), initialPositionMs: positionMs
        )
    }

    private func parseSubtitles(_ json: String?) -> [PluginSubtitle] {
'''),
        ('    let queuedAtUptime: TimeInterval\n}', '    let queuedAtUptime: TimeInterval\n    let initialPositionMs: Int64\n}'),
        ('    func loadFile(_ urlString: String, audioUrl: String? = nil, requestHeaders: [String: String] = [:], subtitles: [PluginSubtitle] = []) {\n',
         '    func loadFile(_ urlString: String, audioUrl: String? = nil, requestHeaders: [String: String] = [:], subtitles: [PluginSubtitle] = [], initialPositionMs: Int64 = 0) {\n'),
        ('            queuedAtUptime: ProcessInfo.processInfo.systemUptime\n', '            queuedAtUptime: ProcessInfo.processInfo.systemUptime,\n            initialPositionMs: initialPositionMs\n'),
        ('        command("loadfile", args: [request.urlString, "replace"])\n',
         '''        let args = PersonalNativeResumePolicy.loadArguments(url: request.urlString, positionMs: request.initialPositionMs)
        if args.count > 2 {
            // If the bundled libmpv rejects the per-file option, use the original load path.
            if commandResult("loadfile", args: args, checkForErrors: false) < 0 {
                command("loadfile", args: [request.urlString, "replace"])
            }
        } else {
            command("loadfile", args: args)
        }
'''),
        ('    private func command(_ command: String, args: [String?] = [], checkForErrors: Bool = true) {\n        guard mpv != nil else { return }\n',
         '    private func command(_ command: String, args: [String?] = [], checkForErrors: Bool = true) {\n        _ = commandResult(command, args: args, checkForErrors: checkForErrors)\n    }\n\n    private func commandResult(_ command: String, args: [String?], checkForErrors: Bool) -> Int32 {\n        guard mpv != nil else { return -1 }\n'),
        ('        let ret = mpv_command(mpv, &cargs)\n        if checkForErrors { checkError(ret) }\n    }\n',
         '        let ret = mpv_command(mpv, &cargs)\n        if checkForErrors { checkError(ret) }\n        return ret\n    }\n'),
    ],
}
