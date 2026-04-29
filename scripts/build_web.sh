#!/usr/bin/env bash
set -euo pipefail

# Build a browser-playable version of Bubble Dungeon with Pygbag.
# Output: build/web/
uvx --from pygbag==0.9.2 pygbag --build .
