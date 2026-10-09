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
set -o pipefail
timeout 120 sudo env \
  BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
  python3 -u /home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable/enable_vcn.py "$@" \
  2>&1 | tee /home/OWNER/vcn_unlock/clock_enable_after_coldboot.out
