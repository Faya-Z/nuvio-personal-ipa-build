from pathlib import Path
bridge = Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
policy = (Path(__file__).parent / 'native/PersonalNativePlaybackPolicy.swift').read_text()
patches = {bridge: [
    ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)', policy + '\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
    ('        let cached = getDouble("demuxer-cache-time")\n', '        let cacheEnd = getDouble("demuxer-cache-time")\n'),
    ('        durationMs = Int64(duration * 1000)\n        positionMs = Int64(max(position, 0) * 1000)\n        bufferedMs = Int64(max(position + cached, 0) * 1000)\n        currentSpeed = Float(speed > 0 ? speed : 1.0)\n',
     '        durationMs = PersonalNativePlaybackPolicy.milliseconds(duration)\n'
     '        positionMs = PersonalNativePlaybackPolicy.milliseconds(position)\n'
     '        bufferedMs = PersonalNativePlaybackPolicy.bufferedPosition(position: position, duration: duration, cacheEnd: cacheEnd)\n'
     '        currentSpeed = PersonalNativePlaybackPolicy.playbackRate(speed)\n'),
    ('                    } else {\n                        DispatchQueue.main.async { self.updateState() }\n                    }\n                case MPV_EVENT_FILE_LOADED:',
     '                    } else if PersonalNativePlaybackPolicy.needsTrackRefresh(name) {\n'
     '                        DispatchQueue.main.async { self.updateState() }\n'
     '                    } else {\n'
     '                        DispatchQueue.main.async {\n'
     '                            self.refreshPlaybackState()\n'
     '                            self.updateStyledSubtitle()\n'
     '                        }\n'
     '                    }\n'
     '                case MPV_EVENT_FILE_LOADED:'),
    ('        var subs = [TrackInfo]()\n        let count = getInt("track-list/count")\n        var audioIdx = 0\n', '        var subs = [TrackInfo]()\n        let count = max(0, getInt("track-list/count"))\n        var audioIdx = 0\n'),
    ('        isFileLoaded = false\n        applyAudioLanguagePreferences(preferredAudioLanguages)\n        startupSubtitles = request.subtitles\n',
     '        isFileLoaded = false\n'
     '        durationMs = 0\n        positionMs = 0\n        bufferedMs = 0\n'
     '        audioTracks = []\n        subtitleTracks = []\n'
     '        applyAudioLanguagePreferences(preferredAudioLanguages)\n        startupSubtitles = request.subtitles\n'),
    ('        var data = Int64()\n        mpv_get_property(mpv, name, MPV_FORMAT_FLAG, &data)\n        return data > 0\n',
     '        var data: Int32 = 0\n        let result = mpv_get_property(mpv, name, MPV_FORMAT_FLAG, &data)\n        return result >= 0 && data != 0\n'),
    ('        var data: Int = flag ? 1 : 0\n        mpv_set_property(mpv, name, MPV_FORMAT_FLAG, &data)\n',
     '        var data: Int32 = flag ? 1 : 0\n        mpv_set_property(mpv, name, MPV_FORMAT_FLAG, &data)\n'),
]}
