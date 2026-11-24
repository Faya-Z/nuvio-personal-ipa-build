package com.nuvio.app.features.player

import platform.Foundation.NSUserDefaults

internal actual object SourceReliabilityStorage {
    private fun key(profileId: Int) = "personal_playback_reliability_v1_$profileId"
    actual fun load(profileId: Int): String? = NSUserDefaults.standardUserDefaults.stringForKey(key(profileId))
    actual fun save(profileId: Int, value: String) {
        NSUserDefaults.standardUserDefaults.setObject(value, forKey = key(profileId))
    }
}
