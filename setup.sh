#!/usr/bin/env bash
# One-time setup: a Python venv with requirements.txt, the Hecate 9.6 um model (MIT, Hugging Face scrollprize/hecate),
# and the VC3D AppImage built from ScrollPrize/villa at 406e767 (GPL-3.0; called as a program, never copied).
# Downloads ~0.6 GB (model) + the AppImage. Scan data is streamed later from the public open-data bucket.
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$R"
PYTHON="${PYTHON:-python3}"
[ -x .venv/bin/python ] || "$PYTHON" -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
H=third_party/hecate; mkdir -p "$H"
for f in hecate.py hecate_9.6um.pth LICENSE README.md; do
  [ -s "$H/$f" ] || curl -sSL --fail -o "$H/$f" "https://huggingface.co/scrollprize/hecate/resolve/main/$f"
done
( cd "$H" && grep ' hecate' ../../SHA256SUMS.models | sha256sum -c - )
V=third_party/vc3d; mkdir -p "$V"
if [ ! -x "$V/squashfs-root/AppRun" ]; then
  if [ ! -s "$V/VC3D.AppImage" ]; then
    echo "Download the VC3D AppImage for villa 406e767 (Linux x86_64) from the ScrollPrize/villa releases page to"
    echo "  $R/$V/VC3D.AppImage"
    echo "(we used VC3D-406e767-2026-10-21-linux-x86_64.AppImage, sha256 in SHA256SUMS.models), then re-run setup.sh."
    exit 2
  fi
  chmod +x "$V/VC3D.AppImage"
  ( cd "$V" && ./VC3D.AppImage --appimage-extract > /dev/null )
fi
echo "setup done: $( .venv/bin/python -c 'import torch; print("torch", torch.__version__, "cuda", torch.cuda.is_available())')"
