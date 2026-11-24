#if PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT
// The bundled Libmpv module must export stream_cb.h for this optional path.
// No callback calls back into MPV. Context lives until mpv_terminate_destroy returns.
private final class PersonalMPVRangeAdapter {
    private let lock = NSLock()
    private var slots: [String: PersonalPrefetchTransport.Prepared] = [:]
    private var registered = false
    private let open: (PersonalPrefetchTransport.Prepared) -> PersonalRangeReader?
    init(open: @escaping (PersonalPrefetchTransport.Prepared) -> PersonalRangeReader? = PersonalPrefetchTransport.open) {
        self.open = open
    }
    func url(for slot: PersonalPrefetchTransport.Prepared, handle: OpaquePointer) -> String? {
        if !registered {
            let status = mpv_stream_cb_add_ro(handle, "nuviorange", Unmanaged.passUnretained(self).toOpaque()) { user, uri, info in
                guard let user, let uri, let info else { return -1 }
                let adapter = Unmanaged<PersonalMPVRangeAdapter>.fromOpaque(user).takeUnretainedValue()
                guard let slot = adapter.take(String(cString: uri)), let reader = adapter.open(slot) else { return -1 }
                info.pointee.cookie = Unmanaged.passRetained(reader).toOpaque()
                info.pointee.read_fn = { cookie, buffer, nbytes in
                    guard let cookie, let buffer, nbytes > 0, let count = Int(exactly: nbytes) else { return -1 }
                    let reader = Unmanaged<PersonalRangeReader>.fromOpaque(cookie).takeUnretainedValue()
                    guard let data = reader.read(count) else { return -1 }
                    if !data.isEmpty { data.copyBytes(to: UnsafeMutableRawPointer(buffer).assumingMemoryBound(to: UInt8.self), count: data.count) }
                    return Int64(data.count)
                }
                info.pointee.seek_fn = { cookie, offset in
                    guard let cookie else { return -1 }
                    return Unmanaged<PersonalRangeReader>.fromOpaque(cookie).takeUnretainedValue().seek(offset)
                }
                info.pointee.size_fn = { cookie in
                    guard let cookie else { return -1 }
                    return Unmanaged<PersonalRangeReader>.fromOpaque(cookie).takeUnretainedValue().identity.length
                }
                info.pointee.cancel_fn = { cookie in
                    guard let cookie else { return }
                    Unmanaged<PersonalRangeReader>.fromOpaque(cookie).takeUnretainedValue().cancel()
                }
                info.pointee.close_fn = { cookie in
                    guard let cookie else { return }
                    let reader = Unmanaged<PersonalRangeReader>.fromOpaque(cookie).takeRetainedValue()
                    reader.cancel()
                }
                return 0
            }
            guard status >= 0 else { return nil }
            registered = true
        }
        let uri = "nuviorange://\(UUID().uuidString.lowercased())"
        lock.lock(); slots = [uri: slot]; lock.unlock()
        return uri
    }
    private func take(_ uri: String) -> PersonalPrefetchTransport.Prepared? {
        lock.lock(); defer { lock.unlock() }; return slots.removeValue(forKey: uri)
    }
    func clear() { lock.lock(); slots.removeAll(); lock.unlock() }
}
#endif
