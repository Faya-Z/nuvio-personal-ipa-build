package com.nuvio.app.features.player
internal expect object PersonalHistoryStorage {
    fun load(profileId: Int): String?
    fun save(profileId: Int, value: String)
}
