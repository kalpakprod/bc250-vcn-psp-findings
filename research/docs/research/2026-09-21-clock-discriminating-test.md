# Offline clock-control discriminator: UclkDiv1M0 byte semantics

## Conclusion

**Result: PASS (observed-bytes + static-analysis; not hardware-verified).** The first exact-clv PEI path preserves `AmdSetup+0x330` (`UclkDiv1M0`) as a typed byte in `$INV` record `0x1204`; it does not perform ratio arithmetic or convert `Enabled=1` into a decoded `/1` divider at this boundary. The immediate callback is an INV-buffer adapter, not a clock/register writer. This changes the decision tree: `Enabled=1` cannot be used as evidence of `UCLK=MCLK` or `UCLK=FCLK`; the final consumer/actuator and crossing semantics remain a blocking offline boundary.

This is a deliberately single-variable discriminator for UclkDiv1M0, not a generic protocol note. It does not modify a ROM, NVRAM, candidate, board, register, or hardware.

## Question and hypothesis

- Question: Does the first exact-clv consumer path transform `UclkDiv1M0` into a divider/ratio, or preserve the Setup enum byte?
- Input control: `AmdSetup+0x330` (`UclkDiv1M0`), with native options `Auto=0xFF` and `Enabled=0x01`.
- Hypothesis H0 (copy-only): values are loaded and written unchanged into a typed record; no ratio assignment is visible in this path.
- Discriminating alternatives: a ratio conversion/arithmetic operation, or a direct clock/register write, would reject H0 at this boundary.
- Scope: exact pinned CLV donor and extracted `CbsBasePei`; no execution of closed firmware and no hardware contact.

## G3 route check and inputs

Existing routes were inspected before execution:

- `scripts/build_clv_oc_candidate.py` supports only the stored-request-only `df1400` profile and explicitly rejects synchronization profiles; it cannot answer this byte-path question.
- `scripts/probe_bc250_clocks_readonly.py` reads live kernel files and is not an offline firmware-semantic test; the current host is not the target BC-250.
- Reused unchanged: `evidence/firmware-audit/20260920-native-uclk-luna/uclk_consumer_trace.py`, copied only to the unique evidence directory so its generated result is isolated.
- No QEMU/emulator route for this closed PEI/INV path was found in the current source map.

Pinned inputs:

| Input                                                                              | Role                     | SHA-256                                                            |
| ---------------------------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------ |
| `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (16,777,216 bytes)           | donor ROM                | `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` |
| `evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin` | exact PEI body           | `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77` |
| `evidence/firmware-audit/20260919-inv-token-consumers/census.json`                 | extraction/census index  | `506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39` |
| `evidence/firmware-audit/20260919-inv-token-consumers/coverage.json`               | bounded coverage         | `0355c37cace8ae69094a5bfbbe4ea5ac14c52b2a5f3f9f6b2300858dfe206c46` |
| `evidence/firmware-audit/20260919-inv-token-consumers/caller-matrix.md`            | retained caller boundary | `a2a01c92c737e4b6495aa468ac53cfc5fdebc4567f3466c19fe710d43e88f8e7` |

## Command and literal result

Command executed:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-clock-discriminating-test/uclk_consumer_trace.py > evidence/firmware-audit/20260921-clock-discriminating-test/test.stdout 2> evidence/firmware-audit/20260921-clock-discriminating-test/test.stderr
```

Exit status: `0`.

Literal stdout:

```json
{
  "status": "PASS",
  "checks": 22,
  "fresh_result": "For setup bytes 00/01/7f at +0x330, the immediate callback output record remains ID 0x1204 with value 00/01/7f respectively. The first static callback is an INV adapter (0x36c0->0x36f0), not a clock/register consumer."
}
```

Literal stderr: empty (`0` bytes).

The machine result is `evidence/firmware-audit/20260921-clock-discriminating-test/uclk-consumer-trace.json`, SHA-256 `bb9ed4ea7b21f9f86f4d2e757fb940a77ce545464da900a26815fdf007796910`; it records `22/22` checks passed.

## Observed byte-backed discriminator

The verifier checks the following exact path in `CbsBasePei`:

```text
CbsBasePei+0x9cc4  mov edx,0x1204
CbsBasePei+0x9ce4  mov al,BYTE PTR [edx+0x330]
CbsBasePei+0x9cea  mov BYTE PTR [ecx+0x3],al
CbsBasePei+0x36c0  callback adapter
CbsBasePei+0x36f0  serializer builds an INV record
CbsBasePei+0x47d..0x499  indirect callback dispatch
```

The host-side discrimination models three input bytes (`0x00`, `0x01`, `0x7f`) and observes the corresponding record values remain `0x00`, `0x01`, and `0x7f`, all under record ID `0x1204`. The checked serializer window contains no ratio arithmetic and no direct clock-register write. This is a static/dataflow observation about the exact PEI adapter, not an execution result.

## Decision-tree effect

- **Closed at this boundary:** `Enabled=1` is not itself a decoded `/1` ratio or synchronism selector. Do not build a `1:1:1` candidate from this enum label alone.
- **Still open:** final `$INV` `0x1204` consumer, UCLK divider/crossing semantics, relation to `MemoryPstate`, FCLK conditions, DF request `+0x704=1420`, units/rate conversion, training behavior, and whether any value is applied to hardware.
- **Not tested by this single discriminator:** `MemoryPstate=Disabled`, `FCLK_DPM`, DF `1420`, physical MCLK/UCLK/FCLK, latency, stability, voltage, firmware acceptance.

The retained census boundary leaves computed/indirect targets, dynamic HOB/DMA paths, closed PSP/ABL/SMU consumers, and runtime behavior unresolved. Therefore the result is **not** a claim that `0x1204` is unused; it is a precise first-boundary finding.

## Next gate

Offline work must next identify the final consumer/actuator for record `0x1204` and connect it to a UMC/DF divider or synchronous-crossing selector before generating a synchronization candidate. If offline analysis cannot recover that edge, the hardware gate is a read-only, one-variable native-menu experiment on the authorized BC-250: capture exact board identity and full recovery dump/readback first; record current `AmdSetup+0x330` and coupled fields; toggle only `UclkDiv1M0` between its native enum values; save/reset; verify byte readback; perform repeated cold boots with the same `MemoryClockSpeed=1800` request, `MemoryPstate`, `FCLK_DPM`, DF control/value and voltage unchanged; and independently measure MCLK, UCLK and FCLK plus any divider/crossing status. Equal aliased driver metrics are insufficient. No flash, voltage change, or multi-field profile is authorized by this result.

## Evidence classification and checks

- **PASS:** exact donor hash and size; exact `CbsBasePei` body; retained census/coverage inputs; byte-backed Uclk serializer path; input-byte preservation; callback adapter classification; literal stdout/stderr/exit capture.
- **INCONCLUSIVE:** final `$INV` consumer, divider/crossing semantics, MCLK/UCLK/FCLK units, Memory-P-state/FCLK/DF interaction, training, and hardware application.
- **UNRUN:** QEMU/emulation, firmware execution, board/menu action, NVRAM readback, physical clock measurement, voltage, latency, and stability.

Artifacts:

- Report: `docs/research/2026-09-21-clock-discriminating-test.md`
- Action log: `docs/action-logs/2026-09-21-clock-discriminating-test.md`
- Evidence directory: `evidence/firmware-audit/20260921-clock-discriminating-test/`
- Verifier copy: `uclk_consumer_trace.py`, SHA-256 `44de5d8c0dc9b715b7c785673e377daddadde8eb95ae674afe0a04b8c24c672d`
- Captures: `test.stdout` SHA-256 `a25c695f68e51a77b88322a980397c761d82daf800a689612ea42aeba729621e`; `test.stderr` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; `test.exit` contains `0`.

No ROM, candidate image, NVRAM, register, board, hardware or network write occurred.
