# G7 correction — `Setup+0x6A3` maps to token `0x1332`, not `0x1331`

> CORRECTION WITHDRAWN: this intermediate correction is itself superseded by the final section. Retained mapping: Setup+0x6A3 -> token0x1331; Setup+0x6A4 -> token0x1332. Preserve historical stdout, do not treat it as the latest verdict.

## Correction

An earlier project-memory sentence in `memory/oc-recheck.md` (line 30, SHA-256 `33fc15ec83a877a5f0e73b2411467b8a619e479b2d4c44ea18ebfbd4a6436802`) stated:

```text
... 0x6A3 ... record IDs ... 0x1331 ...
```

That mapping is wrong by one adjacent serializer record. Independent raw-byte checks on both retained serializer modules establish:

```text
Setup+0x6A2 -> record/token 0x1331
Setup+0x6A3 -> record/token 0x1332
```

The earlier statement is preserved as a superseded assumption here; shared memory correction is left for root/reviewer orchestration.

## Direct raw-byte evidence

Pinned inputs:

- clv ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `CbsBasePei` SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`
- `AmdNbioSmuV10Pei` SHA-256 `905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80`

For both TE modules, raw file offset = instruction RVA `- 0x190`, independently checked against module bytes:

| Module             | Source load RVA / raw bytes                                          | Record-ID RVA / raw bytes                                        |
| ------------------ | -------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `CbsBasePei`       | `0xD9CE: 8a82a2060000` (`+0x6A2`), `0xDA00: 8a82a3060000` (`+0x6A3`) | `0xD9E0: ba31130000` (`0x1331`), `0xDA12: ba32130000` (`0x1332`) |
| `AmdNbioSmuV10Pei` | `0xFA4E: 8a82a2060000` (`+0x6A2`), `0xFA80: 8a82a3060000` (`+0x6A3`) | `0xFA60: ba31130000` (`0x1331`), `0xFA92: ba32130000` (`0x1332`) |

Direct clv `AmdSetup` bytes at body base `0x4CF` are adjacent and equal: `+0x6A2 = 0x0F`, `+0x6A3 = 0x0F`; this confirms the source offset distinction is not a naming artifact.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-token1331-correction/token_correction_verify.py
```

Observed exit status: `0`; stderr empty; `13/13` checks passed.

Observed stdout:

```text
{"checks": {"failed": 0, "passed": 13, "total": 13}, "corrected_mapping": "Setup+0x6A2 -> token 0x1331; Setup+0x6A3 -> token 0x1332", "status": "PASS"}
```

## Boundary

This correction fixes only the serializer field/token identity. Record IDs remain handoff identifiers; downstream consumer, physical clock meaning, training, synchronization, and hardware acceptance remain unresolved.

## Superseded mapping, 2026-09-23

Unequal-marker execution of unchanged native CbsBasePei proves +6A3 ->1331 and +36D ->123C. The earlier report paired the value load with the NEXT record ID across pointer increment. See docs/research/2026-09-23-zen2-bc250-parameter-map.md and evidence/firmware-audit/20260923-oc-parameter-map/discriminator/result.json. Other scope limits still apply.
