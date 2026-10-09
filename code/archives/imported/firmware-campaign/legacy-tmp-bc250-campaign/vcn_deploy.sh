#!/usr/bin/env bash
# vcn_deploy.sh — выгрузить safe-запуск на board (steammachine@127.0.0.1) и проверить импорт.
set -e
RC=/mnt/c/Users/kukuruza/tmp_bc250/recon
IP=127.0.0.1
scp -o ConnectTimeout=4 -o StrictHostKeyChecking=accept-new "$RC/vcn_safe_run.sh" "$RC/vcn_watch.sh" "$RC/VCN-START-SAFE.md" steammachine@$IP:/home/OWNER/vcn_unlock/
echo "=== verify python import on board (bc250_smu + unlock) ==="
ssh -o ConnectTimeout=4 -o StrictHostKeyChecking=accept-new steammachine@$IP 'bash -lc "cd /home/OWNER/vcn_unlock && export BC250_SMU_PATH=/home/OWNER/vcn_unlock/bc250-smu-unlock && python3 -c "import bc250_smu,unlock; print(IMPORT_OK, bc250_smu.__file__)""'
echo "=== chmod + dry-run (does NOT reboot/wedge; just prints steps) ==="
ssh -o ConnectTimeout=4 -o StrictHostKeyChecking=accept-new steammachine@$IP 'bash -lc "chmod +x ~/vcn_unlock/vcn_safe_run.sh ~/vcn_unlock/vcn_watch.sh && echo READY_TO_RUN: ssh ... ~/vcn_unlock/vcn_safe_run.sh"'
