#!/usr/bin/env bash
set -euo pipefail

services=(
  bc250-metrics
  bc250-gpu-watchdog
  bc250-pwrwatch
  bc250-telemetry
  bc250-dpwatch
  bc250-fan
  bc250-netconsole
)

systemctl stop "${services[@]}"

env PYTHONUNBUFFERED=1 \
  BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
  python3 -u /home/OWNER/vcn_unlock/bc250-smu-unlock/unlock.py

printf '%s\n' '=== POST-UNLOCK PROBE ==='
env BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
  python3 - <<'PY'
import sys
sys.path.insert(0, "/home/OWNER/vcn_unlock/bc250-smu-unlock")
from bc250_smu import Bc250Smu
smu = Bc250Smu()
try:
    status, value = smu.sec_smn_read32(0x0005A870)
    print(f"status=0x{status:02x} value=0x{value:08x} alive={smu.alive()}")
    if status != 0x01 or not smu.alive():
        raise SystemExit(2)
finally:
    smu.close()
PY

printf '%s\n' 'READY_FOR_WARM_REBOOT_TO_USB'
