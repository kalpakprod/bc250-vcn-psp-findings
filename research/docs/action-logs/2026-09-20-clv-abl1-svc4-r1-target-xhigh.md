# CLV ABL1 SVC#4 R1 target construction — intent

- Timestamp: 2026-09-20T12:40:00+05:00 (Asia/Almaty; exact wall clock to be appended in result)
- Actor: subagent `/root/svc4_register_target`
- Scope: exact CLV ABL1 FCLK context callback dataflow from dispatcher token `0x61E` to the `R1` argument at helpers `0x6DA4`/`0x6E70`; recover one exact descriptor-field target or numeric target if the exact table path supplies it.
- Target inputs (read-only):
  - `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`
  - `import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c` (historical structural cross-check only)
  - existing SVC4/callback/context reports under `docs/research/20260920-clv-abl1-*`
- ISA/base: exact ABL1 is Thumb-2, payload-relative under `$PS1` header `load_address=0`; no physical runtime base is assumed. Existing conditional base `0x57100` is not used to promote physical addresses.
- Planned command: run a new bounded verifier that hashes exact payload/listing/source, asserts the FCLK dispatcher argument swap, callback table index `0x61E`, `R6=table[0x61E]`, descriptor-bit extraction, exact `R4` address construction branches, and helper callsite `R1=R4` at `0x6DA4`/`0x6E70`; inspect whether exact table initialization provides a numeric slot.
- Expected effect: create only this evidence directory, verifier, report, literal stdout/stderr, result JSON, manifest, and this append-only action log; no firmware/hardware/settings/shared plan/memory/MCP/Cutter/global configuration writes.
- Rollback: remove only `evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/`, this report, and this action log.

## Execution and result

- Timestamp: 2026-09-20T12:52:00+05:00 (Asia/Almaty; exact wall clock captured by shell execution)
- First verifier execution exited `1` on five checker-only expectation errors (Thumb little-endian byte-order transcriptions and two listing-address selections); exact input hashes were unchanged. The checker was corrected only: raw expected bytes at `0x9C00`/`0x9D70`, `ORR` listing sites `0x9C56`/`0x9CC0`, and raw `MOVW R1,#0x61E` encoding `40 f2 1e 61` at `0x107E8`.
- Final command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verify_svc4_r1_target.py > evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verifier.stdout 2> evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verifier.stderr`
- Final observed result: exit `0`, stdout status `PASS`, `58/58` checks, stderr empty.
- Evidence hashes: verifier `0f535997b96061aec92e719633b6d3bfb8cbad91d27e0d6d0bd282c430da315e`; result `05fa26427c0d969a11d3779714089943d01421780beebbe8b62b910661eeecca`; stdout `4aed48b1cb889f0d367ca74790fdb204edfa446cef180b0f72a1e5fd6c8ea325`; stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Readback: exact payload/listing/source hashes remained `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`, `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`, and `9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b`.
- No firmware, ROM, hardware, settings, source inputs, shared plan/memory, MCP/Cutter, installation, global configuration, or commit changed.
- Rollback: remove only `evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/`, this report, and this action log.
