#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/tailwindcss -i app/static/css/input.css -o app/static/css/app.css --minify "$@"
