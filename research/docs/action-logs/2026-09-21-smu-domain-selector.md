# SMU Queue-3 domain selector — action log

## Intent (recorded before task evidence writes)

- Timestamp: 2026-09-21T15:19:00+05:00 (Asia/Almaty).
- Actor: `/root/smu_clock_entrypoints`.
- Target: immutable exact plain-CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, plus contained Robin-5 SMU body at ROM `0x8FEF00`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`.
- Preserved baseline: `AmdSetup+0x316`, ROM `0x7E5`, raw `0x24` (1800MHz label); no ROM, NVRAM, candidate, or hardware state may change.
- Question: the earlier Queue-3 verifier asserted high16 selector index `1..20` but did not check the instruction that loads its bound. Determine, from a fresh exact-address Ghidra listing and the target-array consumer, the accepted selector bound, one index-to-descriptor-to-SMN destination mapping, and the actual request scaling before `FUN_000235C8`. Then test whether local address-bearing sources name that hardware domain as MCLK/UCLK/FCLK or provide a physical MHz/rate conversion.
- Hypothesis H1: `FUN_0002EA08`'s selector bound is smaller than the 20-slot target array; if so, Queue-3 `0x1D` cannot be assumed to address all entries. H2: Group/domain and SMN address are statically derivable for an accepted index, while physical clock name remains absent in local evidence.
- G3 route: reuse Ghidra 12.1.3 `OcConsumerRead.java` and the already-proven `OCConsumer` program, but copy the ~1.1 MiB analysis project into this unique evidence directory first. Open only existing exact Robin-5, `-noanalysis`, and send a bounded address list including `0x2EA08`, `0x2E788`, `0x23890`, `0x235C8`, `0x23C78`, `0x23ECC`, and `0x3ACF8`. This avoids the previous misaligned 0x2EA0C entry listing; no new architecture decoder or board route.
- Procedure: run exact Ghidra disassembly/decompilation in the copied project; byte-check the affected windows against the pinned body; derive one selector index from high16 -> target slot -> consumer loop row -> `0xF7BC+domain*0x1C` program pointer -> `0x235C8` address formula. Perform a bounded local-source name search only for the calculated address/register range. Preserve literal command stdout/stderr/exit and manifest.
- Expected effect: PASS on the concrete index-to-register path, or a bounded unresolved result if Ghidra/bytes do not establish the edge or a name/unit is absent.
- Scope: offline only. No hardware/mailbox/register/NVRAM/network/install/ROM/firmware write, flash, or other worker artifact modification.
- Rollback: remove only the new report and `evidence/firmware-audit/20260921-smu-domain-selector/`; preserve donor, original Ghidra project, previous evidence and prior reports.

## Timestamp correction

The first intent heading transcribed `15:19:00+05:00`; the `date -Iseconds` command observed `2026-09-21T16:17:49+05:00` immediately before file creation. Treat `16:17:49+05:00` as the actual intent-record time; preserve the original transcription as a corrected log error.

## Corrective verifier rerun 1

The first bounded verifier run exited `1` after all preceding byte/selector assertions. Its final coverage threshold expected `>400` instruction records, but the requested exact Ghidra address list produced `301` listed instructions (`grep -c` on the listing). The mismatch is the verifier's over-large expected count; it says nothing about a firmware/input mismatch. Adjust the coverage assertion to `>250` and rerun the same pinned source test.

## Corrective verifier rerun 2

After the listing-count correction, the verifier reached the two-denied-ID status branch but had transcribed the call opcode at `0x2EA68` as `6557D2`; fresh Ghidra/raw bytes show `A5 57 D2` (`call8 0xFE4`). This is another verifier fixture typo, not a firmware contradiction. Preserve the actual byte decode and rerun with `A557D2`.

## Circuit-breaker method change (G6)

`verify_domain_selector.py` has now failed three assertion-style runs in this task: (1) its listing-count floor expected >400 when the bounded address set yielded 301; (2) an opcode byte was transcribed `6557D2` instead of observed `A557D2`; (3) an explanatory disassembly substring used uppercase addresses against lowercase Ghidra output. After this third same-class fixture/assertion failure, stop rerunning that verifier. The method changes to direct reading of the already-successful aligned Ghidra disassembly and raw pinned bytes, plus straightforward index/address arithmetic printed without another assertion harness. Preserve all three failures as verifier defects, not target failures. Ghidra itself exited 0 and identified the correct immediate `movi.n a12,0x14`.

## Final readback and artifact ledger (pending report write)

- Ghidra 12.1.3 exact copy run: exit `0`; aligned listing `q3-aligned-ghidra.txt` SHA-256 `6c6816365ce7b9febf374a092908f3b88033cb3c7a4b2111490c3d458b62af52`; loaded-memory PASS line and 301 byte-matched instructions retained.
- Direct selector measurement: `direct-selector-measurements.txt` SHA-256 `a50af42fce3ff8b6483b8a454c13b38595c1553dab524f415744569c7db55361`, exit `0`, stderr empty.
- Scoped register-name search: zero exact address/header hits; `register-symbol-search.stdout` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, exit `1` (grep no-match, not a firmware error); selected recon address hits are retained separately.
- Original copied project readback matches all original project files; copied project Ghidra `.gpr` SHA-256 equals original empty `.gpr` hash `e3b0c442...`.
- Verifier attempts retained as fixture errors: count threshold `>400` vs 301 rows; opcode typo `6557D2` vs `A557D2`; final verifier stopped per G6 and direct arithmetic readback was used.

## Final result and artifact ledger

- Fresh Ghidra command: exit `0`; exact body equality line; 301 listed instructions byte-matched.
- Direct selector calculation: exit `0`, stderr empty; selector 11 -> target/read slot `0x140B0` -> domain `0x18` -> Group6 -> raw `0x6D150` -> SMU program/poll `0x0116D150/0x0116D174`.
- Rejected neighbors: selector 12/domain `0x13`, selector 13/domain `0x14`; selector 14/domain `0x15` passes visible filters.
- Physical-name search: zero exact symbol/header hits; prior static slot map has `semantic_name=null`.
- Machine result: `evidence/firmware-audit/20260921-smu-domain-selector/domain-selector-result.json`, SHA-256 `97be0a4254c76123235dd23ea7dbf196b77e183c392083c91aaee42c832a0a38`.
- Final evidence manifest: `SHA256SUMS.final`, SHA-256 `00187c94e9008e1cd8f174e1167d71eb5f791cc30ce7b50688e15432f010a464`; all listed files must return `OK`.
- Report final SHA-256: `7f55b352b3d28553a04ed6de777bb6d463da399036588e9628847425f163044f`.
- First unresolved edge: physical identity/unit/runtime Group6 coefficient and caller/provider join; no hardware/mailbox/register action.
