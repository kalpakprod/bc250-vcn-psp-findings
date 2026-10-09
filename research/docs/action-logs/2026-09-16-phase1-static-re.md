# Action log: Phase 1 static RE of C0A-stock (1.1-1.5)

Date: 2026-09-16 (UTC). Actor: root. Read-only; scratch in /tmp
(census-c0a-vs-dump.json, ifr-*.txt, ifr_driver.py). No firmware writes.

## 1.1 Module census (own runs, PASSED)
- Keys: C0A-stock 244, dump 233, P5.00 232. C0A-vs-dump: 85 same-body,
  128 diff-body, 31 only-C0A, 20 only-dump.
- Donor extras: full TCG/TPM stack (Tcg*/Tpm*/TrEE, AmdPspFtpmDxe+Pei,
  AmiPspFtpmDxe+Pei+Smm, SecureBootDXE, HSTI, RedFish, DeviceGuard),
  IT8772E SIO PEI, SmartFan, WakEvn, FboGroupForm.
- BC250 extras: CBS trio (CbsBaseDxe/Pei, CbsSetupDxe), Bc250CoreUnlockDxe,
  OEMBOARD trio, NVMe trio, Realtek LAN x2, NCT6686D SIO, ISL69247+ISL95712
  VRM, FanTuning x2, BctBaseSmm, AmiPspRecovery, SmmChildDispatcher2.
- P5.00-vs-dump: 9 diff-body (Setup, AMITSE, AmdVersionDxe/Pei, Bds, CpuSmm,
  FsRecovery, HardwareSignatureEntry, AmdNbioSmuV10Dxe); only-dump =
  Bc250CoreUnlockDxe; only-P5.00 = none.

## 1.2 Boot-path map (own runs, PASSED)
- PEI dispatch order identical through the AMD silicon chain
  (RomLayout->PeiCore->...->AmiAgesaPei); divergence after: donor adds
  FtpmPei + TcgPei/TrEE/TcgPlatform*, BC250 adds CbsBasePei, PspRecovery,
  FanTuning, OEMBOARD, ISL VRM.
- Mem training entries both sides: MemDetect + AmdMemAm4Pei +
  PlatformMemoryConfigurationPei (+ AmdMemoryHobInfoPeim), but ALL
  diff-body: different AGESA drops (C0A CDBDK-BL5 44.0.0.220406 vs dump
  RBNBDK-BL5 46.1.2.211126 vs P5.00 RBNBDK-BL5 46.1.2.220426).
  Implication: donor training code is an OLDER-numbered drop — R5
  "more modern" does NOT hold for AGESA; M0 tests cross-drop training.
- FCH: FchPei+SbPei+FchDxe(+Aux)+SbDxe+GnbDxe both sides, all diff-body.
- SIO split: IT8772E (donor) vs NCT6686D (BC250), different init PEIMs;
  generic SioDxeInit/GenericSio exist both sides (diff-body).
- GPIO: AmdCpmGpioInit PEI/DXE/SMM both sides (PEIM diff-body).

## 1.3 Setup IFR (existing e1_ifr_dump decoders via thin /tmp driver, PASSED)
- C0A-stock Setup: 40 forms / 323 questions; OC-relevant: ONE question
  ('Memory Clock' @ Setup+0x11e) + one TEXT. OC-poor.
- Dump Setup: 38 forms / 277 questions; full Voltage Configuration form
  (VCORE/GFX/MEMIO fix voltage + loadlines, grayed/hidden but present).
- P5.00 Setup: 39 forms / 277 questions; OC count same as dump (20).
- Dump CbsSetupDxe: 71 forms / 1193 questions; 122 OC hits incl 'Memory
  Clock Speed' @ AmdSetup+0x316. Donor HAS no CbsSetupDxe.
- Verdict: M0-as-is LOSES the entire CBS OC universe (R3 negative for the
  donor base). OC on a donor base must come from transplant (M3) or SMU
  governor (host-side, already proven 1500->2230 MHz).

## 1.4 fTPM review (static strings, PASSED)
- Donor stack complete: AmdPspFtpmPei+Dxe, AmiPspFtpmPei+Dxe+Smm, Tcg/TrEE
  PEI+DXE+SMM, Tpm20 ACPI/SMBIOS/Platform, TpmClearOnRollback.
- Only AmdPspFtpmPei_te shows fTPM logic strings ("Get fTPM cap fail",
  "Install fTPM factory reset PPI"); DXE/SMM bodies string-thin, no
  version strings anywhere. Deeper RE deferred to transplant design.
- R4 carrier set identified; transplant-onto-BC250 acceptance still UNRUN.

## 1.5 Video verdict (byte hunts, PASSED as negative result)
- GOP GUID (9042A9DE...): 0 hits in C0A-stock, dump, P5.00.
- ATOMBIOS: 0 in all three. GOP/VBIOS modules: none anywhere.
- Only traces: "GOP Port" string in all three (NBIO/GFX context, not a
  driver), GraphicsConsole consumer both sides, no producer identified.
- Symmetric unknown: NEITHER image explains pre-OS pixels. 4700S video =
  dGPU OpROM (board fact). BC250 pre-OS pixels = OPEN (OQ-N5): display may
  appear only after amdgpu loads; the D11R "BIOS splash" observation needs
  re-examination against this finding, not assumed GOP.

## Checks (G9)
- Census/PEI/IFR/fTPM/video hunts: PASSED (own runs, byte-level).
- AGESA-drop skew: observed-bytes (version strings). OC-loss verdict:
  static-analysis (IFR decode). Video: negative static result, open question.
- Ghidra decompile of training/FCH deltas: UNRUN (deferred to M1+ design).
