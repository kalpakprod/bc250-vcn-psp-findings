# CLV ABL1 fallback descriptor raw-kind0 R1 construction

## Current

The actual fallback nested descriptor is `0x006F47C0`, and the raw-kind0 branch does **not** leave `R4=0`. Exact code sets `R4` to the descriptor low 12 bits before kind dispatch:

```text
fallback:
  table[0x61E] = 0x006CA7C0
  nested index = 0x6CA
  descriptor = table[0x6CA] = 0x006F47C0

0x9B6A..0x9B74: local_2c = 0x6CA - 0x653 = 0x77; BHS -> 0x9BE0
0x9BE6: compare 0x6CA against 0x671; BLS -> 0x9CEA is not taken
0x9BEA: R0 = descriptor & 0xFFF = 0x7C0
0x9BF0: R4 |= R0 -> R4 = 0x000007C0
0x9C00: raw kind = (descriptor >> 27) & 7 = 0
0x9C16..0x9C1E: invalid-kind log, then continue to 0x9C22
0x9C28: R1 = R4 = 0x000007C0
0x9C2A: BL 0x6DA4
```

Thus the raw-kind0 SVC#4 encoding is page `0x00000000`, offset `0x7C0`. This is an encoded caller value, **not** a physical SMN/MMIO register claim.

## Context+0x40 mask

Before kind extraction, callback `0x9B82..0x9B98` merges `[context+0x40]` into descriptor fields:

```text
bits 15..19  <- context+0x40 bits 15..19
bits 20..27  <- context+0x40 bits 20..27
bits 28..31  <- context+0x40 bits 28..31
replacement mask = 0xFFFF8000
preserved low bits = descriptor & 0x7FFF
```

The descriptor low12 `0x7C0` is preserved. The context merge can change raw kind bits `27..29` and bit30, redirecting execution to kind1..4 address formulas. Therefore `R1=0x7C0` is exact only for the raw-kind0 branch before a context-driven kind change.

## Correction

This supersedes the earlier wording that raw kind0 leaves `R4` zero. It does not. The exact `0x9BEA/0x9BF0` instructions set `R4` from descriptor low12 before `0x9C00` dispatch. No physical map or hardware effect is inferred.

## Verification

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/verify_kind0_r1.py \
  > /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/verifier.stdout \
  2> /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/verifier.stderr
```

Observed exit `0`, `38/38 PASS`, stderr empty.

- Verifier: `evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/verify_kind0_r1.py`.
- Machine result: `evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/kind0-r1-result.json`.
- Literal stdout/stderr: same directory, `verifier.stdout`, `verifier.stderr`.
- Manifest: same directory, `SHA256SUMS.final`.
- Action log: `docs/action-logs/2026-09-20-clv-abl1-svc4-kind0-r1-xhigh.md`.

Evidence class: observed-bytes + static-analysis. No firmware, hardware, settings, shared plan/memory, MCP/Cutter, installation, global config, candidate or commit changed.

## Remaining boundary

`[context+0x40]` value, active HEAP/fallback choice, active dispatcher object, SVC#4 translation, physical map, and hardware behavior remain unresolved. No stronger claim follows from the raw-kind0 encoded value.
