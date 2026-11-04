#!/usr/bin/env bash
# Rasterize an SVG to a 1580x800 PNG with headless Google Chrome.
# Usage: svg_to_png.sh IN.svg OUT.png
# Exit: 0 ok (prints OUT path), 2 usage / input missing / output dir missing,
#       3 Chrome missing, 4 Chrome produced no file, 5 PNG is not 1580x800.
# Set CHROME to override the browser binary path.
set -euo pipefail

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
W=1580; H=800

[ $# -eq 2 ] || { echo "usage: $0 IN.svg OUT.png" >&2; exit 2; }
[ -f "$1" ] || { echo "error: input not found: $1" >&2; exit 2; }
[ -d "$(dirname "$2")" ] || { echo "error: output directory does not exist: $(dirname "$2")" >&2; exit 2; }
if [ ! -x "$CHROME" ]; then
  echo "error: Google Chrome not found at: $CHROME" >&2
  echo "Ship the SVG instead and tell the user the PNG was not produced." >&2
  exit 3
fi

IN="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT_DIR="$(cd "$(dirname "$2")" && pwd)"
OUT="$OUT_DIR/$(basename "$2")"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Inline the SVG in a zero-margin page so Chrome lays it out at exactly WxH.
{
  printf '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;width:%spx;height:%spx;overflow:hidden;background:#fff}svg{display:block}</style></head><body>' "$W" "$H"
  cat "$IN"
  printf '</body></html>'
} > "$TMP/page.html"

# Remove any previous output so a stale file can never pass as success.
rm -f "$OUT"

status=0
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
  --user-data-dir="$TMP/profile" --force-device-scale-factor=1 \
  --window-size="$W,$H" --screenshot="$OUT" "file://$TMP/page.html" >"$TMP/chrome.log" 2>&1 || status=$?

if [ ! -s "$OUT" ]; then
  echo "error: Chrome produced no output at $OUT (Chrome exit status $status)" >&2
  tail -n 10 "$TMP/chrome.log" >&2 || true
  echo "If this ran inside a sandbox, re-run outside it; Chrome cannot launch sandboxed." >&2
  exit 4
fi

# Verify the PNG IHDR dimensions.
python3 - "$OUT" "$W" "$H" <<'PY' || exit 5
import struct, sys
path, w, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
with open(path, "rb") as f:
    data = f.read(24)
gw, gh = struct.unpack(">II", data[16:24]) if len(data) >= 24 else (0, 0)
if (gw, gh) != (w, h):
    sys.stderr.write(f"error: PNG is {gw}x{gh}, expected {w}x{h}\n")
    sys.exit(1)
PY

echo "$OUT"
