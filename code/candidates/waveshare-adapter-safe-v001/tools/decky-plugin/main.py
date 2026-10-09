"""Read-only Decky client of the single localhost telemetry endpoint. No root, installs or power writes."""

import asyncio
import datetime
import json
import math
from urllib.request import ProxyHandler, build_opener


def sanitized_status(data):
    """Unknown/stale data remains unavailable; never accept arbitrary remote labels/keys."""
    if (
        not isinstance(data, dict)
        or data.get("schema") != 1
        or data.get("source") != "linux_hwmon"
        or data.get("board_identity") != "bc250"
    ):
        raise ValueError("unexpected telemetry source")
    stamp = datetime.datetime.fromisoformat(data["observed_at"])
    if stamp.tzinfo is None:
        raise ValueError("missing timestamp timezone")
    age = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds()
    if age < 0 or age > 5:
        return {"available": False, "state": "stale", "metrics": []}
    metrics = []
    for item in data.get("metrics", [])[:128]:
        if (
            not isinstance(item, dict)
            or item.get("source")
            not in ("k10temp", "amdgpu", "nct6683", "nct6687", "nct6686", "nvme")
            or item.get("unit") not in ("°C", "RPM", "W", "V", "A")
        ):
            continue
        value = item.get("value")
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or item.get("valid") is not True
        ):
            continue
        label = item.get("label")
        if not isinstance(label, str) or len(label) > 48:
            continue
        metrics.append(
            {
                "label": label,
                "value": value,
                "unit": item["unit"],
                "source": item["source"],
                "valid": True,
            }
        )
    return {
        "available": True,
        "state": "fresh",
        "power": "unknown",
        "observed_at": data["observed_at"],
        "metrics": metrics,
    }


def read_status():
    """Fixed loopback URL; no external credential/proxy use."""
    with build_opener(ProxyHandler({})).open(
        "http://127.0.0.1:8766/status.json", timeout=1
    ) as response:
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("telemetry response too large")
    return sanitized_status(json.loads(raw))


class Plugin:
    """Decky template API; status only, no root flag or migrations."""

    async def status(self):
        try:
            return await asyncio.to_thread(read_status)
        except Exception:
            return {"available": False, "state": "unavailable", "metrics": []}

    async def _main(self):
        """No service start, file mutation or automatic action."""

    async def _unload(self):
        """No owned background tasks to stop."""
