#!/usr/bin/env bash
# Optional setup for the S2 second read: reader-v2 (MIT, Hugging Face domenicor046/reader-v2) and villa's ink-detection
# package (koine_machines, MIT, ScrollPrize/villa branch merge-ink-pipelines at 47a9c37) in their own locked environment.
# Needs git, curl and uv (`pip install uv`), and about 9 GB of disk. uv fetches a managed CPython 3.12: the locked
# numcodecs 0.15.1 has no wheel for newer Pythons. Everything goes under $R2_DIR (default third_party/reader-v2).
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$R"; . "$R/config.sh"
UV="${UV:-uv}"
mkdir -p "$R2_DIR/models"
[ -d "$R2_DIR/villa" ] || git clone -q --branch merge-ink-pipelines --filter=blob:limit=5m \
  https://github.com/ScrollPrize/villa "$R2_DIR/villa"
( cd "$R2_DIR/villa" && git checkout -q 47a9c37f6f8e99afdab47bb46ad425aa726f5dc0 )
for f in reader-v2-step040000.pth train_config.json; do
  [ -s "$R2_DIR/models/$f" ] || curl -sSL --fail -o "$R2_DIR/models/$f" \
    "https://huggingface.co/domenicor046/reader-v2/resolve/main/$f"
done
( cd "$R2_DIR/models" && grep -E ' (reader-v2-step040000\.pth|train_config\.json)$' "$R/SHA256SUMS.models" | sha256sum -c - )
( cd "$R2_DIR/villa/ink-detection" && UV_PROJECT_ENVIRONMENT="$R2_DIR/venv" "$UV" sync --frozen --python 3.12 )
"$R2_DIR/venv/bin/python" -c "import torch, koine_machines; print('reader-v2 env: torch', torch.__version__, 'cuda', torch.cuda.is_available())"
