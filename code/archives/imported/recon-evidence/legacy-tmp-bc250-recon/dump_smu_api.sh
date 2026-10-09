#!/bin/bash
set -x
SP=~/.local/share/pipx/venvs/bc250-smu-oc
PY=$SP/lib/python3.14/site-packages/bc250_smu
echo "=== api.py (queue addrs + send_message) ==="
cat $PY/api.py
echo "=== api_q3.py (FULL) ==="
cat $PY/api_q3.py
echo "=== api_q2.py ==="
cat $PY/api_q2.py
echo "=== done ==="
