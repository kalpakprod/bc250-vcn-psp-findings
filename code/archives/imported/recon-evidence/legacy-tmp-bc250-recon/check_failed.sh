#!/bin/bash
echo "=== failed units (all) ==="
systemctl list-units --state=failed --all --no-pager | head -30
echo "=== failed services ==="
systemctl list-units --type=service --state=failed --all --no-pager | head -30
echo "=== failed timers ==="
systemctl list-timers --all --no-pager 2>/dev/null | grep -iE 'failed|expired' | head
echo "=== journal: last 25 err/warn ==="
journalctl -p err -n 25 --no-pager 2>/dev/null | tail -30
echo "=== done ==="
