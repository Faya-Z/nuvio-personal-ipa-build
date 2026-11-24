package com.nuvio.app.features.player
fun main() {
    var now = 123456789L
    var disk = ""
    var writes = 0
    val a = SourceReliability(2, nowMs = { now }, persist = { disk = it; writes++ })
    check(writes == 0)
    a.record("https://example.invalid/private?token=secret", true)
    check(writes == 1)
    check(!disk.contains("secret"))
    check(!disk.contains("example"))
    check(disk.startsWith("v1\n"))
    a.record("other", false)
    val b = SourceReliability(2, disk, { now })
    check(b.score("https://example.invalid/private?token=secret") == 0.6)
    check(b.score("other") == 0.4)
    check(b.score("unknown") == 0.5)
    check(b.best(listOf("other", "unknown")) { it } == "unknown")
    b.record("third", true)
    check(b.score("https://example.invalid/private?token=secret") == 0.5)
    check(b.score("third") == 0.6)
    check(SourceReliability(persisted = "junk", nowMs = { now }).score("other") == 0.5)
    check(SourceReliability(persisted = "v1\ninvalid|20|0|$now", nowMs = { now }).snapshot() == "v1\n")
    check(SourceReliability(persisted = "v1\n0123456789abcdef|99|0|$now", nowMs = { now }).snapshot() == "v1\n")
    check(SourceReliability(persisted = "v1\n0123456789abcdef|1|0|${now+1}", nowMs = { now }).snapshot() == "v1\n")
    check(SourceReliability(persisted = "v1\n0123456789abcdef|1|0|-1", nowMs = { now }).snapshot() == "v1\n")
    check(SourceReliability(persisted = "v1\n" + "x".repeat(20_001), nowMs = { now }).snapshot() == "v1\n")
    now += 14L * 86400000 + 1
    check(b.score("other") == 0.5)
    check(b.snapshot() == "v1\n")
    check(SourceReliability(persisted = disk, nowMs = { now }).score("other") == 0.5)
    a.record("other", true)
    check(a.score("other") == 0.6)
    check(disk.lineSequence().filter { it.contains('|') }.count() == 1)
    println("PASS: 22 persistence assertions")
}
