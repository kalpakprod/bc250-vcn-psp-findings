# PSP authority map — static pass on BC250_5.00_clv.bin

## Intent (2026-09-19T14:35+0500, Asia/Almaty)

- Actor: root agent.
- Target: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (`ea578104...`), read-only.
- Scope: no hardware, no flash, no SMU access. Parse `$PSP` only.
- Reason: the VCN isolation grant is applied by PSP-side signed policy. Before any
  black-box verifier work, establish whether any carrier is unauthenticated and
  map which key verifies which carrier.
- Expected effect: a static authority map or a clean negative.
- Rollback: none required (no writes).
- Stop conditions: none reached; run completed.

## Procedure

1. `$PSP` at `0x8E0000`, header `24 50 53 50 | b9 38 aa 17 | 13 00 00 00 | d0 05 00 00`;
   entry count 19, info `0x5D0`.
2. Entry table from `0x8E0010`, **16-byte stride**: `u32 type | u32 size | u64 location`
   where the location's top byte is a tag (`0xFF` = SPI flash) and the low 24 bits are
   the SPI offset. (The 0x18-stride assumption in earlier passes was wrong; this is the
   correction.)
3. Per entry: locate `$PS1` in the body, read its declared sub-size, compute the tail.
4. Search each body for the ten `$KDB` `kid` values from
   `evidence/firmware-audit/kdb-rsa-weakness-audit-clv500.json`.

## Result

- 19 entries, types {1, 2, 8, 9, 0x12, 0x13, 0x20, 0x24, 0x28, 0x30, 0x31, 0x32, 0x33, 0x34, 0x44, 0x45, 0x4F, 0x50, 0x51}.
- `$PS1` sub-header at body `+0x10` in 17 of 19 entries (types 1 and 9 have none).
- Tail (entry size minus `$PS1` sub-size minus 0x10) = `0x1F0` for 13 entries,
  `0x2F0` for the two KDB carriers (types 0x50/0x51), `0x65F0` for type 0x44
  (which holds nested sub-directories). **No entry has an empty or truncated tail.**
- Declared `kid` per carrier and how many KDB kids its own body contains:

| type                         | what                      | kid declared in body | kids in body    |
| ---------------------------- | ------------------------- | -------------------- | --------------- |
| 0x02                         | PSP/ABL-class             | `5a3587b5`           | 1               |
| 0x08                         | SMU firmware (Robin 5)    | `8b8df41e`           | 1               |
| 0x12                         | (twin of 0x08, same size) | `8b8df41e`           | 1               |
| 0x13                         | —                         | `9f0d3830`           | 1               |
| 0x20                         | —                         | `537b4c2e`           | 1               |
| **0x24**                     | **SEC_GASKET**            | **`96ea7cfe`**       | 1               |
| 0x28                         | —                         | `5a3587b5`           | 2               |
| 0x30, 0x31, 0x32, 0x33, 0x34 | —                         | `663ca522`           | 1               |
| 0x44                         | nested                    | `9ace85d9`           | 1               |
| **0x45**                     | **TOS_SECURITY_POLICY**   | **`96ea7cfe`**       | 1               |
| 0x4F                         | key record                | `39bfc192`           | 1               |
| **0x50**                     | **$KDB copy (t50)**       | **`39bfc192`**       | **8 (all t50)** |
| **0x51**                     | **$KDB copy (t51)**       | **`9ace85d9`**       | **3 (all t51)** |

- Report: `evidence/firmware-audit/psp-authority-map-clv500.json`.

## Findings

- **F1 (negative, closes a hypothesis):** every one of the 19 carriers carries a
  signature-sized tail. There is no unsigned `$PSP` entry. "PSP honours an
  unauthenticated carrier" is dead as a hypothesis on this image.
- **F2:** `SEC_GASKET` (0x24) and `TOS_SECURITY_POLICY` (0x45) are verified by the
  **same** kid, `96ea7cfe`, confirming the earlier memory note — and that kid's record
  lives inside the **type 0x50** carrier, i.e. inside the KDB blob itself.
- **F3:** the type 0x4F and type 0x50 carriers **declare their own verifying kid**
  (`39bfc192`) in their own headers, and `39bfc192` is t50's first key — a
  trust-anchor-in-payload shape.
- **F4:** type 0x50/0x51 declare `39bfc192` / `9ace85d9`, both of which are keys held
  in the KDB, not obviously external anchors.

## Uncertainty / what this does not prove

- The declared `kid` field proves which key id the carrier _names_. It does **not**
  prove which key the on-die PSP ROM actually verifies it against. Whether
  `39bfc192` is an on-die/fuse key or is loaded from the image is **untested**.
- No verifier code was read: it is in on-die ROM, not in the SPI image.
- Not verified: that PSP applies the _carrier's own_ declared key to the carrier.

## Next decisive test (not run)

Cheap, local, no hardware: compare `39bfc192` and `9ace85d9` moduli against other
donor images (`evidence/donor/retroweb-20260916/BC250_3.00.bin`, 4700S material). If
those moduli are byte-identical across different vendors' boards, they are AMD/ROM
anchors and the chain is closed. If they differ per image, the anchor is in the image
and the chain is forgeable.

## Rollback

None required. No image, chip or repository artifact was modified.
