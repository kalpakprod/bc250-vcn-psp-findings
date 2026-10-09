# Type-0x44 sub-$PS1 header decode + tail-swap discriminator (V2b, static)

Date: 2026-09-23. Read-only decode + offline candidate build. No flash.
Input: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
(sha256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`).
Builds on `docs/research/2026-09-23-type44-tail-consumer.md` (field offsets there
are corrected below).

## Container frame (SPI `0x9C4400`, size `0x6610`)

```
0x000..0x100  $PS1 header
0x100..0x110  signed body (signed_len=0x10): {0x101D→0x210, 0x101E→0x3410}
0x110..0x210  RSA-2048 signature (kid 9ace85d9… = XHCI key)
0x210..0x6610 unsigned tail (0x6400)
```

| off   | field          | value                      | note                                          |
| ----- | -------------- | -------------------------- | --------------------------------------------- |
| +0x00 | nonce 16B      | `95201783…`                |                                               |
| +0x10 | magic          | `$PS1`                     |                                               |
| +0x14 | signed_len u32 | `0x10`                     |                                               |
| +0x30 | flag           | `1`                        |                                               |
| +0x34 | sigtype        | `0`                        | sig = 0x100 B                                 |
| +0x38 | kid 16B        | `9ace85d9…`                | XHCI, same as both sub-blobs                  |
| +0x50 | body_size u64  | `0x10`                     | signed body only                              |
| +0x58 | format/token   | `0x0101101C`               | parent of workload `0x101D/0x101E`            |
| +0x60 | version        | `1`                        |                                               |
| +0x6C | rom_size u32   | **`0x210`**                | signed extent end — NOT catalog size `0x6610` |
| +0xD0 | hash16         | `sha256(signed_body)[:16]` | **confirmed** `3d311eb…`                      |

Key geometry: verifier-facing `rom_size` stops at `0x210`; the `0x6400` tail is
outside the signed total by construction.

## Sub-$PS1 headers (0xF0 B each)

Two blobs in tail:

| blob | header SPI             | code SPI               | token        | stride   |
| ---- | ---------------------- | ---------------------- | ------------ | -------- |
| 1    | `0x9C4620` (`+0x220`)  | `0x9C4710` (`+0x310`)  | `0x0101101D` |          |
| 2    | `0x9C7820` (`+0x3420`) | `0x9C7910` (`+0x3510`) | `0x0101101E` | `0x3200` |

Signed-table offsets are from body base `0x9C4500`: `0x210→0x9C4710`,
`0x3410→0x9C7910` — exact code starts.

### Field map (both blobs; identical except token/field50/hash32)

| off   | field          | value                       | verdict                       |
| ----- | -------------- | --------------------------- | ----------------------------- |
| +0x00 | magic          | `$PS1`                      |                               |
| +0x04 | size_a u32     | `0x3000`                    | payload hash length           |
| +0x20 | flag u32       | `1`                         |                               |
| +0x28 | kid 16B        | `9ace85d9…`                 | shared with container         |
| +0x40 | size_b u32     | `0x3000`                    | duplicate of size_a           |
| +0x48 | token u32      | `0x0101101D` / `0x0101101E` | workload id (full)            |
| +0x50 | field50 u32    | `0x03298313` / `0x03195837` | **UNRESOLVED**                |
| +0x5C | total_size u32 | `0x3200`                    | header `0xF0` + code `0x3110` |
| +0xC0 | hash32 32B     | `sha256(code[0:0x3000])`    | **CONFIRMED** both            |
| +0xE0 | pad 16B        | zeros                       |                               |

Code length `0x3110` (`0x3200−0xF0`); hash covers only the first `0x3000`
bytes — trailing `0x110` B of code are outside hash32.

`field50` probes (negative): not crc32/adler32 of full/code/header (with or
without zeroing +0x50), not any u32 slice of sha256/md5/sha1/blake2 of those
regions, not a file offset, not present elsewhere in the image as a word.
High byte `0x03` common; low 24 bits distinct per blob. Status: opaque
build/checksum id — open.

Earlier report offsets (`+0x40:01`, kid at `+0x48`, token at `+0x68`) were
miscounted; table above is from `struct.unpack` on raw bytes.

## Tail-swap discriminator candidate (built, NOT flashed)

Path: `candidates/t44-tail-swap-v001/`

| artifact                               | sha256                                                             |
| -------------------------------------- | ------------------------------------------------------------------ |
| `BC250_5.00_clv_t44_tailswap_v001.bin` | `11f1184e50610830b3a0c26bbf80211e6ad1306085501187c064b1a346aa7633` |
| report                                 | `tail-swap-discriminator.json`                                     |

Patch: blob1 code `[0:0x100]` ← blob2 code `[0:0x100]` (SPI `0x9C4710..0x9C4810`).
221 bytes differ; all inside unsigned tail.

Verified:

- signed extent `[0x9C4400, 0x9C4610)` byte-identical to stock
  (`305c09095dbdd6ab…` both)
- signed table still `{0x101D:0x210, 0x101E:0x3410}`
- catalog / other regions untouched

Interpretation (offline; excluded from first flash pair per plan):

- boot OK + workload `0x101D` behavior changes → TRUSTS-TAIL (ROM loads code
  via signed offsets without re-hashing tail)
- boot OK + no observable change → tail not consumed on this path
- boot fail / PSP error → something validates tail beyond the visible RSA sig

Evidence class: static build only.

## Verdict

- Sub-header decode: **RESOLVED** for all fields except `field50` (opaque id).
- `hash32` integrity binding: **RESOLVED** — covers code `[:0x3000]` only;
  last `0x110` B of each blob unsigned even by this local hash.
- Tail-swap discriminator: **BUILT**, ready for a future approved flash session
  (not in first pair). Hardware result: none.
- Consumer of type `0x44` / workload dispatch: still UNRESOLVED (on-die ROM),
  unchanged from `2026-09-23-type44-tail-consumer.md`.
