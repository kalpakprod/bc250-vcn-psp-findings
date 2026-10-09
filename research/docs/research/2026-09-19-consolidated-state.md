# BC-250 consolidated state after a full read of the repository (2026-09-19)

> Audit 2026-09-27: historical snapshot, not a replacement for current plans. Use docs/CURRENT-CONTEXT.md. Section 6 is NOT a safe live-probe recipe: it records a read wedge after an accepted write, so prior programming is not a sufficient safety condition. "Writes are proven-safe first touch" must not be generalized to arbitrary addresses or transports. No live operation is authorized by this record.

Written after reading the project's own documentation end to end, not from recall.
Sources are named inline. This file supersedes the forward-plan sections of every earlier
plan; their measured evidence stands.

## 0. The single most important fact, and it is already hardware-verified

`docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md` (D4 probe, 2026-09-12):

- One byte changed in the SMU payload zero padding (file `0x93c64c`, `00 -> 01`), in a
  21863-byte zero run, behaviorally inert. Readback byte-exact. **Cold boot: "нет
  инициализации" — the hard halt, identical to D3-B2.**
- Verdict: **the SMU firmware is signature-verified by the on-die PSP ROM and is not
  patchable in the BIOS.**
- Same log: the SSH-at-t+90s discriminator ran for the first time (12 probes × 15 s, all
  failed) → the fail-soft-skip hypothesis is disproven; D3-B2 is a hard boot failure.
- **FINAL CAMPAIGN VERDICT (their words): every BIOS-resident enforcer — the `$PS1`
  carriers AND the SMU body — is signature-gated by the on-die ROM; the only freely
  modifiable surface (APCB, checksum-only) is proven not-the-lock; the runtime is
  exhausted; the signing keys are RSA-2048 (math-closed); the verifier lives in the
  on-die ROM.**

Nothing found in any file since 2026-09-12 contradicts this.

## 1. The lock, as established

Five layers (`archives/imported/historical-bios-repo/legacy-bc250-bios/docs/source-docs/VCN-LOCK-MECHANISM.md`):

| Layer                                      | State                                                                                                                                                                                                          |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| L1 discovery/hardware                      | VCN 2.0.3 present, `harvest=0`, harvest table empty. Bases `0x7800/0x7E00/0x02403000`. Not fused off.                                                                                                          |
| L2 amdgpu driver                           | `amdgpu_discovery.c` has an explicit empty `case IP_VERSION(2,0,3): break;` — VCN blocks are deliberately skipped for Cyan Skillfish. Fixed by the `linux-cachyos-vcn-bc250` kernel + `amdgpu.bc250_vcn_mode`. |
| L3 PSP SEC_GASKET (type `0x24`, B.51.0.16) | the main lock — see §2                                                                                                                                                                                         |
| L4 SMU domain 6 (VCN) power                | domain gate re-arms every cold boot; no `PowerUpVcn` message exists in SMU 11.8 (msg `0x8`/`0x9` NULL in BOTH 0.58.6.0 and P5.00, byte-level)                                                                  |
| L5 VCN firmware                            | placed into VRAM (proven) but never proven to execute                                                                                                                                                          |

**Two locks, both required** (`docs/research/2026-09-12-injection-audit.md` §unified theory,
`VCN-LOCK-MECHANISM.md` §7.4): (1) the DFG/NBIF power grant, (2) the gasket aperture
program for SMN bank `0x0900Cxxx` (HWID 12). Robin's gasket ships **without** that bank;
Cezanne carries 56 records. Both locks were addressed; neither opened the bridge.

## 2. The gasket carrier, decoded exactly

PSP type `0x24` at SPI `0x982000`, body `0x2E50`:

```
0x18 header + 0x130 preamble + 1409 x 8 records (table base body 0x148) + 0x100 RSA-2048
0x148 + 1409*8 + 0x100 = 0x2E50   (exact)
```

Groups (header word `{small_addr, count}` then `count` records):

| group | header          | count | window                                                     |
| ----- | --------------- | ----- | ---------------------------------------------------------- |
| 0     | —               | 1230  | `0x201` SMN banks + DF windows + NBIO                      |
| 1     | `0x203 <- 0x1F` | 31    | `0x0322` varA                                              |
| 2     | `0x210 <- 0x0D` | 13    | mailbox: `0x3E810` header + twelve `0x3E814` command words |
| 3     | `0x280 <- 0x64` | 100   | recommit: DF windows + donor VCN bank tail                 |
| 4     | `0x281 <- 0x1F` | 31    | `0x0322` varB (TOS mirror)                                 |

`archives/imported/historical-bios-repo/legacy-bc250-bios/docs/02-gasket-groups.md` states the group-`0x210` semantics: `0x3E810` is a
mailbox **header** (stock `0`, donor `6` = VCN segments enabled) and the twelve `0x3E814`
values are **command words**, not a table to replay. That corrects this session's earlier
"1379-step script" model.

Byte-identical across BC250 2.00 / 3.00 / 3.00_CHIPSETMENU / 5.00 / 5.00_clv (payload
sha `7268388943f98834`, zero differing records) — VCN was never routed differently by any
release.

## 3. Signature scheme, solved structurally

`VCN-LOCK-MECHANISM.md` §6:

```
0x000..0x100  $PS1 header: nonce 16B | '$PS1' | body_size u64 | 16B zero | key-id 16B @0x38
              | {type, 01 01} @0x58 | u32 version @0x60 | u32 total @0x6C
0x100..body   signed body
tail 0x100    RSA-2048 signature (entropy 7.0-7.3 on every policy blob)
```

Every blob's key-id resolves into t50/t51:

| blob                                  | key-id        |
| ------------------------------------- | ------------- |
| SEC_GASKET `0x24` + TOS policy `0x45` | `96ea7cfe...` |
| PMFW (SMU)                            | `8b8df41e...` |
| ABL                                   | `663ca522...` |
| PSP-OS / DRIVER_ENTRIES               | `5a3587b5...` |
| HW_IP_CONFIG `0x20`                   | `537b4c2e...` |
| DEBUG_UNLOCK `0x13`                   | `9f0d3830...` |
| XHCI                                  | `9ace85d9...` |
| `0x4F`                                | `39bfc192...` |

Offline verification was **never** reproduced: 11 keys × 5 modulus transforms × 3
signatures × 2 endian × 15 spans × 4 hashes = empty → the scheme is non-standard
(probably an AES-wrapped signature with a fused key by key-id, or a non-standard span).
The validator is the t01/t02 ARM ladder; its decode would give the exact algorithm.

This session's independent cross-image test (six ROMs incl. the 4700S C0A) confirmed the
key material is identical everywhere and the trust root is external — i.e. it re-derived
§6's conclusion without knowing §6 existed.

## 4. Ledger — closed with hardware evidence

| Route                                            | Verdict                                        | Evidence                                                                                                                                                                                 |
| ------------------------------------------------ | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `$PS1` carriers (`0x24`/`0x45`) edited/relocated | **CLOSED DEFINITIVELY**                        | D3-B2 ×2 byte-exact flashes, hard fail; SSH-at-t+90s discriminator ran (12/12 no-route)                                                                                                  |
| SMU firmware body patched in BIOS                | **CLOSED**                                     | D4 probe: 1 inert byte in a zero pad → hard halt → ROM signature check                                                                                                                   |
| APCB (unsigned, checksum-only)                   | boot-safe but **not the lock**                 | D3-A; D8-D19 all boot carrying DFG `0x007FFF00`                                                                                                                                          |
| Runtime SMU path (Q2 `0x23` → Q3 `0x98`/`0x2A`)  | transport proven, **transition never happens** | S2-A: 59/59 accepted, bank-12 `commit=1`, full donor dataplane 15/15 accepted, island still isolated; dom14 power transaction never completes; NBIF bridge all-ones                      |
| TOS C2P `0x100B`/`0x100C`/`0x1033`               | **measured negative**                          | TOS does not answer direct C2P commands; evidence `d6f74e4d`                                                                                                                             |
| DEBUG_UNLOCK type `0x13`                         | **dead**                                       | RSA-2048 one-shot challenge against AMD's key                                                                                                                                            |
| PEI DF-aperture pair injection                   | **BLOCKED, not falsified**                     | V1 target list EMPTY: stock→VCN seg-3 delta = 0 (91/91); VCN delta is 56 seg-9 writes only; OS-side live proof killed the board at `insmod` (D17)                                        |
| Q4 mailbox probing                               | **closed wedge class**                         | Q4 `0x04` alone wedges the board (reproduced)                                                                                                                                            |
| OS-side DF/SMN probing                           | **parked hazard**                              | `dfprobe` kmod hard-hang at `insmod`                                                                                                                                                     |
| Second-core IPC (D-R1)                           | **inconclusive, not falsified**                | sender `0x1B514` decoded (`0xFE`, `(addr,value)`); receiver absent from the image; Q3 `0x5C` resolves to `0x5C0FC`, outside the forwarding interval `0x5B000..0x5B7FF`                   |
| Independent review of the unlock claims          | **INCONCLUSIVE**                               | `docs/research/2026-09-15-independent-unlock-review.md`: no method supported as a working unlock; `BC250_VCN_UNLOCKED.ROM` APCB checksum FAIL (`0x03` vs `0x41`), DFG stock, broad delta |

## 5. Open — what is genuinely not done

1. **P5.00 SMU `13c93c08` decode** — never decoded or probed. Campaign spec V1/V2/V3.
   C1 explicitly permits a per-version negative closure as an honest exit.
2. **svc `#0x7B`/`#0x7C`/`#0x5E`/`#0x5F` handlers** (PSP director, outside t28) — the
   real SMN read/write primitives behind the C1 chain.
3. **t01/t02 PSP validator RE** — the only way to learn the exact signature algorithm.
   Bounded: keys are RSA-2048, so only an implementation flaw helps.
4. **8-core unlock on BC250-01** — substrate verified (mask `0x77` readable at
   `0x115A870`), `0x98` write of `0xFF` never applied. Community-proven, reversible.
5. **Second-core IPC receiver** — not in the image; route functionality untested.
6. **fTPM graft** — C0A 5 modules, 327 696 B, inventoried, never grafted.
7. **FCLK/MEM OC** — campaign Phase O; NVRAM-pin class disproved (T1 revert); host SMU
   governor proven.
8. **Observation channel** — J5 UART / TPMS1 LPC-POST never populated. The error audit
   names this as the single deepest reason the 4700S campaign produced no localizable
   result.
9. **Hardware/fuse class** — outside software scope.

## 6. Measured safety rules (do not re-derive)

- **DF-space SMN reads wedge even immediately after a successful write to the same
  address.** Stage 2a: write ACCEPTED, `alive=True`, then the readback (`queue 3 msg
0x2A`) killed the mailbox globally, including the kernel driver path.
- DF/bank-12 reads are safe **only after** the region was programmed in the same session.
- **Writes are the proven-safe first touch.**
- VCN MMIO reads wedge while the domain is gated (mode2 controlled differential).
- Q4 `0x04` wedges the board on its own.
- Cold power cycle is the only rollback; the gasket is re-applied fresh at every boot.
- `amdgpu.fw_load_type=0` is prohibited (GFX KIQ failure).

## 7. Direct consequence

The software route to the VCN power grant is closed with hardware evidence on every layer
that can carry it. The honest remaining options, in order of information gain per unit risk:

1. **P5.00 SMU decode (read-only, no board)** — the one unprobed version. Closes C1 or
   opens a new surface.
2. **svc handler + t01 validator RE (read-only, no board)** — decides whether the
   signature scheme has an implementation flaw. This is the only path that could reopen
   the carriers.
3. **Instrument first** (J5 UART / TPMS1 POST) before any further flash rung — standing
   rule from the 2026-09-17 error audit.
4. **8-core + fTPM + OC** — real, reversible value on the unsigned surface while 1-2 run.

Any claim that a BIOS "with a working VCN exploit" can be assembled now contradicts the
D4 probe and the D3-B2 discriminator, both hardware-verified.
