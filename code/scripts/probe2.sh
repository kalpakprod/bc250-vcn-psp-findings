#!/usr/bin/env bash
# probe2.sh — operator-loop automation for the BC-250 Probe2 USB boot stick.
#
# Modes:
#   push   Copy the payload (firmware-flash-pkg/20260923-probe2-usb/) onto
#          the FAT32 stick attached to the BC-250 host, over SSH. One-time
#          setup per stick.
#   fetch  Start the timer, wait for the board to reboot away and come back
#          with a fresh boot, then pull probe2-out.txt off the stick into
#          evidence/runtime/. Run BEFORE the operator reboots.
#          Optional arg 1: return-wait timeout in seconds (default 420).
#
# Board policy: probe3 is read-only for the board; `push` writes only the
# stick. No firmware writes, no boot-order changes.
set -u

REPO=$(cd "$(dirname "$0")/.." && pwd)
# Package dir: probe4 (mailbox transport) after run 1 proved the raw-SMN
# probe3 payload wedges the board. Override: PROBE2_PKG=<dir> scripts/probe2.sh push
PKG=${PROBE2_PKG:-$REPO/firmware-flash-pkg/20260923-probe4-usb}
BOARD_HOST=steammachine@127.0.0.1
KEY=$HOME/.ssh/id_ed25519
MNT=/mnt/probe2
TIMEOUT_DOWN=600
EVID_DIR="$REPO/evidence/runtime"

ssh_b() { ssh -o BatchMode=yes -o ConnectTimeout=8 -i "$KEY" "$BOARD_HOST" "$@"; }

# Echo the stick's vfat partition device (e.g. sdb1) or nothing.
# RM=1 (removable) excludes the NVMe/SATA ESP, which is also vfat.
# NB: use NAME, not PATH - PATH is absolute (/dev/sdb1) and the callers
# prepend /dev/ themselves, which produced /dev//dev/sdb1 (mount failure).
find_stick_dev() {
	ssh_b "lsblk -rno NAME,FSTYPE,RM,TRAN,SIZE | awk '\$2==\"vfat\" && \$3==1 {print \$1; exit}'"
}

# Echo the mount point if the device is already mounted, else nothing.
find_mount_point() { # $1 = device
	[ -n "${1:-}" ] || return 1
	ssh_b "findmnt -rn -S /dev/$1 -o TARGET"
}

# Mount the stick if needed; echo the path; keep MOUNTED_BY_US flag.
mount_stick() { # $1 = mode: ro|rw
	local dev mode="$1" mpoint
	dev=$(find_stick_dev)
	if [ -z "$dev" ]; then
		echo "ERROR: no vfat partition found on the board (stick plugged in?)" >&2
		return 1
	fi
	mpoint=$(find_mount_point "$dev")
	if [ -n "$mpoint" ]; then
		echo "$mpoint"
		return 0
	fi
	if ! ssh_b "grep -q ' $MNT ' /proc/mounts"; then
		if [ "$mode" = rw ]; then
			ssh_b "sudo -n mount -t vfat -o uid=1000,gid=1000,umask=022 /dev/$dev $MNT" || return 1
		else
			ssh_b "sudo -n mount -t vfat -o ro /dev/$dev $MNT" || return 1
		fi
		MOUNTED_BY_US=1
	fi
	echo "$MNT"
}

cmd_push() {
	local mpoint
	MOUNTED_BY_US=0
	mpoint=$(mount_stick rw) || return 1
	echo "stick mounted at: $mpoint"
	ssh_b "mkdir -p $mpoint/EFI/BOOT" || return 1
	scp -o BatchMode=yes -i "$KEY" \
		"$PKG/EFI/BOOT/BOOTX64.EFI" "$PKG/PROBE2.TXT" "$BOARD_HOST:$mpoint/" || return 1
	ssh_b "mv $mpoint/BOOTX64.EFI $mpoint/EFI/BOOT/BOOTX64.EFI" || return 1
	ssh_b "sync" || true
	if [ "$MOUNTED_BY_US" = 1 ]; then
		ssh_b "sudo -n umount $MNT"
	fi
	echo "payload written. Next: start 'fetch' from the agent side, then tell the"
	echo "operator: reboot the board and pick the USB stick ONCE in the boot menu."
}

cmd_fetch() {
	# Return-wait timeout: first arg after the mode (scripts/probe2.sh fetch 900).
	# NB: must be read HERE - a top-level ${1:-420} sees the MODE word ("fetch"),
	# not the timeout, and then $((TIMEOUT_BACK / 5)) dies on the unbound name.
	TIMEOUT_BACK=${1:-420}
	local state=wait_down seen_down=0 i out_local ts
	echo "time: $(date -Is) — waiting for the board to leave (timeout ${TIMEOUT_DOWN}s)"
	for i in $(seq 1 $((TIMEOUT_DOWN / 5))); do
		if ssh_b "uptime -s" >/dev/null 2>&1; then
			sleep 5
		else
			seen_down=1
			echo "time: $(date -Is) — board left, waiting for return (timeout ${TIMEOUT_BACK}s)"
			break
		fi
	done
	if [ "$seen_down" = 0 ]; then
		echo "TIMEOUT: the board never went down. Did the operator reboot it? Aborting." >&2
		return 1
	fi
	state=wait_up
	for i in $(seq 1 $((TIMEOUT_BACK / 5))); do
		if ssh_b "uptime -s" >/dev/null 2>&1; then
			break
		fi
		sleep 5
	done
	if ! ssh_b "uptime -s" >/dev/null 2>&1; then
		echo "TIMEOUT: the board did not come back." >&2
		echo "Likely causes: boot menu picked nothing, or the probe reads wedged the" >&2
		echo "board. Recovery: cold power cycle; the board boots its current P3.00" >&2
		echo "image; nothing was written. The run can be retried." >&2
		return 1
	fi
	sleep 5
	echo "time: $(date -Is) — board is back:"
	ssh_b "uptime -s; uname -r"

	MOUNTED_BY_US=0
	local mpoint
	mpoint=$(mount_stick ro) || return 1
	if ! ssh_b "test -s $mpoint/probe2-out.txt"; then
		echo "probe2-out.txt missing or empty on the stick at $mpoint." >&2
		echo "Either the probe did not run (boot pick missed) or the save failed." >&2
		[ "$MOUNTED_BY_US" = 1 ] && ssh_b "sudo -n umount $MNT"
		return 1
	fi
	mkdir -p "$EVID_DIR"
	ts=$(date +%Y%m%d-%H%M%S)
	out_local="$EVID_DIR/${ts}-probe2-out.txt"
	scp -o BatchMode=yes -i "$KEY" "$BOARD_HOST:$mpoint/probe2-out.txt" "$out_local" || return 1
	[ "$MOUNTED_BY_US" = 1 ] && ssh_b "sudo -n umount $MNT"
	echo "saved: $out_local"
	echo "--- verdict lines ---"
	grep -E "VCN descriptor:|domain bitmap|power status|clock plan words" "$out_local"
}

case "${1:-}" in
push) cmd_push ;;
fetch)
	shift
	cmd_fetch "$@"
	;;
*) echo "usage: scripts/probe2.sh push|fetch [return-timeout-seconds]" ;;
esac
