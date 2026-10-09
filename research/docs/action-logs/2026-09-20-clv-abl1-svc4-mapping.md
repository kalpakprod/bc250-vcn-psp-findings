# CLV ABL1 SVC#4 mapping review — intent

- Timestamp: 2026-09-20T00:00:00+06:00 (Asia/Almaty; exact wall clock to be appended in result)
- Actor: subagent `/root/svc4_mapping`
- Scope: exact CLV ABL1 SVC#4 call sites used by payload helpers `0x6DA4` and `0x6E70`; resolve service/address-space semantics from already imported exact bytes and version-aligned local ABL1 source, or record the closed boundary.
- Target inputs (read-only):
  - `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`
  - `import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c`
  - `import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_strings.txt`
  - `import/from-windows/Users/kukuruza/tmp_bc250/recon/robin5_psp_bodies/TOS_SECURITY_POLICY~0x45_B.51.1.16.body`
- ISA/base: exact ABL1 is Thumb-2 payload-relative under `$PS1` header `load_address=0`; no runtime physical base is assumed. Historical source offsets are structural leads only.
- Planned command: run an explicit-offset verifier that hashes all inputs, checks current SVC#4/#5 instruction bytes and surrounding address split/read/write operations, checks exact current `~SMN R/BW/W` strings, records historical source wrappers and TOS SVC-byte inventory, then emits a machine-readable result and report.
- Rationale: distinguish a descriptor-only field RMW from a mapped SMN/MMIO register access without firmware or hardware changes.
- Expected effect: create only new evidence/report/log files; no source, ROM, firmware, settings, memory, hardware, MCP/Cutter, installation, or global config writes.
- Rollback: remove only the new evidence directory and report; source inputs remain unchanged.

## Result

- Timestamp: 2026-09-20T12:17:57+05:00 (Asia/Almaty)
- Command (first attempt):
  `python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verify_svc4_mapping.py > evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stdout 2> evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stderr`
  failed with exit `1` on an endianness expectation at `ABL raw 0x6DCE` (`got c6f30b04`, `expected c6f3040b`). The command was corrected to use the exact little-endian file bytes and rerun; no input changed.
- Command (successful rerun): same command after correcting only the expected raw-byte literal at `0x6DCE`; observed exit `0`, stdout JSON status `PASS`, `checks=59`; stderr is empty.
- Observed result: exact current CLV ABL1 bytes show both helpers split an encoded address into high `(R1 >> 12) << 12` and low `R1 & 0xFFF`, invoke `SVC #4`, use the returned `R0` as a mapped base, access `mapped+offset`, then invoke `SVC #5` with that base. Current raw strings are `~SMN R`, `~SMN BW`, and `~SMN W`; version-aligned local source has the same `FUN_00006EA4/FUN_00006F70` wrappers with `software_interrupt(4/5)`.
- Claim boundary: SVC#4 is resolved at the caller-contract level as an SMN-page mapping service returning a PSP-accessible window base; SVC#5 is paired cleanup/release by call shape. The on-die SVC handler/translation table, destination physical window, runtime descriptor value, active callback identity, physical register, MMIO/PLL effect, and MCLK/UCLK/FCLK relation remain unavailable/unproven. TOS type-0x45 body is hash-pinned and contains no `DF 04` SVC#4 instruction; it does not supply the missing handler.
- Evidence paths and hashes:
  - verifier: `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verify_svc4_mapping.py` SHA-256 `f6973f508c66ffdd1c0c534b1be898a6302a56749cf48a3d394f93deb5003da7`
  - stdout/result: `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stdout` and `svc4-mapping-result.json`, both SHA-256 `4b9fa6b22d418ee31f284025d2d5f84931e56d222a32e37cfd5d69e08ac39cf0`
  - stderr: `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stderr`, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  - report (to be appended below) and this log are the only new project records.
- Readback: all source-input hashes and the new evidence hashes were recomputed above; no firmware, ROM, hardware, settings, global config, MCP/Cutter, or installation state changed.
- Rollback: delete only `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/` and this report; preserve all original inputs.
- Remaining uncertainty: exact on-die PSP ROM SVC#4 handler and translation table are not represented in the local BIOS/TOS policy images. A ROM-level disassembly or runtime trace would be required to name the physical map/window.
- Report: `docs/research/20260920-clv-abl1-svc4-mapping.md`, SHA-256 `2f04fcaa6da4867dd6322789d3d76a81f90c146d49004646213d9cae2d44c621`.
