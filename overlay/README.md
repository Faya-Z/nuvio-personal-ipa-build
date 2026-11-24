# Nuvio personal Phase 17 — cumulative experimental source overlay

Pinned upstream: `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb` (1.1.0-beta.3). Includes phases 1–16. Apply to a clean pinned checkout only. No compiled IPA.

## Phase 17: range transport hardening and native callback validation

- Reuse one ephemeral URLSession per active range reader instead of creating a fresh session for every byte range. Sequential reads can reuse the connection pool; actual TCP/TLS reuse and performance require live-server testing. Speculative preload sessions are explicitly closed after their single request.
- Idempotent reader cancellation and teardown; the reader cancels its transport on deinitialization. Failed initial resource validation closes the session. HTTP status/ETag/range/body validation, profile identity, no credentials/cookies/redirects/cellular, bounded memory and the experimental opt-in gate remain intact.
- Real URLSession delegate path exercised with mocked URLProtocol responses: first and subsequent requests, session reuse, rejection, retry and cancellation. No external HTTP server was used.
- Added a C callback fixture that compiles and runs the Swift MPV range adapter against a small API-shaped C module. This checks token consumption, read/seek/size, cancellation, EOF and close semantics; it is not the actual libmpv module or iOS ABI.
- All 612 standalone checks pass (584 previously + 8 delegate/session + 20 callback fixture), along with synthetic cumulative patch application and feature-anchor checks.

## Build status and next steps

Run `bash validate_checkout.sh /path/to/clean/NuvioMobile` on a compatible build host with Swift, Kotlin and clang. Keep `PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT` **off** for the normal build. Use a separate debug target to verify the actual bundled libmpv import, then test authorized HTTPS media and compare playback startup, range traffic, energy and error recovery on device. Full application compilation, actual upstream checkout application, live network integration and device tests remain outstanding. No changes were pushed upstream. No volume, spoiler protection or discovery changes.

Historical notes follow; use the latest phase rather than applying older phases independently.

---

# Nuvio personal Phase 16 — experimental cumulative overlay

Pinned upstream: `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb` (1.1.0-beta.3). Includes Phases 1–15. Apply to a clean pinned checkout only. No compiled IPA.

## Phase 16: optional reusable range transport

- The prior single-entry cache is now connected to a seekable reader with partial hits, a 1 MiB rolling read chunk and exact conditional range validation. Each HTTP response must be 206, contain the requested range, match the same strong ETag and total length, and be uncompressed. Invalid or changed responses fail the read rather than combining media from different versions. Cancellation invalidates in-flight reads; EOF and invalid seeks are distinct.
- Bounded URLSession transport: one speculative 1 MiB range, at most 10 seconds per request, ephemeral session, no redirects, cookies, stored credentials or cellular use. No persistent media storage. Normal upstream playback remains the default. Only direct HTTPS URLs with a recognized file extension, no query/userinfo/fragment or non-default port, no request/proxy headers, no server/torrent/debrid selection, no separate audio or external startup subtitles, and no resume offset qualify. URLs are kept in memory; no URL logging is added. Hostname restrictions are not a DNS/IP sandbox. Use only authorized test media. The speculative read starts after next-episode automatic selection, during the existing three-second countdown, not during earlier source search. It requires preload enabled, a current controller, and either completed playback or at least 15 seconds of buffer ahead. Low Power Mode and background use are excluded. A completed exact-URL/profile cache slot is consumed once, otherwise normal playback proceeds and the speculative request is cancelled. Before serving cached bytes the reader performs a one-byte conditional revalidation request. Profile and resource identity are in-memory only.
- MPV custom read/seek/size/cancel/close callback adapter, registered as `nuviorange://` with an opaque one-use token. It is behind the **disabled-by-default** Swift active compilation condition `PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT`. On immediate load-command rejection the normal URL is used. Async errors use the existing recovery/error handling; manual retry can substitute the original URL if MPV still reports the custom path. Automatic native fallback after every possible asynchronous failure is not established. The callback code requires the bundled Libmpv module to expose `stream_cb.h`; its C interop has NOT been compiled on iOS. The flag should remain OFF in a normal build. Transport creates a new URLSession per range; throughput, timeouts and energy may be worse than stock MPV. This is a prototype, not a production performance improvement.
- 45 additional standalone Swift assertions (30 reader, 15 HTTP request/guards). Cumulative suite: 584 assertions; synthetic patch checks passed. The HTTP request construction and state checks use fixtures, not a live server; no actual iOS app build, network-streaming benchmark, or MPV callback ABI validation was performed. Source checkout cloning remains blocked in the container. No GitHub changes were pushed.

## Integration and testing

1. Run `bash validate_checkout.sh /path/to/clean/NuvioMobile` on a host with the pinned checkout and Swift/Kotlin tools. Build with the original compatible Xcode setup, **without** the experimental flag. Test all prior features first, including Phase 15 crop, against authorized media on a separate LiveContainer installation.
2. For a separate experimental debug target only, verify the bundled Libmpv module imports `stream_cb.h` and the supported callback signatures; add `PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT` to Swift Active Compilation Conditions. Compile and resolve any C interop errors before installation. Do not enable the flag in the stable build.
3. Test with an authorized direct HTTPS MP4 or MKV server that supports exact byte ranges and strong ETags. Enable preload and automatic next episode selection. Verify a successful first-range fetch during countdown, one-byte conditional revalidation, cached prefix consumption and seek/read across the boundary. Then test no range support, weak/changed ETag, compressed response, wrong range, redirect, cancellation, no completed prefetch, differing profile and URL, memory warning, background/Low Power Mode, retry and normal direct playback. Server-side request logs and a debug build can confirm actual cache consumption. Compare equivalent startup timings and network/CPU use against stock playback; do not infer gains from standalone tests.

No volume changes, spoiler protection or discovery changes. Earlier README sections below are historical; use Phase 16 for the latest overlay.

---

# Nuvio personal Phase 15 — experimental cumulative source overlay

Pinned Nuvio 1.1.0-beta.3 commit `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb`. Apply only to a clean checkout with `bash validate_checkout.sh /path/to/NuvioMobile` on a suitable build host. Previous phases are retained. No IPA is included.

## New work

* Optional encoded letterbox detection in existing Smart fill mode. Asynchronous MPV `screenshot-raw video bgr0` samples decoded frame bytes on the native event queue (no screenshot is saved), checks symmetry/brightness and requires three matching samples at least five seconds apart. Crop is conservative with margins and uses `options/video-crop` (video-output stage), rather than inserting software filters or changing the hardware decoder. Max six attempts per detection window; raw capture restricted to square-pixel HD frames up to 1920x1080, foreground stable playback and normal power mode. One outstanding request at a time. Stale replies ignored after seek, reload, mode or source change. Existing smart fill remains fallback. This is experimental: varying-aspect films can change after the initial detection; disable Smart fill if picture content is cropped. Raw-frame API and crop option compatibility are not yet confirmed on iOS. Some files/HDR outputs will not qualify.
* Standalone, thread-safe `native/PersonalPrefetchCache.swift` provides a single bounded 4 MiB reusable range entry, 90-second lifetime, profile + opaque resource identity + strong ETag + content-length checking, exact HTTP 206 response validation, partial hits, explicit clearing. Tested with synthetic bytes; the cache is not linked into the Nuvio player or sending HTTP requests. The future MPV range transport must obtain explicit authorized-resource identity and fresh validator, handle cancellation, authentication, normal-URL fallback and consume cached bytes. No claim of completed video prebuffering.
* 54 new standalone checks (27 encoded-bar, 27 range cache). Full regression suite 539 assertions, synthetic cumulative patch application and archive integrity. Prior tests rerun; no Xcode/device build. Integration of the new Swift C API bridge needs actual toolchain verification. A real media transport and LiveContainer testing are the final outstanding work. No volume, spoiler protection or discovery changes.

## Device checks to prioritize

- Enable Smart fill on a known HD letterboxed authorized video and on a normal full-frame video; verify crop only after stable detection. Test a dark scene, manual seek, rapid source changes, PiP, HDR and a variable-aspect film. Disable Smart fill and verify the original display is restored. Test iOS Low Power Mode and 4K fallback. Capture startup and energy baselines.
- Build the pinned checkout using the original compatible Xcode workflow after running `validate_checkout.sh`. All overlay checks are source-level and cannot substitute for full iOS compilation and testing.

The earlier Phase 14 notes below are historical; use Phase 15 files and scripts for this release.

---

# Nuvio personal Phase 14 — release candidate source overlay (not a compiled IPA)

Pinned upstream commit: `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb` (Nuvio 1.1.0-beta.3). Includes all Phase 1–13 changes.

## Changes

- Handover confirmation: save/pause using the existing progress path, then make at most three read-only checks (eight-second total deadline) through the existing Nuvio sync adapter. Require exactly the same content/video/season/episode, position and duration and a timestamp no earlier than the request. Profile/source changes invalidate the check; source changes cancel pending verification. Local, unsupported, offline, completed or unconfirmed checkpoints must not be represented as cloud-confirmed. This confirms server readback, not receipt by another device. Third-party progress providers do not receive these additional readback queries. No new account or remote services.
- Low Power Mode: when the existing native cache option is supported and originally disabled, only enable MPV's `demuxer-hysteresis-secs` after 60 seconds of stable foreground remote playback with 30 seconds or more ahead. Read-ahead can then resume in chunks once 15 seconds are left. Reset to the original value on instability, low cache, pause, seek, source changes, or leaving Low Power Mode. Preserve nonzero existing settings; skip unsupported options. If a runtime restore fails it is retried when loading the next file. No change to forward cache capacity or volume. Benefits require on-device measurement.
- Added `validate_checkout.sh`: checks the exact pinned Git revision and clean worktree, dry-runs the overlay, runs host regression tests, applies the overlay and runs `git diff --check`. This is not an Xcode compile.
- Checked the new independent upstream anchors against retrieved source; narrowed a duplicate source-reset anchor to its unique context. Fixed a low-power timing edge case discovered by regression testing.

## Validation

485 standalone assertions passed (444 prior + 19 handover readback + 22 low-power buffering), along with the synthetic cumulative patch checks. All previous assertions rerun. Full application build, native API compatibility, LiveContainer, and real sync delivery are unverified. The container has Linux Swift/Kotlin but not Xcode, and GitHub clone is blocked by DNS. The upstream connector is read-only. See `VALIDATION.txt`.

## Remaining work before calling this a finished release

1. True next-episode byte prebuffer: existing adaptive source preparation is implemented, but MPV's ordinary cache is tied to its engine instance. Upstream replaces the player at an episode identity change. Its playlist prefetch only opens the next URL when the current URL is fully read; enabling it here would not make bytes reusable. A future reusable direct-file range transport must be bounded, cancellable, validate HTTP range/strong ETag and media identity, avoid credential leakage, handle seeking and normal-URL fallback, and respect authorized downloads. Do not claim this feature is implemented.
2. Encoded black-bar detection: existing optional small aspect-ratio crop remains. Frame analysis/filtering needs native testing to ensure hardware decoding and HDR remain intact. No untested cropdetect filter is enabled.
3. Build and verify on iPhone. No measured improvements or compiled IPA provided.

No volume or audio amplification changes, no spoiler protection, no discovery/recommendation changes.

## Build and device test sequence

On a compatible macOS runner, use a clean pinned checkout:

```sh
git clone https://github.com/NuvioMedia/NuvioMobile.git
cd NuvioMobile
git checkout bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
git switch -c personal-playback-v14
bash /path/to/Nuvio_Phase14/validate_checkout.sh .
```

Use the original/configurable Test IPA workflow and compatible Xcode. Verify on the iPhone 16e with authorized media:

- Startup from zero and a saved position; verify seek fallback and resume accuracy.
- Same-file recovery during repeated stalls; verify no source switch when manually selected or when file fingerprint differs.
- Source switching, audio/subtitle carry-over, subtitle replay and manual subtitle changes.
- Next-episode selection, downloads, recap/intro skip, pause/seek and sleep timer.
- Smart fill with portrait/landscape and PiP, without altering manual resize or HDR.
- Same-profile cloud handover while online, offline, with a second device, during profile changes, and while using a non-Nuvio progress source.
- Low Power Mode on/off, stable/unstable network, high bitrate and seeking; compare startup and completed stalls using diagnostics against original app. Record thermal and energy metrics. Verify runtime cache option availability and correct restoration.
- Rapid player teardown, memory warnings, background/foreground and PiP.

Earlier README sections below are historical, not independent install steps.

---

# Nuvio personal Phase 13 — combined playback feature release (experimental source)

Pinned upstream commit: `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb` (verified commit, upstream 1.1.0-beta.3). This package replaces Phase 12 and includes all prior source changes.

## Six areas changed in this pass

- **Smart fill:** opt-in in Stream Info when the original resize mode is Fit. For valid landscape display dimensions, use the existing MPV panscan mode only when fitting to the screen removes between 0.5% and 10% of one dimension. Otherwise Fit is retained. Manual resize disables the mode; PiP and synchronized watch parties do not use it. No computer-vision detection of black bars baked into a video. No persistent resize setting change, no extra filter/decoder. The existing native state refresh evaluates dimensions at most once a second while enabled.
- **Cross-device handover:** the new Save progress and pause action takes a validated current-source snapshot, pauses locally, requests the existing profile's playback progress flush and remote sync, and flushes the local history ledger. It is disabled during opening, seeks, recovery, autoplay transition, party playback, and invalid progress. The recipient needs the same synced profile and existing sync support. Remote sync acknowledgement and remote device launch are not implemented.
- **Subtitle sync:** tie the existing upstream speech-based AutoSync callback and candidate subscription to the active controller, source URL and playback key; ignore stale callbacks and explicitly disabled subtitles. Existing upstream alignment algorithm and settings are unchanged.
- **Native retry:** pass the current position to the existing per-file MPV resume hint. If necessary, issue one bounded verification seek after the same media is open and has been ready for 750 ms, rather than a blind delayed seek at 500 ms. Cancel on manual seek/new media/destroy, reject stale generation/path and expire after 30 seconds. Existing ordinary load fallback is retained. This does not guarantee faster recovery; it depends on the native engine and source.
- **Memory pressure:** on iOS memory warning, request a cap of 16 MiB on the native *backward* demuxer cache only if its current limit exceeds that value. Do not increase limits or shrink the forward buffer. If unsupported the request may have no effect. The cap stays for that player instance and may make rewinding less immediate.
- **Native teardown:** detach the libmpv wakeup callback, drain the existing serial event queue before freeing the handle, and guard queued file-loaded/restart UI callbacks. This addresses a potential use-after-free during rapid switching/disposal; the native threading change must be exercised on a device, including repeated disposal and background transitions.

## Validation and remaining limits

- 57 new standalone assertions (22 Kotlin handover, 35 Swift convenience); 444 total (308 Kotlin, 136 Swift), all rerun successfully. Synthetic cumulative patch dry-run, application, marker and feature-anchor assertions passed. Independent new upstream anchors verified against retrieved pinned source. Derived patch anchors verified via synthetic fixture, not a full upstream checkout. No full application build or LiveContainer test, no measured speed or memory gains.
- `tests/run_all.sh` runs the complete standalone regression suite with `kotlinc`, Java, Swift and Python 3. Build toolchain is still external (Xcode/macOS). Direct GitHub clone from this Linux container failed DNS; upstream was inspected via read-only GitHub connector. The overlay is not an IPA.
- Still outstanding: actual next-episode video-byte prebuffering that is consumed by the next player instance, encoded-black-bar detection, verified cross-device sync delivery, measured iOS performance and full native/Compose build validation. No new provider integrations, no changes to volume/audio processing, no discovery/recommendation changes, no spoiler-protection additions. Existing upstream features are retained.

## Apply

Use a clean pinned checkout, not any previously patched copy.

```sh
git clone https://github.com/NuvioMedia/NuvioMobile.git
cd NuvioMobile
git checkout bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
git switch -c personal-playback-v13
python3 /path/to/Nuvio_Phase13/apply.py . --dry-run
python3 /path/to/Nuvio_Phase13/apply.py .
git diff --check
```

Use the configurable Build Test IPA workflow on a compatible macOS/Xcode runner. On-device check with authorized media: start/retry at beginning and middle, seek during retry, rapidly switch and close videos, test native PiP and foreground/background, compare Fit/Smart fill in different display ratios, test explicit subtitle disable and source switch during AutoSync, induce memory warnings using development tooling and verify normal playback/rewind, and verify handover progress on a second device with the same synced profile. Earlier README sections below are historical and should not be applied individually.

---

# Nuvio personal Phase 12 — cumulative experimental source overlay

Pinned upstream reference: `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb`.

## Phase 12: recap and next-episode reliability

- Retain upstream configurable intro/recap/outro skipping. Reject automatic seeks that would go backwards or outside a known duration, suppress repeated attempts for substantially overlapping same-category intervals (at least half the longer interval), and respect dismissals/manual skips for that playback item. Require an active, ready snapshot for automatic skipping. This does not infer recap timestamps from speech or video.
- Read chapters only after the active source is open; discard stale chapter results when playback identity changes.
- Track the preloaded next episode by video ID, season and episode, resetting the marker if the next selection changes. Avoid background source lookups while the episode selector or autoplay search is active, and skip remote source preparation if the next episode has a playable download. The existing repository owns its actual search coroutine; resetting the local marker is not a guarantee of immediate cancellation of all shared requests.
- Actual next-episode video-byte prebuffering, automatic cropping, cross-device handover and full native integration remain outstanding. Spoiler protection, discovery changes and volume adjustments are excluded.
- 35 new Kotlin assertions passed. All 352 previous standalone assertions rerun successfully (387 total). Synthetic patch application checks passed; all ten new anchors checked for unique occurrence against retrieved upstream files. No full app build, IPA, or LiveContainer test was performed; device performance improvements remain unmeasured.

## Apply Phase 12

Use a clean upstream checkout, not an earlier patched copy.

```sh
git clone https://github.com/NuvioMedia/NuvioMobile.git
cd NuvioMobile
git checkout bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
git switch -c personal-playback-v12
python3 /path/to/Nuvio_Phase12/apply.py . --dry-run
python3 /path/to/Nuvio_Phase12/apply.py .
git diff --check
```

Run the upstream configurable IPA workflow on a compatible Xcode runner. Earlier sections are historical. Test new behavior with authorized media: manually dismiss recap, seek into an already skipped segment, refresh overlapping chapter/API intervals, switch source while chapters load, change next episode selection, open episode panel, and play a series with the next episode downloaded. Confirm existing manual skip remains usable and normal autoplay proceeds. Test the full native build before relying on it.

## New tests

```sh
P=overlay/composeApp/src/commonMain/kotlin/com/nuvio/app/features/player
kotlinc "$P/PersonalSkipPolicy.kt" tests/PersonalSkipPolicyTest.kt -include-runtime -d /tmp/nuvio12-skip.jar
java -jar /tmp/nuvio12-skip.jar
python3 tests/test_apply.py
```

---

# Nuvio personal Phase 11 — cumulative experimental source overlay

Pinned upstream: `NuvioMedia/NuvioMobile` commit `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb`.

## Phase 11: native event processing and startup responsiveness

- Coalesce consecutive libmpv property events on the existing serial event queue, dispatching the highest required refresh for the batch (subtitle only, lightweight playback and subtitle refresh, or full state and track refresh). Flush before every non-property event, when the drain ends, or at 64 notifications. Unknown property names conservatively require full refresh. No new polling, no changed audio gain or volume, and no changes to error or lifecycle event handling. The batching retains the latest state rather than rendering every intermediate property transition; verify subtitle responsiveness and track changes on-device.
- Attempt a pending media load immediately after externally managed video-surface layout, rather than waiting for the next 50 ms scheduled retry. Preserve original viewport validity and portrait grace period. This does not bypass GPU surface readiness or guarantee a specific startup improvement.
- No new spoiler protection: user removed it from development scope. Existing upstream spoiler features remain untouched. Discovery/recommendations and all volume/audio-processing changes remain excluded. Genuine video-byte prebuffering is not implemented; the existing early source-list preparation remains in place. No new provider integrations.
- 24 new isolated Swift assertions passed; all prior 328 passed again (352 total, 251 Kotlin and 101 Swift). Synthetic cumulative patch dry-run/application/repeat guard passed. The native patch is based on the pinned source inspected through GitHub; a full checkout is not available in this environment (GitHub DNS failed). No full app compilation, IPA or measured performance improvement is claimed.

## Apply Phase 11

Use a clean pinned checkout, not one already patched by any earlier phase.

```sh
git clone https://github.com/NuvioMedia/NuvioMobile.git
cd NuvioMobile
git checkout bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
git switch -c personal-playback-v11
python3 /path/to/Nuvio_Phase11/apply.py . --dry-run
python3 /path/to/Nuvio_Phase11/apply.py .
git diff --check
```

Use the configurable Build Test IPA workflow on a compatible Xcode runner. Full iOS compilation and LiveContainer validation remain outstanding. Earlier README sections below are historical. To rerun tests, use the Phase 9 and 10 commands and additionally:

```sh
cat native/PersonalNativeEventBatch.swift tests/PersonalNativeEventBatchTest.swift >/tmp/nuvio11-batch.swift
swift /tmp/nuvio11-batch.swift
python3 tests/test_apply.py
```

Device checks with authorized media: test rapid pause/seek, track switching, subtitle changes, buffering, background/foreground, rotation and quick episode changes; confirm lifecycle/error handling and track/subtitle updates. Compare startup latency and main-thread CPU using the same media on the baseline and experimental build. No volume settings should change. Next-episode video prebuffering requires a reusable media cache across player instances rather than merely fetching bytes that the next MPV instance will not consume.

---

# Nuvio personal Phase 10 — cumulative experimental source overlay

Pinned upstream: `NuvioMedia/NuvioMobile` commit `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb`.

## Phase 10: native resume startup

- Pass the existing absolute initial resume position through the iOS Kotlin/Swift bridge into the queued MPV load request. For 1 second to 24 hours inclusive, use the file-local `start` option on `loadfile` (documented mpv 0.38+ argument layout); keep ordinary loading for other offsets. If the option command fails synchronously, retry the original load command. No global start option persists across media items. Fraction-only resume continues to use the existing duration-aware seek. The common runtime still checks the actual position and performs its existing bounded seek if necessary; wait for a non-opening snapshot of the active source before that iOS verification. Native hint suppressed for synchronized parties and when the initial seek is already applied. The original `command` wrapper retains its Void signature.
- This is a best-effort native startup optimisation, not a guarantee of instant playback. The provider, container, MPV seek behaviour and installed library version determine actual performance. A successfully accepted load option can still be ignored by the engine, or a later media open can fail; the existing player recovery/error handling remains. No video-byte prebuffering implemented: reusable media cache and lifecycle support need full integration testing first. No volume or discovery changes.
- 17 new pure Swift assertions passed, all 311 previous assertions rerun successfully (328 total: 251 Kotlin, 77 Swift). Synthetic overlay application passed; all 13 new anchor occurrences checked individually against the pinned upstream. These are isolated tests and anchor checks, not a full build or on-device validation.

## Apply Phase 10

Use a clean pinned checkout, not one already patched by an earlier phase.

```sh
git clone https://github.com/NuvioMedia/NuvioMobile.git
cd NuvioMobile
git checkout bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
git switch -c personal-playback-v10
python3 /path/to/Nuvio_Phase10/apply.py . --dry-run
python3 /path/to/Nuvio_Phase10/apply.py .
git diff --check
```

Use the configurable Build Test IPA workflow on a compatible Xcode runner. Full Xcode/Kotlin Native compilation and LiveContainer validation remain outstanding. To rerun earlier tests, see the Phase 9 commands below; additionally run:

```sh
cat native/PersonalNativeResumePolicy.swift tests/PersonalNativeResumePolicyTest.swift >/tmp/nuvio10-resume.swift
swift /tmp/nuvio10-resume.swift
python3 tests/test_apply.py
```

Device checks (authorized media): compare cold start at 0 and saved positions, source recovery and episode changes, very short/near-end offsets, unknown duration, HLS/nonseekable sources, failed load options, party playback and reloading with changed headers. Measure time until first correct video frame at resume position, rather than just first loading event. Confirm no wrong episode, incorrect position, or accidental playback completion. The original Nuvio source is read-only here and Xcode is unavailable. Older README sections are historical.

Reference: https://mpv.io/manual/stable/ (loadfile, start and per-file options).

---

# Nuvio personal Phase 9 — cumulative experimental source overlay

Pinned upstream: `NuvioMedia/NuvioMobile` commit `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb`.

## New in Phase 9

- Subtitle synchronization reliability: tie asynchronous cue requests to the playback identity and selected subtitle ID/URL, discard outdated results, avoid redundant non-forced downloads, preserve cancellation, snapshot request headers before launching, and prevent a late computed media hash from being written against a different current source. Cue capture requires a current nonloading playback snapshot; applying a cue requires it to be present in the current selection's cue list. Clamp subtitle delay in Long arithmetic before conversion to Int. Generic existing localized loading error replaces raw exception text. These changes improve the existing manual cue-based sync workflow, not automatic speech alignment or drift correction.
- Resume optimization: skip the initial seek only if the current playback key owns the snapshot, position is nonzero, and the bounded target is already within 250 ms. Otherwise retain the existing bounded seek path. This avoids redundant seeks in some resume/recovery scenarios; no native start-time load change, new homepage entry point or measured speed gain is claimed.
- 35 new Kotlin assertions passed. All prior 276 assertions rerun successfully (311 total: 251 Kotlin and 60 Swift). Synthetic cumulative patch application passed, and all 13 new upstream anchors plus the original resume anchor were inspected against the pinned source (each unique). No full Kotlin/Native/Swift app integration build or device test has been performed.
- No volume adjustment, discovery/recommendation, or new provider changes. Actual video-byte prebuffering remains outstanding.

## Apply Phase 9

Use a clean pinned checkout, not a checkout already patched by a prior phase:

```sh
git clone https://github.com/NuvioMedia/NuvioMobile.git
cd NuvioMobile
git checkout bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
git switch -c personal-playback-v9
python3 /path/to/Nuvio_Phase9/apply.py . --dry-run
python3 /path/to/Nuvio_Phase9/apply.py .
git diff --check
```

Use the configurable Build Test IPA workflow on a compatible macOS/Xcode runner. Verify baseline and experimental builds separately in LiveContainer. Upstream repository access is read-only here and no Xcode environment is available. Earlier sections are historical; their instructions and status reflect their own phase.

## Phase 9 test commands

```sh
P=overlay/composeApp/src/commonMain/kotlin/com/nuvio/app/features/player
kotlinc "$P/RecoveryPolicy.kt" "$P/PlaybackFeaturePolicy.kt" "$P/PlaybackDiagnostics.kt" "$P/PlaybackPreparationPolicy.kt" "$P/PersonalPlaybackSelection.kt" "$P/PersonalHistoryLedger.kt" "$P/PersonalSubtitleSyncPolicy.kt" tests/*.kt -include-runtime -d /tmp/nuvio9-all.jar
for t in RecoveryPolicyTest FeaturePolicyTest DiagnosticsTest PreparationPolicyTest DiagnosticSummaryTest ReliabilityPersistenceTest PersonalPlaybackSelectionTest PersonalHistoryLedgerTest PersonalSubtitleSyncPolicyTest; do
  java -cp /tmp/nuvio9-all.jar com.nuvio.app.features.player.${t}Kt || exit 1
done
cat native/AdaptiveCachePolicy.swift tests/AdaptiveCachePolicyTest.swift >/tmp/nuvio9-cache.swift
swift /tmp/nuvio9-cache.swift
cat native/PersonalNativePlaybackPolicy.swift tests/PersonalNativePlaybackPolicyTest.swift >/tmp/nuvio9-native.swift
swift /tmp/nuvio9-native.swift
python3 tests/test_apply.py
```

Device checks: with authorized test media, switch subtitles, sources and episodes during cue requests, force reload twice, toggle subtitles off, test offline and cancelled downloads, and verify capture/selection while seeking or buffering. Compare resume with target at 0, near current position, different position, unknown duration, and stale callbacks. Confirm existing automatic and manual subtitle workflows, volume, and discovery remain unchanged.

---

# Nuvio personal Phase 8 (cumulative experimental overlay)

New in Phase 8 (native iOS correctness and resource improvements):

- Corrected a confirmed upstream buffer-accounting bug: MPV `demuxer-cache-time` is an absolute buffered timestamp, not seconds of cache ahead. The original bridge added current position again. For example, at 1,800 s with cache end 1,820 s, it reported 3,620 s rather than 1,820 s; the actual estimate of buffer ahead is 20 s. The corrected native estimator avoids false headroom in the earlier preparation logic and diagnostics, bounds the estimate to known duration without reporting behind current position, and handles missing/invalid cache data conservatively. MPV's cache timestamp is still an estimate, not a guarantee of seekable data. See https://mpv.io/manual/stable/ (`demuxer-cache-time`).
- Reduced native event-path work: pause, cache pause, idle, end and seek property changes update playback state and styled subtitle output without repeatedly enumerating all audio/subtitle tracks. Track-list, aid, sid, unknown events, file loaded and playback restart retain full refresh. Actual CPU/battery/startup gains are not measured.
- Guarded conversion of native duration, position, cache and speed values against non-finite/overflow inputs; corrected MPV_FORMAT_FLAG scalar representation to 32-bit C int; nonnegative track count protects range iteration. Clear cached playback positions and track lists at a new file load to reduce stale cross-source state.
- 33 new pure Swift assertions passed. All prior 216 Kotlin and 27 Swift assertions rerun successfully (276 total including new). Cumulative synthetic overlay application and repeat guard passed. Upstream native anchor inspection performed at the pinned commit. Full app compilation, IPA packaging, and device validation remain outstanding. These changes do not yet implement instant native resume, actual video-byte prebuffering or automatic subtitle synchronization. No changes to volume or discovery.

Apply to a clean checkout of pinned commit `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb`. Use the Phase 8 directory and branch in the prior instructions. Test with authorized media. For the new tests:

```sh
cat native/PersonalNativePlaybackPolicy.swift tests/PersonalNativePlaybackPolicyTest.swift > /tmp/nuvio8-native.swift
swift /tmp/nuvio8-native.swift
python3 tests/test_apply.py
```

Device verification: compare buffer headroom early and late in the same file, test local/remote/unknown-duration media, pause/resume, subtitle and audio track changes, seeks, rebuffering, source/episode changes and invalid timeline metadata. Profile native event CPU and thermal behavior before/after; compare startup, stall counts, and next-episode source preparation against Phase 7. No measured improvement is claimed.

# Nuvio personal Phase 7 (cumulative experimental overlay)

New in Phase 7:

- Persistent local viewing history for each profile and media ID (up to 100 recent items), recording estimated media milliseconds played and distinct player sessions, including rewatches. Only accepted continuous playback movement contributes. Periodic checkpoints every 30 seconds, flush on media change and player/source disposal. No raw stream URLs, headers or credentials are intentionally recorded; media identifiers are reversible hex-encoded local data, not anonymous or encrypted. URL-like IDs are excluded. No new sync service, homepage changes, or discovery functionality. The per-item totals and session count appear in existing Stream Info diagnostics. The existing upstream watch progress remains the resume authority. Abrupt termination can lose the most recent checkpoint interval, and session counts refer to player sessions rather than completed viewings. Android storage is a no-op, as this feature targets iOS.
- Optional sleep timer in Stream Info (15/30/60 minutes or Off). Uses a monotonic elapsed-time deadline and the existing player pause action. Never changes volume. Cancels for synced party playback, does not consume the deadline while a replacement controller is attaching. The timer is scoped to the current player runtime, and may expire on the next available playback callback if suspended or backgrounded. Not sleep detection or a guaranteed background alarm.
- 41 new standalone Kotlin assertions passed for persisted history, malformed records, ID validation, bounds, session accumulation, timer duration, replacement and cancellation. Cumulative synthetic overlay application and repeat guard passed. The previous 202 assertions were reported in Phase 6, not rerun as part of this pass. Full Xcode compilation and LiveContainer testing are still outstanding.

Apply to a clean checkout of the pinned upstream commit. Use the commands below with the Phase 7 folder and branch name; do not layer on an already patched checkout. Test with authorized media. No volume adjustments or discovery changes.

# Nuvio personal playback — Phase 6 (experimental cumulative source overlay)

Pinned upstream: NuvioMedia/NuvioMobile commit `bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb`.
Apply to a clean checkout of that exact commit, not over earlier overlays. No discovery/recommendation changes. **No volume adjustments, amplification, volume leveling, dialogue enhancement or changes to existing audio controls.** Track selection/restoration is distinct from volume processing.

## New in Phase 6

- **Conservative initial source ranking on iOS:** only when the existing automatic fallback preference is enabled and the selection mode is regex matching, with no saved/preferred binge group, and the same profile is still active. It works after upstream eligibility filters, only on a list of direct URLs (no server targets, P2P or client-resolver candidates). Both the original first candidate and a promoted provider must have at least three nonexpired observations; the promoted candidate must exceed the original score by at least 0.15. Ties preserve original order, and all nonpromoted candidates retain relative order. No extra network queries, no changes to manual mode, FIRST_STREAM or discovery. A ranking change is not proof of faster startup. Initial source selection still uses the upstream search/settling schedule.
- **English audio metadata verification:** when explicitly configured to prefer English, after upstream audio selection has settled and stored selection restoration has run, inspect actual engine track metadata. If the selected track is not identified as English and a tagged, non-commentary/non-description English track exists, request that track once per controller/playback key. Skip party playback, server audio tracks, explicit/persisted choices, pending engine carry-over and loading. Do not change volume, mute, gain, saved preferences or source. Stream Info reports whether the selected track is tagged English, other, unknown or missing. This does not analyze spoken dialogue; inaccurate metadata remains possible. Manual choices remain authoritative.
- **Session playback history foundation:** the Stream Info diagnostics also display estimated media time actually played in the current item/session, rather than assuming the current timestamp represents watched time. Counts plausible forward movement between close snapshots, accounts for playback speed, excludes loading, pauses, recent seeks and source transition gaps. No persisted history yet; replays may count again, so the number is not unique coverage. No titles, media IDs or viewing histories are newly stored on disk.

### Phase 6 validation and next checks

56 new pure Kotlin assertions passed (source promotion guardrails, metadata language handling, correction candidate selection, seek-resistant session history and expired score observations). All 119 previous Kotlin assertions and 27 previous pure Swift assertions also passed: 202 total. Synthetic cumulative overlay dry-run/application/repeat guard passed. The new upstream anchors in StreamsRepository, PlayerScreenRuntimeTrackActions, and the Phase 4 underlying anchors in PlayerScreenRuntimeUi and StreamInfoOverlay were checked against the pinned upstream files (each occurred exactly once). No complete upstream checkout, full Kotlin/Native/Swift app compilation, IPA or on-device performance validation is available here.

```sh
P=overlay/composeApp/src/commonMain/kotlin/com/nuvio/app/features/player
kotlinc "$P/RecoveryPolicy.kt" "$P/PlaybackFeaturePolicy.kt" "$P/PlaybackDiagnostics.kt" "$P/PlaybackPreparationPolicy.kt" "$P/PersonalPlaybackSelection.kt" tests/*.kt -include-runtime -d /tmp/nuvio-p6-all.jar
for t in RecoveryPolicyTest FeaturePolicyTest DiagnosticsTest PreparationPolicyTest DiagnosticSummaryTest ReliabilityPersistenceTest PersonalPlaybackSelectionTest; do
  java -cp /tmp/nuvio-p6-all.jar com.nuvio.app.features.player.${t}Kt || exit 1
done
cat native/AdaptiveCachePolicy.swift tests/AdaptiveCachePolicyTest.swift > /tmp/nuvio-p6-cache.swift
swift /tmp/nuvio-p6-cache.swift
python3 tests/test_apply.py
```

Device checks: test regex auto-selection with sufficient evidence, expired scores, equal scores, manual/first-stream mode and preferred binge group. Compare real startup times. Test known English, unknown, other languages, multiple English tracks, commentary, deliberate manual override, stored preference, late tracks, server/party mode and source transitions. Confirm the English diagnostic follows actual reported selected track. Verify session media time across seeks, pauses, speeds, replay and source/episode changes. Actual startup acceleration, persisted item history, video-byte prebuffering and other outstanding Phase 5 goals remain future development; no performance gain is claimed.

## New in Phase 5

- **Persistent source reliability on iOS:** the existing bounded reliability estimator now loads/saves up to 32 provider observations via profile-specific NSUserDefaults keys. Entries expire 14 days after the last observation and are ignored on clock rollback. Invalid, oversized or future-dated records are discarded. It stores a deterministic 64-bit provider pseudonym, bounded counts and observation timestamp, not raw IDs, URLs, titles, headers or credentials. The pseudonym is not cryptographic anonymity. Observations remain limited to the earlier recovery system and accepted startup snapshots; scoring still only ranks upstream-eligible matching-file midstream replacement candidates. No additional provider queries or initial source selection changes. Persistence failures leave in-memory scoring usable; no iOS persistence on Android. Separate simultaneous runtimes can overwrite a profile's last snapshot; no cross-device synchronization.
- **Adaptive native MPV rebuffering:** for remote HTTP(S) VOD, use the existing MPV polling path to detect repeated cache-driven stalls of at least one second, after at least three seconds of stable playback. On the second qualifying stall within 90 seconds, increase `options/cache-pause-wait` by one second from its original value; on another qualifying stall, increase by up to one more second, capped at three seconds. After 90 seconds of uninterrupted playback, return to the baseline. The first startup and isolated stalls retain upstream thresholds. Guard known-duration playback, near-end, seeking, pausing, foreground state, local media and loopback. Restore baseline when loading a new source or retrying; if runtime option changes are rejected, disable this policy for that load. This controls the rebuffer resume threshold, not the number of cached bytes, quality or next-episode video prebuffering. It may trade a longer individual stall for fewer repeated interruptions and requires actual MPV/device verification. No cache-size increase, volume processing or additional polling.
- **Native source transition race guards:** delayed external audio-track attachment and retry seeking now check a load-generation counter and live MPV pointer. This prevents those callbacks from targeting a subsequently queued source or retry. No gain/volume changes. The existing time-based scheduling itself is not redesigned.

MPV option reference: https://mpv.io/manual/stable/ (cache-pause-wait and cache-secs).

### Phase 5 local tests

```sh
P=overlay/composeApp/src/commonMain/kotlin/com/nuvio/app/features/player
kotlinc "$P/RecoveryPolicy.kt" "$P/PlaybackFeaturePolicy.kt" "$P/PlaybackDiagnostics.kt" "$P/PlaybackPreparationPolicy.kt" tests/*.kt -include-runtime -d /tmp/nuvio-p5-all.jar
for t in RecoveryPolicyTest FeaturePolicyTest DiagnosticsTest PreparationPolicyTest DiagnosticSummaryTest ReliabilityPersistenceTest; do
  java -cp /tmp/nuvio-p5-all.jar com.nuvio.app.features.player.${t}Kt || exit 1
done
cat native/AdaptiveCachePolicy.swift tests/AdaptiveCachePolicyTest.swift > /tmp/nuvio-p5-cache.swift
swift /tmp/nuvio-p5-cache.swift
python3 tests/test_apply.py
```

119 standalone Kotlin assertions (including the 97 earlier ones), 27 standalone Swift policy assertions, and the synthetic cumulative overlay application test passed. The Swift tests compile the pure policy on Linux, not the UIKit/libmpv integration. The NSUserDefaults actual implementation and its runtime behavior have not been compiled or tested on iOS. Upstream files were inspected via the repository connector; checkout remains unavailable in the container (GitHub DNS failure). No IPA or measured speed gain is claimed.

### Phase 5 device checks

Test with authorized media and a controlled network: compare initial starts, isolated stalls, repeated stalls, pauses, seeks, source changes, local files, retries, background/PiP and recovery after 90 seconds. Check if the bundled libmpv accepts runtime cache-pause-wait changes, and whether stall count and total stall duration improve or worsen. Verify previous preferences, volume and normal playback are unchanged. Restart the player and app, verify provider scores survive per profile and expire; confirm invalid stored records fail open. Rapidly change sources during delayed audio attachment/retry to verify no stale callbacks reach the new item.

## Included from Phase 4

- Adaptive next-episode **source-list preparation** on iOS: existing opt-in preloading can begin 40–60 seconds ahead instead of 10–30 seconds when playback is progressing, at least 30 seconds into the current video, at least 20 seconds of buffer ahead is reported, and no recent measured stall occurred within 45 seconds. Early preparation is suppressed for party/background state, ongoing fallback/credential refresh, torrent playback, open episode panel and recent pending seeks. Otherwise the previous upstream lead is retained. The existing aired-episode/online checks remain. This is metadata/source search only, not video-byte buffering, second decoder initialization or a guaranteed faster transition. Corrects a missing-content-type case by falling back to parentMetaType, as the actual next-episode autoplay path already does.
- Stream Info diagnostics (iOS): current source startup time when measurable, completed stall count, accumulated completed stall milliseconds, estimated buffer ahead when known, and active stall state. Uses existing accepted playback snapshots; no new polling, network traffic or logging of URLs/credentials. Metrics reset per playback key and do not include interrupted stalls or pre-engine navigation time. English labels for the personal build.
- Resume guard: clamps initial seek to the known duration to avoid out-of-range requests when saved progress exceeds the current file duration. Retains upstream behavior when duration is unknown. Does not add a new one-tap resume entry point or change how cached source links are selected.

## Included from Phase 3

- Proactive iOS stall recovery: requires 15 seconds of uninterrupted loading snapshots at an unchanged playback position, prior startup completion, known duration and file fingerprint, enabled existing auto fallback, current player identity, and an automatically selected source. Excludes manual sources, offline conditions, pauses/seeks, party playback, background party state, near-end playback, credential refresh and torrents. At most one watchdog lookup per playback key; rechecks eligibility, buffering and position after async resolution. Only uses the existing configured eligible source search with matching declared 16-hex video hash and byte size; no new provider or credential setup. If nothing matches or the original playback resumes, a proactive lookup does not create an error screen or spend the existing fallback attempt budget. A real engine error remains visible if reported during a proactive lookup. The watchdog requires engine callbacks reporting loading; it cannot independently detect video-only freezing or a total loss of callbacks. The fingerprint is declared metadata, not independently verified cryptographic identity.
- Source reliability: bounded in-memory provider scoring, smoothed success/failure observations and decay. Scores rank only upstream-eligible matched-file replacement candidates for midstream iOS recovery; upstream ordering wins ties. Observes successful starts and attempted eligible fallback failures once per playback key. No extra probes; does not yet alter initial source selection. Phase 5 adds iOS persistence. No titles, URLs or credentials stored by this scorer.
- Best-effort track carry-over: reuses upstream engine-switch selection capture/restoration for matching-file replacements, targets the replacement identity, and waits for the new controller. Matching uses the existing language/label/forced-state logic, not raw old track indices. Explicit subtitle off state is supported. Exact selection, external subtitle synchronization and timing must be checked on the device; missing tracks fall back to existing behavior.
- Diagnostics: corrects the intentional-seek exclusion to use the existing seek timestamp instead of requiring the pending seek field to be null forever. Avoids new volume or media-processing changes.

## Included from Phase 2 and Phase 1

- Existing automatic source fallback extended to mid-playback errors for matching declared file fingerprints and sizes; preserves resume position and existing fallback limit.
- Replay 10s with subtitles: new action in subtitle menu; temporary non-forced embedded English track when subtitles were off, restored after reaching the original position. Does not change saved preferences. Existing selected subtitles are kept; external/server subtitle cases excluded; manual selection wins.
- Local privacy-conscious playback startup and rebuffer metrics; source/engine identity guards; configurable macOS runner and Xcode path.

## Apply and build

```sh
git clone https://github.com/NuvioMedia/NuvioMobile.git
cd NuvioMobile
git checkout bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
git switch -c personal-playback-v7
python3 /path/to/Nuvio_Phase7/apply.py . --dry-run
python3 /path/to/Nuvio_Phase7/apply.py .
git diff --check
git status --short
```

Use your own fork, enable GitHub Actions and run Build Test IPA in Debug configuration. Runner and Xcode path are configurable; compatibility and the upstream build prerequisites still require verification. The default runner is macos-latest, which may not meet upstream Xcode requirements. No credentials are included. Keep the existing working LiveContainer installation/data separate. Respect upstream GPL license obligations if distributing a modified build.

## Tests performed locally

```sh
P=overlay/composeApp/src/commonMain/kotlin/com/nuvio/app/features/player
kotlinc "$P/RecoveryPolicy.kt" tests/RecoveryPolicyTest.kt -include-runtime -d /tmp/nuvio-recovery.jar
java -jar /tmp/nuvio-recovery.jar
kotlinc "$P/PlaybackFeaturePolicy.kt" tests/FeaturePolicyTest.kt -include-runtime -d /tmp/nuvio-policy.jar
java -jar /tmp/nuvio-policy.jar
kotlinc "$P/PlaybackDiagnostics.kt" tests/DiagnosticsTest.kt -include-runtime -d /tmp/nuvio-diag.jar
java -jar /tmp/nuvio-diag.jar
python3 tests/test_apply.py
```

In Phase 4 all 97 standalone assertions passed: 21 preparation/resume, 11 diagnostics summary, 18 previous diagnostics, 26 recovery and 21 feature policy. Synthetic cumulative overlay dry-run/application/repeat guard passed. Run the two new test programs with:

```sh
kotlinc "$P/PlaybackPreparationPolicy.kt" tests/PreparationPolicyTest.kt -include-runtime -d /tmp/nuvio-preparation.jar
java -jar /tmp/nuvio-preparation.jar
kotlinc "$P/PlaybackDiagnostics.kt" tests/DiagnosticSummaryTest.kt -include-runtime -d /tmp/nuvio-summary.jar
java -jar /tmp/nuvio-summary.jar
``` The patches are based on the retrieved upstream source; a full clone was unavailable (network/DNS blocked in the build container), and the repository is read-only through the connector. Full application compilation, integration and LiveContainer device validation have not been performed. No IPA or measured performance gain is claimed.

## Device verification

1. Validate unmodified baseline build, then experimental build in a separate LiveContainer installation.
2. Use authorized test media: induce a long buffering interval with matching alternate file metadata, short stalls, resumed playback during lookup, user pause/seek, offline mode, manually selected source, party playback, different/missing fingerprints, real engine error during watchdog lookup, and source changes while lookup is pending. Verify no unexpected switching and no error screen for a failed proactive lookup; check attempt limits and position.
3. Test track restoration with reordered tracks, explicitly disabled subtitles, embedded and external subtitles, different languages, missing track and player/controller recreation. Verify no changed saved preferences or volume settings.
4. Replay subtitle action: near-start, seek failure, pause, manual selection, source change and catch-up behavior.
5. Compare at least ten comparable starts and induced stalls before claiming speed/reliability improvements.

## Phase 4 device checks

With authorized test content, compare next-episode search start times with existing preload enabled, varying buffer headroom and recent stalls. Verify no additional early lookup with preload disabled and no competing source search when recovery is active. Check ordinary and unknown-duration resumes, including saved positions past the file end. Open Stream Info on an iPhone before/after a stall and after switching source; verify the values and source reset. Compare episode transition timing and actual rebuffer impact rather than assuming the earlier lookup improves playback.

## Still outstanding

Full application integration/IPA/device test; iOS persistence validation and further initial source selection integration, further adaptive video-byte buffering, faster startup, one-tap instant resume, improved subtitle sync, next-episode video-byte prebuffering, spoiler protection, recap/content filtering, playback history, resource optimization, exportable diagnostics and cross-device handover. Discovery/recommendations deferred. Volume and audio-processing enhancements removed from scope.
