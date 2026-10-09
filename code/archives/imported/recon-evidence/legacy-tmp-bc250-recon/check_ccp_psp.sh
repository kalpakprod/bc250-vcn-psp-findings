#!/usr/bin/env bash
set -u

printf '%s\n' '=== PCI crypto/PSP ==='
lspci -nnk | grep -A4 -B2 -iE 'cryptographic|ccp|psp' || true
printf '%s\n' '=== kernel log ==='
sudo dmesg | grep -iE 'ccp|psp|sev|tee' | tail -120 || true
printf '%s\n' '=== CCP bindings ==='
find /sys/bus/pci/drivers/ccp -maxdepth 2 -type l -printf '%p -> %l\n' 2>/dev/null || true
printf '%s\n' '=== CCP sysfs ==='
find /sys/bus/pci/drivers/ccp -maxdepth 2 -type f -print 2>/dev/null | head -100
