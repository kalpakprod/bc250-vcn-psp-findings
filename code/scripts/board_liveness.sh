#!/usr/bin/env bash
# Read-only liveness check for BC250-01. Prints state, writes nothing.
# Born from MISTAKES.md 2026-09-23: board-state claims must be live-checked,
# never carried from old records.
# Usage: scripts/board_liveness.sh [ip]
set -u
IP="${1:-127.0.0.1}"
USER_HOST="steammachine@${IP}"
KEY="$HOME/.ssh/id_ed25519"

echo "time: $(date -Is)"
echo "target: ${IP}"
if ping -c 1 -W 2 "$IP" >/dev/null 2>&1; then
	echo "ping: UP"
else
	echo "ping: DOWN"
	exit 1
fi
ssh -o BatchMode=yes -o ConnectTimeout=6 -i "$KEY" "$USER_HOST" \
	'echo "booted: $(uptime -s)"; echo "kernel: $(uname -r)"; echo "host: $(hostname)"; sudo -n dmidecode -s bios-version 2>/dev/null | sed "s/^/bios-version: /"; sudo -n dmidecode -s bios-release-date 2>/dev/null | sed "s/^/bios-date: /"' \
	2>&1
