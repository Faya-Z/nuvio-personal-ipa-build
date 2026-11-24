#!/usr/bin/env bash
# Apply only to a clean pinned Git checkout. Does not build or sign the application.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
checkout="${1:?Usage: validate_checkout.sh /path/to/clean/NuvioMobile}"
expected=bd9506cc8574b7fb3d7d2dc25f1a065d5debc7cb
[[ "$(git -C "$checkout" rev-parse HEAD)" == "$expected" ]] || { echo 'Wrong upstream commit' >&2; exit 1; }
[[ -z "$(git -C "$checkout" status --porcelain)" ]] || { echo 'Checkout is not clean' >&2; exit 1; }
python3 "$here/apply.py" "$checkout" --dry-run
bash "$here/tests/run_all.sh"
python3 "$here/apply.py" "$checkout"
git -C "$checkout" diff --check
printf '\nOverlay applied and local checks passed. Run the full Xcode build next.\n'
