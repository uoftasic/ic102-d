#!/usr/bin/env bash
# Print each tool the template's test and gl_test jobs use: the version Tiny
# Tapeout's runner uses, the version installed here, and the version the
# workbench image has. Exits 1 if anything installed here differs from the
# pin, or is missing. The gate-level PDK is optional and only reported.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pins.env
. "$HERE/pins.env"
ROOT="${TT_TOOLS_ROOT:-$HERE/.local}"
WB_PYTHONPATH="${PYTHONPATH:-}"
unset PYTHONPATH LD_LIBRARY_PATH

PY="$ROOT/venv/bin/python"
bad=0

pyver() { [ -x "$PY" ] && "$PY" -c "import importlib.metadata as m; print(m.version('$1'))" 2>/dev/null; }
wbpyver() { PYTHONPATH="$WB_PYTHONPATH" python3 -c "import importlib.metadata as m; print(m.version('$1'))" 2>/dev/null; }
# "Icarus Verilog version 12.0 (stable) ()" -> 12.0
icarus() { [ -x "$1" ] && "$1" -V 2>/dev/null | head -1 | sed -n 's/^Icarus Verilog version \([0-9.]*\).*/\1/p'; }

# row TOOL PINNED HERE WORKBENCH [MATCH [OPTIONAL]]
# MATCH is "exact" (default) or "minor" (compare the first two numbers only).
row() {
  local tool=$1 pinned=$2 here=$3 wb=$4 match=${5:-exact} optional=${6:-} status
  if [ -z "$here" ]; then
    if [ -n "$optional" ]; then status="not installed (optional)"; else status="MISSING"; bad=1; fi
  elif [ "$match" = minor ] && [ "${here%.*}" = "${pinned%.*}" ]; then
    status="ok (${pinned%.*})"
  elif [ "$here" = "$pinned" ]; then
    status="ok"
  else
    status="DIFFERENT"; bad=1
  fi
  printf '%-22s %-14s %-14s %-14s %s\n' "$tool" "$pinned" "${here:--}" "${wb:--}" "$status"
}

echo "IC102-D tools: Tiny Tapeout's pins (tag $TT_ACTION_TAG) against this environment and the workbench"
echo "Installed in: $ROOT"
echo
printf '%-22s %-14s %-14s %-14s %s\n' "Tool (job)" "Runner" "Here" "Workbench" "Status"
printf '%-22s %-14s %-14s %-14s %s\n' "----------" "------" "----" "---------" "------"

here_py=$([ -x "$PY" ] && "$PY" -c 'import platform; print(platform.python_version())')
row "Python (test)" "$PYTHON_RUNNER" "$here_py" "$(python3 -c 'import platform; print(platform.python_version())' 2>/dev/null)" minor
row "cocotb (test)" "$COCOTB_VERSION" "$(pyver cocotb)" "$(wbpyver cocotb)"
row "pytest (test)" "$PYTEST_VERSION" "$(pyver pytest)" "$(wbpyver pytest)"
row "Icarus (test)" "$ICARUS_TEST_VERSION" "$(icarus "$ROOT/icarus-12/bin/iverilog")" "$(icarus /foss/tools/bin/iverilog)"
row "Icarus (gl_test)" "$ICARUS_GL_VERSION" "$(icarus "$ROOT/icarus-13/bin/iverilog")" "$(icarus /foss/tools/bin/iverilog)"
here_pdk=$([ -f "$ROOT/pdk/sky130A/SOURCES" ] && cut -d' ' -f2 "$ROOT/pdk/sky130A/SOURCES" | head -1)
wb_pdk=$(cut -d' ' -f2 /foss/pdks/sky130A/SOURCES 2>/dev/null | head -1)
row "sky130A (gl_test)" "${SKY130_GL_PDK_COMMIT:0:12}" "${here_pdk:0:12}" "${wb_pdk:0:12}" exact optional
wb_ll=$(PYTHONPATH="$WB_PYTHONPATH" python3 -c 'import importlib.metadata as m; print(m.version("librelane"))' 2>/dev/null)
printf '%-22s %-14s %-14s %-14s %s\n' "LibreLane (gds)" "$LIBRELANE_VERSION" "-" "${wb_ll:--}" "not installed: the gds job runs on GitHub"

echo
if [ $bad -eq 0 ]; then
  echo "All pinned tools are installed at the runner's versions."
else
  echo "Something is missing or different. Run 'make install', then check again."
fi
exit $bad
