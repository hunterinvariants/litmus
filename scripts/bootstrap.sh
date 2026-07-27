#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
git submodule sync --recursive
git submodule update --init --recursive
test "$(git -C lib/forge-std rev-parse HEAD)" = "81df7a1a97ab719d65013ab6e6369a58835b882c"
python3 -m pip install -r requirements-dev.txt
