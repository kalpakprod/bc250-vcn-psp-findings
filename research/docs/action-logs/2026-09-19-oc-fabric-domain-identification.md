# Fabric Domain Identification and SMU Rate Encoding Action Log

## Intent — 2026-09-19T23:55:00+05:00

Actor: code / RE agent.
Task: OFFLINE BC250 exact clock rate conversion helper decode and fabric domain provenance report. Root retains scope/integration/hardware decisions.
Model limitation: Configured default model family/model/effort requested, effective identity UNKNOWN unless runtime discloses; no effort override supported.
Permissions: local reads/existing tooling, new evidence/report/log writes only. NO hardware/network/flash/ROM/candidate/builder/probe edits.

## G7 Corrections Logged

- Acknowledged that prior audits hardcoded DF/UCLK identities without physical or firmware telemetry verification.
- Noted absence of promised report `docs/research/oc-fabric-domain-identification.md` from previous workers; created and verified it.
- Corrected verifier `verify-fabric-domains.py` so computed rates and hardware labels cannot masquerade as proven physical semantics.

## Hashes Verified

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, 16,777,216 bytes).
- SMU: `import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, 262,400 bytes).
- SMU body matches ROM offset `0x8FEF00` byte-for-byte.

## Execution & Findings

- Decompiled and disassembled helper `0x2360C` and related callees using Ghidra headless analyzer (`OcConsumerRead.java`), output archived in `evidence/firmware-audit/20260919-oc-clock-provenance/ghidra-2360c-decompiles.txt`.
- Derived exact rate encoding:
  - `0x2360C` converts U9.16 fixed point (`(param_1 & 0x1FF) + (param_1 >> 16) / 65536.0`) to float multiplier.
  - Multiplier times Clock Group `+0x10` (`0.1f`) yields VCO in GHz.
  - `0x1CAD8` translates post-divider DID codes to float divisor using standard AMD DFS formula.
  - Frequency is `VCO / DFS_DID`.
- Traced `0x1E448` argument mapping to actuators:
  - `0x23B7C` (Domain 0x0E): VCO mult `row[0]`, DID `row[1]`.
  - `0x23BA8` (Domains 0x0F & 0x11): VCO mult `row[8]`, DID `row[9]`.
  - `0x23BF4` (Domains 0x10 & 0x12): VCO mult `row[8]`, DID `row[11]`.
- Executed `verify-fabric-domains.py`, successfully validating arithmetic probe, boundary tests, and exact reproduction of all 5 P-state stored rates.
