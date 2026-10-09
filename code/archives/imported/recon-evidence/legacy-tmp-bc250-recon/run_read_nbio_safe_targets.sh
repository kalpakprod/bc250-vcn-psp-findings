#!/usr/bin/env bash
set -u

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
  python3 -u /home/OWNER/vcn_unlock/read_nbio_safe_targets.py \
  2>&1 | tee /home/OWNER/vcn_unlock/read_nbio_safe_targets.out
