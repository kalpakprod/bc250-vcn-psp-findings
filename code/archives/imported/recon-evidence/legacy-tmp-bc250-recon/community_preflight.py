#!/usr/bin/env python3
"""Serialized, non-unlocking BC-250 SMU and gpu_metrics preflight."""
from __future__ import annotations

import json
import os
import signal
import struct
import sys
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(LIB))

from bc250_smu import Bc250Smu  # noqa: E402

GPU_METRICS_PATHS = (
    Path("/sys/class/drm/card1/device/gpu_metrics"),
    Path("/sys/class/drm/card0/device/gpu_metrics"),
)
METRICS_LAYOUT = (
    "<HBB" + "HH" + "8H" + "2H" + "HH" + "Q" + "HHHH" + "8H"
    + "6H" + "6H" + "8H" + "2H" + "I" + "H" + "3H" + "Q"
)
METRICS_FIELDS = [
    "size", "fmt", "content",
    "temp_gfx", "temp_soc",
    *[f"temp_core{i}" for i in range(8)],
    "temp_l3_0", "temp_l3_1",
    "activity_gfx", "activity_mm",
    "clock_counter",
    "power_socket", "power_cpu", "power_soc", "power_gfx",
    *[f"power_core{i}" for i in range(8)],
    "avg_gfxclk", "avg_socclk", "avg_uclk", "avg_fclk", "avg_vclk", "avg_dclk",
    "cur_gfxclk", "cur_socclk", "cur_uclk", "cur_fclk", "cur_vclk", "cur_dclk",
    *[f"coreclk{i}" for i in range(8)],
    "l3clk_0", "l3clk_1",
    "throttle", "fan_pwm", "pad0", "pad1", "pad2", "independent_throttle",
]


def _alarm(_signum: int, _frame: object) -> None:
    raise TimeoutError("gpu_metrics read timed out")


def read_gpu_metrics() -> dict[str, int | str]:
    path = next((candidate for candidate in GPU_METRICS_PATHS if candidate.exists()), None)
    if path is None:
        return {"error": "gpu_metrics not found"}

    old_handler = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(3)
    try:
        raw = path.read_bytes()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    expected = struct.calcsize(METRICS_LAYOUT)
    if len(raw) < expected:
        return {"error": f"short gpu_metrics: {len(raw)} < {expected}", "path": str(path)}
    values = dict(zip(METRICS_FIELDS, struct.unpack_from(METRICS_LAYOUT, raw, 0)))
    keep = (
        "size", "fmt", "content", "cur_gfxclk", "cur_socclk", "cur_uclk",
        "cur_fclk", "cur_vclk", "cur_dclk", "avg_vclk", "avg_dclk", "activity_mm",
    )
    return {"path": str(path), **{key: int(values[key]) for key in keep}}


def attempt(name: str, callback) -> dict[str, object]:
    try:
        return {"ok": True, "value": callback()}
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}


def main() -> int:
    result: dict[str, object] = {
        "bios": Path("/sys/class/dmi/id/bios_version").read_text().strip(),
        "kernel": os.uname().release,
    }
    result["gpu_metrics"] = attempt("gpu_metrics", read_gpu_metrics)

    smu = Bc250Smu(bdf="0000:00:00.0", timeout=5.0)
    try:
        result["smu_alive"] = attempt("smu_alive", smu.alive)
        result["test_message"] = attempt("test_message", lambda: smu.test_message(0x1234))
        result["smu_version"] = attempt("smu_version", lambda: hex(smu._get_smu_version()[1]))
        result["enabled_features"] = attempt(
            "enabled_features", lambda: hex(smu.get_enabled_smu_features())
        )
        result["active_wgp"] = attempt("active_wgp", smu.query_active_wgp)
        result["secure_access_enabled"] = attempt(
            "secure_access_enabled", smu.secure_access_enabled
        )
    finally:
        smu.close()

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("smu_alive", {}).get("value") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
