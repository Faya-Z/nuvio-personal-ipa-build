package com.nuvio.app.features.player

import androidx.compose.runtime.mutableStateOf
import com.nuvio.app.isIos
import kotlin.time.TimeSource

internal class PersonalSleepRuntime {
    private val clock = TimeSource.Monotonic.markNow()
    private val timer = PersonalSleepTimer()
    private val displayMinutes = mutableStateOf<Long?>(null)
    fun set(minutes: Int) { timer.set(minutes, clock.elapsedNow().inWholeMilliseconds); refresh() }
    fun remainingMinutes(): Long? = displayMinutes.value
    fun refresh() { displayMinutes.value = timer.remainingMs(clock.elapsedNow().inWholeMilliseconds)?.let { (it + 59_999L) / 60_000L } }
    fun due(): Boolean = timer.consumeIfDue(clock.elapsedNow().inWholeMilliseconds).also { refresh() }
}

internal fun PlayerScreenRuntime.updatePersonalSleepTimer() {
    if (!isIos) return
    if (isPartySynced) { personalSleepRuntime.set(0); return }
    // Do not consume the deadline while the replacement controller is attaching.
    personalSleepRuntime.refresh()
    if (playerController == null || playerControllerSourceUrl != activeSourceUrl) return
    if (personalSleepRuntime.due() && shouldPlay) setPlaybackPlaying(false)
}
