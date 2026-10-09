# CLV ABL1 SVC#4 descriptor table join — intent

- Timestamp: 2026-09-20T13:28:00+05:00 (Asia/Almaty; exact shell timestamp appended in result)
- Actor: subagent `/root/svc4_register_target`
- Scope: continue the exact table pointer join from B228 fallback allocator/store at context+0x44 to the literals at R1+0x1878 and R1+0x1B44; determine whether the same static table base reaches those stores and compute any exact fallback slot/descriptor values. Existing HEAP early-return path remains separate.
- Inputs (read-only): exact ABL1 payload; exact Thumb listing; prior descriptor-source result and report; exact-clv SMU map report `docs/research/2026-09-20-oc-df-init-route.md`.
- Method: bounded Thumb CFG with symbolic R1 state starting at B26A (`R1=TABLE=[SP+0xC]`), explicit raw byte/pool checks, target-store address arithmetic; no full verifier rerun and no runtime/hardware assumptions.
- Expected effect: only this evidence directory, report, and action log. No firmware/hardware/settings/shared plan/memory/MCP/Cutter/install/global config writes.
- Rollback: remove only `evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/`, report, and action log.

## Execution/result

- Final command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/verify_descriptor_join.py > evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/verifier.stdout 2> evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/verifier.stderr`.
- Observed exit `0`, stdout `PASS`, `56/56` checks, stderr empty.
- Symbolic CFG event: `R1=TABLE+0x70` at both target stores; `TABLE+0x70+0x1808=TABLE+0x1878` and `TABLE+0x70+0x1AB8=TABLE+0x1B28`.
- Raw pool readback: `C47C=c0a76c00 -> 0x006CA7C0`; `CF40=c0476f00 -> 0x006F47C0`.
- Exact fallback chain: `table[0x61E]=0x006CA7C0`; nested index `0x6CA`; `table[0x6CA]=0x006F47C0`.
- Existing HEAP path `B264/B266` returns before fallback stores; active HEAP/fallback choice remains unresolved. Context+0x40 high-bit merge remains dynamic; no physical address/hardware claim follows.
- Evidence role paths were reopened and hashes recorded in `SHA256SUMS.final`; no firmware/hardware/settings/source/shared-plan/memory/global-config/MCP/Cutter/install/commit changes.
- Rollback: remove only the unique evidence directory, report, and action log.

## G7 correction — exact CFG same-base join

The initial pointer-join report treated C7DE/C7E8 and C79A/C7A0 literals as possible `table[0x61E]`/nested values. The corrected symbolic CFG proves those stores use `R1=TABLE+0x70`: C7DE/C7E8 target `TABLE+0x18E8`/index `0x63A`; C79A/C7A0 target `TABLE+0x1BB4`/index `0x6ED`. This candidate binding is withdrawn.

The exact fallback table slots are proven by separate reachable stores: C210 writes `TABLE+0x1878`/index `0x61E` with pool C47C value `0x006CA7C0`; CC22 writes `TABLE+0x1B28`/index `0x6CA` with pool CF40 value `0x006F47C0`. New verifier rerun: exit `0`, `61/61 PASS`, stderr empty. Existing HEAP B264/B266 path still returns before fallback and remains the active-source boundary. No firmware/hardware/settings changes.
