#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8010}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT_DIR/build/web"

if [[ ! -f "$WEB_DIR/index.html" ]]; then
  echo "build/web/index.html introuvable. Lance d'abord: scripts/build_web.sh" >&2
  exit 1
fi

cd "$WEB_DIR"
python3 -m http.server "$PORT" --bind 0.0.0.0
