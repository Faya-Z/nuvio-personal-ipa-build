from pathlib import Path
import ast, subprocess, sys, tempfile
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from phase2_patches import patches as phase2
from phase3_patches import patches as phase3
from phase4_patches import patches as phase4
from phase5_patches import patches as phase5
from phase6_patches import patches as phase6
from phase7_patches import patches as phase7
from phase8_patches import patches as phase8
from phase9_patches import patches as phase9
from phase10_patches import patches as phase10
from phase11_patches import patches as phase11
from phase12_patches import patches as phase12
from phase13_patches import patches as phase13
from phase14_patches import patches as phase14
from phase15_patches import patches as phase15
from phase16_patches import patches as phase16
# Extract the static initial patches without executing the CLI.
source = (root / 'apply.py').read_text()
node = next(n for n in ast.parse(source).body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='patches' for t in n.targets))
ns = {'Path': Path, 'base': Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')}
exec(compile(ast.Module(body=[node],type_ignores=[]), '<patches>', 'exec'), ns)
phase1 = ns['patches']
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    for rel in phase1.keys() | phase2.keys() | phase3.keys() | phase4.keys() | phase5.keys() | phase6.keys() | phase7.keys() | phase8.keys() | phase9.keys() | phase10.keys() | phase11.keys() | phase12.keys() | phase13.keys() | phase14.keys() | phase15.keys() | phase16.keys():
        anchors = list(dict.fromkeys(old for old,new in phase1.get(rel,[])+phase2.get(rel,[])))
        # Add independent Phase 3 anchors; derived anchors must be created by earlier patches.
        original = '\n'.join(anchors)
        intermediate = original
        for old,new in phase1.get(rel,[])+phase2.get(rel,[]):
            if new and new in intermediate: continue
            intermediate = intermediate.replace(old,new,1)
        for old,new in phase3.get(rel,[])+phase4.get(rel,[])+phase5.get(rel,[])+phase6.get(rel,[])+phase7.get(rel,[])+phase8.get(rel,[])+phase9.get(rel,[])+phase10.get(rel,[])+phase11.get(rel,[])+phase12.get(rel,[])+phase13.get(rel,[])+phase14.get(rel,[])+phase15.get(rel,[])+phase16.get(rel,[]):
            if old not in intermediate:
                assert not any(x in old for x in ('failedPlaybackKey','PlaybackDiagnostics()','updateDialogueReplay','finishDialogueReplay()','pendingSeekTarget == null')), (rel, old)
                original += '\n' + old
                intermediate += '\n' + old
            intermediate=intermediate.replace(old,new,1)
        target=d/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(original)
    subprocess.run([sys.executable, str(root/'apply.py'),tmp,'--dry-run'], check=True,stdout=subprocess.DEVNULL)
    assert not (d/'.nuvio-personal-phase17').exists()
    subprocess.run([sys.executable,str(root/'apply.py'),tmp],check=True,stdout=subprocess.DEVNULL)
    assert (d/'.nuvio-personal-phase17').exists()
    assert 'updateDialogueReplay(snapshot)' in (d/ns['base']/'PlayerScreenRuntimePlaybackActions.kt').read_text()
    assert 'Matched-file recovery started' in (d/ns['base']/'PlayerScreenRuntimeSourceFallback.kt').read_text()
    assert (d/ns['base']/'DialogueReplay.kt').exists()
    assert (d/ns['base']/'PlayerRecoveryRuntime.kt').exists()
    assert (d/ns['base']/'PlaybackPreparationPolicy.kt').exists()
    assert 'nextEpisodePreparationLeadMs(' in (d/ns['base']/'PlayerNextEpisodeAutoPlay.kt').read_text()
    assert 'Playback diagnostics (current source)' in (d/ns['base']/'StreamInfoOverlay.kt').read_text()
    fallback=(d/ns['base']/'PlayerScreenRuntimeSourceFallback.kt').read_text()
    assert 'proactivePositionMs: Long? = null' in fallback
    assert fallback.count('if (!stillApplicable()) return@launch') == 4
    assert 'rememberCurrentTrackPreferenceForEngineSwitch(null, url)' in fallback
    bridge = (d/'iosApp/iosApp/Player/MPVPlayerBridge.swift').read_text()
    assert 'PersonalAdaptiveCachePolicy' in bridge
    assert 'self.personalLoadGeneration == loadGeneration' in bridge
    assert 'retry.observe(generation: personalLoadGeneration' in bridge
    assert 'verifyPersonalRetry(seeking:' in bridge
    assert 'PersonalNativeConveniencePolicy.smallCrop' in bridge
    assert 'reducedBackCache(bytes: bytes)' in bridge
    assert 'mpv_set_wakeup_callback(ctx, nil, nil)' in bridge
    assert 'eventQueue.sync {' in bridge
    assert 'confirmPersonalHandover' in (d/ns['base'].parent/'watchprogress/WatchProgressRepository.kt').read_text()
    assert 'savePersonalHandover()' in (d/ns['base']/'PlayerScreenRuntimeUi.kt').read_text()
    assert 'return@setAutoSyncAppliedListener' in (d/ns['base']/'PlayerRuntimeAutoSync.kt').read_text()
    assert "mpv_stream_cb_add_ro" in bridge
    assert "if let existing = session { s = existing }" in bridge
    assert "deinit { cancel() }" in bridge
    assert "defer { http.cancel() }" in bridge
    assert "PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT" in bridge
    assert "PersonalPrefetchTransport.shared.take" in bridge
    assert "personalBarsFromReply" in bridge
    assert "requestPersonalBarSample(eligible:" in bridge
    assert "PersonalNativePlaybackPolicy.bufferedPosition" in bridge
    assert "position + cached" not in bridge
    assert "propertyBatch.add(name)" in bridge
    assert "flushProperties()" in bridge
    assert "case .tracks: self.updateState()" in bridge
    assert (d/ns['base']/'SourceReliabilityStorage.kt').exists()
    assert 'verifyPreferredEnglishAudio()' in (d/ns['base']/'PlayerScreenRuntimeTrackActions.kt').read_text()
    assert 'rankPersonalInitialSources' in (d/ns['base'].parent/'streams/StreamsRepository.kt').read_text()
    assert 'observePersonalSessionHistory(snapshot)' in (d/ns['base']/'PlayerScreenRuntimePlaybackActions.kt').read_text()
    assert "personalSubtitleSyncGate.accepts" in (d/ns['base']/'PlayerScreenRuntimeSubtitleActions.kt').read_text()
    assert "PersonalNativeResumePolicy.loadArguments" in bridge
    assert "loadFileWithAudioAtPosition" in bridge
    assert 'personalShouldResetPreload' in (d/ns['base']/'PlayerNextEpisodeAutoPlay.kt').read_text()
    assert 'personalForwardSkipTarget' in (d/ns['base']/'PlayerScreenRuntimeEffects.kt').read_text()
    assert 'activeSkipInterval?.let(autoSkippedIntervals::add)' in (d/ns['base']/'PlayerScreenRuntimeUi.kt').read_text()
    assert subprocess.run([sys.executable,str(root/'apply.py'),tmp],capture_output=True).returncode != 0
print('PASS: synthetic overlay dry-run, application, feature anchors and repeat guard')
