#!/usr/bin/env bash
set -euo pipefail

# Build PyInstaller bundle for macOS/Linux
# Usage: ./scripts/build_desktop.sh

cd "$(dirname "$0")/.."

if ! command -v pyinstaller >/dev/null 2>&1; then
  python3 -m pip install --upgrade pip
  python3 -m pip install pyinstaller
fi

python3 -m pip install -r requirements.txt

pyinstaller --noconfirm --windowed --name Threesome \
  --collect-all kivy \
  --add-data "ui/widgets.kv:ui" \
  --add-data "ui/assets:ui/assets" \
  main.py

# Output at dist/Threesome
