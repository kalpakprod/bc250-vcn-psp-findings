# Exact CLV ABL1 UCLK/FCLK helper/provider boundary

## Result

The exact pending helper path after the completed UclkDiv1/Fclk branches was executed on the pinned decompressed clv ABL1 payload. Verifier result: `PASS`, `36/36`, exit status `0`, stderr empty.

- Helper `0x4800` subtracts 1 from the incoming token and accepts values `1..0x161` inclusive (checked by `(token-1) <= 0x160`). It sets internal selector `0x0F` and forwards the token/context/output/type arguments to exact provider function `0x49CC`.
- The caller values coming from the exact `0x1FB4` table reader are tokens `0x21..0x24` (UclkDiv1 M0..M3) and `0x15F/0x160` (Fclk branch). They pass that range check.
- Exact `0x49CC` dispatch case `0x0F` reaches helper `0x6374`, then config/APCB memory helper `0x6238`, followed by additional table-backed traversal/copy logic. The bounded source lead in retained ABL3 names a generic helper chain, but source/binary identity is not asserted.
- The end-to-end typed output consumer is still `0x1FB4`, which stores bytes/halfwords/words/doublewords to its caller output buffer according to caller-supplied type `1/2/4/8`.

This supports a **raw typed configuration-parameter lookup/copy** classification. It does not identify the parameter value as an enum, voltage, frequency, or pointer; does not prove a divider or PLL write; and does not prove `MCLK=UCLK=FCLK`, training, a synchronous crossing, runtime invocation, physical clocks, or hardware behavior.

**First unresolved edge:** helper `0x6374` / helper `0x6238` plus its runtime/APCB backing table. This is the next specific evidence requirement; do not restart with generic mailbox or source-wide searches.

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact decompressed ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Retained ABL3 source lead: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/lorek123_psp/ABL3_decompiled.c`
  - SHA-256 `ecd1bfb8be3fe15257038c4db6fd927ab72ca97a920a4639ad10cece04d3e22f`
- Existing exact ABL1 Thumb disassembly: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`
  - SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`
- Prior reader result, revalidated by this verifier:
  - `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json`
  - SHA-256 `537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128`

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1_apcb_consumer_verify.py
```

Observed status `PASS`, `36/36`, exit `0`; stdout is preserved in `verifier.stdout`, stderr empty.

## New artifacts

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1_apcb_consumer_verify.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-apcb-consumer-resume.md`

No firmware, hardware, settings, shared plan/memory, installation, global configuration, candidate, or source input changed. Rollback: delete only this uniquely named evidence directory, report, and action log.
