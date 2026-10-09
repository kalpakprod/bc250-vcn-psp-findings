# VULN-1: BC-250 PSP Security Gasket — runtime reprogrammability (and "owner" gap)

Date: 2026-08-28
Status: PoC exists (runtime SMN replay accepted); A1 (full 1461-write replay) pending board power cycle.

## What is violated
The PSP "security gasket" (SEC_GASKET, $PSP type 0x24, body 11344B, version B.51.0.16) is the
firewall table that defines which agents may access which MMIO/SMN ranges. Design intent
(inferred): it is a BOOT-TIME, one-way, trusted configuration: PSP applies it during boot,
commits per-bank enable registers (0x...234: 0=program, 1=commit) and locks (0x0900cb80=0xff),
and the Data Fabric firewall (SMN 0x0900xxxx / 0x0930xxxx / 0x0322xxxx) then enforces it for
the life of the system. Nothing in the runtime interface set we mapped (PSP SOS/C2P messages
35/81/82/90 on this board; no gasket command in the vendor C2P table either — the vendor
libgv loads gaskets only at firmware-load time, fw_type 0x4B) provides a "re-apply gasket"
operation.

## The gap (vulnerability)
The gasket table lives in ordinary SMN-reachable register space (0x0900c000..0x0900cfff VCN bank,
0x0900c234 enable, 0x0900cb80 lock) that the SMU can reach with its privileged SMN write
message (SMU Q3 msg 0x98 = smn_write32, proven on this board). Consequences:
1. The "committed at boot" table can be re-programmed at runtime by a lower-privilege agent
   (SMU) than the one that owns it (PSP) — the commit/lock protocol (0=program/1=commit) is
   replayable, and readback after SMU writes shows the new values (table accepted).
2. The BC-250 (Robin) gasket ships WITHOUT the VCN bank (HWID 12, 0x0900c000..0x0900cfff):
   its 0x201 group commits 8 banks (0x0902, 0x0930, 0x09006-9, 0x090B6-7) but never 0x0900C.
   Cezanne (working sibling) has the 51-write VCN bank inside its 0x201 group + 0x280
   recommit tail. So the VCN MMIO firewall is closed at boot and, by design, has no runtime
   path to open it.
3. Root cause of the observed 0xFFFFFFFF on VCN BAR5 after our 56-write replay: one of
   (a) missing commit context (the 0x280/0x210 groups were not replayed — A1 tests this),
   (b) requester/owner identity: the firewall policy masks (0x0900c910=0x497fff etc.) encode
   which requester classes pass, and/or the engine tracks the last committing agent (PSP vs
   SMU) — A1/A2 discriminate.

## PoC (existing)
- recon/smn_vcn_gasket_unclamp.py — 56-write Cezanne HWID-12 bank replay via SMU Q3 0x98
  (fire-and-forget). Result 2026-08-26: all writes accepted, readback OK, VCN MMIO still
  0xFFFFFFFF. Proves: runtime reprogram of the gasket table is POSSIBLE from SMU (the
  "boot-time-only" design is not enforced at the register level).
- recon/smn_full_gasket_replay.py (A1) — 1461-write full replay (Robin 1405 in file order +
  Cezanne VCN bank 51 + 0x280 recommit tail 5), same transport. Pending run.

## Exploit chain (toward VCN)
SMU Q2 0x23 overflow -> debug/unlock -> Q3 0x98 privileged SMN write -> gasket table
reprogram (A1: full; A2 alternative: PSP C2P LOAD_IP_FW fw_type=0x4B = vendor's own
gasket-load command, adapted to the SOS interface). If the table takes effect from SMU
context, the x86 host then sees VCN MMIO unclamped (V2), enabling VCN power/clock/firmware
bring-up (already proven: domain 6, VCLK/DCLK, navi10_vcn.bin staging) -> vainfo/VA-API (V3-V5).

## Reproducibility
Power-cycle rollback (board stock kernel restores PSP-applied gasket at boot). No flash writes.
Next run: board steammachine (127.0.0.1) on probe kernel 7.2.0-1.92 mode0.

---
## Fresh evidence (2026-08-29, post-study)
Confirmed against on-board JSON `~/vcn_unlock/smn_vcn_gasket_{control,full}.json` (run 2026-08-26):
- **full (56 writes)**: 56 SMN writes accepted + readback OK; `control_before=0x1 control_after=0x1`
  (Bank-12 enable readable through SMU); **`all_ones_before=True` AND `all_ones_after=True`**;
  every ladder entry incl **UVD_VERSION=0xFFFFFFFF** unchanged. => gasket REPROGRAM takes effect in SMN-space,
  but the x86-side VCN MMIO bus stays power-gated (domain 6 not clocked/enabled) -> needs VULN-C (domain6 bring-up)
  OR a correct owner/last-committer commit context.
- **control (bank-12 enable bit only)**: `control_before=0x0 -> after=0x1` (bit flipped) yet all MMIO still 0xFFFFFFFF.
  => merely toggling the enable bit is NOT enough; the power/clock sequencer must engage.

Root cause of today's board hang reproduced (VULN-C wedge): the `full` replay ran WRITE-FIRST-ish but read the MMIO
ladder via VcnDirect.rd() while domain was still gated -> bus wedge (~04:02, netconsole last `usb 7-2: USB disconnect`,
ping 100%). => SAFE = enable domain FIRST (unlock->install->fire msg 0x61 -> engage dom6), THEN read MMIO.
Full consolidated chain + next PoC steps: `recon/VCN-ATTACK-PLAN.md`.
