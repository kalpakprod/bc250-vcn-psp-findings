# Action log: WSL2 + Arch install on kukuruza-pc (127.0.0.1)

Date: 2026-09-21. Actor: root. Host: `kukuruza@127.0.0.1`
(Windows 11 Pro 26H2, Intel 20C/28T, 64 GB RAM, C: 406.8 GB free).

## Intent (before execution)

User order (explicit, "ВСЛ ставь, ставь Archlinux"): install WSL2 + Arch
Linux on .74 as the kernel build host for the universal BORE+VCN kernel.
Prior state: WSL NOT installed (`wsl.exe` reports missing component).

Planned writes (all on .74):

1. `wsl.exe --install --no-distribution` (enables WSL + VirtualMachinePlatform;
   admin user; reversible via feature disable).
2. `shutdown /r /t 60` (REQUIRED reboot for the hypervisor platform).
3. Post-boot: `wsl.exe --set-default-version 2`, `wsl.exe --update`.
4. Import Arch: download `archlinux-bootstrap-x86_64.tar.zst` (Arch mirror)
   - `wsl.exe --import archlinux C:\WSL\archlinux <tarball>`.
5. Inside Arch: pacman-key init/populate, mirrorlist, `pacman -Syu`,
   `base-devel bc cpio git`.
6. Create build user? (TBD — root acceptable for kernel builds; decide at step 5.)

Expected effect: `archlinux` WSL2 distro ready for kernel builds; nothing
else on the box changes (no Store apps, no Ubuntu).

Rollback: `wsl.exe --unregister archlinux` + delete `C:\WSL\archlinux`;
`Disable-WindowsOptionalFeature` for WSL/VMP + reboot. Photo batch
(HddJxlSd2, state Ready/idle at last check) untouched.

Risks: (a) reboot — operator explicitly ordered; machine is always-on,
no pending reboot blockers recorded 2026-09-20; will poll SSH until back
(~10 min budget), else report for physical check. (b) Kernel-Power-41
history (2 sudden offs 2026-09-20 under sustained load) — observe during
first heavy build; not a WSL-install risk per se. (c) Clock skew +2h on
.74 — use durations from one clock only.

## Step 1: enable WSL (before reboot)

- `wsl.exe --install` (bare and `--no-distribution`) FAILED via stub: only
  prints "not installed, run wsl.exe --install" (rc=1). SSH token IS
  elevated (is_admin=True, High IL) — not a rights issue; stub can't
  bootstrap headless on 26H2.
- Headless path used instead: `Enable-WindowsOptionalFeature -Online
-NoRestart -All` for `Microsoft-Windows-Subsystem-Linux` and
  `VirtualMachinePlatform` — both accepted, `RestartNeeded=True`.
  Network egress OK (aka.ms HEAD, no failure).
- Reboot now required (operator-ordered install implies it).

## Step 2: reboot + wait

- `shutdown /r /t 45` accepted (rc=0, uptime was 1d, batch Ready/idle) but
  executed ~2-3 min late (app grace); host down then back in ~1 min.
  Post-boot uptime 0.6 min confirmed the reboot.
- Post-reboot WSL still stub: DISM features Enabled, but no WSL app.
  `wsl --install` fails headless on 26H2 (3 attempts, G6).
- New method: `winget install -e --id Microsoft.WSL` → 2.7.13 OK
  (GitHub API /releases 404s — Store distribution; direct MSI path dead).
- `wsl --version`: 2.7.13.0, kernel 6.18.33.2-2, default v2. No 2nd reboot.

## Step 3: Arch import + toolchain

- Bootstrap `archlinux-bootstrap-x86_64.tar.zst` (126,491,574 B) via pwsh 7
  (PS 5.1 unusable: TLS/WebException; helper switched to pwsh default).
- Direct Windows-tar extract FAILED (NTFS case collisions + hardlinks);
  import never ran (no vhdx). G6: Ubuntu bootstrap distro
  (`wsl --install -d Ubuntu --no-launch`, WSL2) → real-tar repack
  (ustar failed on longlink → GNU format OK, 576,051,200 B).
- `wsl --import` needs a pre-created dir (`ERROR_PATH_NOT_FOUND` once).
- Arch boots: BOOT_OK, x86_64, 31G RAM, 955G free, persistence verified
  (marker file survives; NOTE: /tmp is tmpfs — builds live in ~/).
- Toolchain: keyring populated, mirrorlist staged via scp (shell `$`
  quoting unreliable — files over scp from here on), Syu clean,
  base-devel/git/bc/cpio/tmux/sudo/make/gcc-16.2.1 all installed,
  user `builder` (uid 1000) + NOPASSWD sudo (verified rc=0).
  nproc count: UNREAD (output filter ate 2-digit numbers; recheck).
- Temp cleaned (C:\Temp ~2.7 KB left). Ubuntu kept as rescue for now.
- Helper: `/tmp/pc-run.py` (pwsh default, `--ps51` fallback, 900 s timeout).
