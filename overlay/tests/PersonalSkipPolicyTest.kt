package com.nuvio.app.features.player

fun main() {
    var count = 0
    fun verify(ok: Boolean) { check(ok) { "Assertion ${count + 1}" }; count++ }
    fun same(a: Double, b: Double, c: Double, d: Double, t: String? = "recap", p: String? = "recap") = personalSameSkipSegment(t,a,b,p,c,d)
    verify(same(0.0,30.0,0.0,30.0)); verify(same(0.0,30.0,2.0,32.0))
    verify(same(0.0,30.0,15.0,45.0)); verify(!same(0.0,30.0,15.1,45.1))
    verify(!same(0.0,30.0,30.0,60.0)); verify(!same(0.0,30.0,60.0,90.0))
    verify(!same(0.0,30.0,0.0,30.0,"intro")); verify(!same(0.0,30.0,0.0,30.0,null,null))
    verify(!same(Double.NaN,30.0,0.0,30.0)); verify(!same(0.0,Double.POSITIVE_INFINITY,0.0,30.0))
    verify(!same(-1.0,30.0,0.0,30.0)); verify(!same(30.0,30.0,0.0,30.0))
    verify(!same(30.0,10.0,0.0,30.0)); verify(!same(0.0,30.0,0.0,1.0))
    verify(same(0.0,30.0,0.0,15.0)); verify(same(0.0,15.0,0.0,30.0))
    fun target(a: Long,b: Long,c: Long) = personalForwardSkipTarget(a,b,c)
    verify(target(5,10,20)==10L); verify(target(5,20,20)==19L); verify(target(5,Long.MAX_VALUE,20)==19L)
    verify(target(5,5,20)==null); verify(target(5,4,20)==null); verify(target(19,20,20)==null)
    verify(target(20,21,20)==null); verify(target(0,1,0)==null); verify(target(0,1,-1)==null)
    verify(target(-1,1,10)==null); verify(target(0,-1,10)==null); verify(target(0,1,2)==1L)
    verify(target(Long.MAX_VALUE-2,Long.MAX_VALUE,Long.MAX_VALUE)==Long.MAX_VALUE-1)
    val a = Triple("video-a",1,2)
    val b = Triple("video-b",1,3)
    verify(!personalShouldResetPreload(a,a,true)); verify(personalShouldResetPreload(a,b,true))
    verify(personalShouldResetPreload(a,null,true)); verify(!personalShouldResetPreload(a,b,false))
    verify(personalShouldResetPreload(null,a,true)); verify(!personalShouldResetPreload(null,null,true))
    println("PASS: $count skip and preload identity assertions")
}
