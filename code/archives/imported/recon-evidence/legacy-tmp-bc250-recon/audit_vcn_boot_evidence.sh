#!/usr/bin/env bash
set -Eeuo pipefail

sudo journalctl --list-boots --no-pager | tail -10
for boot in -5 -4 -3 -2 -1 0; do
  echo "=== BOOT $boot ==="
  sudo journalctl -b "$boot" -k --no-pager \
    | grep -E 'Linux version|Kernel command line|unknown parameter.*bc250_vcn|Found VCN firmware|detected ip block.*vcn|ring kiq.*test failed|KCQ enable failed|hw_init of IP block <gfx_v10_0> failed|Fatal error during GPU init|Initialized amdgpu' \
    | tail -60 || true
done
