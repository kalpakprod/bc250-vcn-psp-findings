#!/usr/bin/env bash
set -u

sudo modprobe amdtee
rc=$?
echo "modprobe_rc=$rc"
lsmod | grep -iE 'amdtee|tee|ccp' || true
find /dev -maxdepth 1 -name 'tee*' -ls 2>/dev/null || true
sudo dmesg | grep -iE 'amdtee|amd-tee|tee' | tail -50 || true
exit "$rc"
