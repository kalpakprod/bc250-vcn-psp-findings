# Exact CLV PSP/ABL payload provenance and phase-2 checkpoint review

## Conclusion

The pinned CLV image contains five exact bootloader payload IDs, `ABL0` through `ABL4`, as PSP types `0x30..0x34`. All five are `$PS1` containers at exact SPI offsets, version `22.4.6.0`, compressed (`compressed=1`, `encrypted=0`), signed with the same ABL key ID `663ca5220aad4b569fc565d36e2e4ed7`, and statically classified as 32-bit ARM little-endian payloads with ARM-state entry stubs and Thumb `BX LR` markers. Each CLV container is byte-identical to the preserved Robin-5 `22.4.6.0` container of the same ID.

The historical ABL1/ABL3/ABL4 decompilations are version-label aligned (`d00_e09/e11/e12 ... 22.4.6.0`) and are useful provenance leads, but source-text-to-current-binary identity is **UNPROVEN**: no source-file-to-binary hash or original `d00_e*` binary link is present. The existing 233-module x86 PE32/TE census therefore does not cover these non-x86 PSP/ABL payloads or prove the memory-training consumer.

## Exact input and parser evidence

- Input: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16777216` bytes
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `$PSP` directory: SPI `0x8E0000`, 19 entries, Fletcher32 PASS in the existing `scripts/firmware_audit.py` report.
- Existing signature output: `evidence/firmware-audit/20260920-clv-sync-stage1/psp-verify/BC250_5.00_clv.bin.stdout`; all five ABL entries report `PASS PSS/SHA256/s32`, key prefix `663ca5220aad4b56`.
- Fresh machine inventory: `evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json`.

## Exact ABL inventory

All hashes below are observed from the pinned CLV bytes. `signed_body_sha256` hashes the compressed `$PS1` signed body (`blob[0x100:0x100+signed_length]`); `decompressed_payload_sha256` hashes the zlib-decoded payload.

| ID / PSP type | SPI offset |   Container size | Container SHA-256                                                  | Signed / zlib / uncompressed | Decompressed payload SHA-256                                       | ISA evidence                                  |
| ------------- | ---------: | ---------------: | ------------------------------------------------------------------ | ---------------------------: | ------------------------------------------------------------------ | --------------------------------------------- |
| ABL0 / `0x30` | `0x99F700` |   `0x520` (1312) | `0859507cd52585ff1139498236d3ec5a73185c90fbc6a6324b50ea60b99824bb` |           `800 / 791 / 7952` | `3405551617c13dc7b1db464edd74e0f7a4240a80b37ed068c7650ccfe2d19e29` | ARM entry `18d09fe5...`; Thumb `7047` markers |
| ABL1 / `0x31` | `0x99FD00` | `0xC020` (49184) | `95ae7826a69ea56b8c52ac703b85f181d45bdc309de334c2b7f9f4130376d515` |      `48672 / 48672 / 94624` | `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` | ARM entry `10402de9...`; Thumb `7047` markers |
| ABL2 / `0x32` | `0x9ABE00` | `0x40C0` (16576) | `e8e90a60d473291ba35e7349a66b7eb7793092ffb033db282ba42171747af3ed` |      `16064 / 16059 / 30336` | `6fcae35368554127c48863169e660c27e19d9fb705871d918dbbbf933c3fbd32` | ARM entry `10402de9...`; Thumb `7047` markers |
| ABL3 / `0x33` | `0x9AFF00` | `0xA2A0` (41632) | `d22643385895c0482b2fd0cdd3cd14db291443c9416d18588dd15506b88c1f39` |      `41120 / 41112 / 85200` | `3f5890b3a830725a11e169861fcfa208fa3f5fab37a38fc7f994a221a1f213be` | ARM entry `10402de9...`; Thumb `7047` markers |
| ABL4 / `0x34` | `0x9BA200` | `0xA1D0` (41424) | `3398a5d859967197ceb871a6c8bd0ec8451e6d73650cf38d9cb59d3f9b1b4c82` |      `40912 / 40900 / 92096` | `1d60a34f1641204423024857249781d9184b2c9c5342f4dd8dbc070df6c5150b` | ARM entry `10402de9...`; Thumb `7047` markers |

Common exact fields for all five: `$PS1`, version `22.4.6.0`, `load_address=0`, `encrypted=0`, `compressed=1`, signature tail length `0x100`, key ID `663ca5220aad4b569fc565d36e2e4ed7`. Existing `psp_ps1_verify.py` independently reports all five signature checks PASS.

## Historical source provenance and limits

- Exact full-container equality was independently checked for all five pairs against:
  - `archives/imported/recon-evidence/legacy-tmp-bc250-recon/robin5_sec_gasket/ABL0~0x30_22.4.6.0`
  - `.../ABL1~0x31_22.4.6.0`
  - `.../ABL2~0x32_22.4.6.0`
  - `.../ABL3~0x33_22.4.6.0`
  - `.../ABL4~0x34_22.4.6.0`
- The corresponding preserved `robin5_psp_bodies/*.body` files are also byte-equal to `clv_blob[0x100:]` (compressed signed body plus signature tail), not merely equal by filename or version.
- Version-aligned historical decompilation sources:
  - `recon/lorek123_psp/ABL1_decompiled.c`, SHA-256 `9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b`, header `d00_e09_ABL1~0x31_22.4.6.0`.
  - `recon/lorek123_psp/ABL3_decompiled.c`, SHA-256 `ecd1bfb8be3fe15257038c4db6fd927ab72ca97a920a4639ad10cece04d3e22f`, header `d00_e11_ABL3~0x33_22.4.6.0`.
  - `recon/lorek123_psp/ABL4_decompiled.c`, SHA-256 `0fcffa6fa8501e6186b74ade298b0e51f0d8e3268101c68ebd07e27b5fcff566`, header `d00_e12_ABL4~0x34_22.4.6.0`.
- No scoped decompiled source is present for ABL0 or ABL2. The decompiled ABL1/3/4 text contains memory/APOB/AGESA strings and control-flow leads, but it is historical/static source evidence only. It does not prove that a particular function is the current binary's training actuator.

## Independent review of phase-2 artifacts

### CBS PPI lifecycle

Reopened `docs/research/20260920-clv-sync-stage2-cbs-ppi-lifecycle.md` and its result: `26/26 PASS`, CLV hash and exact `CbsBasePei`/Gfx/SMU hashes. Direct bytes establish `InstallPpi` at PEI service slot `+0x18`, `NotifyPpi` at `+0x24`, CBS GUID `04126c85-5c4e-458f-abc1-29f1f7da365e`, Notify GUID `60db76a0-5d55-47bb-970f-34d8d0be369e`, and the method indirect callback window `0x47D..0x499`. This is static registration/dispatch ownership, not runtime PPI invocation.

**Correction:** the worker report/result says “token `0x1332` consumer” in its final qualification. The final contiguous serializer evidence in both `CbsBasePei` and `AmdNbioSmuV10Pei` directly checks `mov edx,0x1331` immediately before the `+0x6A3` load/store; `0x1332` is the following `+0x6A4` record. The lifecycle report must use FCLK token `0x1331`, not `0x1332`.

### MemoryClockSpeed and PEI services

Reopened `memclk-consumer-result.json` (`12/12 PASS`) and `mem-init-controlflow-result.json` (`27/27 PASS`). Direct serializer bytes are:

```text
CbsBasePei 0x9837: baed110000  -> record 0x11ED
CbsBasePei 0x9857: 8a8216030000 -> [Setup+0x316]
CbsBasePei 0x985D: 884103 -> record value store
```

The selected native module no-hit result is bounded: it does not prove the field is ignored and does not identify an MHz range, training action, or physical clock.

The updated PEI-service interpretation is **double-pointer correct** at the byte level. `AmdMemAm4Pei` receives the second PEIM entry argument via `mov eax,[esp+8]`, retains it in `ESI` (`0x30F: 8BF0`), dereferences it (`0x311: 8B06`) to obtain the actual service table, and calls:

- `0x316: call [eax+0x4C]` (`AllocatePool`), repeated at `0x3AA`;
- `0x3E5: call [eax+0x18]` (`InstallPpi`).

No `[table+0x44]` (`InstallPeiMemory`) call appears in this bounded entry path. Therefore this evidence supports a PPI/data-handoff wrapper and not a direct training engine. It does not prove what the opaque service/AGESA/PSP/APOB consumer does with the handoff.

### CBS selection, caller, and pointer qualification

The dispatch-selection and caller-chain artifacts both reopen PASS (`21/21` each), but the following qualification is required:

- The static wildcard/event descriptor data and indirect callback bytes establish a **conditional static selection path** for CPU wildcard `0xFFFFFFFF` and event `0xFFFFFFFE`; they do not prove that firmware runtime reaches it.
- The Fabric bytes directly show the first `0x3710` request passing a NULL buffer and a size pointer (`0x1D68..0x1D72`), then a second `0x3710` request passing the local pointer `[ebp-0x17]` (`0x1DC5..0x1DCC`). The same local pointer is loaded at `0x1DF9` and read for the `$INV` header at `0x1DFC`. This proves local pointer identity from the second request to first-reader use.
- The first request is a size pass and cannot be described as filling a buffer. The exact `HOB+0x28` offset is not independently established by the bounded helper decode; retain only “allocation-returned/local pointer” unless a HOB layout edge is recovered.
- The worker verifier contains self-comparison checks for two gateway windows and a callback-pointer check. The independent direct-byte checks in `evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2-checkpoint-review-result.json` are the evidence for this qualification, not the self-comparisons.

## Coverage gap and next decisive edge

The existing 233-module census is an x86 PE32/TE UEFI-module census. It is not a census of PSP type `0x01/0x02`, ABL0-ABL4, SMU, or other non-x86 payloads. The exact ABL inventory closes the payload ID/offset/container/hash/ISA question, but not memory-training semantics.

The next decisive offline edge is a byte-backed trace from the exact decompressed ABL/APOB handoff and/or the opaque `AmdMemAm4Pei` protocol/HOB consumer to a concrete memory divider/training field. Until that edge is recovered, do not call the native wrapper a training service, do not label a stored request synchronized, and do not infer hardware clock application.

## Reproduction and fresh evidence

```text
python3 evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv_psp_abl_inventory.py
python3 evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2_checkpoint_review.py
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs_ppi_lifecycle_verify.py
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-memclk-consumer/memclk_consumer_verify.py
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-memclk-consumer/mem_init_controlflow_verify.py
```

Fresh owned artifacts:

- `evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json`
- `evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2-checkpoint-review-result.json`
- `evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv_psp_abl_inventory.py`
- `evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2_checkpoint_review.py`
- `docs/action-logs/2026-09-20-clv-psp-abl-provenance.md`

No firmware, hardware, shared plan, shared memory, settings, globalconfig, or MCP configuration was modified.
