# Track-B T1: native base + 1750 MHz memory-clock pin

Date: 2026-09-16. Actor: root. Status: BUILT, review running.
Supersedes: 4700S-base ladder M0/M2-full/M4 (3 silent rungs, base exhausted;
see `docs/action-logs/2026-09-16-m0-window.md`).

## 1. Title and scope
First Track-B rung: the board's own shipping BIOS (pre-m0 capture) with
exactly one changed byte — the AmdSetup MemoryClockSpeed default pinned
from Auto (0xFF) to the 1750 MHz IFR option (0x23). No PSP/APCB/BHD/FV
structural change. Goal: prove boot-time memory-clock control (P2 memory)
and the NVRAM-default mechanism on rails that T1b (CBS menu masters) and
T2 (VCN inject) will reuse. Out of scope: menu unhide (T1b), voltages
(T1b IFR or password experiment), VCN (T2), fTPM (T3).

## 2. Planning anchor
Exact base: `evidence/programmer/reads/20260916/pre-m0-read-a.bin`
(16 MiB, SHA-256 `3f836668...`, this board's bytes, booted 2026-09-15/16).
Exact change: absolute offset `0x7E5` (`0x4CF` AmdSetup body + `0x316`),
`0xFF` -> `0x23`. IFR ground truth: MemoryClockSpeed ONE_OF qid 0x20f in
CbsSetupDxe form 0x702c, ungated, option 1750 MHz = 0x23 (decoded live
from the native PE32 with `e1_ifr_dump.py` + EDK2 opcode verification).
Builder: existing `scripts/build_amdsetup_memory_candidate.py` (G3 reuse;
old-value + magic + 1-byte-confinement asserts, refuses overwrite).
Output: `candidates/BC250_T1_mem1750_from_pre-m0.bin` (`b803cb4c...`).

## 3. Connected groups and observed existing logic
- IFR gate census (own runs): CBS hiding is conditional
  SUPPRESS_IF(NOT(EQ_ID_VAL(master,1))) — ~125 distinct masters, all
  AmdSetup-NVRAM-backed; memclk question itself ungated. Setup Voltage
  form grayed by SystemAccess (no NVRAM record — runtime var), so Setup
  OC needs IFR surgery (T1b) or the password experiment, not NVRAM.
- NVAR layout: raw-NVAR area @0x0-0x1000 (AmdSetup @0x4BB, Setup @0x1db)
  separate from the VSS store @0x1000 (45 records, no setup vars).
- Host SMU governor already moves GFX 1500->2230 MHz (proven); memory is
  boot-time-only, hence the BIOS pin.

## 4. Use cases
- P0 POST+video: board boots T1 (native base ⇒ expected; proves the
  Track-B base on this board post-campaign). Signal: video + Setup entry.
- P1 Linux: SSH up; `uptime` + GPU node. Signal: shell.
- P2 memory: UCLK == 1750 MHz via SMU metrics oracle. Signal: metric
  readback. Failure branches: (a) boots, UCLK unchanged ⇒ NVRAM-default
  hypothesis dead ⇒ T1b via IFR DEFAULT opcodes/APCB CBSG; (b) no boot
  (train fail) ⇒ recovery reflash pre-m0 ⇒ T1-redo with down-pin
  (1000 MHz 0x14) to prove control safely.
- Menu recon (same boot, free): photograph Setup/CBS state; decides T1b.

## 5. Implementation checklist
- [x] IFR decode + gate census + memclk option verification (own runs)
- [x] T1 build (1 byte, asserts) + structural verify (audit/PSP/BHD/APCB/
      FV headers/diff confinement)
- [ ] Independent review PASS (dispatched)
- [ ] Operator exact-text approval + CH347 -w + VERIFIED + readback
- [ ] Cold boot: P0/P1/P2 signals + Setup photos + SMU metrics

## 6. Open questions
- OQ-T1a (non-blocking): stock Auto-trained UCLK value (no baseline in
  evidence; T1 result itself implies it if unchanged... actually if T1
  moves UCLK to 1750, stock stays unknown — acceptable).
- OQ-T1b (non-blocking): CBS top-level entry mechanism (no CBS GUID REF
  in Setup PE32; AMITSE/CbsBaseDxe path unresolved — T1 boot photo may
  answer whether the tab shows today).
- OQ-T1c (non-blocking): SystemAccess setter (password-driven? gleaned
  from the password experiment on the T1 boot).

## 7. Decision log
- TD1 2026-09-16: T1 = 1-byte NVRAM pin, not the 125-master unhide (blast
  radius) and not IFR surgery (T1b). Smallest falsifiable OC rung.
- TD2 2026-09-16: pin UP (1750) rather than down-probe (1000): GDDR6
  1750 is inside plausible stock range, recovery is ready (programmer +
  operator + preserved pre-m0), and success delivers memory OC in one
  cycle. Down-probe is the armed fallback on train failure.
- TD3 2026-09-16: menus ride along as free recon; no menu change in T1.
