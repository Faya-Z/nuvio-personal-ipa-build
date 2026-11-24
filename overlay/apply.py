#!/usr/bin/env python3
"""Apply the first Nuvio improvement overlay, checking exact upstream anchors."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('checkout', type=Path)
p.add_argument('--dry-run', action='store_true')
a = p.parse_args()
root = a.checkout.resolve()
base = Path('composeApp/src/commonMain/kotlin/com/nuvio/app/features/player')
patches = {
    base/'PlayerScreenRuntimeState.kt': [
        ('    var playbackSnapshot by mutableStateOf(PlayerPlaybackSnapshot())',
         '    val playbackDiagnostics = PlaybackDiagnostics()\n    var playbackSnapshot by mutableStateOf(PlayerPlaybackSnapshot())'),
    ],
    base/'PlayerScreenRuntimePlaybackActions.kt': [
        ('    if (playbackKey != activePlaybackKey) return false\n',
         '    if (playbackKey != activePlaybackKey) return false\n'
         '    if (playbackSnapshotKey != playbackKey) playbackDiagnostics.reset()\n'
         '    playbackDiagnostics.observe(\n'
         '        loading = snapshot.isLoading,\n'
         '        playing = snapshot.isPlaying,\n'
         '        ended = snapshot.isEnded,\n'
         '        expectedToPlay = shouldPlay && !isScrubbingTimeline && scrubbingPositionMs == null && pendingSeekTarget == null,\n'
         '    )?.let { event -> co.touchlab.kermit.Logger.withTag("PlaybackDiagnostics").d { event } }\n'),
    ],
    base/'PlayerScreenRuntimeSourceFallback.kt': [
        ('    val failedUrl = activeSourceUrl\n',
         '    val failedUrl = activeSourceUrl\n    val failedPlaybackKey = sourcePlaybackKey\n'),
        ('            var polls = 0\n',
         '            if (sourcePlaybackKey != failedPlaybackKey) return@launch\n            var polls = 0\n'),
        ('                val state = PlayerStreamsRepository.sourceState.value\n',
         '                if (sourcePlaybackKey != failedPlaybackKey) return@launch\n                val state = PlayerStreamsRepository.sourceState.value\n'),
        ('                val url = playable?.playableDirectUrl\n',
         '                if (sourcePlaybackKey != failedPlaybackKey) return@launch\n                val url = playable?.playableDirectUrl\n'),
        ('        // The last source that failed may have been saved for reuse.\n',
         '        if (sourcePlaybackKey != failedPlaybackKey) return@launch\n        // The last source that failed may have been saved for reuse.\n'),
    ],
    Path('.github/workflows/ios-test-build.yml'): [
        ('      configuration:\n', '      runner:\n        description: macOS runner label (use the original runner if available)\n        required: true\n        type: string\n        default: macos-latest\n      xcode_path:\n        description: Optional absolute Xcode Developer directory; blank uses runner default\n        required: false\n        type: string\n        default: ""\n      configuration:\n'),
        ('    runs-on: xcode-27\n', '    runs-on: ${{ inputs.runner }}\n'),
        ('      DEVELOPER_DIR: /Applications/Xcode_27.1.app/Contents/Developer\n', ''),
        ('      - name: Verify Apple toolchain\n        run: |\n',
         '      - name: Verify Apple toolchain\n        env:\n          REQUESTED_XCODE_PATH: ${{ inputs.xcode_path }}\n        run: |\n          if [[ -n "$REQUESTED_XCODE_PATH" ]]; then\n            test -d "$REQUESTED_XCODE_PATH"\n            export DEVELOPER_DIR="$REQUESTED_XCODE_PATH"\n            printf "DEVELOPER_DIR=%s\\n" "$DEVELOPER_DIR" >> "$GITHUB_ENV"\n          fi\n'),
    ],
}
from phase2_patches import patches as phase2_patches
for rel, replacements in phase2_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase3_patches import patches as phase3_patches
for rel, replacements in phase3_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase4_patches import patches as phase4_patches
for rel, replacements in phase4_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase5_patches import patches as phase5_patches
for rel, replacements in phase5_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase6_patches import patches as phase6_patches
for rel, replacements in phase6_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase7_patches import patches as phase7_patches
for rel, replacements in phase7_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase8_patches import patches as phase8_patches
for rel, replacements in phase8_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase9_patches import patches as phase9_patches
for rel, replacements in phase9_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase10_patches import patches as phase10_patches
for rel, replacements in phase10_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase11_patches import patches as phase11_patches
for rel, replacements in phase11_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase12_patches import patches as phase12_patches
for rel, replacements in phase12_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase13_patches import patches as phase13_patches
for rel, replacements in phase13_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase14_patches import patches as phase14_patches
for rel, replacements in phase14_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase15_patches import patches as phase15_patches
for rel, replacements in phase15_patches.items():
    patches.setdefault(rel, []).extend(replacements)
from phase16_patches import patches as phase16_patches
for rel, replacements in phase16_patches.items():
    patches.setdefault(rel, []).extend(replacements)
# Read and validate everything before touching the checkout. Exact anchors fail closed.
updates = {}
marker = root / ".nuvio-personal-phase17"
if marker.exists() or (root / ".nuvio-personal-phase16").exists() or (root / ".nuvio-personal-phase15").exists() or (root / ".nuvio-personal-phase14").exists() or (root / ".nuvio-personal-phase13").exists() or (root / ".nuvio-personal-phase12").exists() or (root / ".nuvio-personal-phase11").exists() or (root / ".nuvio-personal-phase10").exists() or (root / ".nuvio-personal-phase9").exists() or (root / ".nuvio-personal-phase8").exists() or (root / ".nuvio-personal-phase7").exists() or (root / ".nuvio-personal-phase6").exists() or (root / ".nuvio-personal-phase5").exists() or (root / ".nuvio-personal-phase4").exists() or (root / ".nuvio-personal-phase3").exists() or (root / ".nuvio-personal-phase2").exists() or (root / ".nuvio-personal-phase1").exists():
    raise SystemExit("A personal overlay already applied; use a clean pinned checkout for reapplication.")
for rel, replacements in patches.items():
    target = root / rel
    contents = target.read_text()
    for old, new in replacements:
        if new and new in contents:
            continue
        if not new and old not in contents:
            continue
        if contents.count(old) != 1:
            raise SystemExit(f'Anchor missing or ambiguous in {rel}: {old!r}')
        contents = contents.replace(old, new, 1)
    updates[target] = contents
for src in (Path(__file__).parent/'overlay').rglob('*.kt'):
    rel = src.relative_to(Path(__file__).parent/'overlay')
    target = root / rel
    contents = src.read_text()
    if target.exists() and target.read_text() != contents:
        raise SystemExit(f'Refusing to overwrite existing custom file: {rel}')
    updates[target] = contents
for target, contents in updates.items():
    print(('Would update ' if a.dry_run else 'Update ') + str(target.relative_to(root)))
    if not a.dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents)

if not a.dry_run:
    marker.write_text("Nuvio personal phase 17\n")
