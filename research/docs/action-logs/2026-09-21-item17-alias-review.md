# Item-17 stack/table alias boundary — intent

- Timestamp: 2026-09-21T18:05:00+05:00 (Asia/Almaty)
- Actor: `/root/pstate_precedence`, bounded offline executor.
- Target: exact CLV ABL1 and item-17 reachability result; no hardware/network/ROM writes.
- Objective read fully: `docs/research/2026-09-21-item17-reachability-review.md` and `docs/action-logs/2026-09-21-item17-reachability-review.md` were reopened before executing. Latest result metadata: `PASS`, `128/128`, candidate base `0x57100` only conditional; DD4 alias unresolved, direct SVC6 edges bounded.
- Scope: determine whether the `0x95FC` output buffer `[SP+0x160..]` can be proven disjoint from `R4+0x278` byte-fill target at `0x963A`. Reuse current exact object and the latest local disassembly command pattern. Do not trace the UCLK caller-pointer identity `0x7FC2 -> 0x8428` owned by `/root/memory_clock_units`.
- Next executable action: fresh bounded LLVM Thumb disassembly of callback argument flow (`0x0C60..0x0C8E`, `0x0E50..0x0EA8`), `0x95FC` frame/fill gate (`0x95FC..0x9652`), and fill helper (`0x6B78..0x6B84`). Then a small deterministic verifier will test only these pointer expressions/ranges and the local stack write. The expected accepted result may be an explicit unresolved runtime/base/alias fact.
- Acceptance: either exact input/pointer lifetime constraints exclude overlap, or the precise unbound pointer/lifetime boundary is named; do not equate “different registers” with disjoint addresses. Reopen report/result/manifests and report concrete command/status.
- Rollback: delete only this unique evidence directory, this report, and this action log. No ROM, firmware, NVRAM, registers, hardware, network, install, or candidate change.

## Observed result

- Timestamp: 2026-09-21T18:07:00+05:00 (Asia/Almaty)
- Fresh command: `/usr/bin/llvm-objdump -D --triple=thumbv7` on the reused exact ABL1 object for four windows: `0x0C60..0x0C8E`, `0x0E50..0x0EA8`, `0x95FC..0x9652`, `0x6B78..0x6B84`. All four exit files record `0`; stderr files are empty.
- Verifier command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-item17-alias-review/item17_alias_bounds.py > evidence/firmware-audit/20260921-item17-alias-review/alias-analysis.stdout 2> evidence/firmware-audit/20260921-item17-alias-review/alias-analysis.stderr`; exit `0`, `32/32 PASS`, stderr empty. Machine result status is `INCONCLUSIVE_ALIAS_UNRESOLVED`, not a no-alias pass.
- Direct result: helper `0x6D10` sets the local `+4` field to `1`; later `0x6B78` writes `0x40` bytes of `0xFF` at `R4+0x278` before branch `0x9646`. No exact pointer/lifetime data proves whether `[R4+0x278,R4+0x2B8)` intersects `[SP+0x164,SP+0x168)`. Therefore `6D10=1` does **not** by itself prove branch `0x984E`.
- Callback arguments: `0x7E38` supplies the caller R4 as dispatcher R2; dispatcher `0x0E50` passes that context object in callback R0; `0x95FC` loads R4 from `[R0]`. The R4 value/address remains caller-supplied and dynamic. No `0x7FC2 -> 0x8428` pointer identity was traced.
- Outgoing on no-alias path: a table U16 is read at `0x986E`, stored to `context+0x2BC` at `0x989A`, and the handler returns callback status zero. The table's numeric U16 is unresolved.
- No ROM, firmware, NVRAM, register, hardware, network, install, or candidate write occurred.
- Remaining unresolved boundary: item-17 context allocation/lifetime and the runtime relation of its `R4+0x278` table to the handler's current stack; this is the smallest decisive fact for DD4 reachability.

## Final readback ledger

- Machine result `item17-alias-bounds-result.json`: SHA-256 `b87e04c178ff69d0806e426249edef5ae156dfcb7fdf195a962b376fa52b8f17`.
- Verifier `item17_alias_bounds.py`: SHA-256 `0d49a4613f639dc97e562530364c36161fcb9a92d47914684677df5740ed7a8a`.
- Literal stdout `alias-analysis.stdout`: SHA-256 `514b3c00ee3019465f060a5a1fa58e4bf3d4c3bbf2a94691e6647f20a1d18b6e`.
- Evidence manifest: 17 entries verified `OK`; SHA-256 `0b7764f4fc26ed3cc596e88ad1bd997c8c11af5f2921c62d9471758b24521761`.
- Report readback: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-item17-alias-review.md`, SHA-256 `1719342ccc3abf517f384b2e432d1a80550f37e2cd5b053ea3ad8b30aba83a79`.
- The alias result is an evidence-layer boundary, not a failed execution: fresh disassembly and 32 input/operand checks passed, but the exact effective runtime addresses needed to compare the intervals are absent.
