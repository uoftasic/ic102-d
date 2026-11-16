#!/usr/bin/env bash
# Run your project's cocotb test the way the template's test workflow runs it
# on GitHub (.github/workflows/test.yaml, step "Run tests"):
#
#   cd test
#   make clean
#   make
#   python -m cocotb_tools.check_results results.xml
#
# with the runner's cocotb and pytest (in .local/venv) and the runner's Icarus
# Verilog 12.0 (in .local/icarus-12).
#
#   ./run-test.sh PROJECT_DIR              as the test job does
#   ICARUS=13 ./run-test.sh PROJECT_DIR    with gl_test's Icarus 13.0 instead
#   ICARUS=workbench ./run-test.sh PROJECT_DIR
#                                          with the workbench's Icarus 14.0
#
# The exit status is check_results's: 0 when every test passed. `make` alone
# exits 0 even when a test fails, which is why the workflow runs check_results.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pins.env
. "$HERE/pins.env"
ROOT="${TT_TOOLS_ROOT:-$HERE/.local}"
ICARUS="${ICARUS:-12}"

die() { printf 'run-test.sh: %s\n' "$*" >&2; exit 2; }

[ $# -eq 1 ] || die "usage: ./run-test.sh PROJECT_DIR"
PROJECT="$(cd "$1" && pwd)" || die "no such folder: $1"
[ -f "$PROJECT/test/Makefile" ] || die "$PROJECT/test/Makefile not found; PROJECT_DIR is your repository's top folder"
[ -x "$ROOT/venv/bin/python" ] || die "the tools aren't installed yet; run: make install"

# The runner has none of the workbench's settings. The workbench's PYTHONPATH
# points at its own Python 3.12 packages, including cocotb 2.0.1.
unset PYTHONPATH
case "$ICARUS" in
  12|13) [ -x "$ROOT/icarus-$ICARUS/bin/iverilog" ] || die "Icarus $ICARUS isn't installed yet; run: make install"
         ICARUS_BIN="$ROOT/icarus-$ICARUS/bin"
         unset LD_LIBRARY_PATH ;;
  # The workbench's own Icarus needs its library folder, which the image puts
  # on LD_LIBRARY_PATH.
  workbench) ICARUS_BIN=/foss/tools/bin
         export LD_LIBRARY_PATH=/foss/tools/iverilog/lib ;;
  *) die "ICARUS must be 12, 13 or workbench, not '$ICARUS'" ;;
esac
export PATH="$ROOT/venv/bin:$ICARUS_BIN:/usr/bin:/bin"
export VIRTUAL_ENV="$ROOT/venv"
"$HERE/check-requirements.sh" "$PROJECT"

echo "run-test: $PROJECT/test"
echo "  python  $(python -c 'import platform; print(platform.python_version())'), cocotb $(cocotb-config --version)"
echo "  icarus  $(command -v iverilog) ($(iverilog -V 2>/dev/null | head -1))"
echo

cd "$PROJECT/test"
make clean
make
python -m cocotb_tools.check_results results.xml
