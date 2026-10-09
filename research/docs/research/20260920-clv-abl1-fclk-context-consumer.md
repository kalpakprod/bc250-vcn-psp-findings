# Exact CLV ABL1 FCLK context+0x78 consumer

## Result

Fresh verifier execution: `PASS`, `59/59`, exit `0`, stderr empty.

Exact raw dataflow:

```text
FCLK caller 0x5FAE
  -> reader 0x463C
  -> stack+0x4 reload at 0x5FB2
  -> halfword store [context+0x78] at 0x5FBA

separate context consumer 0x107E4
  -> ldrh [context+0x78]
  -> compare 0x3E8 or 0x4B0
  -> selector 0x264 / 0x464 / 0x260 / 0x0
```

Raw comparisons against the pinned CLV artifact:

- APCB span `0xAB1000..+0xB9C` contains no aligned raw halfword `0x3E8` or `0x4B0`.
- Persisted `AmdSetup+0x703/+0x704` bytes are `01 8C 05`; `+0x704` is raw `0x058C` (`1420`).
- These are raw comparisons only; no units or MHz interpretation is assigned.

The exact selected windows contain no direct `WRMSR`, `in`, or `out`. Direct caller linkage from the `0x5E68` producer to `0x107E4` remains unresolved; the shared `+0x78` field layout is byte-backed, but selector semantics remain unknown. No divider/PLL, clock equality, synchronization, runtime, or hardware claim follows.

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-context-consumer/abl1_fclk_context_consumer_verify.py
```

Observed stdout:

```json
{
  "status": "PASS",
  "checks": 59,
  "dataflow": {
    "reader_call": "payload+0x5fae -> FCLK reader payload+0x463c",
    "reader_output": "stack+0x4 reload at 0x5fb2 -> halfword store [context+0x78] at 0x5fba",
    "consumer": "separate context layout consumer payload+0x107e4 loads [context+0x78]",
    "comparators": ["0x3e8", "0x4b0"],
    "selectors": ["0x264", "0x464", "0x260", "0x0"],
    "apcb_raw_compare": {
      "thresholds_present_in_apcb": false,
      "setup_0x704_raw": "0x58c (1420)",
      "note": "raw comparison only; no units inferred"
    },
    "direct_control_effect": "no direct WRMSR/in/out in selected windows"
  },
  "unresolved_edge": "Direct caller linkage from 0x5e68 output producer to 0x107e4 consumer and the semantics of emitted selectors 0x264/0x464/0x260 remain unresolved. No divider/PLL/hardware claim follows."
}
```

Observed stderr: empty. Exit status: `0`.

## Pinned inputs and artifacts

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Exact disassembly: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`
  - SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`
- Prior exact FCLK branch result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json`
  - SHA-256 `d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa`

New artifacts:

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-context-consumer/abl1_fclk_context_consumer_verify.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-context-consumer/abl1-fclk-context-consumer-result.json`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-fclk-context-consumer.md`

No firmware, hardware, settings, shared plan/memory, global config, candidate, source, installation or commit changed.
