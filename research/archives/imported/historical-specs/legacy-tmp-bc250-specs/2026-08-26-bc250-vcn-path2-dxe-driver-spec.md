# Path 2 Specification: Pre-OS UEFI DXE Driver (`Bc250VcnUnlockDxe`)

**Status:** partially outdated implementation reference. Retain the UEFI application and same-session chainload; use `2026-08-26-bc250-vcn-unlock-master-plan.md` for timing and future activation work.  
**Date:** 2026-08-26  
**Component:** `Bc250VcnUnlockDxe` (EDK2 DXE Driver for AMD BC-250)  
**Package:** `tmp_bc250/dxe/Bc250VcnUnlockPkg/`  
**GUID:** `b6250780-7e00-4203-900c-23443b1413fe`

---

## 1. Architecture & Execution Timing

### Execution Point in Boot Chain
```
[ Power-On / SEC ]
       ↓
[ PEI / ABL (Memory & GNB Init) ]
       ↓
[ DXE Phase: Bc250VcnUnlockDxe ]  <--- (HERE: after PSP/ABL policy setup, before OS handoff)
       ↓
[ BDS / UEFI Boot Manager ]
       ↓
[ Linux Boot / amdgpu.ko loads ]
```

### What DXE currently proves:
1. **Same-session control:** It can run SMU unlock, power/clock operations, policy-data replay, and chainload Linux without a warm reboot between them.
2. **Timing limit:** PSP/ABL secure-policy initialization precedes DXE. DXE is not assumed to run before SEC_GASKET or IOHC finalization.
3. **No PSP-blob modification:** A standalone UEFI application avoids changing signed PSP components. BIOS injection remains a separate high-risk integration step and is not required for USB execution.
4. **Observed limit:** Replaying Bank 12 from this later context did not open host VCN MMIO.

---

## 2. Driver Implementation Overview

The complete source package has been implemented in `tmp_bc250/dxe/Bc250VcnUnlockPkg/`:

| File | Purpose |
|---|---|
| `Bc250VcnUnlockPkg.dec` | Package declaration, GUID definitions, protocol headers |
| `Bc250VcnUnlockPkg.dsc` | EDK2 platform description and build configuration |
| `Bc250VcnUnlockDxe.inf` | Module metadata, library dependencies, entry point definition |
| `Bc250VcnUnlockDxe.h` | Hardware register offsets, SMU mailbox structures, Gasket Bank 12 types |
| `Bc250VcnUnlockDxe.c` | Core logic: SmnRead/Write, SMU Mailbox send, Xtensa thunks, Gasket write replay |
| `build_ffs.sh` | Containerized EDK2 build script producing the `.ffs` module |

---

## 3. Core Bring-Up Sequence Inside Driver

1. **Host Bridge SMN Interface:**
   - Accesses AMD SMN indirect window via `00:00.0` offsets `0xB8` (Index) and `0xBC` (Data).
2. **SMU Clock Grid Activation:**
   - Installs 20-byte Xtensa thunk into SMU SRAM `0x3FF00`.
   - Calls `FUN_00023744` for slots `0x16`, `0x17`, `0x18` via Q3 msg `0x61` to bring up VCLK / DCLK.
3. **Domain 6 Power Activation:**
   - Installs 12-byte Xtensa thunk into SMU SRAM `0x3FF00`.
   - Calls `FUN_00023B14(6, 1)` via Q3 msg `0x61` to power on VCN domain.
4. **Data Fabric Gasket Apertures:**
   - Writes all 56 ordered descriptors to SMN Bank 12 (`0x0900C000..0x0900CB80`).
5. **Protocol Installation:**
   - Installs `gBc250VcnUnlockProtocolGuid` to signal completion to downstream UEFI drivers and boot loaders.

---

## 4. Integration & Flashing Workflow

1. **Build `.ffs` Image:**
   ```bash
   bash tmp_bc250/dxe/build_ffs.sh
   ```
2. **Insert into BIOS ROM:**
   - Open target BIOS (`BC250_3.00_CHIPSETMENU.ROM`) in `UEFITool`.
   - Locate the main DXE Firmware Volume.
   - Insert `Bc250VcnUnlockDxe.ffs` after `BC250DXEv3SMUUnlockDxe` / `MeiMeiDXE`.
   - Save modified BIOS ROM.
3. **Flash to BC-250:**
   - Flash via external SPI programmer (CH341A) or internal flashrom/AFU if supported.
