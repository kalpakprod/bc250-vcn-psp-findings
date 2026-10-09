# ABL1 FCLK provider-context join — 2026-09-21

## Intent (before artifact creation)

- Timestamp: 2026-09-21 (Asia/Almaty); actor: bounded DF consumer trace worker.
- Target: exact CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, 16 MiB; exact decompressed ABL1 and existing exact ELF object are read-only.
- Existing evidence reused without repeating serialization scans: `20260920-clv-abl1-apcb-reader-boundary-resume` (reader 0x1FB4), `20260920-clv-abl1-apcb-consumer-resume` (0x4800 -> 0x49CC), `20260920-clv-abl1-descriptor-provider-xhigh` (ordered FCLK tokens), and `20260920-clv-abl1-reader-output-context-xhigh` (outer output/context path).
- Bounded question: follow one new dataflow edge from direct caller `0x5FAE` (`R1=0x0F`, output local `SP+0x04`) through FCLK `0x463C`, reader `0x1FB4`, helper `0x4800`, and provider `0x49CC`; prove whether the FCLK selector is also the provider-context argument, and identify the output/context boundary. Do not repeat prior token-array or serializer checks.
- Expected effect: one byte-backed caller/provider edge or a concrete tool/architecture failure. The edge must be kept separate from `$INV 0x1373/0x1374`; no immediate-token absence claim is used as the result.
- Prohibited: no hardware, ROM/NVRAM/register/MMIO/network/install/flash/candidate/source/shared-memory changes.
- Rollback: remove only the uniquely named evidence directory, report, and action log.

## Result

Pending exact-target disassembly and verifier execution.

## Corrective verification attempt (before rerun)

The first exact-byte verifier run exited `1` after 5 checks because the expected raw bytes for Thumb instruction display `f240 40b0` were entered in display-byte order (`f2 40 40 b0`) instead of ELF raw little-endian halfwords (`40 f2 b0 40`). Captured direct disassembly confirms `0x5FA4` is `movw r0,#0x4B0`; correct only the expected raw-byte string and rerun the same bounded verifier. No source/pinned input changed.

## Second verifier error and method pivot (before rerun)

After the first correction, the verifier exited `1` at its next hand-entered Thumb byte expectation (`0x5FA8` raw `01 90`, not the typed display order `90 01`). This is the same test-oracle endianness error class. To avoid a third attempt of that class, stop maintaining per-instruction raw hex manually: use fresh exact `llvm-objdump` windows, parse each Thumb halfword in display order back to target little-endian bytes, compare every decoded instruction in each window against the pinned ABL1 payload, and assert address/operand text only after that byte reconciliation. This method pivot changes verification class within the static route; no input is changed.

## Observed result (after execution)

- Target identity: PASS; ROM size `16777216`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact verifier: `python3 -B evidence/firmware-audit/20260921-abl1-df-key-join/verify_abl1_df_key_join.py`.
- Final literal stdout: `{"status":"PASS","checks_passed":66,"checks_failed":0,"new_edge":"caller 0x5FAE R1=0x0F -> reader 0x1FB4 -> helper 0x4800 R2=0x0F -> provider case 0x0F -> fixed HEAP key 0xA04E; APCB literal correspondence 0x1707 observed","first_unresolved":"HEAP 0xA04E producer and INV 0x1373/0x1374 bridge"}`.
- Final exit `0`; stderr empty; evidence manifest check `21/21 OK`.
- New result: caller `0x5FAE` selector `R1=0x0F` -> reader `0x1FB4` preserves `R1` -> helper `0x4800` forwards selector as provider `R2=0x0F` and current candidate token as provider `R1` -> provider selector case `0x0F` selects fixed literal `0x1707` and HEAP key `0xA04E` -> `0x6374` key lookup -> typed output path.
- Caller output edge: local default `0x4B0` at `0x5FA4`, passed by `R0=SP+0x4` at `0x5FAC`, call `0x5FAE`, reloaded at `0x5FB2`, stored to `[context+0x78]` at `0x5FBA`; context `R5` derives from caller `R0` at `0x5E70`.
- APCB numeric correspondence: exact parser reports CBSG gid `0x1707`; subgroup instance 15 body offset `0x160` is `{u8_0:1,u8_1:189,u16_le:96}`. This is not a schema/runtime join.
- First unresolved boundary: HEAP node `0xA04E` producer/populator and any bridge from native `$INV` `0x1373/0x1374`; no units/frequency/divider/PLL/hardware result.
- Previous verifier attempts retained: first exit `1` at `0x5FA4` due typed raw-vs-display Thumb expectation; second exit `1` at `0x5FA8` for same class. Method then pivoted to display-order LLVM parsing plus raw-byte reconciliation; final run passed `66/66`.
- Artifacts: report `docs/research/2026-09-21-abl1-df-key-join.md`; evidence `evidence/firmware-audit/20260921-abl1-df-key-join/`.
- Verifier SHA-256: `8fc5db7619ae846b496b5de5dd5776aa8b2096f5b97707e5aee0b652775888fb`.
- Result SHA-256: `d17e603a1c8c4cb40b814d1ed2a9ead911c5f912c9907adf9416e6715f1a49b2`.
- `VERIFICATION.txt` SHA-256: `e5c2963c396ee716b19873861a963be22fbedc396f31fe0834d822ff9aa49d01`.
- `SHA256SUMS.final` SHA-256: `7039aaab430fcd93e368e5a2aef9afd0aed95d71eef42cd08734ae942a7978dd`.
- No firmware, ROM, NVRAM, register, hardware, network, installation or candidate write occurred.
