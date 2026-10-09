# Action log: kernel pkgrel 3 (BORE + ThinLTO + Zen2 + NR_CPUS=16, 0025 dropped)

Date: 2026-09-22. Actor: root. Plan: `.procoder/plans/2026-09-22-kernel-pkgrel3.md`.
Operator decisions D1-D7 (plan). Build host kukuruza-pc (.74) WSL archlinux, user builder.

## Pre-checks (observed)

- CachyOS PKGBUILD (linux-cachyos-bore, 7.2.6): `_processor_opt` supports only
  GENERIC_V1-4 / ZEN4 / NATIVE; no MZEN2 in this tree. NATIVE would target the
  build host CPU -> rejected. Zen2 codegen via KCFLAGS `-march=znver2 -mtune=znver2`
  on top of GENERIC_V3 (clang records target-cpu per function, survives ThinLTO).
- Board 1.2 config: NR_CPUS=8192 (MAXSMP), GCC, LTO_NONE, NO_HZ_FULL=y,
  EFI_VARS_PSTORE_DEFAULT_DISABLE=y (R1 already satisfied, no change),
  DEBUG_INFO DWARF5 + BTF + KALLSYMS kept (D7).

## Intent (before execution)

- Script `/tmp/kbore/phase2-pkgrel3.sh` -> C:\Temp\kbore: remove 0025 from
  mypatches, BC250_PKGREL=3, config: MAXSMP off + NR_CPUS=16,
  env `_use_llvm_lto=thin _processor_opt=generic_v3 KCFLAGS="-march=znver2 -mtune=znver2"`,
  pacman makedeps clang llvm lld, nohup makepkg, log ~/kbore/build-full-pkgrel3.log.
- Expected: linux-cachyos-bore-vcn-bc250 7.2.6-1.3 packages, not installed.
- Rollback: nothing installed; 1.2 packages remain on board and on .74.

## Execution

- 10:02 attempt 1: BUILD_RC=1 "Integrity checks (b2) differ in size" — updpkgsums
  ran without `_use_llvm_lto=thin`, which adds dkms-clang.patch to source=().
  Fix: updpkgsums with the same env (relaunch3.sh), makepkg via nohup setsid.
- ~10:06 attempt 2 compiling. Final src .config (observed): CC_IS_CLANG=y,
  LTO_CLANG_THIN=y, SCHED_BORE=y, GENERIC_CPU=y + X86_64_VERSION=3,
  NR_CPUS=16 (MAXSMP unset), KALLSYMS=y, DEBUG_INFO_BTF=y. Zen2 codegen via
  KCFLAGS -march=znver2 -mtune=znver2 (to verify in object flags after build).

## 2026-09-22 10:27 +05 STOPPED on operator order

- Build killed mid-compile (makepkg/clang count 0). No package produced, nothing installed.
- Reason: operator wants the full stack interviewed before building (flags, scope).

## Intent v2 (after operator interview, supersedes Intent above)

- Base: latest released upstream = linux-cachyos-bore 7.2.6-1 (no rc).
- MastaG repo -> origin HEAD 0697a5d (adds 0014-bc250-psp-ccp).
- Config: FRESH CachyOS config from the 7.2.6 source (board.config seed
  NOT used) + MAXSMP off, NR_CPUS=16 (sed on `config`).
- Patches (mypatches3): MastaG patches/linux-cachyos 0001-0014; ours
  0015 vcn-safe-direct-load, 0016 vcn-probe-mode; XanMod kept 4:
  le9 working-set, rq_affinity, wbt 2ms, vfs cache pressure. Dropped:
  0025 sclk-3000, xanmod mq-deadline x2, max_map_count, cpufreq tunes.
- Flags: _use_llvm_lto=thin (clang), _processor_opt=generic_v3,
  KCFLAGS="-march=znver2 -mtune=znver2", CachyOS -O3 default.
- Expected: 7.2.6-1.3 packages on .74, not installed. Rollback: none needed.

## Intent v2 (operator-confirmed, supersedes Intent above)

- Base: latest released upstream linux-cachyos-bore 7.2.6-1 (no rc). Ceiling 2230 (0025 dropped).
- MastaG -> origin HEAD 0697a5d (adds 0014-bc250-psp-ccp).
- Config: FRESH CachyOS config from the 7.2.6 source (board.config NOT used) + MAXSMP off, NR_CPUS=16.
- Patches (mypatches3, 20): MastaG patches/linux-cachyos 0001-0014; ours 0015 vcn-safe-direct-load,
  0016 vcn-probe-mode; XanMod 4: le9 working-set, rq_affinity, wbt 2ms, vfs cache pressure.
- Flags: _use_llvm_lto=thin (clang), _processor_opt=generic_v3, KCFLAGS="-march=znver2 -mtune=znver2", CachyOS -O3 default.
- Expected: 7.2.6-1.3 packages on .74, not installed. Rollback: none needed.
- v2 launched (~11:0x): mastag 0697a5d, pkgrel=1.3, fresh CachyOS config,
  22 patches applied (20 ours/MastaG/XanMod + bore-cachy + dkms-clang),
  offsets only, no FAILED. .config: CC_IS_CLANG, LTO_CLANG_THIN, SCHED_BORE,
  O3, GENERIC_CPU v3, NR_CPUS=16, MAXSMP unset, HZ=1000, NCT6687=m,
  CRYPTO_DEV_SP_PSP=y, KALLSYMS, DEBUG_INFO_BTF. Compiling.
- 10:44 build killed with the WSL VM (no BUILD_RC, VM uptime reset). Relaunched ~10:52 in foreground inside a held ssh session (run3fg.sh) so WSL cannot idle-stop.
- A4 PASS: BUILD_RC=0; pkg sha256 d5378b17…d19d (kernel), 61abb2d6…945e (headers); headers .config = CLANG/THIN/BORE/O3/NR_CPUS=16/MAXSMP unset; amdgpu+sched .cmd carry -march=znver2 -mtune=znver2 -O3 (clang). One non-fatal "cc1: -Wformat-security" line (GCC host step), unexplained. Shipped to board ~/kernel-1.3, sha256 match on .74/laptop/board. NOT installed.

## A5 install 1.3 + prune + MastaG stock kernel — INTENT (operator order 14:5x PKT)

- `pacman -U ~/kernel-1.3/*.zst` (replaces 1.2, same pkgbase; limine
  entries mode0/1/2 + cmdlines carry over via drop-in).
- Remove: linux-cachyos-rc-bc250 7.2.rc7-1.90, linux-cachyos-vcn-bc250
  7.2.0-1.92 (+headers) and their limine-entry-tool drop-in.
- Add [bc250-cachyos] repo per MastaG README (above cachyos-v3), install
  only bc250-cachyos/linux-cachyos-bc250 (stock MastaG kernel, second entry).
  No -Syu: repo also carries patched Mesa; not pulled now.
- Keep default_entry bore-vcn-mode1. Backup /boot/limine.conf first.
  Rollback: 1.2 pkgs on .74 bridge; limine.conf backup; fallback entry.
  RESULT ~14:58 PKT: 1.3 installed (sha d5378b17/61abb2d6 match), 1.2 gone;
  rc-bc250 + vcn-bc250 removed, their drop-in moved to
  /etc/limine-entry-tool.d/retired/. [bc250-cachyos] repo added; stock
  linux-cachyos-bc250 7.2.0-1.1 -> 7.2.6-1.206. Menu: linux-cachyos-bc250,
  bore-vcn-bc250 (+mode0/1/2). default_entry bore-vcn-mode1 unchanged.
  Backup /boot/limine.conf.bak-20260922-prune. Effective at reboot; unbooted.

## MastaG Mesa + FSR4 Proton — INTENT (operator: Spider-Man, FSR4 mandatory)

Install from [bc250-cachyos]: mesa lib32-mesa vulkan-radeon lib32-vulkan-radeon
opencl-mesa vulkan-mesa-implicit-layers lib32-vulkan-mesa-implicit-layers
(26.2.3-*.186, same upstream 26.2.3 + MastaG FSR4/async patches) and
protonge-latest-bc250 11.7-185. Map AppID 1817070 to it.
Rollback: pacman -U cached 26.2.3-1.1 / -2.1 packages.
19:48 FurMark-start hangs persist at UMA 8G and at 2200@1040. MastaG README: async compute (on by default in their Mesa) causes green/black-screen crashes on some boards. Test: swap to stock cachyos Mesa 26.2.3 and repeat FurMark start.
