# BC-250 Worker-1 Stock vs Policy-Only Diff, CoreUnlock, and AMDGPU Paths

## H1-Hn Hypotheses

- **H1**: The policy-only VCN candidate (`candidates/BC250_VCN_policy_only_v001_from_read-a.bin`) differs from stock (`evidence/programmer/reads/20260911/read-a.bin`) *only* in the PSP directory pointer region (`0x8E0000..0x8E010B`) and the relocated policy carriers at `0x9E0000` (`$PS1` SEC_GASKET) and `0x9E4000` (TOS policy), while maintaining complete byte-for-byte APCB identity (`0xAB1000..0xAB1B6F`).
- **H2**: `Bc250CoreUnlockDxe` (GUID `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, body SHA-256 `7d22d80284cd4c9c8af997611002f6916b4fa4b0d3ca9e3e34e450abbe885c55`) interacts with hardware by reading SMN register `0x0115A870` (core mask), evaluating a Setup HII variable guard (`Setup+0x1C4` compared against `0x000157C0`), conditionally issuing SMU Queue-3 mailbox message `0x98` (`0x03B10A20`), verifying response status `0x01`, and requesting a UEFI runtime warm reset.
- **H3**: Enabling AMDGPU VCN on Linux requires hardware detection via the IPDS discovery descriptor (HWID 12, version `2.0.3`, bases `0x7800`, `0x7E00`, `0x02403000`), successful PSP/PMFW initialization of power/clock gating, NBIF aperture mapping (`SEC_GASKET`), and valid `amdgpu` kernel driver firmware loading for `vcn_dec` and `vcn_enc`.
- **H4**: Rival explanation A for persistent no-video output under stock APCB and modified policy: the closed PSP root of trust validates signed blob structures during boot; relocated or modified `$PS1` / TOS policy carriers have invalid or mismatched signatures, causing the PSP to silently halt or reject the policy blob, preventing UEFI display console initialization.
- **H5**: Rival explanation B for persistent no-video output: the IP discovery descriptor and VCN registers (`0x7800`/`0x7E00`) are present in the SPI ROM, but host Linux kernel `amdgpu` fails during ring initialization (timeout `-110`) because the PMFW (PSP type-0x08 SMU binary) does not enable the VCN power domain without matching silicon fuse settings or runtime SMU mailbox handshakes.

## E1-En Evidence

- **E1**: Stock read baseline: `evidence/programmer/reads/20260911/read-a.bin` (16 MiB, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, verified by two independent CH347T flashrom reads).
- **E2**: Policy-only candidate: `candidates/BC250_VCN_policy_only_v001_from_read-a.bin` (16 MiB, SHA-256 `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1`).
- **E3**: Changed range audit command and output:
  - Command: `python3 scripts/firmware_audit.py --output evidence/firmware-audit/policy-only-audit.json evidence/programmer/reads/20260911/read-a.bin candidates/BC250_VCN_policy_only_v001_from_read-a.bin`
  - Result: Confirms 329 exact changed ranges exclusively in PSP directory (`0x8E0004..0x8E010B`) and policy carriers (`0x9E0000..0x9E3010`, `0x9E4000..0x9E4708`). APCB region (`0xAB1000..0xAB1B6F`) has zero differences (`delta = []`).
- **E4**: APCB detail comparison command and output:
  - Command: `python3 scripts/apcb_detail.py --output evidence/firmware-audit/apcb-policy-only-detail.json evidence/programmer/reads/20260911/read-a.bin candidates/BC250_VCN_policy_only_v001_from_read-a.bin`
  - Result: Confirms stock APCB checksum `0xF2`, instance stamps, DFG wildcard words (`0x001FFF00`), and all subgroup body hashes are identical.
- **E5**: CoreUnlock binary analysis:
  - Module path: `evidence/firmware-audit/dump-2-extract/modules/0000_Bc250CoreUnlockDxe_pe32.bin` (GUID `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, size 12,288 bytes, body SHA-256 `7d22d80284cd4c9c8af997611002f6916b4fa4b0d3ca9e3e34e450abbe885c55`).
  - Disassembly reports: `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.llvm-objdump.txt` and `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.functions.txt`.
- **E6**: VCN IP discovery descriptor:
  - Location: Flash offset `0x981A00`.
  - Content: 1 die, 38 IP records; VCN record HWID 12, version `2.0.3`, harvest `0`, MMIO bases `0x7800`, `0x7E00`, `0x02403000`.

## Q1-Qn Quirks

- **Q1**: Rizin analysis of PE32/TE binaries reports `endian=BE` on certain little-endian TE modules due to parser heuristics; instruction semantic verification required `llvm-objdump -d --x86-asm-syntax=intel`.
- **Q2**: `Bc250CoreUnlockDxe` contains an additional Setup variable HII guard (`Setup+0x1C4` compared to `0x000157C0` / 88000) that is absent from the retained C source (`import/.../Bc250CoreUnlockDxe.c`), proving partial semantic divergence and necessitating binary-level analysis.
- **Q3**: APCB checksum byte is located at offset `+0x10` from the start of the APCB block (`0xAB1010`), not `+0x0C` as claimed in legacy documentation.
- **Q4**: Historical Linux driver probes (`import/.../vcn-probe-mode1_2026-08-26.out`) showed VCN ring initialization attempts timing out with `-110`, indicating that hardware discovery descriptors alone are insufficient to bring up ring processing without PMFW and aperture support.

## V1-Vn Verdicts

- **V1**: **VERIFIED (Static & SPI Readback)**: The policy-only candidate (`8cd9d199...`) matches stock across all 16 MiB except the PSP directory pointer table and the relocated `$PS1` / TOS policy carriers (`0x9E0000`/`0x9E4000`). APCB is 100% stock-identical.
- **V2**: **VERIFIED (Static Analysis)**: `Bc250CoreUnlockDxe` targets SMN core-mask register `0x0115A870`, evaluates a Setup HII variable guard, sends SMU Queue-3 message `0x98`, verifies response `0x01`, and triggers a warm reset. Hardware execution in this session remains unrun.
- **V3**: **INCONCLUSIVE (Hardware Execution / Video Output)**: Flashing policy-only or APCB-modified candidates results in identical hardware symptoms (fans spin, status indicators light up, but no video display output). Neither signature acceptance nor VCN codec operation is proven on physical hardware yet.

## R1-Rn Reuse

- **R1**: `scripts/firmware_audit.py` for read-only PSP/BHD/APCB structural inventory and FV/FFS extraction.
- **R2**: `scripts/apcb_detail.py` for token-level APCB group and DFG verification.
- **R3**: Pinned `flashrom v1.8.0` with `ch347_spi` backend for read-only JEDEC detection and verified readback checks.
- **R4**: Rizin and `llvm-objdump` analysis reports under `evidence/firmware-audit/rizin/` for UEFI DXE driver verification.
