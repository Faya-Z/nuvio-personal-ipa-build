from pathlib import Path
bridge = Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
policy = (Path(__file__).parent / 'native/PersonalNativeEventBatch.swift').read_text()
patches = {bridge: [
    ('// MARK: - Player Bridge Implementation (Kotlin protocol conformance)', policy + '\n// MARK: - Player Bridge Implementation (Kotlin protocol conformance)'),
    ('''    func syncVideoSurfaceLayout(size: CGSize) {
        if Thread.isMainThread {
            syncVideoSurfaceLayoutNow(size: size, scheduleDeferredPasses: true)
        } else {
            DispatchQueue.main.async { [weak self] in
                self?.syncVideoSurfaceLayoutNow(size: size, scheduleDeferredPasses: true)
            }
        }
    }
''', '''    func syncVideoSurfaceLayout(size: CGSize) {
        if Thread.isMainThread {
            syncVideoSurfaceLayoutNow(size: size, scheduleDeferredPasses: true)
            attemptStartPendingLoad()
        } else {
            DispatchQueue.main.async { [weak self] in
                self?.syncVideoSurfaceLayoutNow(size: size, scheduleDeferredPasses: true)
                self?.attemptStartPendingLoad()
            }
        }
    }
'''),
    ('''            while true {
                let event = mpv_wait_event(mpv, 0)
                guard let eventPtr = event else { break }
                if eventPtr.pointee.event_id == MPV_EVENT_NONE { break }

                switch eventPtr.pointee.event_id {
''', '''            var propertyBatch = PersonalNativeEventBatch()
            func flushProperties() {
                let refresh = propertyBatch.take()
                guard refresh != .none else { return }
                DispatchQueue.main.async { [weak self] in
                    guard let self, self.mpv != nil else { return }
                    switch refresh {
                    case .none: break
                    case .subtitleOnly: self.updateStyledSubtitle()
                    case .playback:
                        self.refreshPlaybackState()
                        self.updateStyledSubtitle()
                    case .tracks: self.updateState()
                    }
                }
            }
            while true {
                let event = mpv_wait_event(mpv, 0)
                guard let eventPtr = event else { break }
                if eventPtr.pointee.event_id == MPV_EVENT_NONE { break }
                if eventPtr.pointee.event_id != MPV_EVENT_PROPERTY_CHANGE {
                    flushProperties()
                }
                switch eventPtr.pointee.event_id {
'''),
    ('''                    if name == "sub-text" {
                        DispatchQueue.main.async { self.updateStyledSubtitle() }
                    } else if PersonalNativePlaybackPolicy.needsTrackRefresh(name) {
                        DispatchQueue.main.async { self.updateState() }
                    } else {
                        DispatchQueue.main.async {
                            self.refreshPlaybackState()
                            self.updateStyledSubtitle()
                        }
                    }
                case MPV_EVENT_FILE_LOADED:''', '''                    propertyBatch.add(name)
                    if propertyBatch.shouldFlush { flushProperties() }
                case MPV_EVENT_FILE_LOADED:'''),
    ('''                default:
                    break
                }
            }
        }
    }

    // MARK: - MPV Helpers''', '''                default:
                    break
                }
            }
            flushProperties()
        }
    }

    // MARK: - MPV Helpers'''),
]}
