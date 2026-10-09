# Plan: kernel 7.2.6-1.3-cachyos-bore-vcn-bc250 (BC-250 only)

Date: 2026-09-22. Owner: root. Operator decisions recorded 2026-09-22.

## Goal
One kernel package for BC-250 only: BORE + clang ThinLTO + Zen2 codegen,
driver SCLK range back to 350-2230, user-useful debug kept; then a public
build repo (scripts + patches + config) and a pacman repo.

## Decisions (operator)
- D1 BORE + ThinLTO via CachyOS knob `_use_llvm_lto=thin` (clang/lld).
  Source check 2026-09-22: CachyOS linux-cachyos = thin+clang default;
  linux-cachyos-bore = none+GCC default; LTO requires clang.
- D2 `_processor_opt=zen2` (CONFIG_MZEN2) instead of generic_v3.
- D3 NR_CPUS=16.
- D4 Keep all USB/driver modules (no localmodconfig). Check community docs
  for Wi-Fi/BT adapters and modems (AX200/AX210 etc.) and confirm drivers on.
- D5 Drop 0025 (sclk 3000); keep MastaG 0007 (350-2230).
- D6 Remove isolcpus/nohz_full/rcu_nocbs from cmdline and taskset launch
  option; scheduler owns all cores. NO_HZ mode = CachyOS default.
- D7 Keep debug that helps users: KALLSYMS, BTF, ftrace/perf, persistent
  journal, systemd-coredump; add `bc250-report` bundler.
- R1 (pending operator): disable efi_pstore (writes crash dumps into SPI NVRAM).

## Steps and gates
- A1 disk/tmp quota OK (done 2026-09-22: / 59G free, /tmp writable).
- A2 phase2-pkgrel3.sh (D1,D2,D3,D5) + action-log intent.
- A3 build on .74 WSL archlinux (nohup, -j28, ccache).
- A4 pre-install config check: CC_IS_CLANG, LTO_CLANG_THIN, MZEN2,
  NR_CPUS=16, SCHED_BORE; mypatches has no 0025.
- A5 side-by-side install (1.2 stays as fallback entry); cmdline for D6/R1.
- A6 board: uname, OD_RANGE 350-2230, VCN probe, game smoke, FPS/1%-low A/B
  vs 1.2 same scene (MangoHud CSV).
- A7 bc250-report tool.

## Tracks after kernel
- T1 GPU clock governor (idle pinned 2000 MHz / 75 W).
- T2 async compute: in-game use and benefit (queues already exposed).
- T3 FSR4 INT8 per-game trial.
- T4 public build repo + pacman repo.

## D4 result (2026-09-22, observed in pkgrel3 .config)
- In-kernel USB Wi-Fi/BT/modem drivers all =m: RTW88 8821CU/8822BU/8822CU/8723DU,
  RTW89 8852BU, RTL8XXXU, MT7601U/MT76x0U/MT76x2U/MT7921U/MT7925U, IWLWIFI+MVM+MLD
  (BE200/AX2xx M.2), BT_HCIBTUSB/RTL/INTEL, RNDIS/CDC_NCM/MBIM/QMI (phone/LTE modem),
  USB_SERIAL_OPTION.
- Gap: AIC8800D80 ("AX900", Tenda/UGREEN) is out-of-tree. Track T5: ship
  aic8800 DKMS + usb_modeswitch rule in our repo; verify DKMS builds with
  clang/ThinLTO kernel (CachyOS dkms-clang.patch). Source: docs/research/telegram-bc250-6mo/wifi.md.
- R1 closed: EFI_VARS_PSTORE_DEFAULT_DISABLE=y already in config.
