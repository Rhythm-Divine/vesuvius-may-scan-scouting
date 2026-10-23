"""Tests for tools/gpu_guard.py against a fake nvidia-smi (the real GPU is never touched). Linux only."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tools" / "gpu_guard.py"
FAKE = Path(__file__).resolve().parent / "fake_nvidia_smi.py"
pytestmark = pytest.mark.skipif(not Path("/proc/self/stat").exists(), reason="needs Linux /proc")

sys.path.insert(0, str(ROOT / "tools"))
from gpu_guard import group_members  # noqa: E402


def _cpu():
    return str(min(os.sched_getaffinity(0)))


@pytest.fixture
def ctx(tmp_path):
    state = tmp_path / "state.json"
    smi = tmp_path / "nvidia-smi"
    smi.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
    smi.chmod(0o755)
    c = {"tmp": tmp_path, "state": state, "smi": smi, "reserve": tmp_path / "RESERVED",
         "pidfile": tmp_path / "job.pid", "log": tmp_path / "guard.log",
         "env": dict(os.environ, FAKE_NVSMI_STATE=str(state))}
    _set(c, free_mib=20000)
    return c


def _set(c, **state):
    tmp = c["state"].with_suffix(".tmp")
    tmp.write_text(json.dumps({"free_mib": 20000, "apps": [], **state}))
    os.replace(tmp, c["state"])


def _start(c, *cmd):
    args = [sys.executable, str(GUARD), "--reserve-file", str(c["reserve"]), "--nvidia-smi", str(c["smi"]),
            "--cpus", _cpu(), "--poll", "0.2", "--grace", "2", "--log", str(c["log"]), "--pidfile", str(c["pidfile"]),
            "--", *cmd]
    return subprocess.Popen(args, env=c["env"])


def _pgid(c, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if c["pidfile"].exists() and c["pidfile"].read_text().strip():
            return int(c["pidfile"].read_text())
        time.sleep(0.05)
    raise AssertionError("job never started")


def test_refuses_when_reserved(ctx):
    ctx["reserve"].touch()
    marker = ctx["tmp"] / "ran"
    assert _start(ctx, "touch", str(marker)).wait(10) == 3
    assert not marker.exists()


def test_refuses_when_too_little_free(ctx):
    _set(ctx, free_mib=4000)
    assert _start(ctx, "true").wait(10) == 4


def test_refuses_when_smi_fails(ctx):
    _set(ctx, fail=True)
    assert _start(ctx, "true").wait(10) == 5


def test_returns_job_exit_code(ctx):
    assert _start(ctx, "sh", "-c", "exit 7").wait(10) == 7


def test_caps_threads_and_pins_cpu(ctx):
    check = ("import os,sys; ok = os.environ['OMP_NUM_THREADS'] == '1' and os.environ['CUDA_VISIBLE_DEVICES'] == '0'"
             f" and os.sched_getaffinity(0) == {{{_cpu()}}}; sys.exit(0 if ok else 9)")
    assert _start(ctx, sys.executable, "-c", check).wait(10) == 0


def test_yields_when_reservation_appears(ctx):
    p = _start(ctx, "sh", "-c", "sleep 30 & sleep 30")
    pgid = _pgid(ctx)
    time.sleep(0.5)
    ctx["reserve"].touch()
    assert p.wait(10) == 10
    assert not group_members(pgid)  # the background child was stopped too


def test_kills_job_over_its_cap(ctx):
    p = _start(ctx, "sleep", "30")
    _set(ctx, apps=[[_pgid(ctx), 5000]])
    assert p.wait(10) == 11


def test_yields_on_low_free_only_while_holding(ctx):
    p = _start(ctx, "sleep", "30")
    pgid = _pgid(ctx)
    _set(ctx, free_mib=500)  # low, but we hold nothing: keep running
    time.sleep(1.0)
    assert p.poll() is None
    _set(ctx, free_mib=500, apps=[[pgid, 1000]])
    assert p.wait(10) == 12
    assert "yield: free 500 MiB" in ctx["log"].read_text()
