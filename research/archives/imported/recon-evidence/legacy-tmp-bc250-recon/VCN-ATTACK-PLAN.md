# BC-250 VCN: attack plan (deep study, 2026-08-29)

Goal chain toward VCN on: **BC250, BIOS 3 (Robin1), PMFW 0.58.6.0**, Linux 7.2.0-1.1-cachyos-bc250, amdgpu loaded.
Reaches: **V2** (UVD_VERSION@0x05C9 != 0xFFFFFFFF) -> V3/V4 (VA-API enc/dec, no SW fallback) -> V5 (amdgpu_pm_info VCN ON) -> V6 (cold-reboot reproducible).

---
## The vulnerability chain (root cause -> effect)
### VULN-A : SMU secure-access debug unlock  (foundation of everything)
Exploit = queue-2 **msg 0x23** ring-overflow bug (see `upstream/bc250-smu-unlock/unlock.py`).
Transport: PCI config space, index/window at **0xB8 (index) / 0xBC (data)**, root-only (`write32(0xB8,reg); read32(0xBC)`). Each queue = SMN (cmd,rsp,arg) triple:
- Q0 0x03B10A08/068/048 (amdgpu-owned, racy); Q1 ...A00/A60/A40; **Q2 0x03B10528/0564/0998 (safe)**; **Q3 0x03B10A20/A80/A88 (safe, OC-tool uses it)**; Q4 ...A24/A84/A8C.
- send: rsp:=0; arg / arg_high; cmd=msg_id; poll rsp 0x01 OK / 0xFF reject / 0xFE / 0xFD / 0xFC.
Mechanic: overflow ring **subqueue 4** -> overwrites subqueue counters (just after ring) -> repoints transfer-table pointer
`TR_TABLE_PTR=0x19784` -> stage a **fake transfer table** at a dead-zone base `P < 0x7B20` (walk 72 zero-byte blocks) -> transfer-engine
(dram2smu) writes `NEW_ENTRY_KEY(0x37)` over the debug byte `DBG_DISABLE=0x7B3C` (**0xFD closed -> 0x0 open**). Probe at `PROBE_ADDR=0x0005A870`.
State after unlock: `smu_read(0x7B3C)==0`. Fixup zeros staged zone (0x7950), ring slots+counters (0x18DF0), and restores
0x7B38/0x19780/0x19784/0x19788/0x1978C/0x17E1C. **BIOS-3 only** (offsets differ in BIOS 5).
Effect: fully-arbitrary SMU read/write + code exec (the SMU's own native exec vector).

### VULN-B : SEC_GASKET runtime reprogrammability (the VCN-specific gate)
SEC_GASKET = PSP `$PSP` type **0x24** firewall table (Robin body 11344B, ver B.51.0.16). Design intent = **BOOT-TIME one-way**: PSP applies per-bank enable registers (0x0900c234: 0=program / 1=commit) and locks (0x0900cb80=0xff); Data Fabric firewall enforces for life.
Gap = the gasket table sits in ordinary SMN-reachable register space the SMU can reach via privileged **Q3 0x98 smn_write32**. So a lower-priv agent (SMU) can re-program it at runtime -> commit/lock protocol (0 program/1 commit) is replayable.
Known blocker (from decoded gasket): **Robin ships WITHOUT the VCN bank (HWID 12, 0x0900c000..0x0900cfff)**. Cezanne (working sibling) carries the 51-write VCN bank in its 0x201 group + 0x280 recommit tail.
Evidence 2026-08-26 (`recon/smn_vcn_gasket_{control,full}.json`): **56 writes accepted + readback OK through SMU, but VCN MMIO stayed 0xFFFFFFFF** (all_ones_after=True; UVD_VERSION=0xFFFFFFFF; control-mode even toggled bank-12 enable bit ctrl 0x0->0x1 without effect). => gasket reprogram is POSSIBLE but insufficient alone -> also need the domain power/clock OR a proper owner/last-committer context.
Two remediation paths from here:
- **A1 full replay (1461 writes)**: Robin 1405 in-file-order + Cezanne VCN bank 51 + 0x280 recommit tail 5, same transport.
- **A2**: PSP C2P LOAD_IP_FW with vendor fw_type **0x4B** (= the vendor's own gasket-load command, adapted to the SOS interface).

### VULN-C : native-domain6 bring-up (the "vehicle of record" -> direct-load)
`enable_vcn.py` (daveconde, 204 KB) installs a 20-byte Xtensa sequence into SMU scratch SRAM **0x3ff00**; repoints reserved Queue-3 msg-**0x61** handler ptr at SMU SRAM **0x776c**; fires msg 0x61; firmware's dispatcher runs `call8 0x00023744` three times for slots **0x16/0x17/0x18** (`soc_clk_program_slot @0x2362c`) to enable domain-6 (VCN) clock. Then `--direct-load`: stage **navi10_vcn** firmware in VRAM ourselves (driver's AMDGPU_FW_LOAD_DIRECT path), ring-test proof = driver flips **mmUVD_SCRATCH9 0xCAFEDEAD -> 0xDEADBEEF**. amdgpu needed only as raw MMIO/VRAM transport; dec-ring doorbell rung by writing GPU **PCI BAR2** directly (`VcnDirect.doorbell_ring/open`, `rd()` reads VCN MMIO, VCN_SEG0_DW=0x07800, VCN_SEG1_DW=0x07E00; UVD_VERSION@0x05C9 STATIC VERSION CONST).
Safety README: several measured SMU-wedge paths; recovery = **cold power cycle**.

---
## ROOT CAUSE of the observed hang (confirmed 29.08)
Reading VCN MMIO (`VcnDirect.rd()`) **while the domain is still power-gated** wedges the bus. Reproduced today: `full` gasket replay started, netconsole telemetry healthy until ~04:02, last line `usb 7-2: USB disconnect`, then dead (ping 100%, SSH No-route-to-host). Same class as A1 v1.
=> SAFE ordering (WRITE-FIRST): **enable domain (unlock -> install/fire dom6 clock -> engage) BEFORE any VCN MMIO read.** `--verify` is the safe read-only first contact; `--direct-load`'s first `rd()` is the wedge point.

---
## Feature framework levers (driver-unused, unlocked via Q2 0x05 enable_smu_features(mask))
feature_mask @0x17374; feature **6 gates the GPU power path** (RequestActiveWgp + q1_0x08 check FUN_0001db54(6)). Other levers: power_limit_set (Q2 0x2c -> 0x18450 fast+slow PPT), set_cpu_gpu_vid (Q3 0x0f), per-domain OC (Q3 0x24/0x25). `GetEnabledSmuFeatures` (Q0 0x3D) reads mask.

---
## Next PoC (when board is back up) -- in order
1. `sudo python3 enable_vcn.py --verify`          # read-only dom6/slot state (SAFE first contact)
2. `sudo python3 enable_vcn.py --no-fire`         # unlock + install + repoint, disarm on exit
3. `sudo python3 enable_vcn.py`                   # install + fire msg 0x61 (3s warning) -> fw executes dom6 clock
4. `sudo python3 enable_vcn.py --direct-load`     # stage navi10_vcn in VRAM + ring-test (CAFEDEAD->DEADBEEF)
   - parallel track (independent): re-run `smn_vcn_gasket_unclamp.py --mode full` (WRITE-FIRST variant) -> capture fresh JSON; only READ mmio AFTER writes.
5. Checkpoints: V2 UVD_VERSION@0x05C9 != 0xFFFFFFFF ; V3 vainfo VCN enc/dec ; V5 amdgpu_pm_info VCN=ON ; V6 cold-reboot reproducible.

## Rollback / reversibility
- Power-cycle restores stock PSP-applied gasket at boot. No flash writes.
- On-board: `~/vcn_unlock/rebc250.sh` (reboot), `rebc250-rollback.sh` (limine), `rebc250-info.sh`.
- Boot fixed: limine trimmed, default=fallback=CachyOS/linux-cachyos-bc250(stock), BOOTX64.EFI fallback intact.
Sources: `upstream/{bc250-smu-unlock,daveconde-bc250-vcn-enable}`, `bc250_smu/`, `recon/{vuln-1,gasket,SMU-HANDLERS,SMU-FINDINGS}*`.
