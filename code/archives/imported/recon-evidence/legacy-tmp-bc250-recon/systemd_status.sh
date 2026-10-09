#!/bin/bash
echo "=== is-system-running ==="
systemctl is-system-running
echo "=== reboot.target status ==="
systemctl status reboot.target --no-pager 2>&1 | head -20
echo "=== jobs (reboot/restart) ==="
systemctl list-jobs --all 2>&1 | grep -iE 'reboot|restart|shutdown|target' | head -30
echo "=== last reboot times ==="
last reboot 2>/dev/null | head -5
echo "=== systemctl show reboot.target ==="
systemctl show reboot.target -p SubState -p ActiveState -p UnitFileState 2>&1
echo "=== done ==="
