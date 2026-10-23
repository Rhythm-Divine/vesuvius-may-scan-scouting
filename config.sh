# Shared settings for the kit's shell jobs, sourced by every *.sh after it sets R (the repo root).
# Every value can be overridden from the environment, e.g. `CPUS=0-7 NICE=19 bash m1/grow_more.sh ...`.
: "${VES_ROOT:=$R}"; export VES_ROOT
: "${PY:=$VES_ROOT/.venv/bin/python}"                               # Python with requirements.txt installed
: "${VC3D:=$VES_ROOT/third_party/vc3d/squashfs-root/AppRun}"        # extracted VC3D AppImage (villa 406e767)
: "${HECATE_DIR:=$VES_ROOT/third_party/hecate}"                     # hecate.py + hecate_9.6um.pth (Hugging Face)
: "${THREADS:=4}"                                                    # CPU threads for numpy/scipy/torch steps
: "${GROW_THREADS:=8}"                                               # GrowPatch thread_limit
: "${NICE:=10}"                                                      # CPU priority of every job
RUN="nice -n $NICE"
if [ -n "${CPUS:-}" ]; then RUN="$RUN taskset -c $CPUS"; fi          # optional CPU pinning
# GPU: Hecate always runs through tools/gpu_guard.py, which refuses to start below GPU_MIN_FREE_GB free memory, stops
# the job if it grows past GPU_MAX_OWN_GB, and yields at once if GPU_RESERVE_FILE appears (for shared GPUs).
: "${GPU_MIN_FREE_GB:=8}"; : "${GPU_MAX_OWN_GB:=4}"; : "${GPU_RESERVE_FILE:=/tmp/GPU_RESERVED}"
GUARD_ARGS="--poll 5 --min-free-gb $GPU_MIN_FREE_GB --max-own-gb $GPU_MAX_OWN_GB --reserve-file $GPU_RESERVE_FILE"
if [ -n "${CPUS:-}" ]; then GUARD_ARGS="$GUARD_ARGS --cpus $CPUS"; fi
gpu_reserved () { [ -e "$GPU_RESERVE_FILE" ]; }
mkdir -p "$VES_ROOT/cache/tmp" "$VES_ROOT/logs"
export PY VC3D HECATE_DIR THREADS GROW_THREADS NICE RUN GUARD_ARGS GPU_RESERVE_FILE
