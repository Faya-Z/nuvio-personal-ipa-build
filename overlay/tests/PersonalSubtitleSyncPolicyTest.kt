package com.nuvio.app.features.player

fun main() {
    var count = 0
    fun verify(value: Boolean) { check(value) { "Assertion ${count + 1}" }; count++ }
    val gate = PersonalSubtitleSyncGate<String>()
    verify(!gate.isBound(null)); verify(gate.bind("a")); verify(!gate.bind("a"))
    val a = gate.begin("a")
    verify(gate.accepts(a,"a")); verify(!gate.accepts(a,"b")); verify(!gate.accepts(a,null))
    val b = gate.begin("a")
    verify(!gate.accepts(a,"a")); verify(gate.accepts(b,"a")); verify(gate.bind("b"))
    verify(!gate.accepts(b,"b")); verify(gate.bind("a")); verify(!gate.accepts(b,"a"))
    val c = gate.begin("a"); verify(gate.bind(null)); verify(!gate.accepts(c,"a")); verify(!gate.isBound(null))
    fun delay(a: Long,b:Long,r:Long=200L) = personalSubtitleDelayMs(a,b,r,-5000,5000)
    verify(delay(1000,800)==0); verify(delay(1000,0)==800); verify(delay(0,1000)==-1200)
    verify(delay(Long.MAX_VALUE,0)==5000); verify(delay(0,Long.MAX_VALUE)==-5000)
    verify(delay(Long.MIN_VALUE,Long.MIN_VALUE)==-200); verify(delay(0,0,Long.MAX_VALUE)==-5000)
    verify(delay(0,0,-1)==0); verify(delay(5200,0)==5000); verify(delay(0,4800)==-5000)
    verify(!personalNeedsResumeSeek(0,0,false)); verify(personalNeedsResumeSeek(10000,0,true))
    verify(personalNeedsResumeSeek(10000,10000,false)); verify(!personalNeedsResumeSeek(10000,10000,true))
    verify(!personalNeedsResumeSeek(10000,9750,true)); verify(!personalNeedsResumeSeek(10000,10250,true))
    verify(personalNeedsResumeSeek(10000,9749,true)); verify(personalNeedsResumeSeek(10000,10251,true))
    verify(personalNeedsResumeSeek(Long.MAX_VALUE,1,true)); verify(personalNeedsResumeSeek(1,Long.MAX_VALUE,true))
    println("PASS: $count subtitle sync and resume assertions")
}
