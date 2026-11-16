#!/usr/bin/env bash
# Run your project's cocotb test on the gate-level netlist, the way the gl_test
# job does on GitHub (tt-gds-action/gl_test at ttsky26d):
#
#   cp tt_submission/*.v test/gate_level_netlist.v
#   cd test
#   make clean
#   GATES=yes make
#   ! grep -E '<(failure|error)' results.xml
#
# with Icarus 13.0, the runner's cocotb, and the sky130 standard cells at the
# PDK commit the gds job used.
#
#   ./run-gl-test.sh PROJECT_DIR TT_SUBMISSION_DIR
#   ICARUS=12 ./run-gl-test.sh ...      with the test job's Icarus 12.0 instead
#   ICARUS=workbench ./run-gl-test.sh ...  with the workbench's Icarus 14.0
#
# TT_SUBMISSION_DIR is the tt_submission artifact of a gds run, downloaded and
# unzipped (it holds <top_module>.v). This needs `./install.sh gl-pdk` first.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pins.env
. "$HERE/pins.env"
ROOT="${TT_TOOLS_ROOT:-$HERE/.local}"
ICARUS="${ICARUS:-13}"

die() { printf 'run-gl-test.sh: %s\n' "$*" >&2; exit 2; }

[ $# -eq 2 ] || die "usage: ./run-gl-test.sh PROJECT_DIR TT_SUBMISSION_DIR"
PROJECT="$(cd "$1" && pwd)" || die "no such folder: $1"
SUB="$(cd "$2" && pwd)" || die "no such folder: $2"
[ -f "$PROJECT/test/Makefile" ] || die "$PROJECT/test/Makefile not found"
[ -f "$ROOT/gl-pdk.ok" ] || die "the standard cells aren't installed yet; run: ./install.sh gl-pdk"
want=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["PDK_VERSION"])' "$SUB/pdk.json" 2>/dev/null || true)
if [ -n "$want" ] && [ "$want" != "$SKY130_GL_PDK_COMMIT" ]; then
  echo "warning: this gds run used PDK $want, and .local/pdk has $SKY130_GL_PDK_COMMIT"
fi

unset PYTHONPATH
case "$ICARUS" in
  12|13) [ -x "$ROOT/icarus-$ICARUS/bin/iverilog" ] || die "Icarus $ICARUS isn't installed yet; run: make install"
         ICARUS_BIN="$ROOT/icarus-$ICARUS/bin"
         unset LD_LIBRARY_PATH ;;
  workbench) ICARUS_BIN=/foss/tools/bin
         export LD_LIBRARY_PATH=/foss/tools/iverilog/lib ;;
  *) die "ICARUS must be 12, 13 or workbench, not '$ICARUS'" ;;
esac
export PATH="$ROOT/venv/bin:$ICARUS_BIN:/usr/bin:/bin"
export VIRTUAL_ENV="$ROOT/venv"
"$HERE/check-requirements.sh" "$PROJECT"
export PDK_ROOT="$ROOT/pdk" PDK=sky130A

echo "run-gl-test: $PROJECT/test with $(ls "$SUB"/*.v)"
echo "  python  $(python -c 'import platform; print(platform.python_version())'), cocotb $(cocotb-config --version)"
echo "  icarus  $(command -v iverilog) ($(iverilog -V 2>/dev/null | head -1))"
echo "  PDK     $PDK_ROOT/sky130A ($(cut -d' ' -f2 "$PDK_ROOT/sky130A/SOURCES" | head -1))"
echo

cp "$SUB"/*.v "$PROJECT/test/gate_level_netlist.v"
cd "$PROJECT/test"
rm -f tb.vcd tb.fst results.xml
make clean
GATES=yes make
test -f results.xml
! grep -E '<(failure|error)' results.xml
