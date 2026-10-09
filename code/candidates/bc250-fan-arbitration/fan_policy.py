"""Pure BC250 fan minimum arbitration. No hardware access or service actions."""
from __future__ import annotations
import argparse
import json
import time

FAN_PRESETS = ("quiet", "balanced", "boost", "automatic")
FAN_CHANNELS = (2, 3, 4, 5)
FAN_MIN_PERCENT = 20
FAN_MAX_PERCENT = 100
FAN_MINIMUM_PWM = 85
TELEMETRY_MAX_AGE_SECONDS = 5.0

def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer from {low} to {high}")
    return value

def choose_pwm(automatic_pwm: int, manual_percent: int | None = None,
               minimum_pwm: int = 85) -> int:
    automatic = _integer(automatic_pwm, 0, 255, "automatic PWM")
    minimum = _integer(minimum_pwm, 0, 255, "minimum PWM")
    requested = 0 if manual_percent is None else round(
        _integer(manual_percent, 20, 100, "manual percentage") * 255 / 100)
    return max(automatic, minimum, requested)

def validate_preset(preset: object) -> str:
    if preset not in FAN_PRESETS:
        raise ValueError("Unsupported system-fan preset.")
    return str(preset)

def validate_channel(channel: object) -> int:
    if isinstance(channel, bool) or type(channel) not in {int, str}:
        raise ValueError("Unsupported Quick Access fan channel.")
    try:
        normalized = int(channel)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Unsupported Quick Access fan channel.") from exc
    if str(normalized) != str(channel) or normalized not in FAN_CHANNELS:
        raise ValueError("Unsupported Quick Access fan channel.")
    return normalized

def validate_manual_target(target: object) -> str:
    """Allowlist for fan-channel write target: 'automatic' or 20-100 as str."""
    if target == "automatic":
        return "automatic"
    if isinstance(target, bool) or type(target) not in {int, str}:
        raise ValueError("Fan speed must be Automatic or 20-100%.")
    try:
        percent = int(target)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Fan speed must be Automatic or 20-100%.") from exc
    if str(percent) != str(target) or not FAN_MIN_PERCENT <= percent <= FAN_MAX_PERCENT:
        raise ValueError("Fan speed must be Automatic or 20-100%.")
    return str(percent)

def is_telemetry_stale(sample_mtime: float, now: float | None = None,
                       max_age: float = TELEMETRY_MAX_AGE_SECONDS) -> bool:
    """Pure stale-state check: True means caller must refuse to use the sample."""
    if now is None:
        now = time.time()
    try:
        age = float(now) - float(sample_mtime)
    except (TypeError, ValueError):
        return True
    return not (0 <= age <= float(max_age))

def decide_arbitration(*, automatic_pwm: int, manual_percent: int | None,
                       legacy_service_active: bool,
                       governor_conflict: bool = False,
                       minimum_pwm: int = FAN_MINIMUM_PWM) -> dict:
    """Pure service-arbitration decision. Never touches hardware/services.

    Returns dict with keys: ok, pwm, stop_legacy, resume_legacy, mode, error.
    - governor_conflict (cyan+oberon both active) refuses the write.
    - manual mode pauses legacy curve; automatic/failed-manual resumes it.
    - thermal floor (max of automatic/minimum/requested) is never weakened.
    """
    if governor_conflict:
        return {"ok": False, "pwm": None, "stop_legacy": False,
                "resume_legacy": False, "mode": "refused",
                "error": "Cyan and Oberon governors are both active. Stop one from Desktop Mode."}
    try:
        pwm = choose_pwm(automatic_pwm, manual_percent, minimum_pwm)
    except ValueError as exc:
        # Failed write: do not pause legacy; resume path stays with legacy.
        return {"ok": False, "pwm": None, "stop_legacy": False,
                "resume_legacy": bool(legacy_service_active), "mode": "failed",
                "error": str(exc)}
    if manual_percent is None:
        return {"ok": True, "pwm": pwm, "stop_legacy": False,
                "resume_legacy": bool(legacy_service_active), "mode": "automatic",
                "error": ""}
    return {"ok": True, "pwm": pwm,
            "stop_legacy": bool(legacy_service_active),
            "resume_legacy": False, "mode": "manual-minimum", "error": ""}

def rollback_record(*, previous_pwm: int, previous_mode: str,
                    attempted_mode: str, succeeded: bool) -> dict:
    """Pure rollback metadata: what to restore after a failed write."""
    _integer(previous_pwm, 0, 255, "previous PWM")
    if previous_mode not in ("automatic", "manual-minimum"):
        raise ValueError("previous mode must be automatic or manual-minimum")
    if attempted_mode not in ("automatic", "manual-minimum"):
        raise ValueError("attempted mode must be automatic or manual-minimum")
    return {
        "restore_pwm": previous_pwm,
        "restore_mode": previous_mode,
        "attempted_mode": attempted_mode,
        "needs_rollback": not succeeded,
        "resume_legacy": previous_mode == "automatic",
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--automatic", type=int, required=True)
    parser.add_argument("--manual", default="auto")
    args = parser.parse_args()
    requested = None if args.manual == "auto" else int(args.manual)
    print(json.dumps({"pwm": choose_pwm(args.automatic, requested),
                      "mode": "automatic" if requested is None else "manual-minimum"}))
