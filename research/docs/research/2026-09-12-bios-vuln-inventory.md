# BC-250 BIOS vulnerability inventory, pass 1 (2026-09-12)

Goal: every surface a custom patched/AGESA BIOS build could use, with the
exact trust boundary and what is proven vs open. Evidence classes per
`memory/evidence-model.md`. All inputs are existing repo files (see action
log `docs/action-logs/2026-09-12-deep-re-pass1.md`).

## 1. Measured maps (observed-bytes + static-analysis)

### 1.1 PSP directory (19 entries, D10R image = stock layout)

| Idx   | Type      | Name (AGESA header / PSPTool)                                             | Size        | SPI       | Boundary              |
| ----- | --------- | ------------------------------------------------------------------------- | ----------- | --------- | --------------------- |
| 0     | 0x01      | PSP_FW_BOOT_LOADER                                                        | 43,008      | 0x8E0400  | signed, ROM-verified  |
| 1     | 0x02      | PSP_FW_TRUSTED_OS                                                         | 82,768      | 0x8EAC00  | signed                |
| 2     | 0x08      | SMU_OFFCHIP_FW (0.58.6.0, Robin3-identical body)                          | 262,656     | 0x8FF000  | signed                |
| 3     | 0x09      | AMD_SEC_DBG_PUBLIC_KEY                                                    | 1,088       | 0x93F200  | key mat.              |
| 4     | 0x12      | SMU_OFF_CHIP_FW_2                                                         | 262,656     | 0x93F700  | signed                |
| 5     | 0x13      | PSP_EARLY_UNLOCK_DEBUG_IMAGE                                              | 8,192       | 0x97F900  | signed                |
| 6     | 0x20      | HW_IP_CONFIG_FILE (IP discovery, VCN hwid12 desc.)                        | 1,616       | 0x981900  | signed envelope       |
| 7     | 0x24      | SECURE_GASKET_BINARY (gasket groups, no VCN bank)                         | 11,856      | 0x982000  | signed (kid 96ea7cfe) |
| 8     | 0x28      | DRIVER_ENTRIES (t28, ARM Thumb-2; 5-domain program, svc#6/#0x7c wrappers) | 108,400     | 0x984F00  | signed                |
| 9-13  | 0x30-0x34 | AGESA_BOOT_LOADER_0..4 (0x31 = ABL1 48,848 B)                             | —           | 0x99F700+ | signed                |
| 14    | 0x44      | FW_XHCI (hosts a hidden $PS1 envelope, tool a12)                          | 26,128      | 0x9C3D00  | signed                |
| 15    | 0x45      | TOS_SECURITY_POLICY (1,760 B, zero VCN-bank records)                      | 1,760       | 0x9CA400  | signed (same kid)     |
| 16    | 0x4F      | key DB region (in-repo $KDB decode: 8 RSA-2048 keys)                      | 66,048      | 0x9CAB00  | key mat.              |
| 17-18 | 0x50/0x51 | BL_PUBLIC_KEY / TOS_PUBLIC_KEY                                            | 3,536/1,856 | 0x9DAD00+ | key mat.              |

BHD (4 entries): 0x60 APCB (8,192), 0x61 APOB (size 0), 0x62 BIOS_FW
(2,088,960 @0xE02000), 0x63 APOB_NV_COPY (8,192). No 0x66 microcode entry.

### 1.2 x86 FV/FFS (234 modules: 179 PE32 + 55 TE)

SEC_CORE 1, PEI_CORE 1, DXE_CORE 1, PEIM 59, DXE_DRIVER 127, SMM_DRIVER 44,
SMM_CORE 1 (PiSmmCore). AGESA presence is dense in all three phases
(AmiAgesaDxe/Pei, AmdCcxVh/Fabric/Nbio/Alib/Base/Pcie/Smu/ARIPei/Dxe/Smm,
AmdSocBl5, AmdPspPei/DxeV2, AmdApcbObrDxe/Smm, AmdCpm*, AmdMemSmbiosV2,
AmdAcpiDxe). Display path: ConSplitter + GraphicsConsole (no vendor GOP UI
name; exact GOP/VBIOS carrier unresolved, low priority).

### 1.3 NVRAM (read-only probe of D10R image)

Store parses; visible names: Boot0001/BootOrder/DefaultBootOrder/ConIn/
ConOut/Setup/AmdSetup/SbNvramVar/CpuS3Resume/AmiAcpiTableAddrS3/
MemoryOverwriteRequest*. `scripts/nvar_audit.py` deliberately redacts
security-like names, so SecureBoot/PK/KEK state is INCONCLUSIVE from this
list (V15).

## 2. Vulnerability / modifiability inventory

- V1 — In-ship SMU-debug primitive (Bc250CoreUnlockDxe, slot
  2F3D426D-…). PROVEN usable (D9R/D10R `alive=True`). Dump-only vs
  BC250_3.00.ROM: vendor left a debug unlock driver in this board's BIOS.
  Setup-gated (`Setup+0x1C4 == 0x157C0` skips). This is the carrier every
  D-image reused.
- V2 — Unsigned x86 DXE FV (FV/FFS checksums only, explicit-size LZMA
  envelope `0x420010` required — D5-D7 lesson). PROVEN: arbitrary same-size
  PE32 replacement boots (D8/D9R/D10R). This is the custom-BIOS build
  surface for any DXE/AGESA-DXE patch.
- V3 — Unsigned APCB (byte checksum only). PROVEN bootable with DFG
  `0x007FFF00` (D8-D19; G7 2026-09-12 corrected the old "boot-unsafe"
  verdict). Custom-APCB surface for memory/DF policy.
- V4 — Unsigned NVRAM Setup/AmdSetup (control+value pairs coupled).
  Builder exists; one-field MemoryClock candidate built, static-only.
  Live effect UNPROVEN. No guessed voltages (rule stands).
- V5 — SMM attack surface, 44 drivers by FFS type (37 name-matched in
  `/tmp/clv_ext`, 233-module extraction of `BC250_5.00_clv.bin`
  `ea578104`): TRIAGED 2026-09-19, handler RE still OPEN (no zero-day
  claimed here). Present: AmdPspSmmV2 (`SwSmiCallBack`,
  `mPspMboxSmmBuffer`, `SmmCommunicationProtocol`), AmdApcbObrSmm,
  PspS3Smm + SmmS3SaveState + DXE BootScriptExecutorDxe/S3SaveStateDxe +
  PEI S3Resume2Pei → classic S3-resume/boot-script class intact.
  Absent: TPM/FTPM, VariableSmm/VariableRuntimeDxe. `SmiHandler` literal
  refs: 0 in all 7 top targets (EDK2 registers via protocol GUIDs, not
  literals — expected, not a finding). Port-IO index over all 37 SMM
  PEs (`objdump -d -Mintel`, 2026-09-19): 208 `out` / 166 `in`, CF8
  outs 26, CFC outs 24, SWSMI port B2 refs 11, PMIO CD6 refs 19;
  hottest: AmdPspSmmV2 (16 out/9 in, CF8+CFC+B2+CD6 all present),
  AmdApcbObrSmm (17/6), PspS3Smm (8/4). Handler RE NOT done: status is
  "audited to scope, no vulnerability established", recorded with the
  named next test in
  `docs/research/2026-09-19-zero-day-confirmation.md` §5 — per-handler
  decode of `AmdPspSmmV2` `SwSmiCallBack` + the S3 boot-script opcode set.
- V6 — Capsule/update + netstack surface: CapsuleRuntimeDxe (5632 B,
  `5d5ddcec`), CapsulePei, CapsuleX64 + full HTTP/PXE/IPv4/IPv6/USB/NVMe
  stack present. NARROWED 2026-09-19: CapsuleRuntimeDxe has 0
  verify/RSA/Pkcs/Auth/Cert/Hash strings and a PE with no import
  directory (reloc-only) — verification does NOT live in this driver.
  CapsulePei (6096 B) and CapsuleX64 (14432 B) carry none either;
  CapsuleX64's strings are an x64 exception-dump template, i.e. a fault
  handler, not a verifier. Status: "audited to scope, no vulnerability
  established" (`2026-09-19-zero-day-confirmation.md` §6). Named next
  test: decode the `CapsulePei` entry + platform capsule PCDs before
  calling an unsigned-capsule path a finding.
- V7 — Runtime SMU transports: TWO pre-auth defects, evidence
  self-contained in `docs/research/2026-09-19-zero-day-confirmation.md`
  (`720e5422`), which reproduces both handler bodies verbatim so no
  ignored path has to be trusted:
  ZD-1 = Q2 `0x23` (`FUN_0002D620`, in
  `evidence/firmware-audit/20260919-zd/secure_cluster_decomp.txt`
  `874a0d98`) — 8-bit ring count `*(count+0x780) & 0xff` indexes the
  slot while the count is incremented with no bound check, walking past
  the ring (`_DAT_000181b0 = 0x000188a0`) into the transfer-engine table
  pointer; pre-auth by construction.
  ZD-2 = Q3 `0x98` (`FUN_00028340`, table map
  `raw_messages__smu_fw_robin_5.txt:288`) — unguarded FIXED-`0xFF`
  writer; this CONFIRMS `smu-window-followup.md:132-137,174-177`
  (fixed-FF probe, not a general (address,value) primitive, cannot
  express gasket values). The earlier "arbitrary masked value" phrasing
  is RETRACTED; the surviving defect is the missing `*(0x1714C+4)` gate,
  sufficient for mask/bitmap writes.
  Both volatile, cold-cycle rollback. SVC7C zero-write NOT claimed
  (`svc7c-input-audit.md:32-34` stands). Domain-ACK unbounded poll
  DoS-only (`smu-window-followup.md:220-222` stands).
  Remaining untested: Q0 table transfer + sane 0x5C, Q3 secure-cluster
  `0x27-0x2F`, msg `0xFE`, PEI 0021 targets on clv.
- V8 — C2P TOS mailbox 0x100B direct: measured NEGATIVE (class closed as
  tried, G6).
- V9 — Signed $PS1 carriers (0x24/0x45 relocation/growth): PSP rejects
  stale-signature material, x86 never releases (D3-B2 discriminator,
  CLOSED as implemented). Only clean discriminator left: D3-C
  byte-identical signed relocation (unbuilt, deprioritized).
- V10 — RSA-2048 KDB: 11 records audited (no shared factor, Wiener/
  Fermat negative). Generically CLOSED; needs oracle/fault/leak.
- V11 — DEBUG_UNLOCK 0x13 token: needs AMD private key. DEAD.
- V12 — PSP S3 NV 0x1A absent from dir; APOB size 0: S3 resume leans on
  NVRAM/SMM paths (feeds V5).
- V13 — Microcode load path CLOSED as a standalone surface (decisive
  test RUN 2026-09-19, read-only on `BC250_5.00_clv.bin` `ea578104`):
  no BHD 0x66 entry (BHD = 0x60–0x63 only), no PSP microcode type,
  `cpuid 0x870F10` = 0 hits, `patch_id 0x08400707` = 0 hits, 0 hits in
  all 233 extracted modules; FV `0xE02000` RAW sections are all
  LZMA-compressed PE images (`MZ` after decompress), not ucode
  containers; sole `Microcode` string is recovery text `No Microcode`
  at `0xED703B`. Microcode ships inside AGESA PEI drivers, not as a
  replaceable file — preserve rule is trivially satisfied (we touch no
  RAW). No microcode-based zero-day claimed.
- V14 — Display-init carrier unresolved (works, name unknown). Low
  priority; do not touch until V2 workflow needs it.
- V15 — SecureBoot state CLOSED as ABSENT (decisive test RUN
  2026-09-19, read-only): `SecureBoot` GUID LE = 2 hits (NVRAM `0x404`
  MonotonicCounter + `0x1FED0`, both non-key records); variable names
  `SecureBoot/SecureBootEnable/SetupMode/CustomMode/VendorKeys/
PKDefault/KEKDefault/dbDefault/dbxDefault/BootOrder/OsIndications` =
  0 in NVRAM (`0x0–0x20000`) and 0 in full image (unicode+ASCII);
  SecurityStubDxe = 0 GUID refs; Setup (1608 unicode strings) has
  `Security` menu but no SecureBoot option; AMITSE has 1 unicode hit
  inside the `OsIndicationsSupported` capability list (not an option);
  `KEK` ascii = 0; `Secure` ascii = 2, both
  `DBG_UNLOCK_MODULE::Secure...` PSP-trace strings. No SecureBoot
  enforcement surface exists in this BIOS — nothing to bypass, nothing
  to claim as a zero-day.

## 3. What to do about the PSP block

The PSP is a hardware root of trust, not a software bug farm: on-die ROM
verifier + RSA-2048, private keys mathematically closed (V10), direct C2P
closed (V8), unsigned carriers fatal (V9). There is no evidence for a PSP
software bypass on this board revision, and the runtime power/isolation
denial sits below the SMU firmware (S2-L7/L8). So: stop attacking PSP
verification; use PSP as a fixed constraint and build around it:

1. Custom BIOS = V2+V3+V4 surfaces (DXE/AGESA-DXE patches, APCB policy,
   NVRAM) + V7 runtime, all of which PSP already accepts (proven by boot).
2. Understanding PSP (not bypassing it): finish the t28/DRIVER_ENTRIES
   executor RE (group dispatch, commit/lock, requester derivation) to
   predict which boot-time-applied values stick — that tells custom builds
   what to request vs what to do at runtime.
3. Single reserved flash discriminator: D3-C signed relocation, only after
   offline work says what it would prove.
4. Physical lanes (fuses/glitch/HDT) are out of software scope: no setup,
   no authorization record, high brick risk. Not recommended.

## 4. MCP reverse program: does it help, does it work

- Installed/pinned: Cutter 2.5.0 AppImage (`b8ad215d…`, 144 MB),
  CutterMCP_native v0.1.6 (`b4073e5b…`), CutterMCP-plus @ `69613e45…`
  (LICENSE present, third-party, loopback-only design `127.0.0.1:8000/9000`).
- Prior trial (recorded): native plugin on a fixture returned loopback
  health + initialize + tools/list + read-only queries (28 seg/36 fn/137
  str); CoreUnlock MCP transcript confirmed the Setup guard + Q3 path.
  So: yes, it works for interactive read-only RE.
- Right now: NO MCP listener on this host (`ss -ltnp` checked) — it is not
  "connected". Starting it requires the Cutter GUI process (server lives in
  the Cutter MCP dock/plugin); headless `QT_QPA_PLATFORM=offscreen` aborted
  in the recorded trial and Wayland/Orca GUI control failed before. No
  system rizin/rabin2/UEFIExtract exist; batch-capable tools present are
  `llvm-objdump`/`objdump` + repo parsers.
- Verdict: MCP helps for deep interactive decompile of 1-2 targets
  (t28 svc handlers, `AmdNbioGfxARIPei` 0x1e0/0x1e1 serialization), not for
  batch triage of 234 modules. Do not block on it: run the CLI batch now
  (V5/V13/V15 probes are scriptable), and bring MCP up via the operator GUI
  path (`tools/cutter/run-cutter-bc250`, isolated profile, verify
  127.0.0.1 binding, health → initialize → tools/list → one read-only
  query) when a target needs eyes-on decompile. Mutating MCP tools stay
  per-call approval per contract.

## 5. Ranked next (custom-BIOS oriented, no flash)

1. V13 microcode-magic sweep + V15 SecureBoot name scan (both read-only,
   one script, closes two unknowns).
2. V5 batch: `llvm-objdump -d` over the 44 SMM PEs → SMN/PMIO/SWSMI-
   pattern index (new script, hashed report). This is the largest
   unexamined privileged surface.
3. V6 capsule-verification read (CapsuleRuntimeDxe strings/xrefs).
4. t28 executor RE to completion (group dispatch/commit/lock) — informs
   what custom builds may request at boot.
5. Only then: Q0-table runtime combo (volatile) and, much later, D3-C.
