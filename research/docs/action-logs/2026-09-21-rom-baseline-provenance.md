# 2026-09-21 ROM baseline provenance ledger

## Intent

- Timestamp: 2026-09-21T03:18:56+05:00 (Asia/Almaty; host-clock observation before the read-only checks).
- Actor: delegated project executor (Luna xhigh; root-owned integration).
- Scope: read-only audit of actual BC-250 programmer captures/readbacks and comparison to the local RetroWeb BC-250 5.00_clv donor; no board access, programmer transaction, firmware write, NVRAM/register change, or hardware action.
- Target artifacts: `dump/2.bin`; `evidence/programmer/reads/20260911/read-a.bin`/`read-b.bin`; `evidence/programmer/reads/20260914-identification/read-a.bin`/`read-b.bin`; `evidence/programmer/reads/20260916/pre-m0-read-a.bin`/`pre-m0-read-b.bin`; latest recorded postwrite capture `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin`; comparison candidate `candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin`; donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`.
- Existing route: reuse `scripts/firmware_audit.py`, the 2026-09-19 root-verified identity report, and existing programmer logs/manifests; do not inventory/hash the entire imported corpus or create a duplicate parser.
- Expected effect: one factual ledger separating donor ROM, dated board readbacks, last confirmed chip contents, and unknown current physical state. Verify only decisive files by size/hash/cmp and existing structured evidence.
- Rollback: report and this action log are the only planned repository writes; remove only these new files if a material provenance error is found. All source ROMs and prior logs remain immutable.
- Safety: no secrets, raw security material, or credentials accessed/copied. No external or board operation.

## Correction to intent timestamp

The draft intent header's `18:00:00+06:00` was a placeholder entered in error; it was not the execution time. `date '+%Y-%m-%dT%H:%M:%S%:z %Z'` observed `2026-09-21T03:18:56+05:00 +05` in the execution environment, so the task is dated 2026-09-21 Asia/Almaty (+05:00). All later result timestamps will be taken from the host clock, not estimated.

## Observed result

- `sha256sum` and `stat` were executed on the decisive primary files only. Every listed image is 16,777,216 bytes.
- Reproduced hashes:
  - original pair / dump: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`;
  - 2026-09-14 pair: `c0f5f1c59cd0503d99cec9fffc5b95c8897a2deabfa42dd389c924d6be6cc4de`;
  - 2026-09-16 pre-M0 pair: `3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd`;
  - 2026-09-16 post-M6: `3e75177e96e21a8a25814a0d16613453662d497ca88afbcb9a0c92e43da6868b`;
  - 2026-09-18 W9 readback: `449475563a332a67a594d794cb2e2fbe4d251e0660b65742660b1ff1ce8463fb`;
  - 2026-09-19 W11 readback and W9-labelled candidate: `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`;
  - RetroWeb `5.00_clv` donor: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- `cmp` observed exit `0` for dump/read-a/read-b, both 2026-09-14 reads, both 2026-09-16 pre-M0 reads, and W11 readback versus the W9-labelled candidate. `cmp` observed exit `1` for 2026-09-18 W9 versus W11 and W11 versus pristine CLV.
- Existing `scripts/firmware_audit.py` was reused against five decisive images only. Exact command:
  `python3 scripts/firmware_audit.py --output /tmp/bc250-rom-ledger.k01Fx6.json dump/2.bin evidence/programmer/reads/20260914-identification/read-a.bin evidence/programmer/reads/20260916/pre-m0-read-a.bin evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  Observed stdout: `{"output": "/tmp/bc250-rom-ledger.k01Fx6.json", "images": 5, "extracted": 0}`; exit `0`; stderr empty. The temporary report hash was `1f0395f2e01bc7342e53cdf60a3f9566b0abe671628594570a3f5fca27897d60` before disposal.
- Parser summary for all five: 19 PSP entries/checksum PASS; 4 BHD entries/checksum PASS; four FVs. APCB/DGF details: original = 2,928 B, `0x001FFF00`; 2026-09-14 = 2,928 B, `0x007FFF00`; 2026-09-16 pre-M0 = 2,928 B, `0x007FFF00`; W11 = 2,972 B, `0x001FFF00`; CLV donor = 2,972 B, `0x001FFF00`. APCB checksums PASS in each parser result.
- Human ledger was written and reopened: `docs/research/2026-09-21-baseline-rom-ledger.md`, 9,776 bytes, SHA-256 `d047374261e923f60857aa6c344e8be613646decf652e02187cc7730beae39cc`.
- No board/programmer transaction, firmware/NVRAM/register write, external search, or secret access occurred.

## Evidence classification and remaining uncertainty

- `observed-bytes`: all hashes, sizes, byte comparisons, parser output, and donor manifest metadata.
- `static-analysis` / `emulated-or-host-tested`: only the existing parser's structural interpretation; no runtime behavior inferred.
- `hardware-verified`: limited to SPI programmer readback identity for the dated captures, not current board state or boot behavior.
- Not proven: current chip contents after 2026-09-19, physical PCB revision/serial, memory training, MCLK:UCLK:FCLK ratio, SoC/CORE/GFX rail voltage, latency/bandwidth/performance, or stability.
- Next decisive identity check: a new operator-authorized read-only CH347T full-chip capture pair, with board identity/power state recorded, compared against the ledger. This task did not perform that operation.

## Execution corrections and provenance boundary

- Initial broad `sha256sum` invocation named `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w9-v001.bin`, which does not exist; the shell emitted `sha256sum: evidence/programmer/reads/20260919/postwrite-vcn-unlock-w9-v001.bin: No such file or directory`. The correct original W9 readback path is under `20260918`, and the later targeted command hashed that path and returned the exact hashes above. The initial wrapper call did not expose its nested exit-code field, so that failed invocation's numeric status is not claimed or used.
- A first parser-launch command was rejected before process start by `exec_command` because it included `rm -f` cleanup. The tool returned `Rejected: rm -f style commands are not permitted. Use a safer approach`; there was no parser process or process exit status. The changed command omitted cleanup, ran the five-image parser successfully, and left its temporary JSON under `/tmp` (not in the repository).
- A bounded filename inventory (`find evidence docs/action-logs docs/research -type f -iname '*w11*'`) found only the W11 readback binary. No separate W11-named raw flashrom log/manifest was located. Thus this report freshly verifies the preserved bytes and candidate match; exact Sep-19 programmer stdout is not represented as newly observed.
