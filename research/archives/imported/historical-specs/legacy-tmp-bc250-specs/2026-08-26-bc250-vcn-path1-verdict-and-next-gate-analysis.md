# BC-250 VCN Unlock: Path 1 Execution Verdict & Second Gate Architecture

**Status:** superseded forward plan. The 56-write runtime-replay result remains evidence; use `2026-08-26-bc250-vcn-unlock-master-plan.md` for the remaining path.  
**Date:** 2026-08-26  
**Target:** ASRock BC-250 (Cyan Skillfish, DID `1002:13FE`), BIOS Robin P3.00, Kernel `7.2.0-1.1-cachyos-bc250`

---

## 1. Executive Summary & Verdict

1. **Path 1 (Runtime SMN Dynamic Gasket Unclamp via SMU) has been executed and evaluated on live hardware:**
   - **Control register write:** `0x0900c234: 0x00000000 -> 0x00000001` succeeded and read back verified.
   - **Full profile replay:** All 56 ordered Cezanne/Renoir HWID-12 Bank configuration writes (`0x201` and `0x280`) were dispatched via privileged SMU SMN access (`smn_write32`).
   - **Hardware MMIO outcome:** All 11 VCN BAR5 liveness registers (`UVD_PGFSM_CONFIG`, `UVD_POWER_STATUS`, `UVD_VERSION`, `UVD_STATUS`, etc.) remained `0xFFFFFFFF`.
   - **Conclusion:** Raw runtime register stores from SMU context alone cannot unclamp the host PCIe-to-VCN MMIO bridge.

---

## 2. Technical Anatomy of the Second Gate

Reverse engineering of BIOS Robin 3.00, AGESA UEFI PEI (`AmdNbioGfxARIPei`), PSP binaries (`SEC_GASKET`, `HARDWARE_IP_CONFIG`, `ABL1..ABL4`), and sibling APU policies supports the following layered hypothesis. Power, clocks, and firmware staging are proven; exact Fabric/IOHC semantics remain unproven:

| Layer | Subsystem | Mechanism | Status on BC-250 |
|---|---|---|---|
| **1. Power Domain** | SMU Power Management | Domain 6 power gate (`FUN_00023b14`) | **SOLVED** (`status = 0x01010101`) |
| **2. Clock Grid** | SMU PLL Sequencer | VCLK / DCLK slots `0x16..0x18` (`FUN_00023744`) | **SOLVED** (`cur_vclk=625`, `cur_dclk=1111`) |
| **3. Firmware Buffer** | VRAM MC Base | Direct VRAM staging bypassing PSP (`0x00f400e00000`) | **SOLVED** (`navi10_vcn.bin` verified in VRAM) |
| **4. Fabric Aperture** | Data Fabric / Gasket Bank 12 | 56 aperture descriptors (`0x0900c000..0x0900cb80`) | **Omitted in Robin SEC_GASKET** |
| **5. Bridge Translation** | IOHC / NBIF candidate route | Indexed-port and aperture candidates including `0x3e810/0x3e814` and `0x1f820` | **Host route remains closed; exact ownership and lock semantics unproven** |
| **6. Trust Anchor** | PSP Bootloader | RSA `$PS1` verification of `SEC_GASKET` container | **Cryptographically enforced by PSP** |

---

## 3. Why Runtime SMU Replay Was Insufficient

1. **Security Gasket group semantics remain unresolved:**
   The group types are ordered policy data consumed from a signed PSP component, but no recovered handler yet proves that `0x280`/`0x281` is a lock operation or that `0x0900cb80` freezes the table. Ordinary SMU writes reproducing the data are insufficient.
2. **Host-route ownership remains unresolved:**
   Host BAR5 transactions to VCN master-abort while IP discovery advertises the block. IOHC/NBIF routing is a leading candidate, but the exact requester validation, remap registers, and finalization function require loader/executor reverse engineering.

---

## 4. Next Strategic Gates (Roadmap to Full Unlock)

```
[ Gate 1: Power & Clocks ]  --->  [ Gate 2: Bridge Unclamp ]  --->  [ Gate 3: VCPU & Ring ]  --->  [ Gate 4: Linux VAAPI ]
       (COMPLETE)                     (CURRENT FOCUS)                     (PENDING)                     (PENDING)
```

### UEFI DXE/SMM instrumentation
- **Use:** Preserve SMU unlock, clocks, domain state, and chainload Linux in one UEFI session.
- **Correction:** DXE executes after PSP/ABL early policy initialization; it is not evidence of execution before gasket finalization. Bank replay from UEFI/SMU context did not open VCN MMIO.

### PSP TEE / Secure Debug analysis
- **Use:** Reverse-engineer the signed `DEBUG_UNLOCK` and type-`0x24` policy consumer.
- **Correction:** Secure debug support is proven, but its ability to disable the VCN gasket is not. A valid RSA token or a separately authorized secure-world vulnerability would be required for live use.

---

## 5. Artifacts Produced in Session

- `tmp_bc250/recon/smn_vcn_gasket_unclamp.py` — Dynamic unclamp runner.
- `tmp_bc250/recon/run_smn_vcn_gasket_unclamp.sh` — Safe telemetry-isolated runner script.
- `tmp_bc250/recon/smn_vcn_gasket_control_2026-08-26.json` — Control write evidence (`954ca2a0…06684`).
- `tmp_bc250/recon/smn_vcn_gasket_full_2026-08-26.json` — Full 56-write replay evidence (`36d16561…be52f`).
- `tmp_bc250/recon/smn_vcn_gasket_full_2026-08-26.out` — Execution log (`2f6a8511…a78d`).
