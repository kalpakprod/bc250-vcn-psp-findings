# HackSkills application to BC-250 BIOS failure

## Analysis intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Trigger: D7 no-op BIOS does not initialize; operator requested applying the
  newly installed skills.
- Exact input: `/tmp/d3a_flash/pre_d3b2_retest.bin`, 16 MiB, SHA-256
  `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- RSA task: parse public RSA moduli from PSP `$KDB` types 0x50/0x51 and run
  bounded attack prerequisites from `rsa-attack-techniques`: duplicate/shared
  modulus checks, pairwise batch GCD, small-prime divisibility, bounded Fermat,
  and Wiener. No private data, oracle, fault injection, or online service.
- Deobfuscation task: treat the nested GUID/LZMA/FV layers separately and
  compare the original accepted compressed envelope against an unchanged
  decode/re-encode. Determine whether D5-D7 changed a wrapper property that
  the structural parser does not validate.
- Symbolic-execution decision: do not install/run angr unless a bounded branch
  condition inside an executable verifier is identified. On-die ROM is absent
  from the image, so whole-image symbolic execution currently has no valid
  target.
- VM decision: not applicable; no custom bytecode dispatcher is observed in
  the failing DXE capsule path.
- Expected result: either find a concrete weak RSA prerequisite, or close
  generic RSA attacks for these public keys; and identify whether the next
  BIOS must preserve the original LZMA stream/envelope instead of rebuilding.
- No firmware or hardware write is part of this action.

## Results (2026-09-12, Asia/Almaty)

### RSA attack-selection audit

- PASS: parsed 11 RSA-2048 public-key records (10 unique moduli) from the exact
  board baseline `$KDB` types 0x50/0x51; every exponent is 65537 and every
  observed modulus is 2048 bits.
- NEGATIVE: no pair shares a non-trivial factor; no factor at or below 100,000;
  no Wiener small-`d` solution; no Fermat factor within 1,000,000 increments.
- NOT APPLICABLE from available evidence: small-`e`, broadcast, common-modulus
  ciphertext, padding-oracle, CRT-fault, and partial-prime Coppersmith attacks.
- Evidence: `evidence/firmware-audit/kdb-rsa-weakness-audit.json`, SHA-256
  `e0fab0fd2fb8f0ddbc18240acd6ec78ee53053f6972a7c31670a963d77c0f479`;
  deterministic tool `scripts/kdb_rsa_weakness_audit.py`, SHA-256
  `4fd331ab410b885bfce79e1f6ca5d3e5f6f8a5dedc3f08079e48fd41305b9d85`.
- Conclusion: the installed RSA playbook produced no viable signing-key
  recovery vector for the board's own public artifacts. This is bounded
  negative evidence, not a proof that every implementation attack is absent.

### Layered LZMA/FV analysis

- FINDING: accepted baseline LZMA-alone header is
  `5d000000011000420000000000`: properties `lc=3/lp=0/pb=2`, dictionary
  16 MiB, and explicit uncompressed size `0x420010` (4,325,392), exactly
  matching the decoded stream.
- FINDING: D5, D6, and D7 all used header
  `5d00000001ffffffffffffffff`; Python's encoder emitted the unknown-size
  marker although the streams decode with the host parser.
- Eight bounded decode/re-encode trials of the unchanged baseline did not
  reproduce the vendor stream byte-for-byte and all emitted the unknown-size
  marker. Therefore host decompression success did not establish compatibility
  with the firmware's bounded LZMA decoder.
- Evidence: `evidence/firmware-audit/d5-d7-lzma-envelope-comparison.json`,
  SHA-256 `17eeb0c809e81d4bd5119687c94cc92d6fe6e84f0718b97f61403977e84d63fa`.
- Decision: D8 explicitly restores the accepted header's exact uncompressed
  size before any further unlock payload is tested.

### Skill applicability

- `code-obfuscation-deobfuscation`: applied as layered envelope/payload
  separation; it exposed the concrete LZMA header discrepancy.
- `rsa-attack-techniques`: applied; common weak-key prerequisites are negative.
- `symbolic-execution-tools`: routing applied, but execution deferred because
  the relevant PSP verifier is in unavailable on-die ROM and D7's current
  discriminator is a container-header question, not a symbolic branch.
- `vm-and-bytecode-reverse`: not applicable; no custom VM dispatcher is
  observed in the failing DXE capsule path.
