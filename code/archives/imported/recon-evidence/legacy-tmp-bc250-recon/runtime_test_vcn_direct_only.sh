#!/usr/bin/env bash
set -u

vcn=${1:-0}
label=${2:-control}
start_time=$(date --iso-8601=seconds)

restore_services() {
  if [[ ! -e /sys/bus/pci/devices/0000:01:00.0/driver ]] &&
     [[ -e /sys/bus/pci/drivers/amdgpu/bind ]]; then
    echo 0000:01:00.0 | sudo tee /sys/bus/pci/drivers/amdgpu/bind >/dev/null || true
  fi
  sudo systemctl start display-manager 2>/dev/null || true
  sudo systemctl start \
    bc250-metrics bc250-gpu-watchdog bc250-pwrwatch bc250-telemetry \
    bc250-dpwatch bc250-fan bc250-netconsole 2>/dev/null || true
}
trap restore_services EXIT

systemctl --user stop \
  steam-launcher.service gamescope-mangoapp.service gamescope-session.service \
  2>/dev/null || true
sudo systemctl stop display-manager 2>/dev/null || true
sudo systemctl stop \
  bc250-metrics bc250-gpu-watchdog bc250-pwrwatch bc250-telemetry \
  bc250-dpwatch bc250-fan bc250-netconsole 2>/dev/null || true

echo "=== $label: UNBIND AND REMOVE STOCK MODULE ==="
if [[ -e /sys/bus/pci/devices/0000:01:00.0/driver ]]; then
  echo 0000:01:00.0 | sudo tee /sys/bus/pci/drivers/amdgpu/unbind >/dev/null
fi
sudo modprobe -r amdgpu
remove_rc=$?
echo "remove_rc=$remove_rc"
if ((remove_rc != 0)); then
  exit "$remove_rc"
fi

echo "=== $label: LOAD OVERLAY vcn=$vcn global_fw=auto ==="
timeout 40 sudo modprobe amdgpu \
  bc250_cc_write_mode=3 "bc250_vcn=$vcn" fw_load_type=-1
load_rc=$?
echo "load_rc=$load_rc"
sudo udevadm settle --timeout=10 || true

echo '=== RESOLVED MODULE ==='
modinfo amdgpu | grep -E '^filename:|^srcversion:|^vermagic:'

echo '=== EFFECTIVE PARAMS ==='
for parameter in bc250_cc_write_mode bc250_vcn fw_load_type; do
  if [[ -r "/sys/module/amdgpu/parameters/$parameter" ]]; then
    printf '%s=' "$parameter"
    cat "/sys/module/amdgpu/parameters/$parameter"
  else
    echo "$parameter=MISSING"
  fi
done

echo '=== BINDING ==='
lspci -nnk -s 01:00.0
ls -l /dev/dri /dev/video* /dev/media* 2>&1 || true

echo '=== NEW LOG ==='
sudo journalctl -k --since "$start_time" --no-pager \
  | grep -iE 'bc250|bc-250|vcn|uvd|kiq|ring.*test|KCQ|amdgpu.*(error|fail|timeout)|firmware|Initialized amdgpu|probe with driver' \
  | tail -220 || true

exit "$load_rc"
