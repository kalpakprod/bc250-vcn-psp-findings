# Mode1 deep read + mode2 no-trace finding (2026-09-12, SSH read-only)

## Mode2 boot attempt left zero journal trace

- Operator report: mode2 (`linux-cachyos-vcn-bc250-mode2`) "не грузится" (does not boot). Board returned to mode1.
- `journalctl --list-boots`: boots -2 (23:11:48–23:13:15), -1 (23:13:38–23:21:30), 0 (23:50:52–now). The gap 23:21:30 → 23:50:52 contains NO boot record.
- Full-journal grep for `bc250_vcn_mode=2` finds only the 23:14:47 sudo line that appended the mode2 cmdline line to `/etc/limine-entry-tool.d/90-bc250-vcn-probe.conf`. No boot ever logged a mode2 kernel command line.
- Interpretation (inferred, not observed): the mode2 attempt hung or reset before journald activation. amdgpu is a module loaded early (initramfs KMS stage); a hard hang in `vcn_v2_0` hardware init would leave no persistent journal. Exact hang/reset point UNKNOWN — no console capture, no serial trace, no POST evidence.
- Evidence class for the mode2 failure: `operator-observed` + absence-of-log. The hang location is INCONCLUSIVE.

## Mode1 deep read (current boot, all read-only)

- `modinfo -p amdgpu`: `bc250_vcn_mode: BC-250 VCN mode: 0=off, 1=probe-only, 2=hardware; mode 2 is experimental (int)`. `/sys/module/amdgpu/parameters/bc250_vcn_mode` = `1`.
- Firmware on board: `green_sardine_vcn.bin.zst` (275k compressed) and `renoir_vcn.bin.zst -> green_sardine_vcn.bin.zst` (404,544 B decompressed, verified 2026-09-11). No cyan_skillfish2 files.
- Debugfs `/sys/kernel/debug/dri/` shows only `client-*` entries in the captured listing; no VCN-specific debugfs node observed.
- `dmesg` this boot: zero VCN/MMSCH lines after the 23:50:57-58 probe lines. Mode1 probe performs NO VCN hardware interaction (probe-only confirmed by behavior).
- Working hypothesis (static-analysis class, unproven): mode2 attaches the real `vcn_v2_0` block; `vcn_v2_0_hw_init` starts VCPU and waits; if PSP policy keeps VCN power-gated/disabled (the VCN-lock mechanism under study), MMIO/VCPU access hangs or times out abnormally early. The zero-journal result is consistent with a hard hang, not with the historical mode1-style graceful `-110` ring timeouts.

## Proposed next decisive test (requires operator approval; no flash)

- Add a diagnostic limine entry: mode2 cmdline with `quiet splash` removed and `loglevel=7` (one variable: console verbosity). Operator boots it once and reads/photographs the last console line before hang.
- Alternative if wired: serial console on UART header J5 for the same runbook.
- This changes only the OS bootloader cmdline of the test entry; rollback is restoring the previous entry text (backup `.bak` already exists from 2026-09-11).
