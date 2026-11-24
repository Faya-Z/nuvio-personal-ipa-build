package com.nuvio.app.features.player
fun main() {
    val h = "1234567890abcdef"
    check(samePlaybackFile(h, 100L, h.uppercase(), 100L))
    check(!samePlaybackFile(h, 100L, h, 101L))
    check(!samePlaybackFile(h, 100L, "0000000000000000", 100L))
    check(!samePlaybackFile(null, 100L, h, 100L))
    check(!samePlaybackFile(h, null, h, null))
    check(!samePlaybackFile(h, 0L, h, 0L))
    check(!samePlaybackFile("bad", 100L, "bad", 100L))
    check(!samePlaybackFile("zzzzzzzzzzzzzzzz", 100L, "zzzzzzzzzzzzzzzz", 100L))
    check(replayEnglishLanguage("ENG"))
    check(replayEnglishLanguage("en-GB"))
    check(replayEnglishLanguage("English"))
    check(replayEnglishLanguage("en_US"))
    check(!replayEnglishLanguage("es"))
    check(!replayEnglishLanguage(null))
    check(!replayEnglishLanguage("enigma"))
    check(DialogueReplayWindow.from(0L) == null)
    check(DialogueReplayWindow.from(5000L) == DialogueReplayWindow(0L, 5000L))
    val r = DialogueReplayWindow.from(30000L)!!
    check(r.startMs == 20000L)
    check(!r.finished(29999L, false))
    check(r.finished(30000L, false))
    check(r.finished(100L, true))
    println("PASS: 21 feature policy assertions")
}
