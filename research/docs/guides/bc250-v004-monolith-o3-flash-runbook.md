# BC250 v004 Monolithic Option O3 — Programmer Flash Runbook

Status: STAGED, NOT flashed. Physical execution requires operator authorization.
Package: `firmware-flash-pkg/20260923-v004-combined-o3/` (`SHA256SUMS`).
Method: **Hardware programmer (CH347 + flashrom) ONLY**. No AFU, no in-OS flash.

Build evidence:
- Base: `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3` (sha256 `606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182`).
- Payload: `candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.ffs` (sha256 `da2f70ccc9de2df5fe530a61197b0f3154ba853b9711e68fe31c7ef76caa9fbe`).
- Candidate: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v004.bin` (sha256 `2981b2525c4a101af745d3f22d4b78815566ee5445131a1aa0f5578ae97c5638`).
- Build manifest: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v004.build.json`.
- Action log: `docs/action-logs/2026-09-23-vcn-monolith-o3.md`.
- Gate: `pytest tests/ -q` (83/83 pass), `make test` (7/7 pass).

---

## 1. Package Identity

| File | SHA-256 | Size | Description |
|---|---|---|---|
| `BC250_3.00_MeiMeiDXEv3_vcn_v004.bin` | `2981b2525c4a101af745d3f22d4b78815566ee5445131a1aa0f5578ae97c5638` | 16,777,216 B | Option O3: Clean PSP directory (no 0x24/0x45) + Autonomous `Bc250VcnUnlockDxe` |

### Architecture and Modifications

- Base ROM: Community 3.00 MeiMeiDXEv3 (CPU core unlock + SMU unlock drivers pre-integrated).
- PSP Directory (`0x8E0000`):
  - Entry 7 (`0x24` SEC_GASKET, 11,856 B): Zeroed to 16x 0xFF.
  - Entry 15 (`0x45` TOS_SECURITY_POLICY, 1,760 B): Zeroed to 16x 0xFF.
  - Fletcher32 checksum refreshed: `0x63fffcc8` -> `0x3d1e03f9` (mathematically verified).
- Injected DXE Driver:
  - GUID: `B6250780-7E00-4203-900C-23443B1413FE` (`Bc250VcnUnlockDxe`)
  - Autonomous flow: sets domain bitmap bit 6 via `0x28`/`0x29`, logs clock plan words, issues SMU `MSG_VCN_POWER_UP` (`0x1B`).
  - No O6 abort guards (eliminated emulator-induced artifacts).
  - Inner FV module count: 193 -> 194.
  - FFS State byte: `0xF8`.

---

## 2. Containment and Safety Boundaries

1. **Strictly Confined Modifications**:
   - Total diff: 1,331,335 bytes.
   - Range 1: `0x008E0004` – `0x008E010F` (PSP directory header and slots).
   - Range 2: `0x00AE0088` – `0x00C2652B` (inner FV LZMA recompression).
   - Zero byte differences anywhere outside these two windows.

2. **BootBlock & Recovery Intact**:
   - `0x00E00000` – `0x00FFFFFF` (top 2 MiB, BootBlock and reset vector) is bit-for-bit identical to donor base.

3. **Signed Firmware Unchanged**:
   - Unreferenced bodies of 0x24 and 0x45 remain at their original ROM offsets without alteration.
   - BHD and all other PSP directory entries are intact.

---

## 3. Hardware Flash Execution (CH347 + flashrom)

### Step 1: Pre-flash Backup and Chip ID Verification
```bash
flashrom -p ch347_spi:spispeed=1.875M -r /tmp/bc250-preflash-backup-$(date +%Y%m%d-%H%M%S).bin
flashrom -p ch347_spi:spispeed=1.875M -r /tmp/bc250-preflash-backup2.bin
cmp /tmp/bc250-preflash-backup-*.bin /tmp/bc250-preflash-backup2.bin
```
*Requirement: Backup images must match bit-for-bit before continuing.*

### Step 2: Write Option O3 Candidate ROM
```bash
flashrom -p ch347_spi:spispeed=1.875M -w firmware-flash-pkg/20260923-v004-combined-o3/BC250_3.00_MeiMeiDXEv3_vcn_v004.bin
```

### Step 3: Readback Verification
```bash
flashrom -p ch347_spi:spispeed=1.875M -r /tmp/bc250-readback-v004.bin
sha256sum /tmp/bc250-readback-v004.bin
# Must match: 2981b2525c4a101af745d3f22d4b78815566ee5445131a1aa0f5578ae97c5638
```

---

## 4. Boot Observation and Verification Protocol

1. **Power Sequence**:
   - Reconnect CR2032 battery and 12V ATX/PCIe power.
   - Power on. Monitor P0 status LED.
   - Rapid green blink confirms successful UEFI POST and OS handoff.

2. **Linux OS Diagnostics**:
   - Check dmesg for amdgpu VCN discovery:
     ```bash
     dmesg | grep -iE "vcn|amdgpu"
     ```
   - Check DRM / VA-API endpoints:
     ```bash
     ls -l /dev/dri/renderD*
     vainfo
     ```
   - Verify SMN domain bitmap:
     ```bash
     # Bit 6 must be 1 (0x40 active)
     ```

3. **Rollback Trigger**:
   - If board hangs on POST (static red or no blink after 90 seconds), cut power and re-flash pre-flash backup or community base `BC250_3.00_MeiMeiDXEv3`.
