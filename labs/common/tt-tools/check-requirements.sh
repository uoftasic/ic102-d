#!/usr/bin/env bash
# Warn when a project's test/requirements.txt asks for different packages
# than the course venv has. Both the test job and the gl_test job run
# `pip install -r test/requirements.txt` from your repository, so a project
# that changes that file gets different versions on the runner than here.
# Prints a warning and returns 0; it never stops a run.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${TT_TOOLS_ROOT:-$HERE/.local}"
req="$1/test/requirements.txt"
[ -f "$req" ] || { echo "warning: $req not found; the runner installs cocotb 1.8.0 in gl_test when it's missing"; exit 0; }
PYTHONPATH= "$ROOT/venv/bin/python" - "$req" <<'PY'
import sys, re, importlib.metadata as md
bad = []
for line in open(sys.argv[1]):
    line = line.split("#")[0].strip()
    m = re.fullmatch(r"([A-Za-z0-9_.-]+)\s*==\s*([^\s;]+)", line)
    if not line:
        continue
    if not m:
        bad.append(f"  {line!r}: not an exact pin, so the runner takes whatever pip picks on the day")
        continue
    name, want = m.groups()
    try:
        have = md.version(name)
    except md.PackageNotFoundError:
        have = None
    if have != want:
        bad.append(f"  {name}: your test/requirements.txt pins {want}, this venv has {have or 'nothing'}")
if bad:
    print("warning: the runner installs your test/requirements.txt, and it differs from this venv:")
    print("\n".join(bad))
    print("  Results here may not match the runner's. See README.md, 'Your own requirements.txt'.")
    print()
PY
exit 0
