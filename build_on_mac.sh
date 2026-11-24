#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/output"
mkdir -p "$OUT"
PIN=bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
[[ $(uname -s) == Darwin ]]
WORK="$(mktemp -d "${TMPDIR:-/tmp}/nuvio-health.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
SRC="$WORK/NuvioMobile"
git init -q "$SRC"
git -C "$SRC" remote add origin https://github.com/NuvioMedia/NuvioMobile.git
git -C "$SRC" fetch --depth=1 origin "$PIN"
git -C "$SRC" checkout --detach FETCH_HEAD
[[ $(git -C "$SRC" rev-parse HEAD) == "$PIN" ]]
cd "$SRC"
touch local.properties
# Intentionally start from the upstream base of Hybrid v3, not Phase 17.
python3 - <<'PY'
from pathlib import Path
base=Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams')
screen=base/'StreamsScreen.kt'
s=screen.read_text()
def change(old,new):
 global s
 assert s.count(old)==1, old
 s=s.replace(old,new,1)
change('import androidx.compose.runtime.LaunchedEffect\n','''import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.snapshotFlow
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.collect
''')
change('    val filteredGroups = uiState.filteredGroups\n','''    val healthTargets = remember(uiState.groups) {
        uiState.groups.flatMap { it.streams }.mapNotNull { it.personalProbeTarget() }.distinctBy { it.url }
    }
    val latestHealthTargets by rememberUpdatedState(healthTargets)
    val healthBudget = remember(uiState.requestToken) { StreamProbeBudget() }
    var failedHealthUrls by remember(uiState.requestToken) { mutableStateOf(emptySet<String>()) }
    var firstHealthBatchDone by remember(uiState.requestToken) { mutableStateOf(false) }
    LaunchedEffect(uiState.requestToken) {
        snapshotFlow { latestHealthTargets }.collect { targets ->
            if (targets.isEmpty()) return@collect
            val known = targets.filter { PersonalStreamHealth.cached(it) == StreamHealthResult.MISSING }.map { it.url }.toSet()
            failedHealthUrls = known
            var pending = targets.filter { PersonalStreamHealth.cached(it) == null }
            while (true) {
                val batch = healthBudget.next(pending)
                if (batch.isEmpty()) break
                val results = coroutineScope { batch.map { target -> async { target.url to PersonalStreamHealth.probe(target) } }.awaitAll() }
                failedHealthUrls = failedHealthUrls + results.filter { it.second == StreamHealthResult.MISSING }.map { it.first }
                firstHealthBatchDone = true
                pending = pending.filterNot { candidate -> batch.any { it.url == candidate.url } }
            }
            firstHealthBatchDone = true
        }
    }
    val initialHealthWait = healthTargets.isNotEmpty() && !firstHealthBatchDone
    val failedGroups = uiState.filteredGroups.map { group ->
        group.copy(streams = group.streams.filter { it.personalProbeTarget()?.url in failedHealthUrls }, isLoading = false)
    }.filter { it.streams.isNotEmpty() }
    val filteredGroups = uiState.filteredGroups.map { group ->
        group.copy(streams = group.streams.filterNot { it.personalProbeTarget()?.url in failedHealthUrls })
    }
''')
change('    val hasAnyStreams = filteredGroups.any { it.streams.isNotEmpty() }\n','    val hasAnyStreams = filteredGroups.any { it.streams.isNotEmpty() } || failedGroups.isNotEmpty()\n')
change('        when {\n            hasGroups && anyLoading && !hasAnyStreams -> {','''        when {
            initialHealthWait -> {
                item { LoadingStateBlock(findingStreamsText = "Checking stream links…") }
            }
            hasGroups && anyLoading && !hasAnyStreams -> {''')
change('                item {\n                    Spacer(modifier = Modifier.height(nuvioSafeBottomPadding(80.dp)))\n                }','''                if (failedGroups.isNotEmpty()) {
                    item(key = "personal_failed_health_header") {
                        StreamSectionHeader(addonName = "Failed checks (HTTP 404/410) — tap to try anyway", isLoading = false, fetchingText = fetchingText)
                    }
                    failedGroups.forEachIndexed { index, group ->
                        streamSection(
                            sectionKey = "personal_failed_${index}:${group.addonId}",
                            group = group,
                            showHeader = uiState.selectedFilter == null,
                            debridEnabled = debridEnabled,
                            appendInstantServiceToDefaultName = appendInstantServiceToDefaultName,
                            showFileSizeBadges = streamBadgeSettings.showFileSizeBadges,
                            showAddonLogo = streamBadgeSettings.showAddonLogo,
                            badgePlacement = streamBadgeSettings.badgePlacement,
                            torrentNotSupportedText = torrentNotSupportedText,
                            fetchingText = fetchingText,
                            onStreamSelected = onStreamSelected,
                            onStreamLongPress = onStreamLongPress,
                            resumePositionMs = resumePositionMs,
                            resumeProgressFraction = resumeProgressFraction,
                        )
                    }
                }
                item {
                    Spacer(modifier = Modifier.height(nuvioSafeBottomPadding(80.dp)))
                }''')
screen.write_text(s)
(base/'PersonalStreamHealthPolicy.kt').write_text(r'''package com.nuvio.app.features.streams

internal enum class StreamHealthResult { REACHABLE, MISSING, UNVERIFIED, COOLDOWN }
internal fun classifyStreamHead(status: Int): StreamHealthResult = when (status) {
    404, 410 -> StreamHealthResult.MISSING
    429, 503 -> StreamHealthResult.COOLDOWN
    in 200..299 -> StreamHealthResult.REACHABLE
    else -> StreamHealthResult.UNVERIFIED
}
internal data class StreamProbeTarget(val url: String, val origin: String)
private val directMedia = Regex("^https://([A-Za-z0-9.-]+)(?::443)?(/[^?#\\s]*)$", RegexOption.IGNORE_CASE)
private val mediaExtensions = setOf("mp4", "mkv", "webm", "mov", "m4v", "m3u8", "mpd", "ts")
internal fun streamProbeTarget(raw: String): StreamProbeTarget? {
    val match = directMedia.matchEntire(raw) ?: return null
    val host = match.groupValues[1].lowercase()
    val labels = host.split('.')
    if (labels.size < 2 || labels.any { it.isEmpty() || it.startsWith('-') || it.endsWith('-') } ||
        labels.last().none { it in 'a'..'z' } || labels.last() in setOf("local", "localhost", "internal", "lan", "test", "invalid", "home")) return null
    if (match.groupValues[2].substringAfterLast('/').substringAfterLast('.', "").lowercase() !in mediaExtensions) return null
    return StreamProbeTarget(raw, host)
}
internal class StreamProbeBudget {
    private val attempted = mutableSetOf<String>()
    private val byOrigin = mutableMapOf<String, Int>()
    fun next(candidates: List<StreamProbeTarget>): List<StreamProbeTarget> {
        val batch = mutableListOf<StreamProbeTarget>()
        for (candidate in candidates) {
            if (attempted.size >= 4 || batch.size >= 2) break
            if (candidate.url in attempted || (byOrigin[candidate.origin] ?: 0) >= 2 || batch.any { it.origin == candidate.origin }) continue
            attempted += candidate.url
            byOrigin[candidate.origin] = (byOrigin[candidate.origin] ?: 0) + 1
            batch += candidate
        }
        return batch
    }
}
''')
(base/'PersonalStreamHealth.kt').write_text('''package com.nuvio.app.features.streams

import com.nuvio.app.core.network.createApiHttpClient
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.HttpMethod
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.time.TimeSource

internal fun StreamItem.personalProbeTarget(): StreamProbeTarget? {
    if (isTorrentStream || isDirectDebridStream || debridResolved || clientResolve != null ||
        serverTarget != null || shouldOpenExternally || behaviorHints.notWebReady ||
        !behaviorHints.proxyHeaders?.request.isNullOrEmpty() ||
        !behaviorHints.proxyHeaders?.response.isNullOrEmpty()) return null
    return playableDirectUrl?.let(::streamProbeTarget)
}
internal object PersonalStreamHealth {
    private val client by lazy { createApiHttpClient() }
    private val mutex = Mutex()
    private val slots = Semaphore(2)
    private data class Entry(val result: StreamHealthResult, val time: TimeSource.Monotonic.ValueTimeMark)
    private val entries = linkedMapOf<String, Entry>()
    private val cooldowns = linkedMapOf<String, TimeSource.Monotonic.ValueTimeMark>()
    private val inFlight = mutableSetOf<String>()
    private fun fresh(url: String): StreamHealthResult? {
        val entry = entries[url] ?: return null
        val ttl = if (entry.result == StreamHealthResult.MISSING) 60_000 else 120_000
        if (entry.time.elapsedNow().inWholeMilliseconds >= ttl) { entries.remove(url); return null }
        return entry.result
    }
    suspend fun cached(target: StreamProbeTarget): StreamHealthResult? = mutex.withLock { fresh(target.url) }
    suspend fun probe(target: StreamProbeTarget): StreamHealthResult {
        val allowed = mutex.withLock {
            fresh(target.url)?.let { return it }
            if (cooldowns[target.origin]?.elapsedNow()?.inWholeMilliseconds?.let { it < 120_000 } == true) return StreamHealthResult.UNVERIFIED
            inFlight.add(target.origin)
        }
        if (!allowed) return StreamHealthResult.UNVERIFIED
        try {
            val result = withTimeoutOrNull(1250) {
                slots.withPermit {
                    try {
                        client.prepareRequest(target.url) { method = HttpMethod.Head }.execute { response ->
                            classifyStreamHead(response.status.value)
                        }
                    } catch (e: CancellationException) { throw e }
                    catch (_: Exception) { StreamHealthResult.UNVERIFIED }
                }
            } ?: StreamHealthResult.UNVERIFIED
            mutex.withLock {
                if (result == StreamHealthResult.COOLDOWN) {
                    cooldowns[target.origin] = TimeSource.Monotonic.markNow()
                    while (cooldowns.size > 64) cooldowns.remove(cooldowns.keys.first())
                }
                entries[target.url] = Entry(result, TimeSource.Monotonic.markNow())
                while (entries.size > 128) entries.remove(entries.keys.first())
            }
            return result
        } finally {
            kotlinx.coroutines.withContext(kotlinx.coroutines.NonCancellable) { mutex.withLock { inFlight.remove(target.origin) } }
        }
    }
}
''')
p=Path('iosApp/iosApp/Player/MPVPlayerBridge.swift')
s=p.read_text()
old='''            let pos = getDouble("time-pos")
            isFileLoaded = false
            command("loadfile", args: [path, "replace"])
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
                self?.command("seek", args: [String(format: "%.3f", pos), "absolute"])
            }'''
new=r'''            let pos = getDouble("time-pos")
            isFileLoaded = false
            if pos.isFinite && pos > 0 && pos < Double(Int64.max / 1000) {
                let ms = Int64(pos * 1000)
                let start = String(format: "%lld.%03lld", ms / 1000, ms % 1000)
                command("loadfile", args: [path, "replace", "-1", "start=\(start),resume-playback=no"])
            } else {
                command("loadfile", args: [path, "replace"])
            }'''
assert s.count(old)==1
p.write_text(s.replace(old,new))
p=Path('iosApp/iosApp.xcodeproj/project.pbxproj')
s=p.read_text()
for a,b in [
 ('PRODUCT_BUNDLE_IDENTIFIER = com.nuvio.app;','PRODUCT_BUNDLE_IDENTIFIER = com.nuvio.media;'),
 ('PRODUCT_BUNDLE_IDENTIFIER = com.nuvio.app.DownloadsWidgetExtension;','PRODUCT_BUNDLE_IDENTIFIER = com.nuvio.media.DownloadsWidgetExtension;'),
 ('./gradlew :composeApp:embedAndSignAppleFrameworkForXcode','./gradlew :composeApp:embedAndSignAppleFrameworkForXcode --console=plain --info --stacktrace --max-workers=2'),
]:
 assert s.count(a)==1,a
 s=s.replace(a,b)
p.write_text(s)
# Disable split debug executable so the IPA uses a normal single main executable.
p=Path('scripts/build-ios-ipa.sh')
s=p.read_text()
assert s.count('    CODE_SIGNING_ALLOWED=NO')==1
p.write_text(s.replace('    CODE_SIGNING_ALLOWED=NO','    ENABLE_DEBUG_DYLIB=NO \\\n    CODE_SIGNING_ALLOWED=NO'))
PY
git diff --check
xcodebuild -version
sysctl hw.memsize
./scripts/prepare-ios-dependencies.sh
export NUVIO_IOS_DISTRIBUTION=full
export NUVIO_GRADLE_JVMARGS="-Xmx3072M -Dfile.encoding=UTF-8 -XX:MaxMetaspaceSize=768M"
export NUVIO_KOTLIN_NATIVE_JVMARGS="-Xmx4096M"
export GRADLE_OPTS="-Dfile.encoding=UTF-8"
# Link independently, in Debug mode; Kotlin release LLVM optimization stalled on this runner.
env "ORG_GRADLE_PROJECT_org.gradle.jvmargs=$NUVIO_GRADLE_JVMARGS" "ORG_GRADLE_PROJECT_kotlin.native.jvmArgs=$NUVIO_KOTLIN_NATIVE_JVMARGS" ./gradlew :composeApp:linkDebugFrameworkIosArm64 --console=plain --info --stacktrace --max-workers=2 2>&1 | tee "$OUT/kotlin-compile.log"
IOS_IPA_OUTPUT_DIR="$WORK/ipa" IOS_CONFIGURATION=Debug ./scripts/build-ios-ipa.sh 2>&1 | tee "$OUT/xcode-build.log"
shopt -s nullglob
ipas=("$WORK"/ipa/*.ipa)
[[ ${#ipas[@]} == 1 ]]
DEST="$OUT/Nuvio_Phase17_unsigned.ipa"
python3 - "${ipas[0]}" "$DEST" <<'PY'
import sys,zipfile,shutil,plistlib
config=b'''# Nuvio Hybrid v3 final: conservative network playback defaults.
cache=auto
cache-secs=35
demuxer-max-bytes=112MiB
demuxer-max-back-bytes=32MiB
cache-on-disk=no
cache-pause=yes
cache-pause-initial=no
cache-pause-wait=2.0
slang=eng,en
network-timeout=20
stream-lavf-o=reconnect=1,reconnect_on_network_error=1,reconnect_on_http_error=%7%502,504,reconnect_delay_max=4,reconnect_max_retries=3,reconnect_delay_total_max=12,respect_retry_after=1
demuxer-hysteresis-secs=0
'''
with zipfile.ZipFile(sys.argv[1]) as i,zipfile.ZipFile(sys.argv[2],'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as o:
 for item in i.infolist():
  if item.filename=='Payload/Nuvio.app/mpv.conf': continue
  if item.is_dir(): o.writestr(item,b''); continue
  with i.open(item) as f,o.open(item,'w') as out: shutil.copyfileobj(f,out)
 o.writestr('Payload/Nuvio.app/mpv.conf',config)
with zipfile.ZipFile(sys.argv[2]) as z:
 assert z.testzip() is None
 p=plistlib.loads(z.read('Payload/Nuvio.app/Info.plist'))
 assert p['CFBundleIdentifier']=='com.nuvio.media'
 assert not any(x.endswith('/Nuvio.debug.dylib') for x in z.namelist())
PY
python3 "$HERE/check_ipa.py" "$DEST" --max-min-os 18.3
shasum -a 256 "$DEST" | tee "$OUT/SHA256.txt"
echo "Final candidate IPA: $DEST"
