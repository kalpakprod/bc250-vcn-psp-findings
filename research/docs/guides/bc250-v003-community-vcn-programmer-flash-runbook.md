# BC250 v003 Community MeiMeiDXE + VCN Unlock DXE — Programmer Flash Runbook

> Историческая процедура, статус пересмотрен 2026-09-27. Старое «следующий шаг» не является текущим разрешением на прошивку или runtime-запись. Сверять точную ветку, полный путь и хеш; одинаковые v001/v002/v003 в разных каталогах не равнозначны. См. `docs/research/2026-09-27-vcn-smu-status-audit.md`.


Status: STAGED, NOT flashed. Physical execution requires operator approval.
Package: `firmware-flash-pkg/20260923-v003-community-vcn/` (`SHA256SUMS`).
Method: **Hardware programmer (CH347 + flashrom) ONLY**. No AFU, no in-OS flash.

Build evidence:
- Base: `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3` (sha256 `606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182`).
- Payload: `candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.ffs` (normalized sha256 `0a4c997bc352e45c90f6f87b7b17c91892f073f969d5908f7aea1beb2990a20a`).
- Candidate: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003.bin` (sha256 `0fafe2c12bbdecf15cf7e06f474d4f3518d447205a4fbf351bfa097f309f0a36`).
- Build manifest: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003.build.json`.
- Action log: `docs/action-logs/2026-09-23-vcn-driver-v001.md`.
- Gate: `pytest tests/ -q` (83/83 pass).

---

## 1. Package Identity

| File | SHA-256 | Size | Description |
|---|---|---|---|
| `BC250_3.00_MeiMeiDXEv3_vcn_v003.bin` | `0fafe2c12bbdecf15cf7e06f474d4f3518d447205a4fbf351bfa097f309f0a36` | 16,777,216 B | Boot-proven Community 3.00 MeiMeiDXE base + `Bc250VcnUnlockDxe` |

### Capsule and Volume Properties

- Base ROM lineage: Community 3.00 MeiMeiDXEv3 (193 FFS files in inner FV, boot-proven on BC-250 hardware).
- Inner FV file count: 193 -> 194 (+1 modular DXE driver).
- Injected FFS:
  - GUID: `B6250780-7E00-4203-900C-23443B1413FE` (`Bc250VcnUnlockDxe`)
  - Inner FV offset: `0x432000`, size `0x301c` (12,316 bytes)
  - FFS State byte: `0xF8` (`EFI_FILE_HEADER_CONSTRUCTION` | `EFI_FILE_VALID` | `EFI_FILE_MARKED_FOR_UPDATE`)
- Compressed capsule size: `0x1464d4` -> `0x145b69`.

---

## 2. Containment and Safety Boundaries

1. **Strictly Confined Modifications**:
   - Changed range vs base: `0x00AE0088` – `0x00C2654B` (`ndiff = 1331302` bytes due to LZMA capsule recompression).
   - Strictly inside the main compressed FV volume `[0xAE0000, 0xE00000)`.
   - Every byte outside `[0xAE0000, 0xE00000)` is **100% byte-identical** to the community base image (`cmp` exit 0).

2. **BootBlock & Crisis Recovery Intact**:
   - Range `0x00E00000` – `0x00FFFFFF` (top 2 MiB, including the 512 KiB AMD BootBlock) is completely untouched.
   - Crisis SPI recovery hooks remain bit-identical to factory.

3. **Signed Subtrees Preserved**:
   - PSP directory (`0x8E0000`), BHD, APCB tokens, and all 14 signed `$PS1` containers are byte-for-byte identical.
   - Zero cryptographic signature risks; no root keys or KDB containers altered.

4. **Residual Risks**:
   - DXE driver dispatch order relies on standard UEFI DXE Core scheduler; driver includes Depex `TRUE` / architectural protocols.
   - SMU mailbox interaction is safe (read-first, mailbox busy-wait with timeout); if SMU rejects messages, driver logs status and exits cleanly without hanging POST.
   - Live donor clock plan integration (O6 guard) will activate once extracted via `Bc250VcnProbe2.efi`.

---

## 3. Preconditions (Mandatory Hardware Discipline)

1. **Board Power Isolation**:
   - Disconnect 12V ATX/PCIe power supply cables completely.
   - Remove CR2032 CMOS battery.
   - Wait 60 seconds and short CMOS clear jumper to fully discharge capacitors.

2. **Programmer Hardware**:
   - Use CH347 programmer (native 3.3V logic level).
   - **NEVER** use unmodded 5V black-PCB CH341A programmers.

3. **SPI Flash Identification**:
   - Execute:
     ```bash
     flashrom -p ch347_spi:spispeed=1.875M --flash-name
     ```
   - Must report: `W25Q128.V` (16 MiB). If chip ID does not match, reposition SOIC-8 clip/header before proceeding.

4. **Observation & Output Channels**:
   - Connect direct DisplayPort display (HDMI may not initialize in early UEFI).
   - Connect LAN to monitoring host for DHCP/ping observation.
   - Note P0 status LED oracle:
     - Rapid green blink: UEFI boot / OS handoff in progress.
     - Static red or silence: POST halt / crash (trigger rollback).

---

## 4. Physical Flash Procedure

### Step 1: Pre-Write Backup Capture (Mandatory Double Read)

Read the current SPI flash contents twice to new files:
```bash
flashrom -p ch347_spi:spispeed=1.875M -r pre-v003-read-a.bin
flashrom -p ch347_spi:spispeed=1.875M -r pre-v003-read-b.bin
cmp pre-v003-read-a.bin pre-v003-read-b.bin && echo "READS MATCH OK"
sha256sum pre-v003-read-a.bin
```
**STOP** if reads differ. Do not proceed until two consecutive identical reads are obtained.

### Step 2: Verify Candidate Package Hash

Verify candidate checksum directly against the staged package manifest:
```bash
cd /home/OWNER/orca/projects/bc250/firmware-flash-pkg/20260923-v003-community-vcn
sha256sum -c SHA256SUMS
```
Expected output: `BC250_3.00_MeiMeiDXEv3_vcn_v003.bin: OK`.

### Step 3: Explicit Operator Approval Template

Before flashing, operator confirms in session:
```text
Подтверждаю запись файла firmware-flash-pkg/20260923-v003-community-vcn/BC250_3.00_MeiMeiDXEv3_vcn_v003.bin
SHA-256: 0fafe2c12bbdecf15cf7e06f474d4f3518d447205a4fbf351bfa097f309f0a36 на плату BC-250-01, чип W25Q128.V.
Pre-write дамп: pre-v003-read-a.bin, SHA-256 [хеш], 16 MiB, два чтения совпали.
Recovery: pre-v003-read-a.bin + evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3.
Route: programmer re-write + readback.
```

### Step 4: Write Candidate Image

Flash candidate firmware to the board:
```bash
flashrom -p ch347_spi:spispeed=1.875M -w BC250_3.00_MeiMeiDXEv3_vcn_v003.bin
```
Require: Return code 0 and `VERIFIED`.

### Step 5: Independent Verification Readback

Read back the written content into a fresh file:
```bash
flashrom -p ch347_spi:spispeed=1.875M -r post-v003-readback.bin
sha256sum post-v003-readback.bin
cmp post-v003-readback.bin BC250_3.00_MeiMeiDXEv3_vcn_v003.bin && echo "FLASH VERIFIED EXACT"
```
**STOP** if checksum does not match `0fafe2c1…`. Do not power on board if verification fails.

### Step 6: Post-Flash Board Bring-Up

1. Disconnect programmer clip/cable from board.
2. Reinstall CR2032 CMOS battery.
3. Reconnect 12V PCIe power cables.
4. Power on system and monitor P0 LED indicators and display.

---

## 5. Hardware Acceptance Gates

| Gate | Check | Pass Criteria |
|---|---|---|
| **H1** | POST & Display | LED green activity, DP video output, UEFI splash/shell visible |
| **H2** | UEFI Stability | System stable in UEFI Setup / UEFI Shell for >= 5 minutes |
| **H3** | Driver Dispatch | `drivers` or `dmem` in UEFI Shell indicates `Bc250VcnUnlockDxe` loaded |
| **H4** | OS Boot | Linux kernel boots to login prompt / SSH reachable |
| **H5** | VCN IP Block Detection | `dmesg | grep -i vcn` shows VCN discovery / initialization attempt |
| **H6** | Driver Power Gating | `amdgpu` driver loads without kernel panic or ring timeout |
| **H7** | Hardware Codec Readiness | `vainfo` / `vdpauinfo` reports VCN hardware decoding profiles |

---

## 6. Stop and Rollback Procedures

### Trigger Conditions
Immediately abort and disconnect power if:
- Programmer verification reports mismatch.
- Board displays static red LED or darkness for > 3 minutes (no POST).
- Thermal anomaly or audible regulator whine occurs.

### Rollback Path A (Immediate Restore to Pre-Flash State)
```bash
flashrom -p ch347_spi:spispeed=1.875M -w pre-v003-read-a.bin
flashrom -p ch347_spi:spispeed=1.875M -r rollback-verify.bin
cmp rollback-verify.bin pre-v003-read-a.bin && echo "ROLLBACK VERIFIED"
```

### Rollback Path B (Stock Community MeiMeiDXE Baseline)
```bash
flashrom -p ch347_spi:spispeed=1.875M -w /home/OWNER/orca/projects/bc250/evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3
```

---

## 7. Evidence Boundaries and Honest Assessment

- **Static Build Acceptance**: Candidate verified via automated scripts (`build_vcn_v002_candidate.py`), structural analysis, and containment checks.
- **Hardware Status**: UNFLASHED. All behavioral predictions (driver execution, SMU handshake, VCN IP un-gating) remain theoretical until physical execution.
- **Probe2 Prerequisite**: Running `Bc250VcnProbe2.efi` via FAT32 USB in UEFI Shell remains the recommended safe precursor to confirm donor clock plan before permanent driver activation.
