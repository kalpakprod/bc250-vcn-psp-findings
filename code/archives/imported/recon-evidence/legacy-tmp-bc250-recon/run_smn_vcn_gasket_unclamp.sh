#!/usr/bin/env bash
set -euo pipefail

SVCS="bc250-metrics bc250-gpu-watchdog bc250-pwrwatch bc250-telemetry bc250-dpwatch bc250-fan bc250-netconsole"

restart_services() {
    echo "[*] Restoring telemetry services..."
    sudo systemctl start $SVCS || true
}

trap restart_services EXIT

echo "[*] Stopping telemetry services to prevent SMU contention..."
sudo systemctl stop $SVCS || true

echo "[*] Re-establishing VCN clocks after cold boot..."
timeout 120 sudo env \
    BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
    python3 -u /home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable/enable_vcn.py \
    2>&1 | tee /home/OWNER/vcn_unlock/gasket_clock_enable.out

echo "[*] Re-establishing native domain-6 power..."
timeout 120 sudo env \
    BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
    python3 -u /home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable/enable_vcn.py --manual-powerup \
    2>&1 | tee /home/OWNER/vcn_unlock/gasket_manual_powerup.out

echo "[*] Running SMN VCN Gasket Dynamic Unclamp..."
timeout 120 sudo env \
    BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock \
    BC250_VCN_SOURCE=/home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable \
    python3 -u /home/OWNER/vcn_unlock/smn_vcn_gasket_unclamp.py --mode "${1:-control}" \
    2>&1 | tee /home/OWNER/vcn_unlock/smn_vcn_gasket_unclamp.out

echo "[*] Execution complete."
