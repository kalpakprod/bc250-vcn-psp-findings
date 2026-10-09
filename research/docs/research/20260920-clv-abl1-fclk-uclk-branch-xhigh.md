# Exact CLV ABL1 UCLK/FCLK policy branches — narrow structural match

## Result

A fresh byte-backed verifier (`53/53 PASS`, exit `0`) matched retained ABL3/ABL1 source-string leads to two concrete branches in the exact decompressed BIOS 5.00 clv ABL1 payload. This is static policy/data handoff evidence only.

1. **UclkDiv1 M0..M3 read/log branch**
   - Exact branch slices: payload `0x2CF0`, `0x2D20`, `0x2D48`, `0x2D70`.
   - Descriptor field keys: `0x21`, `0x22`, `0x23`, `0x24`; common descriptor prefix begins with `0x20`.
   - Each slice calls the common reader at payload `0x1FB4` (raw little-endian `ff f7 ...` BL encoding), reads the returned byte from `[sp+0x0C]`, and sends it to the logger.
   - Exact payload string anchors are contiguous: `0x30AC`, `0x30C8`, `0x30E4`, `0x3100` for `Override UclkDiv1 M0..M3`.
   - No context/clock-register write or FCLK/UCLK PLL call occurs in these four slices. Therefore this branch is a concrete configuration read/log handoff, not proof of divider application.

2. **Fclk override read/write branch**
   - Exact branch slice: payload `0x463C..0x4695` (function body enters at `0x463E`).
   - Input: incoming `r0` pointer is preserved in `r5` at `0x4642`; selector `r1` must equal `0x0F` (`cmp r1,#0xF` at `0x4648`).
   - Descriptor: halfwords `0x015F` and `0x0160` are constructed at `0x464E..0x465A`.
   - The branch calls the same reader at `0x1FB4`; returned halfword at `[sp+0x08]` is loaded at `0x467E` and stored through the caller pointer with `str r0,[r5]` at `0x4682`.
   - Exact logger ADR at `0x4678` targets exact payload string `0x469C` (`Override Fclk: %d`).
   - A wider caller reaches helper `0x46B4` from payload `0x7000`; that helper also remains a config/container handoff and does not establish a physical clock write in this bounded evidence.

## Source-lead match and limits

The retained ABL3 decompilation (version-aligned lead, not source-to-binary identity) names the UclkDiv1 M0..M3 sequence in `FUN_000033B4` case `2`: `0x21`, `0x22`, `0x23`, `0x24`, common reader `FUN_00002734`, and the four corresponding strings. The retained ABL1 string listing supplies `UclkDiv1` and `Fclk` names only; its historical offsets are not used as exact-clv addresses. Exact addresses above come from fresh byte searches and raw Thumb decoding of the pinned clv payload.

The first unresolved mapping edge is the exact common reader at payload `0x1FB4`: these branches prove descriptor construction and returned byte/halfword flow, but not what downstream component consumes the value, any UCLK divider ratio, MCLK/FCLK unit conversion, PLL programming, training selection, synchronous crossing, or physical clock result. No MCLK=UCLK=FCLK claim follows.

The known cross-channel minimum function `0x95FC` and aggregate classifier `0x751C` were not used as the deliverable.

## Pinned inputs and hashes

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact decompressed ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - SHA-256: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Retained ABL3 source lead: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/lorek123_psp/ABL3_decompiled.c`
  - SHA-256: `ecd1bfb8be3fe15257038c4db6fd927ab72ca97a920a4639ad10cece04d3e22f`
- Retained ABL1 strings lead: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/lorek123_psp/ABL1_strings.txt`
  - SHA-256: `c27bf19fb46415703c1e761641d3ac08102dda775b9152ea1b6a557c47741170`
- Existing exact Thumb disassembly: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`
  - SHA-256: `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`

## Reproduction and evidence ledger

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1_fclk_uclk_branch_verify.py
```

Observed stdout:

```json
{
  "status": "PASS",
  "checks": 53,
  "uclk_branch": [
    {
      "field": "UclkDiv1M0",
      "descriptor_key": "0x21",
      "branch_start": "0x2cf0",
      "reader": "payload+0x1fb4",
      "output": "returned byte at [sp+0xc] -> logger only",
      "exact_string": "0x30ac"
    },
    {
      "field": "UclkDiv1M1",
      "descriptor_key": "0x22",
      "branch_start": "0x2d20",
      "reader": "payload+0x1fb4",
      "output": "returned byte at [sp+0xc] -> logger only",
      "exact_string": "0x30c8"
    },
    {
      "field": "UclkDiv1M2",
      "descriptor_key": "0x23",
      "branch_start": "0x2d48",
      "reader": "payload+0x1fb4",
      "output": "returned byte at [sp+0xc] -> logger only",
      "exact_string": "0x30e4"
    },
    {
      "field": "UclkDiv1M3",
      "descriptor_key": "0x24",
      "branch_start": "0x2d70",
      "reader": "payload+0x1fb4",
      "output": "returned byte at [sp+0xc] -> logger only",
      "exact_string": "0x3100"
    }
  ],
  "fclk_branch": {
    "branch_start": "0x463c",
    "selector": "r1 == 0x0f",
    "input": "r0 pointer preserved in r5",
    "descriptor": ["0x015f", "0x0160"],
    "reader": "payload+0x1fb4",
    "returned_value": "halfword at [sp+0x8]",
    "output": "str r0,[r5] at payload+0x4682",
    "logger_string": "payload+0x469c"
  },
  "unresolved_edge": "payload+0x1fb4 consumes the UclkDiv1/Fclk descriptors and supplies the returned byte/halfword; its downstream consumer/clock-divider/PLL semantics are not proven by these branches. No MCLK=UCLK=FCLK or physical-clock claim follows."
}
```

Captured stderr was empty; verifier exit status was `0`.

Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json`.
Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1_fclk_uclk_branch_verify.py`.
Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-fclk-uclk-branch-xhigh.md`.

Checks: exact input hashes PASS; retained source/string leads PASS; exact UCLK string/descriptor/reader/output-flow checks PASS; exact FCLK selector/descriptor/reader/output-flow checks PASS; physical clock/training/hardware behavior UNRUN.
