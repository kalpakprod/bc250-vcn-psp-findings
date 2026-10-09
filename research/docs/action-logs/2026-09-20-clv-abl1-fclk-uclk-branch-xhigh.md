# CLV ABL1 UCLK/FCLK narrow branch audit — intent

Timestamp: 2026-09-20T08:00:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor
Target: exact BIOS 5.00 clv ABL1 decompressed payload from `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, with retained ABL3 source/ABL1 string leads only.

Bounded task: match one concrete UclkDiv1/Fclk policy branch to the exact ABL1 bytes by structural anchors, record its input/output dataflow, and stop at the first unresolved consumer edge. Do not reuse cross-channel minimum 0x95FC or aggregate classifier 0x751C as the deliverable.

Inputs and expected hashes:

- ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact decompressed ABL1 SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Retained ABL3 source SHA-256 `ecd1bfb8be3fe15257038c4db6fd927ab72ca97a920a4639ad10cece04d3e22f`.
- Retained ABL1 strings SHA-256 `49e341226838db8a5005ebd36a881f4010e7140a081041997cf8bbd428bdfae3`.

Next executable action: run the uniquely owned verifier `evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1_fclk_uclk_branch_verify.py`; it will emit a machine-readable result and literal stdout/stderr captures.

Expected effect: new evidence/report/action-log artifacts only. No firmware, hardware, settings, shared plan, memory, install, global configuration, Cutter/MCP, candidate, or source artifact changes.

Rollback: remove only this uniquely named evidence directory, report, and action log; preserve all pinned inputs and prior evidence.

## Correction after first verifier execution

Timestamp: 2026-09-20T08:05:00+05:00 (+05:00)
Observed execution error: first verifier run exited `1` because the action-intent hash for `import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_strings.txt` was transcribed from the ABL3 strings file. The measured ABL1 strings SHA-256 is `c27bf19fb46415703c1e761641d3ac08102dda775b9152ea1b6a557c47741170`; ABL3 strings is separately `49e341226838db8a5005ebd36a881f4010e7140a081997cf8bbd428bdfae3` only as a source-lead comparison and is not the selected input.

Correction: update only the verifier's expected ABL1-strings hash to the measured value and retain the error as evidence; no project artifact or source input changed. The exact payload and source hashes matched before the failure.

## Correction after second verifier execution

Timestamp: 2026-09-20T08:08:00+05:00 (+05:00)
Observed execution error: the corrected verifier reached the exact UCLK branch but compared disassembly halfwords in display order rather than raw little-endian byte order (`BL 0x1fb4` is raw `ff f7`, returned-byte load is raw `9d f8 0c 30`; FCLK selector/store similarly require raw encodings).

Correction: retain the failed exit and change only verifier byte literals to raw payload order. The exact payload, source, and string hashes remain unchanged. No source/firmware/shared state changed.

## Correction after third verifier execution

Timestamp: 2026-09-20T08:10:00+05:00 (+05:00)
Observed execution error: verifier selected the preceding function's ADR at `0x4634`, whose valid raw target is unrelated. The exact FCLK logger ADR is the byte-backed `ADR r2,#0x20` at payload `0x4678`; its Thumb PC-relative target is `0x469c`, the exact `Override Fclk` string.

Correction: bind the FCLK string check to `0x4678` only. No input or source hash changed.

## Correction after fourth verifier execution

Timestamp: 2026-09-20T08:11:00+05:00 (+05:00)
Observed execution error: all branch checks reached the result write, but JSON serialization exited `1` because byte-valued check fields were not normalized.

Correction: normalize byte values to `hex:` strings in the verifier's evidence ledger only. The branch checks themselves passed before serialization; no source/input change occurred.

## Observed result

Timestamp: 2026-09-20T08:15:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor

Command:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1_fclk_uclk_branch_verify.py
```

Observed exit status: `0`. Captured stderr was empty. Literal stdout:

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

Evidence hashes:

```text
d902c0d78ae9650363f0870c23c08b41ae3570e06145c41df9c3d2364cd8a6bf  evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1_fclk_uclk_branch_verify.py
d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa  evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json
bfd2e9b773283d870c0378febbd42f33bd5b154a62143fed8d0838e8d66a6da6  evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/verifier.stderr
21727b96fb5706beabfa0c6c55bed75c1fa00731f9d374499af315d115281d02  docs/research/20260920-clv-abl1-fclk-uclk-branch-xhigh.md
ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8  pinned ROM
af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a  exact ABL1 decompressed
ecd1bfb8be3fe15257038c4db6fd927ab72ca97a920a4639ad10cece04d3e22f  retained ABL3 source lead
c27bf19fb46415703c1e761641d3ac08102dda775b9152ea1b6a557c47741170  retained ABL1 strings lead
b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65  exact ABL1 disassembly
```

Observed static result: exact ABL1 UclkDiv1 M0..M3 read/log slices are bound at `0x2CF0/0x2D20/0x2D48/0x2D70`, with descriptor keys `0x21..0x24`, reader `0x1FB4`, returned byte `[sp+0x0C]`, and exact strings `0x30AC/0x30C8/0x30E4/0x3100`. Exact Fclk slice `0x463C..0x4695` gates on selector `0x0F`, constructs `0x015F/0x0160`, calls `0x1FB4`, and stores the returned halfword through the caller pointer at `0x4682`; exact logger string is `0x469C`. The common reader `0x1FB4` is the first unresolved downstream edge. No MCLK=UCLK=FCLK, divider ratio, PLL, training, runtime, or hardware claim is made.

Readback: reopened the JSON result, report, verifier, and action log after writes; all four parse/read successfully. No firmware, hardware, settings, global configuration, install, source input, shared plan, or memory file changed.

Rollback: remove only this unique evidence directory, report, and action log; pinned ROM and prior evidence remain untouched.
