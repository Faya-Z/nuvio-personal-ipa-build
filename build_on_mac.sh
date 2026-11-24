#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PIN=bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
OUT="${NUVIO_OUTPUT_DIR:-$HERE/output}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
[[ "$(uname -s)" == Darwin ]] || { echo 'macOS with Xcode is required.' >&2; exit 1; }
[[ -f "$HERE/overlay/apply.py" ]] || { echo 'Missing Phase 17 source overlay.' >&2; exit 1; }
xcodebuild -version
xcrun --sdk iphoneos --show-sdk-version
java -version
WORK="$(mktemp -d "${TMPDIR:-/tmp}/nuvio-build.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
SRC="$WORK/NuvioMobile"
git init -q "$SRC"
git -C "$SRC" remote add origin https://github.com/NuvioMedia/NuvioMobile.git
git -C "$SRC" fetch --depth=1 origin "$PIN"
git -C "$SRC" checkout --detach FETCH_HEAD
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]]
[[ -z "$(git -C "$SRC" status --porcelain)" ]]
python3 "$HERE/overlay/apply.py" "$SRC" --dry-run
python3 "$HERE/overlay/apply.py" "$SRC"
git -C "$SRC" diff --check
if [[ -n "${NUVIO_LOCAL_PROPERTIES_BASE64:-}" ]]; then
  python3 - "$SRC/local.properties" <<'PY'
import os,base64,sys,pathlib,re
value=base64.b64decode(os.environ['NUVIO_LOCAL_PROPERTIES_BASE64'],validate=True).decode()
pathlib.Path(sys.argv[1]).write_text('\n'.join(line for line in value.splitlines() if not re.match(r'^\s*(sdk\.dir|NUVIO_RELEASE_STORE_FILE)\s*=',line))+'\n')
PY
fi
# Gradle validates this declared input even when optional credentials are absent.
# Preserve any supplied configuration and create an empty file only if missing.
if [[ ! -f "$SRC/local.properties" ]]; then
  touch "$SRC/local.properties"
fi
cd "$SRC"
./scripts/prepare-ios-dependencies.sh
# Build Kotlin independently to capture its full compiler diagnostic before Xcode packaging.
export NUVIO_IOS_DISTRIBUTION=full
export GRADLE_OPTS="${GRADLE_OPTS:--Dfile.encoding=UTF-8}"
# The upstream packaging script also supplies the dotted Gradle property environment variables.
env "ORG_GRADLE_PROJECT_org.gradle.jvmargs=${NUVIO_GRADLE_JVMARGS:--Xmx4608M -Dfile.encoding=UTF-8 -XX:MaxMetaspaceSize=768M}" \
    "ORG_GRADLE_PROJECT_kotlin.native.jvmArgs=${NUVIO_KOTLIN_NATIVE_JVMARGS:--Xmx4608M}" \
    ./gradlew :composeApp:compileKotlinIosArm64 --stacktrace --console=plain 2>&1 | tee "$OUT/kotlin-compile.log"
python3 - <<'PY'
from pathlib import Path
p=Path("iosApp/iosApp.xcodeproj/project.pbxproj")
s=p.read_text()
old="./gradlew :composeApp:embedAndSignAppleFrameworkForXcode"
assert s.count(old)==1, "Unexpected Xcode Gradle script"
p.write_text(s.replace(old,old+" --stacktrace --console=plain"))
PY
IOS_IPA_OUTPUT_DIR="$WORK/ipa" IOS_CONFIGURATION="${IOS_CONFIGURATION:-Release}" ./scripts/build-ios-ipa.sh 2>&1 | tee "$OUT/xcode-build.log"
shopt -s nullglob
ipas=("$WORK"/ipa/*.ipa)
[[ ${#ipas[@]} -eq 1 ]] || { echo 'Expected exactly one newly built IPA.' >&2; exit 1; }
python3 "$HERE/check_ipa.py" "${ipas[0]}" --max-min-os 18.3
DEST="$OUT/Nuvio_Phase17_unsigned.ipa"
cp "${ipas[0]}" "$DEST.tmp"
mv "$DEST.tmp" "$DEST"
shasum -a 256 "$DEST" | tee "$OUT/SHA256.txt"
echo "IPA: $DEST"
