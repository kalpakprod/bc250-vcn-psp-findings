# BC-250 VCN — Continue Community Work (Second Gate → Decode)

**Status:** superseded forward plan. Historical community tasks remain context; current work is defined by `2026-08-26-bc250-vcn-unlock-master-plan.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: use executing-plans / step-by-step execution.  
> Steps use checkbox (`- [ ]`) syntax. One change → verify → note. Power-cycle OK (user).

**Goal:** продолжить работу community (`thelamer/bc250-vcn` + SMU RE), не изобретать параллельный трек.  
**End state (this plan's horizon):** second gate снят (VCLK leaves 0 / isolation clear) + decoder ring smoke без hang.  
**Beyond (отдельный plan после green):** VAAPI O3 apps (mpv/Jellyfin/browser) — не смешивать.

**Date:** 2026-08-25  
**Board:** `steammachine` 127.0.0.1 · BIOS **P3.00** (Robin 3.00) · kernel `7.2.0-1.1-cachyos-bc250`  
**Skills:** using-superpowers → brainstorming (done) → writing-plans (this file) → executing-plans  
**Prior evidence:** `tmp_bc250/specs/a1-readonly-report.md`, `tmp_bc250/recon/thelamer-bc250-vcn-README.md`

---

## 0. Where community stopped (source of truth)

### Done (do not re-prove from zero)

| Item | Evidence |
|------|----------|
| VCN 2.0.3 present, harvest=0 | thelamer README |
| amdgpu skips `vcn_v2_0` on cyan by default | thelamer + our ko strings / no local patch |
| PSP type13 `ITEM_NOT_FOUND`; type64 no-op | thelamer ruled out |
| Direct-load FW → `device_fw_loading` 0, reaches `vcn_v2_0_hw_init` placement | thelamer |
| **No** host `PowerUpVcn` mailbox msg in SMU 11.8 (7 queues) | thelamer Ghidra; our `bc250_smu` has 0 VCN helpers |
| Domain 6 = VCN power; **`FUN_00023b14(6, 1)` powers it ON** | thelamer — SMU ack poll OK |
| Stock clocks: **VCLK=0, DCLK=1111** | thelamer + our A1 `gpu_metrics` |
| PMFW 88.6.0 / SMU 11.8 | thelamer + our `0x580600` |
| q3 `0x98` = ungated SMN write (core unlock primitive) | core-unlock + thelamer |
| q2 `0x23` bug → SMU arb r/w + code exec (`bc250-smu-unlock`, **BIOS 3 only**) | unlock.py; **our BIOS P3.00 matches** |
| Direct VCN MMIO / UMR / SMN-debugfs → **board hang** | thelamer — ban until gate clear |
| Empty `dpm_set_vcn_enable` → driver fake-success → MMIO hang | thelamer — ban early driver register |

### Current blocker (THE work)

> After domain-6 power-on: **"VCN is gated by something else"** — clock / reset / isolation.

Teardown reference (community):
- `FUN_00024764` tears down domain 6
- touches clock slots **`0x16` / `0x17` / `0x18`** via  
  `FUN_00023744` → `FUN_0002362c` (`soc_clk_program_slot`)

**Critical naming trap:** mailbox message IDs `0x16/0x17/0x18` on Q0 are  
`ConfigureS3PwrOff*Hi/Lo` and `RequestActiveWgp` — **NOT** the clock slots.  
Slots are **arguments to `soc_clk_program_slot`**, internal SMU clock table indices.

### Open threads (community priority order — we adopt)

1. Diff VCN power/clock/reset/isolation **regs before vs after** `FUN_00023b14(6,1)`
2. Check whether slots `0x16/0x17/0x18` need programming as power-up prerequisite
3. Trace VCLK/DCLK enable; confirm clocks move from 0
4. Cross-ref Renoir/Van Gogh `dpm_set_vcn_enable` isolation/reset steps
5. Only then: decoder ring test (firmware execute, not just place)

### Our board gap vs community tip

| | Community tip | Us (A1) |
|--|---------------|---------|
| Domain 6 power | ON | **not done yet** |
| Second gate work | active | blocked on missing domain6 + call path |
| Driver VCN register | patched | **no** 7.2 patch |
| skillfish VCN fw blob | direct-load used | **absent** on disk |
| BIOS | Robin 3.x assumed | **P3.00** ✓ |

We must **catch up to domain6**, then **own the second-gate diff** (community's unfinished edge).

---

## 1. Success criteria (this plan)

**Must (second gate cleared):**
- [ ] Reproducible domain-6 ON without hang (idle ≥10 min, netconsole alive)
- [ ] Documented pre/post register or metrics diff for power vs gate
- [ ] **`cur_vclk` leaves 0** OR equivalent proven clock/isolation clear (with evidence)
- [ ] Board survives soft path; hang → power-cycle + note, no silent retry storm

**Should (ring smoke):**
- [ ] Decoder ring test does **not** hang board
- [ ] Optional: one short bitstream decode path if nodes appear

**Must not (this plan):**
- PSP key extraction / TA abuse as primary path (community ruled out)
- Early `vcn_v2_0` register before gate clear
- Unguarded `pp_dpm_*` reads
- Random navi/other `*_vcn.bin` symlink as “fw”
- q3 `0x98` spray without written target addr

---

## 2. Hard bans & safety (every session)

```
BANS:
  - pp_dpm_* without timeout wrapper
  - VCN BAR5 / UMR / kernel SMN-debugfs poke before gate-clear green
  - concurrent SMU: leave bc250-metrics + gpu-watchdog running during mailbox/RCE
  - more than ONE intentional SMU state change per boot without note
  - driver register VCN before P3 clocks green

REQUIRED:
  - netconsole → 127.0.0.1:6666 pulse before writes
  - baseline note: CU=38, gfx=2000/1013, vclk=0 dclk=1111, features mask
  - serialize: systemctl stop bc250-metrics bc250-gpu-watchdog (and pwrwatch if needed)
    → work → start back (or reboot)
  - physical power-cycle OK (user confirmed)
  - boot-forensics / 12V vs SoC hang split already on board — keep enabled
```

Rollback ladder:
1. `systemctl start` stopped units  
2. soft reboot  
3. known-good boot entry  
4. wall power-cycle  

---

## 3. Architecture of the attack (community-aligned)

```
                    ┌─────────────────────┐
                    │ Host (bc250_smu /   │
                    │  smu-unlock RCE)    │
                    └─────────┬───────────┘
                              │ mailbox / code exec
                              ▼
                    ┌─────────────────────┐
                    │ PMFW 88.6.0 Xtensa  │
                    │ FUN_00023b14(dom,1) │── domain 6 power
                    │ soc_clk_program_slot│── slots 0x16/17/18
                    └─────────┬───────────┘
                              ▼
                    ┌─────────────────────┐
                    │ VCN 2.0.3 silicon   │
                    │ power + clocks      │
                    └─────────┬───────────┘
                              │ only after gate clear
                              ▼
                    ┌─────────────────────┐
                    │ amdgpu vcn_v2_0 +   │
                    │ direct-load FW      │
                    │ ring / VAAPI later  │
                    └─────────────────────┘
```

**Call path decision (must resolve in Task 1):**

| Option | How | Risk | When |
|--------|-----|------|------|
| **C1** SMU code exec | `bc250-smu-unlock` (q2 0x23) then call `FUN_00023b14` | high, BIOS3 OK | default if no host msg |
| **C2** Host msg equivalent | if RE finds msg that wraps domain power | medium | prefer if exists |
| **C3** SMN via q3 0x98 | poke power regs directly | very high, easy brick | last resort, written addrs only |

Community already used internal FUN path → **C1 is the continuation**, not a fork.

---

## 4. Task list

### Task 0 — Session harness (read-mostly)

**Files:** `tmp_bc250/recon/session_baseline.sh` (new), notes in `tmp_bc250/specs/session-log.md`

- [ ] **Step 0.1** SSH: confirm BIOS P3.00, kernel, netconsole, CU/gfx fixed  
  ```bash
  ssh steammachine 'cat /sys/class/dmi/id/bios_version; uname -r; systemctl is-active bc250-netconsole'
  ```
  Expected: `P3.00`, `7.2.0-1.1-cachyos-bc250`, `active`

- [ ] **Step 0.2** Stop contenders (change — needs explicit OK first time):  
  `sudo systemctl stop bc250-metrics bc250-gpu-watchdog bc250-pwrwatch`  
  Verify SMU read: `check_test_message` OK, version `0x580600`

- [ ] **Step 0.3** Snapshot metrics once: parse `gpu_metrics` → log `cur_vclk/cur_dclk/cur_gfxclk`  
  Expected stock: vclk=0 dclk=1111 gfx=2000

- [ ] **Step 0.4** Write baseline line to `session-log.md`  
  **Restore:** start the three units (or reboot)

---

### Task 1 — Reproduce community domain-6 power (catch up)

**Depends on:** Task 0  
**Refs:** thelamer README; `rw-r-r-0644/bc250-smu-unlock`; collective SMU RE fw Robin3

- [ ] **Step 1.1** Vendor tree locally (Windows or board):  
  - clone/sparse `bc250-smu-unlock`  
  - clone/sparse `amd_smu_reverse_engineering` (smu_fw_robin matching 3.00, ghidra helpers)  
  Path: `tmp_bc250/upstream/`

- [ ] **Step 1.2** Confirm unlock offsets = BIOS 3 (README: BIOS5 needs different offsets).  
  Our BIOS P3.00 → use BIOS3 artifacts only.

- [ ] **Step 1.3** Dry-run unlock **without** domain call: prove RCE/read primitive returns known PMFW byte (from RE).  
  Verify: read matches Ghidra dump; board alive.

- [ ] **Step 1.4** ONE shot: call `FUN_00023b14(6, 1)` (or RE-confirmed wrapper).  
  **Do not** touch VCN MMIO after.

- [ ] **Step 1.5** Immediate verify (same boot):  
  - SMU still answers test_message  
  - `gpu_metrics` vclk/dclk (may still be 0/1111 — OK)  
  - netconsole: no storm  
  - idle 10 min  

- [ ] **Step 1.6** Note in session-log: domain6=ON method, time, metrics dump path  
  **Fail:** power-cycle → log → stop; do not loop  

**Exit:** domain6 ON reproducible on our board (= community tip).

---

### Task 2 — Second gate: pre/post diff (community open #1)

**Depends on:** Task 1 green

- [ ] **Step 2.1** Define register set to snapshot (from RE + Renoir/Vangogh vcn enable):  
  candidates: VCN power status, soft reset, clock gate, isolation, RB enable — **addresses from Ghidra/linux headers**, not guess.  
  Deliverable: `tmp_bc250/specs/vcn-reg-watchlist.md` (addr, name, width, source file:line)

- [ ] **Step 2.2** Tooling: SMU RCE memory read **or** safe SMN read path that community used for “register state confirms power” — **not** BAR5 VCN poke.  
  Script: `tmp_bc250/recon/reg_snapshot.py` → JSON before/after

- [ ] **Step 2.3** Capture **before** domain6 (cold or domain off if reversible) and **after** domain6 ON  
  Diff → `tmp_bc250/recon/domain6_regdiff.json`

- [ ] **Step 2.4** Classify each delta: power rail vs clock vs reset vs isolation vs unknown  
  **Exit:** named hypothesis for remaining gate (one primary)

---

### Task 3 — Clock slots 0x16 / 0x17 / 0x18 (community open #2–3)

**Depends on:** Task 2 hypothesis points at clocks/slots

- [ ] **Step 3.1** In PMFW RE: locate `FUN_0002362c` / `soc_clk_program_slot`; document args (slot, divider, enable).  
  Note: **not** mailbox 0x16–0x18.

- [ ] **Step 3.2** Trace who programs these slots on teardown (`FUN_00024764`) vs missing on power-up path.

- [ ] **Step 3.3** ONE slot experiment per boot (start with community order 0x16→0x17→0x18 or RE-proven enable sequence).  
  After each: metrics vclk/dclk + reg snapshot + 5 min idle.

- [ ] **Step 3.4** Success signal: **`cur_vclk != 0`** (or documented alt: isolation bit clear + non-zero VCN clk field in SMU telemetry).  
  Log exact call sequence that did it.

- [ ] **Step 3.5** Reproduce sequence cold boot ×2  
  **Exit:** written “clock bring-up recipe” + green metrics

**Fail paths:**  
- hang → cycle, mark slot+args bad  
- no clock move after all three → pivot Task 3b isolation/reset from Renoir `dpm_set_vcn_enable` (Task 4)

---

### Task 4 — Isolation/reset parity (community open #4)

**Depends on:** Task 3 failed or partial

- [ ] **Step 4.1** Extract from linux `*_dpm_set_vcn_enable` (Renoir/Van Gogh/VCN 2.0 family) the MMIO/SMU steps for reset clear + isolation  
  Table in `vcn-reg-watchlist.md`

- [ ] **Step 4.2** Map each step to skillfish addr via IP discovery / RE (no blind BAR walk)

- [ ] **Step 4.3** Apply **only** missing steps post-domain6+slots; one at a time  
  **Exit:** same success signal as 3.4

---

### Task 5 — Firmware placement (only after clocks green)

**Depends on:** Task 3 or 4 green

- [ ] **Step 5.1** Hunt skillfish/cyan VCN fw (board, linux-firmware git, community gist).  
  Ban: navi/beige_goby symlink.

- [ ] **Step 5.2** If no signed blob: port community **direct-load** path (buffer place, skip PSP).  
  Verify: load status 0; still **no** ring yet if unsure.

- [ ] **Step 5.3** Optional minimal driver register **with** real power/clock hooks (must not use empty dpm success).  
  Prefer out-of-tree / single patch file under `tmp_bc250/patches/`

**Exit:** fw placed; dmesg no hang × reboot

---

### Task 6 — Decoder ring smoke (community open #5)

**Depends on:** Task 5 + gate clear

- [ ] **Step 6.1** Netconsole watching; hand on PSU  
- [ ] **Step 6.2** Single ring test (kernel selftest or minimal IB)  
- [ ] **Step 6.3** If alive: short VAAPI/ffmpeg decode if nodes exist  
- [ ] **Step 6.4** Write results upstream-style notes:  
  `tmp_bc250/specs/community-continuation-notes.md` (for possible PR/comment to thelamer)

**Exit this plan:** ring does not hang; decode optional bonus

---

### Task 7 — Package findings back

- [ ] **Step 7.1** Compress: what worked, offsets BIOS3, slot recipe, failed dead ends  
- [ ] **Step 7.2** Diff against thelamer README — propose exact paragraph updates  
- [ ] **Step 7.3** Stop. O3 apps = **new plan** only after Task 6 green

---

## 5. Parallelism

| Parallel OK | Serial only |
|-------------|-------------|
| Task 1.1 upstream clone ∥ Task 0 harness docs | Task 1.4 domain call |
| Task 2.1 watchlist from public trees ∥ after 1.x | Task 2.3 snapshots around power |
| Task 5.1 fw hunt anytime (no install) | Task 3 slot writes |
| | Task 6 ring |

---

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R1 | Hang on MMIO/ring | ban until gate green; PSU cycle |
| R2 | smu-unlock wrong BIOS offsets | P3.00 only; verify read before call |
| R3 | Confuse mailbox 0x16 with clock slot 0x16 | checklist in every slot step |
| R4 | metrics D-state / SMU 0x00 | stop metrics/watchdog window |
| R5 | Driver register too early | hard gate Task 5 after clocks |
| R6 | Scope creep to Jellyfin | Task 7 stop rule |

---

## 7. Execution handoff

Plan complete and saved to `tmp_bc250/specs/2026-08-25-bc250-vcn-community-second-gate-plan.md`.

**Two execution options:**

1. **Subagent-driven (this session)** — dispatch executing-plans style worker for Task 0→1 only (catch up domain6), report after Task 1 exit  
2. **Inline** — same steps in this chat, stop at first fail/hang need

Which approach? (User picks.)

**Default recommendation:** inline Task 0 + Task 1.1–1.3 (no domain write) first; **explicit OK** before Step 1.4 domain6 call.

---

## 8. Source index (fetched this work)

| Source | Path / URL |
|--------|------------|
| thelamer notes | `tmp_bc250/recon/thelamer-bc250-vcn-README.md` |
| A1 board | `tmp_bc250/specs/a1-readonly-report.md` |
| SMU handlers Robin3 | `tmp_bc250/recon/SMU-HANDLERS.md` |
| SMU findings | `tmp_bc250/recon/SMU-FINDINGS.md` |
| known messages robin5 | `tmp_bc250/recon/known_messages_robin5.txt` |
| smu-unlock | https://github.com/rw-r-r-0644/bc250-smu-unlock (BIOS3) |
| SMU RE | https://github.com/bc250-collective/amd_smu_reverse_engineering |
| Board BIOS | P3.00 (dmi) |
