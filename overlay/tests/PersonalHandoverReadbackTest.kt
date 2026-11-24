package com.nuvio.app.features.player
fun main() {
    var count = 0
    fun verify(v: Boolean) { check(v) { "Assertion ${count+1}" }; count++ }
    val target = PersonalHandoverCheckpoint("tt123", "series", "tt123:1:2", 1, 2, 120_000, 900_000, 100_000)
    fun match(id: String="tt123", type: String="series", video: String="tt123:1:2", s: Int?=1, e: Int?=2, p: Long=120_000, d: Long=900_000, t: Long=100_000) = target.matches(id,type,video,s,e,p,d,t)
    verify(match()); verify(match(t=100_001)); verify(match(type="SERIES")); verify(!match(t=99_999)); verify(!match(t=0)); verify(!match(id="tt124")); verify(!match(type="movie")); verify(!match(video="tt123:1:3")); verify(!match(s=2)); verify(!match(e=3)); verify(!match(s=null)); verify(!match(e=null)); verify(!match(p=120_001)); verify(!match(p=119_999)); verify(!match(d=900_001)); verify(!match(d=0)); verify(!target.copy(requestedAtMs=0).matches("tt123","series","tt123:1:2",1,2,120_000,900_000,100_000))
    val movie=PersonalHandoverCheckpoint("tt3","movie","tt3",null,null,50_000,1_000_000,100_000)
    verify(movie.matches("tt3","movie","tt3",null,null,50_000,1_000_000,100_001)); verify(!movie.matches("tt3","movie","tt3",1,1,50_000,1_000_000,100_001))
    println("PASS: $count handover readback assertions")
}
