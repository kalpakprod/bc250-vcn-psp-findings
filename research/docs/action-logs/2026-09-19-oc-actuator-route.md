# Voltage actuator route — intent and results

## Intent — 2026-09-19T20:15:08+05:00

Actor: bounded code/RE agent. Root retains decisions and integration; this task supplies offline voltage-path evidence only. Requested routing is OpenAI Codex / high via model alias; no dispatch/model-verification tool is exposed here, so effective model/effort and independent delegation cannot be certified.

Read project contract, OC correction memory, evidence/tool memory, applicable reverse-engineering, firmware-forensics, SMU and verification skills, and the three task inputs. Memory API failed with AI_NoSuchToolError; repository memory is available. Preserve all pre-existing modifications and outputs.

Targets: new `docs/research/2026-09-19-oc-actuator-route.md`, this log, and new `actuator-*` evidence under `evidence/firmware-audit/20260919-oc-final-consumer-pass/`. No source, builder, candidate, source image, security-material, network or hardware changes. Rollback is removal of these new owned artifacts only (not performed).

Procedure: freshly assert clv SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 (16777216 bytes), SMU cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37 (262400 bytes), and equality of SMU body with clv at 0x8FEF00. Reuse unchanged OcConsumerRead.java and OCConsumer project with analyzeHeadless `-readOnly -noanalysis`; fresh output/log paths only. Start functions 0x207C8/0x30070, follow narrowly coupled voltage arithmetic, base source, bounds and actuator helpers, optionally state 0x134A4. No more INV inventory. Compare every printed instruction byte with the raw SMU. Preserve literal interpretations, exact commands, manifest and bounded unknowns. Describe, never implement, an upstream PPTable override possibility; compiled B000000A is already excluded.

## Arithmetic error correction and verification log — 2026-09-19T20:45:00+05:00

Arithmetic correction:

- In prior explore passes, an arithmetic transcription error claimed `0x01159E00 + 0x230 = 0x01159E30`.
- The actual sum computed from raw base literal `_DAT_000171a4` (`0x01159e00`) is:
  - `0x01159e00 + 0x230 = 0x0115a030`
  - `0x01159e00 + 0x200 = 0x0115a000`
  - `0x01159e00 + 0x250 = 0x0115a050`
  - `0x01159e00 + 0x260 = 0x0115a060`
  - `0x01159e00 + 0x270 = 0x0115a070`
  - `0x01159e00 + 0x274 = 0x0115a074`
- Hardware/register context: `0x0115a000` is the SMU hardware status/busy register (polled with bit 31 via `bbsi aX, 0x1f`), and `0x0115a030` is the primary command/VID write port.

Verifier execution:

- Executed `actuator-verify.py` with parameter `actuator-verification-recheck.json` preserving original verification files untouched.
- Verifier outputs PASS across all 11 actuator passes and followup files, confirming exact binary correspondence with robin_5 (cae8617c...) and BC250_5.00_clv.bin at 0x8FEF00.

Expected result: byte-backed rail/units/actuator chain or exact missing function/register semantic edge. Hardware safety and an applied voltage cannot be established offline. No project build/lint is applicable; evidence correspondence and input identity are the verification layer.
