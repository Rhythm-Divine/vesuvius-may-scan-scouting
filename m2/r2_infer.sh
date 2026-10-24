#!/usr/bin/env bash
# S2: reader-v2 (domenicor046/reader-v2, step 40000) on one native 8.64 um surface volume (OME-Zarr, level "0", depth
# first), through villa's koine_machines (merge-ink-pipelines, 47a9c37), installed by setup_reader_v2.sh into $R2_DIR.
# Forward and reverse, each with three 17-layer depth windows: centred, +2 and -2 layers, as reader-v2's "best quality"
# mode averages. The windows come from --layer-start 4 (+2) and --layer-end D-4 (-2); the model takes the central 17
# layers of what it is given.
# Writes OUT/r2_<forward|reverse>_<c|p2|m2>.tif (uint8). Finished outputs are skipped, so a rerun resumes.
# Usage: bash m2/r2_infer.sh ZARR OUT GPU [CPUS]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; . "$R/config.sh"
Z=$1; O=$2; G=$3; CPUS=${4:-0-$(( $(nproc) - 1 ))}
PY2=$R2_DIR/venv/bin/python; CK=$R2_DIR/models/reader-v2-step040000.pth
mkdir -p "$O"
D=$($PY2 -c "import zarr; g = zarr.open('$Z', mode='r'); print((g['0'] if hasattr(g, 'keys') else g).shape[0])") || exit 1
for dir in forward reverse; do
  for w in c p2 m2; do
    case $w in c) A="";; p2) A="--layer-start 4";; m2) A="--layer-end $((D - 4))";; esac
    out=$O/r2_${dir}_$w.tif
    [ -s "$out" ] && continue
    CUDA_VISIBLE_DEVICES=$G OMP_NUM_THREADS=$THREADS nice -n $NICE taskset -c $CPUS $PY2 -m koine_machines.inference.infer \
      "$Z" "$CK" "$out" --overlap 0.5 --blend-mode hann --direction $dir --batch-size 32 --num-workers 4 --no-compile $A \
      > "$O/r2_${dir}_$w.log" 2>&1 < /dev/null || { echo "reader-v2 failed: $Z $dir $w (see $O/r2_${dir}_$w.log)"; exit 1; }
  done
done
