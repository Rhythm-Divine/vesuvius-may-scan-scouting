#!/usr/bin/env python3
"""Run one job opportunistically on a shared GPU, and yield as soon as its owners need it.

Before starting (refusals exit 3, 4 or 5):
  * the reservation file (default /tmp/GPU_RESERVED, or env GPU_RESERVE_FILE) must be absent             -> else exit 3
  * the GPU must have at least --min-free-gb free                                   -> else exit 4
  * nvidia-smi must answer                                                          -> else exit 5
While the job runs (polled every --poll s), its whole process group is stopped with SIGTERM, then SIGKILL after
--grace s, if:
  * the reservation file appears                                                    -> exit 10
  * our processes use more than --max-own-gb of GPU memory                          -> exit 11
  * free GPU memory falls below --floor-gb while we hold any                        -> exit 12
  * nvidia-smi fails 3 polls in a row (we can no longer enforce the cap)            -> exit 5
Otherwise the job's own exit code is returned.

The job runs pinned with `taskset -c --cpus`, with OpenMP/BLAS threads capped at 1 and CUDA_VISIBLE_DEVICES set.
VESUVIUS_GPU_CAP_GB is exported so our own torch code can call torch.cuda.set_per_process_memory_fraction.
Stdlib only. Run it detached: setsid nohup python3 tools/gpu_guard.py --log L --pidfile P -- CMD ... &
"""
import argparse
import os
import signal
import subprocess
import sys
import time

EXIT_RESERVED, EXIT_LOW_FREE_START, EXIT_SMI = 3, 4, 5
EXIT_YIELD_RESERVED, EXIT_OVER_CAP, EXIT_YIELD_LOW_FREE = 10, 11, 12
THREAD_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
               "NUMBA_NUM_THREADS")


def log(fh, msg):
    fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} [gpu_guard] {msg}\n")
    fh.flush()


def smi(exe, query):
    out = subprocess.run([exe, query, "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"nvidia-smi exit {out.returncode}")
    return [[c.strip() for c in line.split(",")] for line in out.stdout.splitlines() if line.strip()]


def free_mib(exe, gpu):
    for row in smi(exe, "--query-gpu=index,memory.free"):
        if int(row[0]) == gpu:
            return int(row[1])
    raise RuntimeError(f"GPU {gpu} not listed by nvidia-smi")


def group_members(pgid):
    """PIDs whose process group is pgid, read from /proc (never pgrep -f)."""
    pids = set()
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as f:
                stat = f.read()
            fields = stat[stat.rindex(")") + 2:].split()  # comm may contain spaces; fields[2] is pgrp
            if int(fields[2]) == pgid:
                pids.add(int(d))
        except (OSError, ValueError, IndexError):
            continue
    return pids


def own_mib(exe, pgid):
    members = group_members(pgid)
    total = 0
    for row in smi(exe, "--query-compute-apps=pid,used_memory"):
        try:
            pid, mib = int(row[0]), int(row[1])
        except (ValueError, IndexError):
            continue  # e.g. "[N/A]"
        if pid in members:
            total += mib
    return total


def kill_group(proc, grace, fh):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        proc.wait()
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if proc.poll() is not None and not group_members(proc.pid):
            log(fh, "job group stopped")
            return
        time.sleep(0.2)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
        log(fh, "job group killed with SIGKILL")
    except ProcessLookupError:
        pass
    proc.wait()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reserve-file", default=os.environ.get("GPU_RESERVE_FILE", "/tmp/GPU_RESERVED"))
    ap.add_argument("--min-free-gb", type=float, default=8.0)
    ap.add_argument("--max-own-gb", type=float, default=4.0)
    ap.add_argument("--floor-gb", type=float, default=1.0)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--cpus", default=os.environ.get("CPUS") or f"0-{(os.cpu_count() or 1) - 1}",
                    help="taskset CPU list (default: env CPUS, else all CPUs)")
    ap.add_argument("--poll", type=float, default=10.0)
    ap.add_argument("--grace", type=float, default=20.0)
    ap.add_argument("--log", required=True)
    ap.add_argument("--pidfile", required=True)
    ap.add_argument("--nvidia-smi", default="nvidia-smi")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if not cmd:
        ap.error("missing command after --")

    with open(a.log, "a") as fh:
        if os.path.exists(a.reserve_file):
            log(fh, f"refuse: {a.reserve_file} present")
            return EXIT_RESERVED
        try:
            free = free_mib(a.nvidia_smi, a.gpu)
        except Exception as e:  # noqa: BLE001 - any failure means we cannot check, so we do not start
            log(fh, f"refuse: nvidia-smi failed: {e}")
            return EXIT_SMI
        if free < a.min_free_gb * 1024:
            log(fh, f"refuse: {free} MiB free < {a.min_free_gb} GB")
            return EXIT_LOW_FREE_START

        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(a.gpu), VESUVIUS_GPU_CAP_GB=str(a.max_own_gb),
                   **{v: "1" for v in THREAD_VARS})
        proc = subprocess.Popen(["taskset", "-c", a.cpus, *cmd], stdout=fh, stderr=subprocess.STDOUT, env=env,
                                start_new_session=True)
        with open(a.pidfile, "w") as pf:
            pf.write(f"{proc.pid}\n")
        log(fh, f"start pgid={proc.pid} free={free}MiB cpus={a.cpus} cap={a.max_own_gb}GB cmd={cmd}")

        got = {"sig": None}

        def on_signal(signum, _frame):
            got["sig"] = signum

        signal.signal(signal.SIGTERM, on_signal)
        signal.signal(signal.SIGINT, on_signal)
        smi_failures = 0
        while True:
            rc = proc.poll()
            if rc is not None:
                log(fh, f"job exited rc={rc}")
                return rc
            reason = None
            if got["sig"] is not None:
                reason = (f"guard received signal {got['sig']}", 128 + got["sig"])
            elif os.path.exists(a.reserve_file):
                reason = (f"{a.reserve_file} appeared", EXIT_YIELD_RESERVED)
            else:
                try:
                    own = own_mib(a.nvidia_smi, proc.pid)
                    free = free_mib(a.nvidia_smi, a.gpu)
                    smi_failures = 0
                    if own > a.max_own_gb * 1024:
                        reason = (f"own GPU use {own} MiB > cap {a.max_own_gb} GB", EXIT_OVER_CAP)
                    elif own > 0 and free < a.floor_gb * 1024:
                        reason = (f"free {free} MiB < floor {a.floor_gb} GB while holding {own} MiB",
                                  EXIT_YIELD_LOW_FREE)
                except Exception as e:  # noqa: BLE001
                    smi_failures += 1
                    log(fh, f"warn: nvidia-smi poll failed ({smi_failures}/3): {e}")
                    if smi_failures >= 3:
                        reason = ("nvidia-smi unavailable, cannot enforce the cap", EXIT_SMI)
            if reason:
                log(fh, f"yield: {reason[0]}")
                kill_group(proc, a.grace, fh)
                return reason[1]
            time.sleep(a.poll)


if __name__ == "__main__":
    sys.exit(main())
