// File-local resume hints; no persistent mpv option mutation.
private enum PersonalNativeResumePolicy {
    static func startOption(positionMs: Int64) -> String? {
        // Ignore tiny or unreasonable offsets; the ordinary validated seek is still available.
        guard positionMs >= 1_000, positionMs <= 24 * 60 * 60 * 1_000 else { return nil }
        let whole = positionMs / 1_000
        let fraction = String(positionMs % 1_000)
        let padded = String(repeating: "0", count: 3 - fraction.count) + fraction
        return "start=\(whole).\(padded)"
    }
    static func loadArguments(url: String, positionMs: Int64) -> [String?] {
        guard let start = startOption(positionMs: positionMs) else { return [url, "replace"] }
        return [url, "replace", "-1", start]
    }
}
