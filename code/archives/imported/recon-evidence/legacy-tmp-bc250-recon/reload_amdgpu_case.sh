#!/usr/bin/env bash
set -u

mode=${1:-0}
vcn=${2:-0}
fw_load_type=${3:--1}
label=${4:-case}
services=(
  bc250-metrics bc250-gpu-watchdog bc250-pwrwatch bc250-telemetry
  bc250-dpwatch bc250-fan bc250-netconsole
)
active_services=()
for service in "${services[@]}"; do
  if systemctl is-active --quiet "$service"; then
    active_services+=("$service")
  fi
done
restart_services() {
  if ((${#active_services[@]})); then
    sudo systemctl start "${active_services[@]}" || true
  fi
}
trap restart_services EXIT

sudo systemctl stop "${active_services[@]}" 2>/dev/null || true
start_time=$(date --iso-8601=seconds)

echo "=== $label: REMOVE CURRENT MODULE ==="
sudo modprobe -r amdgpu
remove_rc=$?
echo "remove_rc=$remove_rc"
if ((remove_rc != 0)); then
  exit "$remove_rc"
fi

echo "=== $label: LOAD mode=$mode vcn=$vcn fw_load_type=$fw_load_type ==="
timeout 35 sudo modprobe amdgpu \
  "bc250_cc_write_mode=$mode" "bc250_vcn=$vcn" "fw_load_type=$fw_load_type"
load_rc=$?
echo "load_rc=$load_rc"
sleep 3

echo '=== EFFECTIVE PARAMS ==='
for param in bc250_cc_write_mode bc250_vcn fw_load_type; do
  printf '%s=' "$param"
  cat "/sys/module/amdgpu/parameters/$param" 2>/dev/null || echo MISSING
done

echo '=== BINDING ==='
lspci -nnk -s 01:00.0
ls -l /dev/dri /dev/video* /dev/media* 2>&1 || true

echo '=== NEW LOG ==='
sudo journalctl -k --since "$start_time" --no-pager \
  | grep -iE 'bc250|bc-250|vcn|uvd|kiq|ring.*test|KCQ|amdgpu.*(error|fail|timeout)|firmware|Initialized amdgpu|probe with driver' \
  | tail -180 || true

exit "$load_rc"
