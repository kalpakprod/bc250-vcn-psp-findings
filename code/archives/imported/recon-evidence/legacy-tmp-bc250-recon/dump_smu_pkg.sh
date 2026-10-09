#!/bin/bash
set -x
SP=~/.local/share/pipx/venvs/bc250-smu-oc
PY=$SP/lib/python3.14/site-packages/bc250_smu
echo "=== bc250_smu files ==="
ls -la $PY
echo "=== __init__.py ==="
cat $PY/__init__.py
echo "=== transport.py ==="
cat $PY/transport.py
echo "=== mailbox.py ==="
cat $PY/mailbox.py
echo "=== grep SMU msg/queue/0x98/SMN in package ==="
grep -rniE 'msg|queue|0x98|smn|mailbox|write_reg|config' $PY/*.py | grep -iE 'def |0x98|queue|smn|msg' | head -60
echo "=== done ==="
