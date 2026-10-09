# BC-250 candidate catalog

All files in this directory are **offline candidates**, not release images and not authorization to flash. The matching source baseline is preserved under `evidence/programmer/reads/20260911/` and has SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.

## Current candidates

| Candidate | SHA-256 | Track | Static status | Hardware status |
|---|---|---|---|---|
| `BC250_APCB_DFG_only_v001_from_read-a.bin` | `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70` | VCN/APCB DFG hypothesis | Byte/parser/checksum verified; independent review PASS | SPI write/readback PASS; first boot produced no display, boot stage inconclusive |
| `BC250_MemoryClock_1750_only_v001_from_read-a.bin` | `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee` | Memory clock only | Byte/NVAR/parser/checksum verified; independent review PASS | Not tested; no approval |
| `BC250_VCN_D3B2_combined_v001_from_read-a.bin` | `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d` | Combined APCB + SEC_GASKET + TOS policy | Root checks 25/25 PASS; independent review APPROVE_FOR_HARDWARE_TRIAL | SPI write/readback PASS; first boot produced no display, boot stage inconclusive |
| `BC250_VCN_policy_only_v001_from_read-a.bin` | `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1` | SEC_GASKET + TOS policy, stock APCB | Root checks 26/26 PASS; independent review APPROVE_FOR_HARDWARE_TRIAL | Not tested; exact approval pending; signature acceptance unknown |

## VCN candidate

`BC250_APCB_DFG_only_v001_from_read-a.bin` changes only:

- APCB absolute `0xAB1010`: checksum `F2 -> 32`;
- APCB absolute `0xAB1132`: DFG byte `1F -> 7F`;
- APCB absolute `0xAB116E`: DFG byte `1F -> 7F`.

The corresponding DFG words change from `0x001FFF00` to `0x007FFF00`. PSP, `$PS1`, BHD, FV/FFS, NVRAM, and all other bytes are unchanged. This is a static policy hypothesis. It does not prove PSP acceptance or VCN runtime behavior.

Manifest and reports:

- `evidence/candidates/BC250_APCB_DFG_only_v001/build-manifest.json`
- `evidence/candidates/BC250_APCB_DFG_only_v001/apcb-detail.json`
- `evidence/candidates/BC250_APCB_DFG_only_v001/firmware-audit.json`
- `evidence/candidates/BC250_APCB_DFG_only_v001/independent-review-gemini.md` (review PASS; SHA-256 `90e15006a3093c8ba484fa702d4dab12225d522878892e6bba01d39666db7905`)

## Memory candidate

`BC250_MemoryClock_1750_only_v001_from_read-a.bin` changes only `AmdSetup+0x316` at absolute `0x7E5`, from `0xFF` (Auto) to `0x23` (the IFR-labelled 1750 MHz option). It intentionally does not change UCLK, FCLK, DF override, voltage, timings, power limits, APCB, PSP, `$PS1`, BHD, or FV/FFS.

This is a one-field memory-clock hypothesis. Memory training, live clocks, stability, and bootability are unrun.

Manifest and reports:

- `evidence/candidates/BC250_MemoryClock_1750_only_v001/build-manifest.json`
- `evidence/candidates/BC250_MemoryClock_1750_only_v001/nvar-primary.json`
- `evidence/candidates/BC250_MemoryClock_1750_only_v001/firmware-audit.json`
- `evidence/candidates/BC250_MemoryClock_1750_only_v001/independent-review-gemini.md` (review PASS; SHA-256 `47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb`)

## SoC-voltage track

No SoC-voltage binary exists. `AmdSetup+0x6E5/+0x6E6` is identified as a separate control/u32 value pair, but the physical unit, sign/encoding, SMU consumer, allowed range, training dependency, and rail response are not proven. Do not insert historical `+35`, `+80`, or `+100` values.

## Hardware restrictions

Before any physical write, require a complete verified recovery method, independent review of the actual image and failure path, exact board/chip identity, and the explicit approval form:

`Подтверждаю запись файла <exact path> SHA-256: <exact hash> на плату <identifier>`

The APCB candidate was written to `BC250-01` after exact operator approval and independently read back byte-identical on 2026-09-11. On the first reported cold-boot attempt, board indicators illuminated but no display image appeared. This fails the user-visible video check but does not identify the execution stage or cause. Roll back to stock before further candidate testing. No register mutation or JTAG target-memory write has occurred.

Hardware-trial manifest: `evidence/programmer/reads/20260911/apcb-v001-hardware-trial-manifest.json`.

## Combined D3-B2 candidate

`BC250_VCN_D3B2_combined_v001_from_read-a.bin` is rebuilt from the verified current stock baseline rather than copied from the historical D3 package. It repoints PSP types `0x24` and `0x45` to modified copies at `0x9E0000` and `0x9E4000`, applies the donor-derived VCN policy values/tails in both carriers, and includes the APCB DFG change.

The modified payloads retain the old 0x100-byte signature tails. PSP acceptance is unknown and no valid-signature claim is made. Root verification passes 25/25 after closing the reviewer's signature-region coverage gap. Independent Claude Opus review recommends `APPROVE_FOR_HARDWARE_TRIAL`; a fresh current-chip capture and new exact operator approval remain mandatory before hardware write.

Evidence: `evidence/candidates/BC250_VCN_D3B2_combined_v001/`.

The exact D3-B2 candidate was written to `BC250-01` after a fresh current-state capture and exact operator approval. A separate full-chip readback is byte-identical. Hardware-trial manifest: `evidence/programmer/reads/20260911/d3b2-v001-hardware-trial-manifest.json`. This proves only SPI contents; boot and VCN behavior remain unrun.

Historical unsigned gasket and OC images under `import/` remain reference/rejected artifacts and are not candidate sources.


## Static DFG consumer context

Direct Rizin context `evidence/firmware-audit/rizin/AmdApcbObrDxe.dfg-context.txt` (SHA-256 `fcb666f776d700933878024166c39929147cf06210d85fd9ffbeceac72241201`) shows the APCB consumer masking token words with `0x001FFF00` and recognizing the wildcard marker. The candidate `0x007FFF00` preserves that masked marker while extending upper bits. This is static semantic support only; policy recipients, PSP acceptance, and runtime VCN behavior remain unverified.
