package com.nuvio.app.features.player

internal actual object SourceReliabilityStorage {
    actual fun load(profileId: Int): String? = null
    actual fun save(profileId: Int, value: String) = Unit
}
