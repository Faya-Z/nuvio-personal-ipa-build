#include "fixture.h"
#include <stdlib.h>
#include <string.h>
struct mpv_handle { void *cookie; open_cb open; int registrations; };
mpv_handle *fixture_create(void) { return calloc(1,sizeof(mpv_handle)); }
void fixture_destroy(mpv_handle *h) { free(h); }
int mpv_stream_cb_add_ro(mpv_handle *h,const char *protocol,void *cookie,open_cb cb) {
    if (!h || strcmp(protocol,"nuviorange") || !cb || h->open) return -1;
    h->cookie=cookie; h->open=cb; ++h->registrations; return 0;
}
int fixture_open(mpv_handle *h,const char *uri,mpv_stream_cb_info *i) {
    if (!h || !h->open || !i) return -1;
    char *copy=strdup(uri); memset(i,0,sizeof(*i)); int r=h->open(h->cookie,copy,i); free(copy); return r;
}
int fixture_registrations(mpv_handle *h) { return h->registrations; }
