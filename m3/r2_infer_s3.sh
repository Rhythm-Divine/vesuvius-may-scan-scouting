#!/usr/bin/env bash
# S3: reader-v2 on one native 8.64 um surface volume, as m2/r2_infer.sh does for S2, with a list of 17-layer windows
# (WINDOWS, default "c p2 m2 p6 m6"). The model takes the central 17 layers of what it is given, so trimming layers
# from one end shifts the window: c = centred; p2 / m2 = +2 / -2 layers (S2's read); p6 / m6 = +6 / -6 layers (S3's
# deeper read, reaching 14 layers from the mesh instead of 10).
# Writes OUT/r2_<forward|reverse>_<window>.tif (uint8). Finished outputs are skipped, so a rerun resumes.
# Usage: WINDOWS="c p2 m2 p6 m6" bash m3/r2_infer_s3.sh ZARR OUT GPU [CPUS]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; . "$R/config.sh"
Z=$1; O=$2; G=$3; CPUS=${4:-0-47}
N=$R2_DIR; PY=$N/venv/bin/python; CK=$N/models/reader-v2-step040000.pth
mkdir -p "$O"
D=$($PY -c "import zarr; g = zarr.open('$Z', mode='r'); print((g['0'] if hasattr(g, 'keys') else g).shape[0])") || exit 1
for dir in forward reverse; do
  for w in ${WINDOWS:-c p2 m2 p6 m6}; do
    case $w in
      c) A="";;
      p2) A="--layer-start 4";;
      m2) A="--layer-end $((D - 4))";;
      p6) A="--layer-start 12";;
      m6) A="--layer-end $((D - 12))";;
      *) echo "unknown window $w"; exit 2;;
    esac
    out=$O/r2_${dir}_$w.tif
    [ -s "$out" ] && continue
    CUDA_VISIBLE_DEVICES=$G OMP_NUM_THREADS=4 nice -n 5 taskset -c $CPUS $PY -m koine_machines.inference.infer "$Z" "$CK" \
      "$out" --overlap 0.5 --blend-mode hann --direction $dir --batch-size 32 --num-workers 4 --no-compile $A \
      > "$O/r2_${dir}_$w.log" 2>&1 < /dev/null || { echo "reader-v2 failed: $Z $dir $w (see $O/r2_${dir}_$w.log)"; exit 1; }
  done
done
