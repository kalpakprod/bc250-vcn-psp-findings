# Clock-control semantics — UclkDiv1M0 byte-path discriminator

## Intent

Timestamp: 2026-09-21T13:02:30+05:00 (Asia/Almaty; intent recorded before evidence writes)
Actor: `discriminating_test` executor
Target: immutable donor ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, size `16777216`; exact extracted `CbsBasePei` PEI body and its census/coverage artifacts, all locally retained.

Question: at the first exact-clv code path handling `AmdSetup+0x330` (`UclkDiv1M0`), does enum value `Enabled=1` get converted into a divider ratio before handoff, or preserved as a typed byte? A positive copy-only result rejects treating the Setup byte itself as a ratio at this layer; it does not establish the downstream interpretation.

G3 route check: inspected `scripts/build_clv_oc_candidate.py` (supports only the hash-pinned, stored-request-only `df1400` profile and rejects other profiles) and `scripts/probe_bc250_clocks_readonly.py` (live kernel-file collector; not a host-side semantic decoder). Existing exact-byte route is `evidence/firmware-audit/20260920-native-uclk-luna/uclk_consumer_trace.py`; it pins the same donor and module, checks the serializer/callback bytes, and models input bytes `00`, `01`, and `7f`. Its only project write is the result JSON beneath its own directory. No QEMU/emulator route exists for this closed firmware path in the current source map. Reuse the existing verifier unchanged by copying it into the uniquely named evidence directory so output stays isolated; no new analyzer or candidate is planned.

Planned command: copy the existing verifier to `evidence/firmware-audit/20260921-clock-discriminating-test/`, execute it with `python3 -B`, capture literal stdout/stderr/exit, and retain its generated JSON result in that directory. Read-only with respect to all ROMs, source, NVRAM, registers, hardware, network, and existing evidence files. Expected effect: discriminate byte-preserving serialization from ratio conversion within the checked PEI adapter, or expose a reproducible verifier/input blocker.

Rollback: remove only the unique `evidence/firmware-audit/20260921-clock-discriminating-test/` directory and this uniquely named action log; do not touch the donor, retained census, or any existing evidence. No firmware candidate, board change, or hardware write is authorized or intended.

## Execution & Observed Result

Timestamp: 2026-09-21T13:08:45+05:00 (Asia/Almaty)
Actor: `discriminating_test` executor
Target: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
Command:

```bash
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-clock-discriminating-test/uclk_consumer_trace.py
```

Exit code: `0`
Literal stdout:

```json
{
  "status": "PASS",
  "checks": 22,
  "fresh_result": "For setup bytes 00/01/7f at +0x330, the immediate callback output record remains ID 0x1204 with value 00/01/7f respectively. The first static callback is an INV adapter (0x36c0->0x36f0), not a clock/register consumer."
}
```

Literal stderr:

```
(empty)
```

Input hashes:

- `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `evidence/firmware-audit/20260919-inv-token-consumers/census.json`: `506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39`
- `evidence/firmware-audit/20260921-clock-discriminating-test/uclk_consumer_trace.py`: `44de5d8c0dc9b715b7c785673e377daddadde8eb95ae674afe0a04b8c24c672d`

Output hashes:

- `evidence/firmware-audit/20260921-clock-discriminating-test/uclk-consumer-trace.json`: `bb9ed4ea7b21f9f86f4d2e757fb940a77ce545464da900a26815fdf007796910`
- `evidence/firmware-audit/20260921-clock-discriminating-test/stdout.log`: `a25c695f68e51a77b88322a980397c761d82daf800a689612ea42aeba729621e`
- `evidence/firmware-audit/20260921-clock-discriminating-test/stderr.log`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

Findings:

1. `CbsBasePei` reads `AmdSetup+0x330` at `0x9ce4` (`8a8230030000`) and serializes it into record ID `0x1204` at `0x9cc9` without ratio conversion or mathematical translation.
2. Modeled enum inputs (`00`, `01`, `7f`) are preserved identically as raw bytes into the output record structure.
3. The immediate downstream callback is an INV adapter (`0x36c0 -> 0x36f0`), not a hardware clock register writer.

Remaining uncertainty:
The downstream consumer of record `0x1204` (e.g. within DXE or SMU message generator) performs the eventual interpretation of the byte; this test confirms only that PEI CBS serialization does not alter the byte representation.

## Post-write readback

Timestamp: 2026-09-21T13:10:00+05:00 (Asia/Almaty).

The report and evidence directory were reopened. Stable manifest: `evidence/firmware-audit/20260921-clock-discriminating-test/SHA256SUMS.final`. Report SHA-256: `3c4ee171fec107c5d9a690db6267e8110033a67884d4f8b2f4e62edfd864b086`. The evidence result remains `bb9ed4ea7b21f9f86f4d2e757fb940a77ce545464da900a26815fdf007796910`; verifier copy remains byte-identical to the reused source (`cmp` exit `0`). No source input changed. Hardware and final-consumer checks remain unrun.
