#!/usr/bin/env bash
# Prove the install works: run the digital template's own test, at the
# template commit in pins.env, the way the runner's test job runs it.
#
#   ./selftest.sh               with Icarus 12.0, as the test job does
#   ./selftest.sh all           with Icarus 12.0, 13.0 and the workbench's 14.0
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pins.env
. "$HERE/pins.env"
ROOT="${TT_TOOLS_ROOT:-$HERE/.local}"
W="$ROOT/selftest"

rm -rf "$W" && mkdir -p "$W"
git init -q "$W"
git -C "$W" fetch -q --depth 1 "https://github.com/$TT_TEMPLATE" "$TT_TEMPLATE_COMMIT"
git -C "$W" -c advice.detachedHead=false checkout -q FETCH_HEAD

if [ "${1:-}" = all ]; then
  for i in 12 13 workbench; do
    echo "=================== Icarus: $i"
    ICARUS=$i "$HERE/run-test.sh" "$W"
  done
else
  "$HERE/run-test.sh" "$W"
fi
