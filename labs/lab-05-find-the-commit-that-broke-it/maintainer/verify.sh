#!/usr/bin/env bash
# Check data/history.bundle the way Lab 05 uses it. Run it in the workbench, after
# `make install` in labs/common/tt-tools:
#
#   bash maintainer/verify.sh [WORKDIR]
#
# 1. Runs the test at every commit with the test job's tools and prints pass, FAIL or "no build".
# 2. Runs git bisect from v1.0 to main with three scripts: one that exits with make's status,
#    one that calls a commit with no results bad (the guide's protocol-emulator script), and
#    solutions/bisect.sh, which skips it with 125. Only the last should name the planted commit.
# 3. Reverts the planted commit on main and runs the test again, which should pass.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TT="$HERE/../common/tt-tools"
W="${1:-/tmp/lab05-verify}"
rm -rf "$W" && mkdir -p "$W"
git clone -q "$HERE/data/history.bundle" "$W/dimmer"
cd "$W/dimmer"
git config user.name verify && git config user.email verify@example.com

classify() {
  rm -f test/results.xml
  "$TT/run-test.sh" . > "$W/run.log" 2>&1
  if [ ! -f test/results.xml ]; then echo "no build"
  elif grep -q "<failure" test/results.xml; then echo "FAIL"
  else echo "pass"; fi
}

echo "== every commit, oldest first"
for c in $(git rev-list --reverse main); do
  git -c advice.detachedHead=false checkout -q "$c"
  printf '%s  %-8s %s\n' "$(git rev-parse --short "$c")" "$(classify)" "$(git log -1 --format=%s "$c")"
done
git checkout -q main

cat > "$W/make-status.sh" <<'S'
#!/bin/bash
cd test && make clean >/dev/null 2>&1; make >/dev/null 2>&1
S
cat > "$W/no-results-is-bad.sh" <<'S'
#!/bin/bash
cd test || exit 125
rm -rf sim_build results.xml
make > /tmp/bisect-make.log 2>&1
if [ ! -f results.xml ]; then exit 1; fi
if grep -q "<failure" results.xml; then exit 1; fi
exit 0
S
chmod +x "$W"/*.sh
export PATH="$TT/.local/venv/bin:$TT/.local/icarus-12/bin:/usr/bin:/bin"; unset PYTHONPATH

for s in "$W/make-status.sh" "$W/no-results-is-bad.sh" "$HERE/solutions/bisect.sh"; do
  echo "== git bisect run $(basename "$s")"
  git bisect start main v1.0 >/dev/null
  git bisect run "$s" > "$W/bisect.log" 2>&1
  grep -E "is the first bad commit|could be any of|^[0-9a-f]{40}$" "$W/bisect.log" | head -5
  git bisect log | grep -c '^git bisect \(good\|bad\|skip\)' | sed 's/^/   commits tested: /'
  git bisect reset -q >/dev/null 2>&1
done

echo "== revert the planted commit on main"
bad=$(git log --format=%h --grep='^pwm: tidy up the comparator' main)
git revert --no-edit "$bad" >/dev/null && echo "git revert $bad: applied cleanly"
echo "test after the revert: $(classify)"
