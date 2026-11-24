package com.nuvio.app.features.player

internal expect object SourceReliabilityStorage {
    fun load(profileId: Int): String?
    fun save(profileId: Int, value: String)
}
