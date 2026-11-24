#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
clang -c tests/callback_fixture/fixture.c -o "$work/fixture.o"
{ echo 'import MPVCallbackFixture'; cat native/PersonalPrefetchCache.swift native/PersonalRangeReader.swift native/PersonalRangeHTTP.swift native/PersonalMPVRangeAdapter.swift tests/PersonalMPVRangeAdapterTest.swift; } > "$work/main.swift"
swiftc -D PERSONAL_EXPERIMENTAL_RANGE_TRANSPORT -I tests/callback_fixture "$work/main.swift" "$work/fixture.o" -o "$work/test"
"$work/test"
