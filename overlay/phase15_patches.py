from pathlib import Path
bridge=Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
policy=(Path(__file__).parent/'native/PersonalEncodedBarPolicy.swift').read_text()
patches={bridge:[
 ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)',policy+'\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
 ('    private var personalCropCheckedAt: Double = -1\n','''    private var personalCropCheckedAt: Double = -1
    private var personalBarPolicy = PersonalEncodedBarPolicy()
    private var personalBarToken: UInt64 = 0xB400000000000000
    private var personalBarPending: UInt64?
    private var personalBarInFlight: UInt64?
    private var personalBarSampleRequests = 0
    private var personalBarLastRequest: Double = -1
    private var personalEncodedCrop: String?
'''),
 ('        personalRetrySeek = nil\n        personalCropCheckedAt = -1\n','        personalRetrySeek = nil\n        resetPersonalEncodedBars()\n        personalCropCheckedAt = -1\n'),
 ('        personalSmartFill = enabled\n','        if personalSmartFill != enabled { resetPersonalEncodedBars() }\n        personalSmartFill = enabled\n'),
 ('        personalResizeMode = mode\n','        if personalResizeMode != mode { resetPersonalEncodedBars() }\n        personalResizeMode = mode\n'),
 ('        personalRetrySeek = nil\n        guard mpv != nil else { return }\n        let seconds = Double(ms) / 1000.0\n        command("seek",','        personalRetrySeek = nil\n        resetPersonalEncodedBars()\n        guard mpv != nil else { return }\n        let seconds = Double(ms) / 1000.0\n        command("seek",'),
 ('        personalRetrySeek = nil\n        guard mpv != nil else { return }\n        let seconds = Double(ms) / 1000.0\n        let seekMode','        personalRetrySeek = nil\n        resetPersonalEncodedBars()\n        guard mpv != nil else { return }\n        let seconds = Double(ms) / 1000.0\n        let seekMode'),
 ('            personalLoadGeneration &+= 1\n            resetPersonalCachePolicy(url: path)','            personalLoadGeneration &+= 1\n            resetPersonalEncodedBars()\n            resetPersonalCachePolicy(url: path)'),
 ('    private func updatePersonalSmartFill() {','''    private func resetPersonalEncodedBars() {
        personalBarPending = nil
        personalBarPolicy = PersonalEncodedBarPolicy()
        personalBarSampleRequests = 0
        personalBarLastRequest = -1
        if personalEncodedCrop != nil, let mpv {
            _ = mpv_set_property_string(mpv, "options/video-crop", "")
        }
        personalEncodedCrop = nil
        personalCropCheckedAt = -1
    }

    // Request a raw video frame asynchronously. The MPV-owned bytes are sampled only
    // on its event queue before the next mpv_wait_event; no frame is written to storage.
    private func requestPersonalBarSample(eligible: Bool) {
        guard Thread.isMainThread, let mpv, eligible, personalSmartFill, personalResizeMode == 0,
              personalEncodedCrop == nil, personalBarInFlight == nil, personalBarSampleRequests < 6,
              !ProcessInfo.processInfo.isLowPowerModeEnabled,
              UIApplication.shared.applicationState == .active else { return }
        let now = ProcessInfo.processInfo.systemUptime
        guard personalBarLastRequest < 0 || now - personalBarLastRequest >= 5 else { return }
        personalBarLastRequest = now
        personalBarSampleRequests += 1
        // Limit raw readback allocation to ordinary HD frames. Higher resolutions keep normal smart fill.
        let w = getInt("video-params/w"), h = getInt("video-params/h")
        guard (320...1920).contains(w), (180...1080).contains(h), w >= h,
              getString("options/video-crop") == "", getDouble("video-params/par") == 1 else {
            _ = personalBarPolicy.observe(nil); return
        }
        personalBarToken &+= 1
        let token = personalBarToken
        var args = makeCArgs("screenshot-raw", ["video", "bgr0"]).map { $0.flatMap { UnsafePointer<CChar>(strdup($0)) } }
        defer { for ptr in args where ptr != nil { free(UnsafeMutablePointer(mutating: ptr!)) } }
        personalBarPending = token
        personalBarInFlight = token
        if mpv_command_async(mpv, token, &args) < 0 {
            personalBarPending = nil
            personalBarInFlight = nil
            _ = personalBarPolicy.observe(nil)
        }
    }

    private static func personalBarsFromReply(_ result: mpv_node) -> PersonalEncodedBarPolicy.Bars? {
        guard result.format == MPV_FORMAT_NODE_MAP, let list = result.u.list?.pointee,
              list.num > 0, list.num <= 16, let keys = list.keys, let values = list.values else { return nil }
        var width: Int?, height: Int?, stride: Int?, format: String?, data: mpv_byte_array?
        for i in 0..<Int(list.num) {
            guard let key = keys[i] else { continue }
            let node = values[i]
            switch String(cString: key) {
            case "w" where node.format == MPV_FORMAT_INT64: width = Int(exactly: node.u.int64)
            case "h" where node.format == MPV_FORMAT_INT64: height = Int(exactly: node.u.int64)
            case "stride" where node.format == MPV_FORMAT_INT64: stride = Int(exactly: node.u.int64)
            case "format" where node.format == MPV_FORMAT_STRING: format = node.u.string.map { String(cString: $0) }
            case "data" where node.format == MPV_FORMAT_BYTE_ARRAY: data = node.u.ba?.pointee
            default: break
            }
        }
        guard let width, let height, let stride, let data, let pointer = data.data,
              format == "bgr0", data.size > 0, data.size <= 64 * 1024 * 1024 else { return nil }
        return PersonalEncodedBarPolicy.detect(width: width, height: height, stride: stride,
            bytes: UnsafeRawBufferPointer(start: pointer, count: data.size))
    }

    private func acceptPersonalBarSample(token: UInt64, bars: PersonalEncodedBarPolicy.Bars?) {
        guard token == personalBarInFlight else { return }
        personalBarInFlight = nil
        guard token == personalBarPending else { return }
        personalBarPending = nil
        guard let mpv, personalSmartFill, personalResizeMode == 0, isFileLoaded,
              pendingLoadRequest == nil, !getFlag("seeking"), !getFlag("paused-for-cache"),
              !ProcessInfo.processInfo.isLowPowerModeEnabled,
              UIApplication.shared.applicationState == .active else { return }
        let valid = bars.flatMap { candidate in
            getInt("video-params/w") == candidate.width && getInt("video-params/h") == candidate.height ? candidate : nil
        }
        guard let confirmed = personalBarPolicy.observe(valid), getString("options/video-crop") == "" else { return }
        if mpv_set_property_string(mpv, "options/video-crop", confirmed.crop) >= 0 {
            personalEncodedCrop = confirmed.crop
            personalCropCheckedAt = -1
        }
    }

    private func updatePersonalSmartFill() {'''),
 ('        updatePersonalSmartFill()\n        verifyPersonalRetry(seeking:', '''        requestPersonalBarSample(eligible: isFileLoaded && !paused && !seeking && !bufferingCache && !idle && !eofReached &&
            positionMs > 15_000 && durationMs > 0 && durationMs - positionMs > 30_000)
        updatePersonalSmartFill()
        verifyPersonalRetry(seeking:'''),
 ('                case MPV_EVENT_FILE_LOADED:\n                    DispatchQueue.main.async {\n                        guard self.mpv != nil else { return }','''                case MPV_EVENT_COMMAND_REPLY:
                    let token = eventPtr.pointee.reply_userdata
                    if token >> 56 == 0xB4 {
                        let bars: PersonalEncodedBarPolicy.Bars?
                        if eventPtr.pointee.error >= 0, let data = eventPtr.pointee.data {
                            bars = Self.personalBarsFromReply(data.assumingMemoryBound(to: mpv_event_command.self).pointee.result)
                        } else { bars = nil }
                        DispatchQueue.main.async { [weak self] in self?.acceptPersonalBarSample(token: token, bars: bars) }
                    }
                case MPV_EVENT_FILE_LOADED:
                    DispatchQueue.main.async {
                        guard self.mpv != nil else { return }'''),
 ('        personalRetrySeek = nil\n        personalLoadGeneration &+= 1\n','        personalBarPending = nil\n        personalRetrySeek = nil\n        personalLoadGeneration &+= 1\n'),
]}

base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
patches[base/'StreamInfoOverlay.kt'] = [
 ('Automatically crops up to 10% for near-matching screen proportions. Does not detect encoded black bars.',
  'Fits near-matching screens and experimentally trims consistent encoded letterbox bars on HD video. Turn off if the film changes aspect ratio.'),
]
