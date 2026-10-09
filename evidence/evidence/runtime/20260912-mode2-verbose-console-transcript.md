# Mode2 verbose console transcript (operator-typed, 2026-09-12)

- Source: operator transcription of the board console during a mode2 boot with the diagnostic cmdline (no quiet/splash, loglevel=7). Photo OCR corroborated: `/tmp/orca-paste-1789163730794-7912d56b-d052-4b73-a60a-70bc27f56b4f.png` (OCR `/tmp/bc250-console-ocr.txt`).

## Transcribed console tail

```
nvme nvme0: 16/0/0 default/read/poll queues
 nvme0n1: p1 p2 p3
[  OK  ] Found device WDC PC SN530 SDBPNPZ-512G-1114 root.
[  OK  ] Reached target Initrd Root Device.
         Mounting /sysroot...
BTRFS: device label root devid 1 transid 241094 /dev/nvme0n1p3 (259:3) scanned by mount (267)
BTRFS info (device nvme0n1p3): first mount of filesystem 14fe5cec-acf0-4986-8103-251a5706bbac
BTRFS info (device nvme0n1p3): using crc32c checksum algorithm
BTRFS info (device nvme0n1p3): enabling ssd optimizations
BTRFS info (device nvme0n1p3): turning on async discard
BTRFS info (device nvme0n1p3): enabling free space tree
[  OK  ] Mounted /sysroot.
[  OK  ] Reached target Initrd Root File System.
         Starting Mountpoints Configured in the Real Root...
[  OK  ] Finished Mountpoints Configured in the Real Root.
[  OK  ] Reached target Initrd File Systems.
         Starting Setup OverlayFS on Root Filesystem...
[  OK  ] Finished Setup OverlayFS on Root Filesystem.
[  OK  ] Reached target Initrd Default Target.
         Starting Cleaning Up and Shutting Down Daemons...
[  OK  ] Stopped target Initrd Default Target.
[  OK  ] Stopped target Basic System.
[  OK  ] Stopped target Initrd Root Device.
[  OK  ] Stopped target Path Units.
[  OK  ] Stopped target Slice Units.
[  OK  ] Stopped target Socket Units.
[  OK  ] Stopped target System Initialization.
[  OK  ] Stopped target Swaps.
[  OK  ] Stopped target Timer Units.
[  OK  ] Stopped Setup OverlayFS on Root Filesystem.
         Starting Plymouth switch root service...
         Stopping Display Boot-Time Emergency Messages in Full Screen...
[  OK  ] Stopped Load Kernel Modules.
[  OK  ] Stopped Create System Files and Directories.
[  OK  ] Stopped target Local File Systems.
[  OK  ] Stopped target Preparation for Local File Systems.
[  OK  ] Stopped Coldplug All udev Devices.
         Stopping Rule-based Manager for Device Events and Files...
[  OK  ] Stopped Display Boot-Time Emergency Messages in Full Screen.
[  OK  ] Finished Cleaning Up and Shutting Down Daemons.
[  OK  ] Finished Plymouth switch root service.
[***   ] A stop job is running for Rule-based Manager for Device Events and Files (2s / 1min 30s)
```

## Interpretation (root analysis, static + console evidence)

- The kernel, NVMe, BTRFS root mount, and the entire initramfs init reached `Initrd Default Target` and began orderly teardown for switch-root. No amdgpu/VCN lines are present in the transcribed tail.
- The screen currently holds at: `A stop job is running for Rule-based Manager for Device Events and Files (2s / 1min 30s)` — the initramfs systemd-udevd is not exiting. A live counter implies the CPU is still executing (not a fully dead kernel at this instant).
- Likely chain: a udev worker (coldplug already ran — "Stopped Coldplug All udev Devices") left udevd blocked in a kernel call; a task in uninterruptible sleep inside a wedged kernel path would make the stop job run to its 90 s timeout. Whether the kernel then survives switch-root or wedges at real-root amdgpu/mode2 module load is the next observation point.
- This refines the earlier zero-journal conclusion: mode2 does NOT hang before the initramfs; it reaches switch-root. The earlier "no trace" result implies the final wedge happens after journald starts but before it syncs to disk, or inside the initramfs teardown.
- Amgpu load point is still unresolved: if amdgpu is in the initramfs, its mode2 probe output should have appeared before `Initrd Default Target`; its absence in the transcription suggests either transcription gap or amdgpu loads from the real root (mode1 journal showed amdgpu +5 s after kernel start, consistent with either). Check `mkinitcpio.conf` MODULES in mode1.

## Final observed state of this attempt (operator report)

- After the stop-job stall the screen went fully BLACK. No panic text, no SteamOS splash, no further lines.
- One LAN LED blinks; ping 100% loss, SSH `No route to host` (re-probed twice). A blinking LAN LED at this state is PHY hardware link pulses, not an OS network stack.
- Root interpretation (inferred): at real root, plymouth (present in the initramfs: `Plymouth switch root service`) took the console and drew a black full screen despite the removed `splash` token; the real-root udev coldplug then loaded amdgpu in mode2, and the kernel wedged during VCN hardware init before any journal sync. Alternative (weaker): console blank timer or silent further boot — to be excluded by the next run.
- Evidence class: operator-observed console + host-side network absence.

## Plan for the next diagnostic run (mode2 cmdline v2)

- Add to the diagnostic mode2 entry: `plymouth.enable=0` (console stays text through real root; plymouth black-screen can no longer mask the freeze point) and `boot_delay=250 printk.time=1` (slow, time-stamped prints; readable freeze frame).
- Rollback unchanged: `/boot/limine.conf.bak-prediag-20260912`, dropin `.bak-prediag-20260912`.
- On return to mode1 also check: `journalctl --list-boots` for any trace of this attempt, `/sys/fs/pstore`, and whether amdgpu is in the initramfs (`/etc/mkinitcpio.conf` MODULES / `lsinitcpio`).
