# Community BIOS 5.00 study (operator order 2026-09-23)

Operator: "в репозитории Community уже есть BIOS пятой версии, который прошивают —
найди и изучи". Found: the community's `Robin5.00` = our local
`evidence/donor/retroweb-20260916/BC250_5.00.bin`, sha256 `0d6f136cb120cf3b…` — the same
hash the community reference lists as the stock P5.00 that people flash
(`docs/reference/amd-bc250-docs/source/docs/bios/flashing.md`; multi-source: forgenam,
MrrZed0, scrakcho, dannybastos). No download needed — already in the corpus, hash
confirmed against the community reference. Read-only study, script output inline
(diff of PSP directories + full-image byte diff vs our CLV base).

## Finding 1: the community-flashed 5.00 carries the SAME locks

All 19 PSP entries of P5.00 (`0d6f136c…`) are BYTE-IDENTICAL to our CLV base
(`ea578104…`), including:

- `0x24` SEC_GASKET (11856 B): 0 differing bytes;
- `0x45` TOS_SECURITY_POLICY (1760 B): 0 differing bytes;
- SMU fw `0x8`, root `0x9`, KDB `0x4F`, container `0x44`, all ABL/keys — all SAME.

So every flashed community 5.00 runs the identical PSP region and the identical VCN
lock. No community shortcut exists at the PSP level; there is nothing new to lift from
this image's lock machinery.

## Finding 2: the two 5.00 builds differ ONLY outside the PSP region

Full-image diff: 1,336,988 bytes across 5 ranges:

| range                | size    | what it is                                                 |
| -------------------- | ------- | ---------------------------------------------------------- |
| `0x2AD..0x2144`      | 7.8 KB  | boot FV (reset vector area)                                |
| `0x1FE40..0x1FFEF`   | 432 B   | boot FV                                                    |
| `0xAB1008..0xAB1010` | 9 B     | APCB header — size field (CLV APCB 2972 B vs stock 1160 B) |
| `0xAB1440..0xAB1B9B` | 1.9 KB  | APCB tail — the CBSG group (CLV 1896 B vs stock 84 B)      |
| `0xAE0088..0xC25586` | 1.33 MB | BIOS FV body (DXE build differences)                       |

Consistent with the project record: CLV = stock 5.00 with a FULL CBSG group
("full CBSG, unauthenticated", 2026-09-16 deep-research) and its own boot-FV/DXE bits.
The PSP region is common to both.

## Net meaning for the mission

1. The PSP/lock surface is build-independent across 5.00: any community flash evidence
   (boards booting Robin5.00, VCN still closed) transfers to our base and vice versa.
2. Our glitch-signed candidate differs from a community-proven image ONLY in the
   intended changes (spoofed key, rebuilt lock carriers) — the community 5.00 is the
   closest "known-bootable" control for the flash session.
3. The remaining copyable differences (APCB CBSG, boot FV, DXE body) are config/build
   deltas, not VCN unlock material — consistent with the 4700S result
   (`2026-09-23-donor-4700s-vcn.md`): the unlock is not hiding in a donor image.
