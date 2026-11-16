#!/usr/bin/env bash
# Install the tools Tiny Tapeout's test and gl_test jobs use, at the runner's
# versions, inside the IIC-OSIC-TOOLS workbench. Everything goes under .local/
# next to this file, which is on your own disk (/foss/designs is the workspace
# folder), so it survives a container restart and nothing in the image changes.
#
#   ./install.sh                  python, icarus-12 and icarus-13
#   ./install.sh gl-pdk           the standard cells for a local gate-level test
#
# Parts: python  icarus-12  icarus-13  gl-pdk
# A part that finished before is skipped. Delete .local/<part>.ok to redo it.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pins.env
. "$HERE/pins.env"
ROOT="${TT_TOOLS_ROOT:-$HERE/.local}"
mkdir -p "$ROOT/dl"

# The workbench sets PYTHONPATH to its own Python 3.12 folders, and a 3.11
# interpreter that reads them breaks in confusing ways.
unset PYTHONPATH

PARTS=("$@")
[ ${#PARTS[@]} -gt 0 ] || PARTS=(python icarus-12 icarus-13)

log() { printf '\n== %s\n' "$*"; }
die() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }

# fetch URL SHA256 FILE: download once, and refuse a file whose checksum differs.
fetch() {
  local url=$1 sha=$2 out=$3
  if [ -f "$out" ] && echo "$sha  $out" | sha256sum -c --status; then return 0; fi
  curl -fsSL --retry 3 -o "$out.part" "$url" || die "could not download $url"
  echo "$sha  $out.part" | sha256sum -c --status || die "checksum mismatch for $url"
  mv "$out.part" "$out"
}

done_already() { [ -f "$ROOT/$1.ok" ] && [ "$(cat "$ROOT/$1.ok")" = "$2" ]; }
mark_done() { echo "$2" > "$ROOT/$1.ok"; }

part_python() {
  local stamp="python $PYTHON_VERSION $(sha256sum "$HERE/requirements.txt" | cut -c1-12)"
  done_already python "$stamp" && { echo "python: already installed"; return; }
  command -v uv >/dev/null || die "uv not found; the workbench image ships it in /foss/tools/bin"
  export UV_PYTHON_INSTALL_DIR="$ROOT/python" UV_CACHE_DIR="$ROOT/cache/uv"
  uv python install "$PYTHON_VERSION"
  rm -rf "$ROOT/venv"
  uv venv --python "$PYTHON_VERSION" "$ROOT/venv"
  uv pip install --python "$ROOT/venv/bin/python" -r "$HERE/requirements.txt"
  mark_done python "$stamp"
}

# install_icarus NAME VERSION URL SHA LIBDIR: unpack an Icarus package and put
# two small wrappers in front of it. The binaries look for their helper
# programs (ivl, ivlpp) and VPI modules (system.vpi) in the folder they were
# built for, /usr/lib/..., so the wrappers point them at the unpacked copy.
install_icarus() {
  local name=$1 version=$2 url=$3 sha=$4 libdir=$5
  local dir="$ROOT/$name" deb
  done_already "$name" "$version" && { echo "$name: already installed"; return; }
  deb="$ROOT/dl/$(basename "$url")"
  fetch "$url" "$sha" "$deb"
  rm -rf "$dir" && mkdir -p "$dir/bin"
  dpkg-deb -x "$deb" "$dir/pkg"
  cat > "$dir/bin/iverilog" <<EOF
#!/usr/bin/env bash
# Icarus Verilog $version, unpacked from $(basename "$url") (install.sh).
exec "$dir/pkg/usr/bin/iverilog" -B"$dir/pkg/$libdir" "\$@"
EOF
  cat > "$dir/bin/vvp" <<EOF
#!/usr/bin/env bash
# Icarus Verilog $version, unpacked from $(basename "$url") (install.sh).
exec "$dir/pkg/usr/bin/vvp" -M"$dir/pkg/$libdir" "\$@"
EOF
  chmod +x "$dir/bin/iverilog" "$dir/bin/vvp"
  "$dir/bin/iverilog" -V 2>/dev/null | head -1 | grep -q "version $version " \
    || die "$name doesn't report Icarus Verilog version $version"
  mark_done "$name" "$version"
}

part_gl_pdk() {
  done_already gl-pdk "$SKY130_GL_PDK_COMMIT" && { echo "gl-pdk: already installed"; return; }
  command -v uv >/dev/null || die "uv not found; the workbench image ships it in /foss/tools/bin"
  # ciel, the PDK installer the runner uses, in a venv of its own so that the
  # test venv stays identical to the runner's test job.
  export UV_PYTHON_INSTALL_DIR="$ROOT/python" UV_CACHE_DIR="$ROOT/cache/uv"
  uv python install "$PYTHON_VERSION"
  [ -x "$ROOT/ciel-venv/bin/ciel" ] || {
    uv venv --python "$PYTHON_VERSION" "$ROOT/ciel-venv"
    uv pip install --python "$ROOT/ciel-venv/bin/python" -r "$HERE/requirements-ciel.txt"
  }
  # gl_test reads only the sky130_fd_sc_hd Verilog models, so fetch only that
  # library instead of the whole PDK.
  "$ROOT/ciel-venv/bin/ciel" enable --pdk-root "$ROOT/pdk" --pdk-family sky130 \
    --include-libraries sky130_fd_sc_hd "$SKY130_GL_PDK_COMMIT"
  grep -q "$SKY130_GL_PDK_COMMIT" "$ROOT/pdk/sky130A/SOURCES" \
    || die "sky130A/SOURCES does not name $SKY130_GL_PDK_COMMIT"
  # ciel unpacks both variants of the PDK, and gl_test reads only sky130A.
  rm -rf "$ROOT/pdk/ciel/sky130/versions/$SKY130_GL_PDK_COMMIT/sky130B" "$ROOT/pdk/sky130B"
  mark_done gl-pdk "$SKY130_GL_PDK_COMMIT"
}

for p in "${PARTS[@]}"; do
  log "$p"
  start=$SECONDS
  case "$p" in
    python) part_python ;;
    icarus-12) install_icarus icarus-12 "$ICARUS_TEST_VERSION" "$ICARUS_TEST_DEB_URL" "$ICARUS_TEST_DEB_SHA256" usr/lib/x86_64-linux-gnu/ivl ;;
    icarus-13) install_icarus icarus-13 "$ICARUS_GL_VERSION" "$ICARUS_GL_DEB_URL" "$ICARUS_GL_DEB_SHA256" usr/lib/ivl ;;
    gl-pdk) part_gl_pdk ;;
    *) die "unknown part '$p' (python, icarus-12, icarus-13, gl-pdk)" ;;
  esac
  printf '%s: %d s\n' "$p" $((SECONDS - start))
done
rm -rf "$ROOT/cache" "$ROOT/dl"
log "done. Check with: make check-tools"
