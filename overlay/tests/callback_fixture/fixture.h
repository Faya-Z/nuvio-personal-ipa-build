#ifndef CALLBACK_FIXTURE_H
#define CALLBACK_FIXTURE_H
#include <stdint.h>
/* Minimal ABI-shaped test fixture, not libmpv. Based on documented stream_cb API. */
typedef struct mpv_handle mpv_handle;
typedef int64_t (*read_cb)(void *, char *, uint64_t);
typedef int64_t (*seek_cb)(void *, int64_t);
typedef int64_t (*size_cb)(void *);
typedef void (*close_cb)(void *);
typedef void (*cancel_cb)(void *);
typedef struct {
    void *cookie;
    read_cb read_fn;
    seek_cb seek_fn;
    size_cb size_fn;
    close_cb close_fn;
    cancel_cb cancel_fn;
} mpv_stream_cb_info;
typedef int (*open_cb)(void *, char *, mpv_stream_cb_info *);
int mpv_stream_cb_add_ro(mpv_handle *, const char *, void *, open_cb);
mpv_handle *fixture_create(void);
void fixture_destroy(mpv_handle *);
int fixture_open(mpv_handle *, const char *, mpv_stream_cb_info *);
int fixture_registrations(mpv_handle *);
#endif
