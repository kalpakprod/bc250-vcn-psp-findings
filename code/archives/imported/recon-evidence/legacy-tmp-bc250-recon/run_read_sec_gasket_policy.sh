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

restart_services() {
  sudo systemctl start "${services[@]}"
}
trap restart_services EXIT

sudo systemctl stop "${services[@]}"
timeout 45 sudo env \
  BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
  python3 -u /home/OWNER/vcn_unlock/read_sec_gasket_policy.py \
  2>&1 | tee /home/OWNER/vcn_unlock/read_sec_gasket_policy.out
