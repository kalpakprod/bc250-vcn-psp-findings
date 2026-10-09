# CLV offline goal continuation review

Date: 2026-09-21 (Asia/Almaty).

## Objective and bound TARGET

The objective attachment `/home/OWNER/.codex/attachments/9d7bcc99-0793-46b7-a070-9d0a73377101/pasted-text-1.txt` was reopened in full (9,956 bytes). It asks for a practical evidence-based BC-250 guide preserving the native 1800 MHz memory request, establishing physical MCLK:UCLK:FCLK = 1:1:1, evaluating SoC 1.15 V without assuming safety, and measuring performance. It explicitly forbids flash/NVRAM/register/voltage/hardware changes without separate approval.

Root's explicit operator clarification binds offline development to plain CLV 5.00: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, size 16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. The source manifest identifies this as a RetroWeb community redistribution with unknown uploader. The current installed GitHub image is not an offline blocker; the clarification does not establish present board identity or authorize flashing.

## Checkpoint and selected existing artifact

The current decision record identifies the first unfinished offline path as the indirect provider/consumer handoff for `$INV 0x1204` (`UclkDiv1M0`), from known CLV PEI serializers into the ABL1/HOB/APOB/SMU consumer side. The plan remains Phase 2 `PARTIAL`; no candidate is yet defensible as 1:1:1. The selected completed P-state/memory-clock artifact was `docs/research/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`; its logged prior action is `docs/action-logs/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`. The bounded evidence directory search found machine-readable command metadata: `none`.

## Executed verification

Reused existing checkpointed `scripts/nvar_audit.py` (SHA-256 `16d35db736f5ca0e4423c444ff892b9d2b583bd8efcafda1a5e752ff04cb1160`), with exact CLV TARGET and unique temporary output path `/tmp/bc250-goal-continuation-pstate-7xcq6z9y/clv-nvar.json`.

Command: `["/usr/bin/python3", "-B", "scripts/nvar_audit.py", "/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin", "--store-offset", "0", "--store-length", "0x20000", "--variable", "AmdSetup", "--output", "/tmp/bc250-goal-continuation-pstate-7xcq6z9y/clv-nvar.json"]`

Literal stdout: `{"output": "/tmp/bc250-goal-continuation-pstate-7xcq6z9y/clv-nvar.json", "records": 53, "selected": 1, "errors": 0}`  
Literal stderr: ``  
Exit status: `0`  
Output JSON SHA-256: `ddf79399db3d860a99f05ad0f5ad5e3e8e2c97cd4125a4bf15f3917551255ee3`

Named selected-field summary from the output JSON: `MemoryClockSpeed@0x316=36 (0x24); UclkDiv1M0@0x330=1; PhyPowerSaving@0x368=255; MemoryPstate@0x36D=255; FclkDpm@0x6A3=15; VddcrVddOffsetControl@0x6E5=0; VddcrVddOffset@0x6E6=0; VddcrGfxOffsetControl@0x6EA=0; VddcrGfxOffset@0x6EB=0; DfClockOverrideControl@0x703=1; DfClockOvrd@0x704=1420`

This is a direct saved-NVAR field check on the exact bound CLV TARGET. Concrete new result: the exact plain CLV image contains the native saved `MemoryClockSpeed=0x24` request (the static `1800MHz` option), `UclkDiv1M0=1`, `MemoryPstate=0xFF`, `FclkDpm=0x0F`, manual DF override control `1` with value `1420`, and zero VDDCR_VDD/GFX offsets. It confirms only stored bytes in that image; it does not validate the P-state consumer/behavior, training, physical clocks, or voltage safety/application.

## Requirements still unproved / first next technical action

- Preserve the `Memory Clock Speed=0x24` request (static menu label `1800MHz`); no downgrade was made.
- Physical `MCLK:UCLK:FCLK=1:1:1` remains unproved. `UclkDiv1M0=Enabled`, menu values, software metrics, or static source labels do not prove the ratio or synchronous crossing.
- SoC `1.15 V` remains an operator target/constraint, not a safe rating; no voltage was applied or measured.
- First unfinished offline action remains the bounded `$INV 0x1204` indirect/provider consumer trace, already assigned to the concurrent `luna_dispatch_check`; this worker did not duplicate it. Continue with actual byte-backed handoff and report a bounded unresolved edge if unavailable.
- Downstream field-to-actuator/domain and GDDR6 unit/rate conversion, Memory-P-state/training relation, migration/default precedence, physical clocks, independent performance measurement, and hardware acceptance remain open.
- No flash, candidate build, NVRAM/register write, voltage change, board contact, or shared-registry edit occurred.

## Continuation result — 2026-09-21

### Bound TARGET and objective

The supplied objective attachment was reopened in full. Offline TARGET is `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`); this is plain CLV 5.00, not the installed GitHub image. Preserve native Memory Clock request `0x24` (`1800MHz`); physical `MCLK:UCLK:FCLK=1:1:1` remains unproven; SoC `1.15 V` remains a target, not a safe rating. No flash, NVRAM/register write, voltage application, or board action is authorized.

### Executed pending check

No machine-readable command array was found in the selected P-state checkpoint evidence. The checkpoint names the existing verifier `evidence/firmware-audit/20260921-pstate-precedence-next/pstate_precedence_verify.py` (`b5d70cf67ca3c585d8dba3d09ff260d3e44fb8157c2f24b4919ac10333f31043`); it was run as `["/usr/bin/python3", "-B", "/tmp/bc250-pstate-precedence-recheck-hy0pi02k/evidence/firmware-audit/20260921-pstate-precedence-next/pstate_precedence_verify.py"]` in disposable CWD `/tmp/bc250-pstate-precedence-recheck-hy0pi02k`.

Literal stdout: `{"branch_precedence": {"slot_164_gt_1_and_slot_174_eq_0": "0x964E/0x9650 branches to 0x9746/0x9794; it gathers channel+0x20 values, calls helpers 0x118C and 0x10C0, then writes the output slot to context+0x2BC (0x981E) and each channel+0x20 (0x983C). Helper selection semantics are opaque.", "slot_164_gt_1_and_slot_174_ne_0": "Collects per-channel+0x20 values at 0x9672/0x9674; zero slave-table entries substitute 0x7D1 at 0x96E4..0x96E8; a 0x7D1-initialized current value is lowered on smaller candidates at 0x971E..0x9722; selected value is stored to context+0x2BC at 0x973E and each channel+0x20 at 0x9758.", "slot_164_le_1": "0x9644/0x9646 branches to 0x9744 then 0x984E system-master/table retrieval; the selected table value is stored to context+0x2BC at 0x989A. The bounded single-state window does not store a value to channel+0x20."}, "checks": {"failed": 0, "passed": 47, "total": 47}, "setup_raw": {"DfClockOverrideControl": 1, "DfClockOvrd": 1420, "FclkDpm": 15, "MemoryClockSpeed": 36, "MemoryPstate": 255, "UclkDiv1M0": 1}, "status": "PASS"}`  
Literal stderr: ``  
Exit status: `0`  
Verifier result: `{"failed": 0, "passed": 47, "total": 47}`

Persisted unique run evidence: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-goal-continuation-abl1-inputtrace-143944-3018034`.

### New edge and next missing boundary

The verified static edge is the ABL1 policy gate: `[SP+0x164] <= 1` bypasses multi-channel collection/writeback; `>1` reaches the `[SP+0x174]` zero/nonzero selector; nonzero enters channel `+0x20` collection/minimum/writeback, while the alternate/single-state paths commit other values. This is static branch/field behavior only. Exact producer/meaning of both stack slots remains unknown; there is still no byte-backed link from `$INV 0x11ED` (`AmdSetup+0x316`, 1800-labelled request) to the ABL1 context input.

**Next unfinished action:** Trace the caller/input-object construction for ABL1 function 0x95FC, binding the producers of [SP+0x164] and [SP+0x174] (and, if reached, the DF reader at 0x1FB4) to an observed configuration source such as $INV 0x11ED. The present verifier confirms branch effects only; both slot meanings/producers remain unknown.

No 0x1204/HOB trace was repeated, no shared registry or other agent report was edited, and no hardware/network/ROM/NVRAM/register action occurred.
