# Item-17 callback reachability and DD4/SVC6 path review

## Conclusion

The exact local ABL1 bytes accept a **conditional static callback edge**:

```text
item selector 0x17
  -> dispatcher 0x0C60
  -> table literal 0x0006E224 at payload 0x0F10
  -> table row {ptr=0x000606FD, key=0x17} at payload 0x17134
  -> under candidate base 0x57100: 0x606FD - 0x57100 = Thumb 0x95FD
  -> code entry 0x95FC
```

The candidate base `0x57100` remains conditional static coherence only; no loader/runtime-base proof exists.

The item-17 route is a **conditional static dispatch edge** to `0x95FC`; runtime loader/base and callback invocation remain unproven. The callback returns a **status value** `R0=0`, not a frequency result: the dispatcher checks it at `0x0EA8` and then exits because the selected row pointer is nonzero. On the single-state handler route, the memory-policy value read at `0x986E` is a runtime table U16 stored to `context+0x2BC` at `0x989A`; its numerical content/unit is not established.

- The initial `0x6C20` helper call makes the `[SP+0x164]` value `1`, but a later `0x6B78` call at `0x963A` fills 0x40 bytes through dynamic destination `R4+0x278`. Exact disassembly shows the distinct expressions but not their runtime alias relation. Therefore **DD4 (`0x0DD4`) reachability is conditional/unresolved**: with disjoint context/table and stack-local ranges, `BLS 0x9744 -> 0x984E` skips the DD4 call at `0x9780`; if the ranges alias, the fill can alter the branch input. The next offline discriminator is the active `R4` object/table provenance, not a repeated arithmetic scan. If DD4 is entered, its own `0x6C20`/`0x6D10` gate returns zero before the `0x0FB8` call.
- **SVC6 (`0x12AC -> SVC #6`) is rejected on the known direct item-17 edges, not globally.** The `0x0C60` selector path takes `0x0E50`, not the `0x0FD8` alternative containing direct callsite `0x102C -> 0x12AC`. The other direct callers are `0x1104` and `0x11E8` in `0x10C0`/`0x118C`; those helpers test their own `[SP+0x58]` output from `0x6C20` (`+0x14=1`) and return error `9` before their `0x12AC` call. The SVC6 handler/recipient and other/global or indirect SVC6 routes remain outside scope.

No clock, training, unit, runtime, or hardware claim follows.

## Exact inputs and latest metadata

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, size `16,777,216`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin`, size `94,624`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Reused exact object: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`, SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Latest item-17 helper metadata: `evidence/firmware-audit/20260921-abl-item17-consumer/item17-helper-metadata.exit` = `0`; stderr empty.
- Prior input review: `evidence/firmware-audit/20260921-abl1-pstate-inputs/abl1-pstate-inputs-result.json` = `PASS`, `54/54`.

## Fresh execution

Tool: `/usr/bin/llvm-objdump`, LLVM `22.1.8`. Fresh windows were generated from the existing exact object; all `17` windows exited `0` with empty stderr. New ranges include `0x0E50..0x0ED0` (key lookup and indirect branch), `0x0FD8..0x1038` (fallback SVC caller), `0x6B78..0x6B84` (fill writes through dynamic R0), `0x7544..0x7560` (R4 source), `0x95FC..0x98B0` (handler/branch), `0x0DD4..0x0E18`, `0x10C0..0x118C`, `0x118C..0x12AC`, and `0x12AC..0x12C8`.

Verifier:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  evidence/firmware-audit/20260921-item17-reachability-review/item17_reachability_verify.py \
  > evidence/firmware-audit/20260921-item17-reachability-review/verifier.stdout \
  2> evidence/firmware-audit/20260921-item17-reachability-review/verifier.stderr
```

Observed final status: exit `0`, `128/128 PASS`, stderr empty. The filtered direct `BL 0x12AC` callsite extraction exited `0` and found exactly `0x102C`, `0x1104`, and `0x11E8`. Machine result: `evidence/firmware-audit/20260921-item17-reachability-review/item17-reachability-result.json`.

## Exact edges

### Dispatcher and table row

- `0x7E36`: `MOVS R1,#0x17`; `0x7E3A`: `BL 0x0C60`.
- `0x0C6C`: `BL 0x6C20`; `0x0C74`: `BLS 0x0C7A`; `0x0C80`: `BL 0x0E50`; `0x0C8E`: alternate `BL 0x0FD8`.
- `0x0E8C`: loads table pointer from payload literal `0x0F10` (`0x0006E224`).
- `0x0E94..0x0E9A`: eight-byte row stride and key comparison.
- `0x0E9E`: loads matching row pointer; `0x0EA6`: `BLX R2`.
- Raw payload row at `0x17134`: `fd06060017000000` = pointer `0x000606FD`, key `0x17`.
- Conditional mapping: `0x606FD - 0x57100 = 0x95FD`; clearing the Thumb bit gives entry `0x95FC`; raw prologue bytes are `2de9f04f`.

### Local gate and callback return

- `0x6D1E/0x6D20`: helper returns `1`; `0x6C2A/0x6C2E` stores it in output block `+4`.
- `0x0C72/0x0C74`: the independent dispatcher gate sees `+4=1` and selects `0x0E50`.
- `0x095FC` calls `0x6C20` and then clears table memory via `0x6B78` using dynamic destination `R4+0x278`, length `0x40`, fill byte `0xFF`. Non-alias with the status block is not established.
- If no alias, `0x9646` takes `BLS 0x9744` to the single-state path `0x984E`; it loads a runtime table U16 at `0x986E`, stores it to context `+0x2BC` at `0x989A`, and returns callback status zero at `0x9848..0x984A`.
- `0x0EA8`: callback return zero takes `0x0EAE`; `0x0EB0/0x0EB4` sees the selected row pointer is nonzero; `0x0EB6` branches to `0x0E84`, which returns dispatch status zero.

### Rejected DD4 and SVC6 edges

- The `0x095FC -> 0x0DD4` edge at `0x9780` is bypassed when the local output survives the preceding `0x6B78` fill. Potential alias between dynamic `R4+0x278..+0x2B7` and `SP+0x160..+0x178` remains unresolved. If DD4 is entered, its own `0x6C20`/`0x6D10` result drives `BLS 0xE14`, returning zero before the `0x0FB8` call.
- `0x12AC` contains `SVC #6` at `0x12C0`.
- Exact full-listing direct callers of `0x12AC` are `0x102C`, `0x1104`, and `0x11E8`. The first is on the skipped `0x0FD8` dispatcher branch; the latter two are on `0x10C0`/`0x118C` paths whose local `+0x14` checks bypass the wrapper call for helper result `1`. This bounds only direct item-17 paths, not global/indirect SVC6 reachability.

## Acceptance classification

| Claim                                                             | Status                                | Boundary                                                                                                                                                                                            |
| ----------------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Item `0x17` table row exists and has pointer `0x606FD`            | **PASS, observed bytes**              | Exact payload offset `0x17134`                                                                                                                                                                      |
| `0x606FD -> 0x95FC` under base `0x57100`                          | **PASS, conditional static**          | Loader/runtime base unproven                                                                                                                                                                        |
| Item `0x17` conditionally reaches `0x95FC`                        | **ACCEPTED, conditional static path** | Requires active dispatcher object/table and candidate base                                                                                                                                          |
| DD4 `0x0DD4` reachable from this item-17 path                     | **CONDITIONAL / UNRESOLVED**          | `0x6B78` writes 0x40 bytes through dynamic `R4+0x278`; stack-block alias is not resolved. If DD4 is entered, its own `0x6D10=1` gate returns zero before `0x0FB8`.                                  |
| SVC6 `0x12AC -> 0x12C0` reachable from known direct item-17 paths | **REJECTED (bounded)**                | Dispatcher takes `0x0E50`, callback returns status0, and exits. Direct wrapper calls from the skipped `0x0FD8`/alternate helper routes are gated off. Global/indirect SVC6 path remains unsearched. |
| SVC6 handler/recipient, clock/training effect                     | **UNRESOLVED**                        | Outside ABL1 local evidence                                                                                                                                                                         |

## Limits and next test

No runtime loader execution or callback invocation was performed. The next offline discriminator is to recover the active object/table initialization and the dynamic `R4+0x278` range so the candidate-base/table binding and stack-buffer non-alias can be proved or rejected; do not repeat the same pointer arithmetic. This resolves the conditional DD4 edge. The separate SVC6 handler/recipient boundary remains closed and is not promoted to a clock actuator.

No hardware, ROM, NVRAM, register, firmware, candidate, network, or installation write occurred.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-item17-reachability-review.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-item17-reachability-review.md`
- Evidence: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-item17-reachability-review/`
- Machine result: `item17-reachability-result.json`
- Verifier: `item17_reachability_verify.py`
- Failed/previous-attempt audit: `attempt1/` through `attempt7/`
- Manifest: `SHA256SUMS.final`
