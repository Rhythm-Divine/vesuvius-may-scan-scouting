#!/usr/bin/env bash
# E1: dense displacement field from align4's tiles (align5), then rescore every transfer (score4). CPU only.
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; D="$R/data/e1"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS NUMEXPR_NUM_THREADS=$THREADS \
       NUMBA_NUM_THREADS=$THREADS CUDA_VISIBLE_DEVICES=""
T="$RUN"
echo "== $(date -u +%FT%TZ) align5"
$T "$PY" e1/align5.py --e1 "$D" || exit 1
echo "== $(date -u +%FT%TZ) score4"
$T "$PY" e1/score4.py --e1 "$D" "$D/pred_win_fwd.png" "$D/pred_win_rev.png"
echo "== $(date -u +%FT%TZ) E1-field DONE"
