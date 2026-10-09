# KDB cross-image anchor test — the PSP signature-bypass lane is CLOSED

## Intent (2026-09-19T14:42+0500, Asia/Almaty)

- Actor: root agent.
- Target: six 16 MiB ROM images, read-only. No hardware, no flash.
- Reason: decide whether the KDB trust anchor (`39bfc192`, declared by the type-`0x4F`/`0x50`
  carriers) is an in-image value, which would make the chain forgeable, or an external
  AMD anchor, which closes the lane.
- Design: if a key's modulus is byte-identical across independent AMI builds of the same
  board AND across a different AMD product from a different era, it is a shipped platform
  constant, not an image-local secret.
- Expected effect: a verdict, not a patch. Rollback: none required.
- Stop conditions: none reached.

## Images

| label                  | path                                                                    | sha256 (16)        |
| ---------------------- | ----------------------------------------------------------------------- | ------------------ |
| BC250_5.00_clv         | `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`                   | `ea5781049160ab33` |
| BC250_5.00             | `evidence/donor/retroweb-20260916/BC250_5.00.bin`                       | `0d6f136cb120`     |
| BC250_3.00             | `evidence/donor/retroweb-20260916/BC250_3.00.bin`                       | `07595ca3aecf`     |
| BC250_3.00_CHIPSETMENU | `evidence/donor/retroweb-20260916/BC250_3.00_CHIPSETMENU.bin`           | `48fbe5d366e6`     |
| BC250_2.00             | `evidence/donor/retroweb-20260916/BC250_2.00.bin`                       | `ee6150dfed33`     |
| **AMD_4700S_C0A**      | `/tmp/4700s/C0A/C0A` (from `evidence/donor/amd-4700s-20260916/c0a.zip`) | `bb2cf51df409`     |

The 4700S C0A is a different product (Ariel/Cardinal C0A desktop kit), AMI build dated
2022-04-26, 18 PSP entries, no `0x24`/`0x45` (VCN fused off). It is the control: any key
that survives into it unchanged is not a BC-250 or a per-build artifact.

## Procedure

Signature-scan rather than entry-table parse, so the result does not depend on the PSP
directory geometry: walk each image for the KDB record pattern
`u32 size == 0x150 && u32@+0x0C == 65537 && u32@+0x20 in (1024, 2048)`, take the 16-byte
`kid` at `+0x10` and the `bits/8`-byte modulus at `+0x50`, hash the full modulus.

## Result — all 15 kid→modulus pairs are IDENTICAL everywhere they appear

| kid                    | BC250 5.00clv | 5.00 | 3.00 | 3.00CM | 2.00 | 4700S C0A | modulus sha256 (12) |
| ---------------------- | ------------- | ---- | ---- | ------ | ---- | --------- | ------------------- |
| `39bfc1922fa14ef2`     | YES           | YES  | YES  | YES    | YES  | **YES**   | `238e1f6b7f36`      |
| `9ace85d9b8084270`     | YES           | YES  | YES  | YES    | YES  | **YES**   | `aecffabed865`      |
| `cc7d248a744643a7`     | YES           | YES  | YES  | YES    | YES  | **YES**   | `5c4aad785603`      |
| `30b8865125424499`     | YES           | YES  | YES  | YES    | YES  | -         | `4664bed619bd`      |
| `537b4c2ef4704afb`     | YES           | YES  | YES  | YES    | YES  | -         | `ab7184b66f6f`      |
| `5a3587b59f4a4537`     | YES           | YES  | YES  | YES    | YES  | -         | `5361184e9ee6`      |
| `663ca5220aad4b56`     | YES           | YES  | YES  | YES    | YES  | -         | `43d4bd1b7dc3`      |
| `8b8df41e2a6649be`     | YES           | YES  | YES  | YES    | YES  | -         | `53743e256442`      |
| **`96ea7cfec59d4c2a`** | YES           | YES  | YES  | YES    | YES  | **-**     | `bd4d51fb34c8`      |
| `9f0d38309c0f4509`     | YES           | YES  | YES  | YES    | YES  | -         | `a096f788ce99`      |
| `28d319025e5643df`     | -             | -    | -    | -      | -    | YES       | `6475b9154ae2`      |
| `61a3d108bedb489d`     | -             | -    | -    | -      | -    | YES       | `8be0ddfec5be`      |
| `8c77cdf9a60444ac`     | -             | -    | -    | -      | -    | YES       | `ae85ffaedc99`      |
| `b6f9ac22323444f9`     | -             | -    | -    | -      | -    | YES       | `289221de7710`      |
| `c551a33053774b1f`     | -             | -    | -    | -      | -    | YES       | `6969bab82598`      |

Zero conflicts: no kid anywhere carries two different moduli. Report:
`evidence/firmware-audit/kdb-crossimage-kids-clv500-lineage.json`.

## Findings

- **F1 — PSP signature-bypass lane CLOSED.** `39bfc192` is byte-identical across five
  independent BC250 AMI builds (2.00 through 5.00) and across the 4700S C0A, a different
  product from a different year. An anchor that survives a product change unchanged is a
  shipped platform constant, not an image-local secret. The chain
  ROM -> `39bfc192` -> KDB is therefore not forgeable by editing the KDB: replacing the
  modulus gains nothing, because the value that is trusted is not the image's copy of it.
- **F2 — corroboration.** The observed D3-B2 result (substituting the `0x24`/`0x45`
  carriers produced a non-booting board) shows the chain is actively enforced. Combined
  with F1, the enforcement root is external to the image.
- **F3 — the KDB is per-platform, not universal.** BC250 carries 7 kids absent from the
  4700S; the 4700S carries 5 absent from BC250. Only `39bfc192`, `9ace85d9`,
  `cc7d248a` span both.
- **F4 — `96ea7cfe` is BC250-family, not AMD-universal.** The key that verifies the
  SEC_GASKET (`0x24`) and the TOS policy (`0x45`) is present, byte-identical, in all five
  BC250 builds, and **absent** from the 4700S — consistent with the 4700S having no
  `0x24`/`0x45` entries at all. It is a BC-250-family signing key held by the vendor.
- **F5 — the trust-anchor-in-payload shape from the authority map is real but not
  exploitable.** Types `0x4F`/`0x50`/`0x51` do name their own verifying kid, but that kid
  is an external constant (F1), so the naming is a selector, not a trust source.

## What stays open

Three lanes do not require forging a signature and remain untouched:

1. SMU second-core register class — `FUN_000235c8` routes addresses in
   `_DAT_000178b8.._DAT_000178bc` to `0x1b514` (second core) instead of the master
   window. A class of domain registers reachable only through that core. Never tested.
2. The gate byte `*(_DAT_000171ec + 0xf6)` — one byte decides whether the firmware-side
   domain-14 power route runs. Who sets or clears it is unknown.
3. Persistence of `secure` across the `amdgpu` load (the `3c50bc9a` lineage).

## Rollback

None required. No image, chip or repository artifact was modified. `/tmp/4700s` is a
scratch extraction of the already-archived `c0a.zip`.
