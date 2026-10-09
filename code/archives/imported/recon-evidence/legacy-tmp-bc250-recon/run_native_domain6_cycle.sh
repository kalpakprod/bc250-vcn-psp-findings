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

timeout 120 sudo env \
  BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
  python3 -u /home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable/enable_vcn.py \
  2>&1 | tee /home/OWNER/vcn_unlock/native_cycle_clock_enable.out

timeout 120 sudo env \
  BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
  python3 -u /home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable/enable_vcn.py --manual-powerup \
  2>&1 | tee /home/OWNER/vcn_unlock/native_cycle_manual_powerup.out

timeout 120 sudo env \
  BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
  python3 -u /home/OWNER/vcn_unlock/native_domain6_cycle.py \
  2>&1 | tee /home/OWNER/vcn_unlock/native_domain6_cycle.out
