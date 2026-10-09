# SMU address trace — 2026-09-14, Asia/Almaty

## Intent

Root will inspect the preserved PMFW and reuse `recon/disasm_xtensa.py`
to trace Q3 handlers 0x2B/0x2C/0x98 and their address transforms. Outputs
will be retained in `evidence/firmware-audit/20260914-smu-address-trace/`.
No hardware access or firmware modifications are authorized by this entry.
The prior temporary pypcode environment is absent; restore the existing
analysis dependency in an isolated uv environment if needed. Preserve the
original ROM and record hashes, addressing assumptions and unresolved links.
Rollback: remove only newly generated analysis outputs if incorrect; retain
this journal and append corrections. No BIOS candidate is planned until the
actual destination of the write primitive is established.

## Static result

- PMFW source body: `import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body` (PMFW identity previously hardware-correlated; preserve source hash in existing audit).
- Q3 0x2B handler at `0x27D1C` and Q3 0x2C handler at `0x27D34` are distinct secure handlers in the table (`flags=0x201`). Q3 0x2B sets the SMN write address; Q3 0x2C performs the mem64 SMN write, matching the Python primitive.
- Q3 0x98 resolves to handler `0x280E0` with normal flags (`0x6`), not a secure SMN-write sibling. Its entry calls `0xFFC`, then branches on the result and updates a table via calls `0x2A74` and `0x29F8`; it contains no direct Q3 mailbox setup and no visible SMN address/value store in the decoded range. It is not a replacement for `smn_write32()` based on current evidence.
- The D19 disassembly confirms the C830 candidate uses the same documented pair: immediate address `0x0900C830`, value `0x00FFFFFB`, then Q3 `0x2B` and Q3 `0x2C`.

## Interpretation

- The transport hypothesis is resolved at the available source level: D19 did not accidentally use a different known transport from the replay. The remaining defect class is execution phase/state (ReadyToBoot versus the earlier successful runtime session), or an additional prerequisite performed by the runtime script before the write.
- No hardware command was run and no firmware was modified in this investigation.

## Unrun

- Caller-level decode for handler `0x280E0` helper calls `0xFFC`, `0x2A74`, `0x29F8`.
- Direct trace proving any historical gasket write used Q3 `0x98`.
- PEI candidate build or hardware test.
