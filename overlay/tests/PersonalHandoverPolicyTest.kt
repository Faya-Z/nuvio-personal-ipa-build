package com.nuvio.app.features.player
fun main() {
    var count = 0
    fun verify(v: Boolean) { check(v) { "Assertion ${count+1}" }; count++ }
    fun position(p: Long = 40_000, d: Long = 120_000, active: Boolean = true, ctrl: Boolean = true,
                 initial: Boolean = true, loading: Boolean = false, opening: Boolean = false, ended: Boolean = false,
                 scrub: Boolean = false, seek: Long? = null, party: Boolean = false, error: Boolean = false) =
        personalHandoverPosition(p,d,active,ctrl,initial,loading,opening,ended,scrub,seek,party,error)
    verify(position() == 40_000L); verify(position(p=1000) == 1000L)
    verify(position(p=0) == null); verify(position(p=-1) == null); verify(position(p=999) == null)
    verify(position(d=59_999) == null); verify(position(d=0) == null); verify(position(p=120_000) == null)
    verify(position(p=Long.MAX_VALUE) == null); verify(position(active=false) == null); verify(position(ctrl=false) == null)
    verify(position(initial=false) == null); verify(position(loading=true) == null); verify(position(opening=true) == null)
    verify(position(ended=true) == null); verify(position(scrub=true) == null); verify(position(seek=0) == null)
    verify(position(seek=1499) == null); verify(position(seek=1500) == 40_000L); verify(position(seek=-1) == null)
    verify(position(party=true) == null); verify(position(error=true) == null)
    println("PASS: $count handover assertions")
}
