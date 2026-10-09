# 2026-09-23 — R2: +VDDCR_SOC BIOS path — limitation proven (Plane issue #2)

## Intent

Work Plane board «BC250» issue #2 (R2, id `1f000934-ff36-4765-ae7e-0f5ffcc5c867`):
find a verified BIOS control path for +VDDCR_SOC, or prove the limitation with
evidence classes. No firmware image, board, or hardware state was to be modified;
all inputs read-only (pinned donor ROM, pinned GenCAD netlist, imported recon corpus).

## Procedure

1. Reconciled the robin_5 hash flagged unresolved by the previous session:
   fresh slice `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` at `0x8FEF00`,
   262,400 bytes → SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`
   — identical to every pinned recording in the corpus (action logs, verify scripts,
   VERIFICATION.txt). The 63-character "recorded" variant from the previous summary
   exists in no repository file (grep over docs/, evidence/, memory/, scripts/ returned
   zero holders): it was a rendering artifact, not a corpus inconsistency.
2. Read `docs/research/2026-09-19-oc-channel-identity.md` and
   `docs/research/2026-09-21-voltage-evidence-integration.md` (CBS side re-verified).
3. Read the full SMU mailbox table
   (`import/…/recon/known_messages_robin5.txt`) and `api_q3.py`: no SoC-voltage
   message exists in the surface; the only VddcrSoc messages are clock-domain queries.
4. Byte-level literal census of robin_5 (in-memory): single `0x01159E00` literal at
   `0x171a4`; zero direct literals of `0x0115A030`/`0x0115A000`; `0x13474` stored at
   `0x17124` and `0x15394`; `0x1714c` stores `0x8b18`.
5. Ghidra headless (`ghidra_12.1.3_PUBLIC`, existing `OCConsumer` project, `-noanalysis`,
   read-only scripts):
   - `evidence/firmware-audit/20260923-r2-svi-census/SviCensus.java` — slot-reference
     census + explicit decompiles of the VID helpers and handlers → `census-out.txt`.
   - `evidence/firmware-audit/20260923-r2-svi-census/HandlerSweep.java` — decompile of
     every non-reserved handler in queues 0/1/2/3/5 (~120 functions) → `sweep-out.txt`.
6. GenCAD netlist queries (pinned `ASRock AMD BC-250_ISL_X5R r1.00.cad`,
   SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`):
   SVI2 wiring, PMBus wiring, PUS1 pin set, +VDDCR_SOC members, SOC_EN drivers.
7. Wrote the result doc + deterministic verifier, ran gates.

## Result

- **Limitation proven**: no BIOS/firmware path to +VDDCR_SOC on this board revision.
  Full chain and evidence classes in
  `docs/research/2026-09-23-r2-soc-vddcr-limitation.md`.
  - SVI2 planes 0/1 (CPU/GFX) reach ISL69247 via `APU_SVD/SVT/SVC` → `CORE_GFX_SVD/SVT/SVC`;
    PMBus goes to `SMB0_CL/DA_ISO` (EC side). PUS1 (RT8237E) has 11 pins, all analog.
    No third plane, no SoC digital receiver, SOC_EN hardware-sequenced.
  - SMU actuator: exactly three writers of `base+0x230` (selectors `0x00`, `0x01`,
    calib `0x20`); the whole handler surface touches only two state domains;
    `q3 0x0F` maps kind 0→CPU wrapper, kind 1→GFX wrapper, else reject.
  - Corollary: the 1275/912 mV telemetry words (2026-09-13 capture) are CPU/GFX
    droop-calibration floats, not SoC; the driver label `Voltage[0]=VDDSOC` is a
    mislabel on this firmware.
- `verify_r2.py`: **PASS, 52/52 checks** (ROM/slice hashes, literal census, GenCAD
  member sets, census/sweep decompile line assertions, full-handler-surface negative
  checks, doc assertions).
- Consequence for the plan: P2 SoC sub-item resolved as limitation; P4's SoC-voltage
  precondition is unachievable via BIOS (operator decision needed: drop the SoC
  ≤1.15 V requirement or move it to a hardware-only track).
- Gates: `pytest tests/` 83 passed; `make test` 7/7 OK.
- Plane sync (REST via the standard `plane-mcp` tunnel, 127.0.0.1:18080 → CT203):
  issue #2 comment `871a6299-15cb-41eb-86ae-66e62ebf88e3` posted (verdict), state
  moved Backlog → Done (`fdbc0105-47ec-4401-bd28-85d8fe4376f2`).

## Writes

New files only (no existing file modified except the plan update recorded below):

- `docs/research/2026-09-23-r2-soc-vddcr-limitation.md`
- `evidence/firmware-audit/20260923-r2-svi-census/{SviCensus.java,HandlerSweep.java,census-out.txt,census-err.txt,sweep-out.txt,sweep-err.txt,verify_r2.py}`
- `.procoder/plans/clv500-actuator-first.md` (P2 sub-item, open questions, checkpoint)

No firmware image, board, bus, or hardware state was touched.
