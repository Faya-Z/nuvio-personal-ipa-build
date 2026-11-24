#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
p=overlay/composeApp/src/commonMain/kotlin/com/nuvio/app/features/player
kotlinc "$p/RecoveryPolicy.kt" "$p/PlaybackFeaturePolicy.kt" "$p/PlaybackDiagnostics.kt" "$p/PlaybackPreparationPolicy.kt" "$p/PersonalPlaybackSelection.kt" "$p/PersonalHistoryLedger.kt" "$p/PersonalSubtitleSyncPolicy.kt" "$p/PersonalSkipPolicy.kt" "$p/PersonalHandoverPolicy.kt" tests/*.kt -include-runtime -d "$work/policies.jar"
for f in tests/*.kt; do
    java -cp "$work/policies.jar" "com.nuvio.app.features.player.$(basename "$f" .kt)Kt"
done
for name in AdaptiveCachePolicy PersonalNativePlaybackPolicy PersonalNativeResumePolicy PersonalNativeEventBatch PersonalNativeConveniencePolicy PersonalLowPowerBufferPolicy PersonalEncodedBarPolicy PersonalPrefetchCache; do
    if [[ "$name" == PersonalNativeEventBatch ]]; then
        cat native/PersonalNativePlaybackPolicy.swift "native/$name.swift" "tests/${name}Test.swift" > "$work/$name.swift"
    else
        cat "native/$name.swift" "tests/${name}Test.swift" > "$work/$name.swift"
    fi
    swift "$work/$name.swift"
done
for name in PersonalRangeReader PersonalRangeHTTP PersonalRangeSession; do
    cat native/PersonalPrefetchCache.swift native/PersonalRangeReader.swift native/PersonalRangeHTTP.swift "tests/${name}Test.swift" > "$work/$name.swift"
    swift "$work/$name.swift"
done
bash tests/run_callback_fixture.sh
python3 tests/test_apply.py
