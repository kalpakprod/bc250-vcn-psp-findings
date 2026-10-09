#!/usr/bin/env bash
set -u

printf '%s\n' '=== device nodes ==='
find /dev -maxdepth 1 -name 'tee*' -ls 2>/dev/null || true
printf '%s\n' '=== modules ==='
lsmod | grep -iE 'amdtee|tee|psp' || true
printf '%s\n' '=== kernel config ==='
zgrep -E 'CONFIG_AMDTEE|CONFIG_TEE|CONFIG_CRYPTO_DEV_SP_PSP' /proc/config.gz 2>/dev/null || true
printf '%s\n' '=== module metadata ==='
modinfo amdtee 2>/dev/null || true
printf '%s\n' '=== sysfs ==='
find /sys -maxdepth 5 -iname '*tee*' 2>/dev/null | head -100
