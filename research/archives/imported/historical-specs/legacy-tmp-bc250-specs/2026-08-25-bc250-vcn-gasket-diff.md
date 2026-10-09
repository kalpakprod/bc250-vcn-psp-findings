# BC-250 VCN: working-sibling SEC_GASKET differential

**Status:** active evidence, interpreted by `2026-08-26-bc250-vcn-evidence-reassessment-and-safe-next-slice.md`; HWID 12 is a leading hypothesis, not a proven sole blocker.  
**Date:** 2026-08-25  
**BC-250 source:** Robin 3.00 `SEC_GASKET B.51.0.16`  
**Working sibling source:** ASRock DeskMini A300/Cezanne `A3MSTX_3.70E`

## Result

The missing secure-world object is localized to the gasket register bank whose address prefix ends in `0x0c`, matching VCN hardware ID 12.

Both working Cezanne PSP directories report:

```text
VCN HWID      = 12 (0x0c)
VCN version   = 2.2.0
harvest       = 0
base families = 0x00007800, 0x00007e00, 0x02403000
```

Their primary SEC_GASKET policies contain an identical 56-write bank at:

```text
0x0900c000..0x0900cfff
```

Robin 3.00 contains zero writes in that bank:

```text
BC-250 count          = 0
working sibling count = 56
working-bank SHA-256  = 8c67c82a786081a83a82989904e024d1bbecaa429275105c7779f2c14fd46ad3
```

## Working VCN range descriptors

The bank configures eight compact VCN register ranges:

| Gasket registers | VCN range |
|---|---|
| `0x0900c934/38` | `0x00021800..0x000218ff` |
| `0x0900c958/5c` | `0x00020300..0x000206ff` |
| `0x0900c97c/80` | `0x0001f844..0x0001f84f` |
| `0x0900c9a0/a4` | `0x00020180..0x00020183` |
| `0x0900c9c4/c8` | `0x00020108..0x00020117` |
| `0x0900c9e8/ec` | `0x00021078..0x0002107f` |
| `0x0900ca0c/10` | `0x00020eb0..0x00020eb7` |
| `0x0900ca30/34` | `0x0001f860..0x0001f863` |

## Field decode

The recurring descriptor layout is now structurally decoded:

```text
descriptor N base = bank + 0x92c + N*0x24
+0x00 selector       = 0x00000000
+0x04 policy_mode    = 0x00000036
+0x08 range_start
+0x0c range_end
+0x18 attributes     = 0x00000307
```

Eight complete VCN descriptors use this shape. A ninth slot contains only selector/mode and is treated as an incomplete/sentinel entry.

`bank+0xb80` is decoded with high confidence as the range enable/valid bitmap. Across all 55 populated Cezanne banks it equals `(1 << complete_range_count) - 1`. For VCN: eight ranges -> `0x000000ff`. The alternate group `0x280` clears it to zero.

`bank+0x234` is a programming commit/enable gate with medium confidence: the normal sequence writes `0`, programs the bank, then writes `1`; the alternate sequence repeats the same framing.

The remaining fields are bounded but not named conclusively:

```text
0x830 = 0x00fffffb   24-bit access mask 0
0x834 = 0x00ffffff   24-bit access mask 1
0x838 = 0x00ffffff   24-bit access mask 2
0x910 = 0x00497fff   policy mask 0
0x914 = 0x00007fff   policy mask 1
0x920 = 0x000003ff   policy/class mask, not a range count
```

Client/master bit identities remain unresolved. `policy_mode=0x36` and `attributes=0x307` are shared by all eight VCN ranges and two ACP ranges, but their individual bits cannot yet be assigned safely.

## Interpretation

This is stronger than the previous host-read inference:

- Cezanne has working VCN and an explicit HWID-12 gasket bank.
- BC-250 advertises VCN HWID 12 in IP discovery but omits that bank entirely.
- Native PMFW OFF -> ON cannot create the missing secure policy and does not open MMIO.

The evidence strongly identifies an omitted secure gasket configuration as the platform difference. Field semantics are not fully proven. The bank may authorize PSP clients, host clients, or both; therefore replaying it blindly is not justified.

## Offline insertion preflight

A research-only unsigned body was rebuilt with the complete sibling bank inserted at the correct HWID ordering points. The original was not modified.

```text
source size       = 11344 (0x2c50)
candidate size    = 11792 (0x2e10)
size delta        = 448 bytes (56 writes * 8)
group 0x201 count = 1230 -> 1281 (+51)
group 0x280 count = 100  -> 105  (+5)
```

The rebuilt body parses successfully and its extracted HWID-12 bank is byte-for-byte identical to the working sibling hash `8c67c82a…6ad3`.

It is deliberately marked `UNSIGNED_DO_NOT_FLASH`. The original full container occupies 11,856 bytes and has only 176 bytes of padding before `DRIVER_ENTRIES`. The candidate full container would require 12,304 bytes, exceeding the available 12,032-byte slot by 272 bytes. Applying it therefore requires relocation plus PSP-directory metadata changes. Independently, changing one signed byte invalidates the AMD RSA signature.

A compaction pass found only eight byte-identical duplicate writes in the two target groups, worth 64 bytes theoretically. The insertion needs 448 bytes, leaving a 384-byte shortfall. Even those duplicates are not declared removable because repeated writes may trigger hardware side effects. The 103 ordered rewrites include commit/enable transitions and cannot be compacted safely. Therefore no evidence-backed, size-preserving insertion exists.

## Runtime SMU replay result

Path 1 was executed on the live BIOS P3.00 board after restoring VCN clock slots and releasing the domain-6 gate.

1. Control probe: the SMU privileged SMN path changed `0x0900c234` from `0x00000000` to `0x00000001`; SMU remained alive.
2. Full replay: all 56 ordered sibling writes returned through the SMU API while the SMU remained responsive. The final control read remained `0x00000001`.
3. VCN MMIO was unchanged: all 11 liveness registers remained `0xffffffff` before and after replay.
4. Board and SMU remained online; all seven stopped telemetry services were restored and verified active.

Therefore raw runtime replay from the SMU context is not sufficient to instantiate the missing HWID-12 policy for host VCN access. The remaining possibilities are that SEC_GASKET group types carry trusted-loader semantics beyond ordinary register stores, the configuration is committed only from a PSP/ABL requester context, or another signed policy stage still clamps the NBIF/Fabric route.

Applying the bank now requires one of:

1. a correctly signed replacement SEC_GASKET/BIOS component;
2. an AMD/OEM-authorized secure-debug token;
3. an already trusted PSP/ABL boot-stage service that accepts and commits this policy;
4. separately authorized secure-world vulnerability research.

## Artifacts

- `tmp_bc250/recon/working_vcn_gasket_template.json`
- `tmp_bc250/recon/vcn_hwid12_gasket_diff.txt`
- `tmp_bc250/recon/bc250_vs_cezanne_sec_gasket_diff.txt`
- `tmp_bc250/recon/cezanne_a3mstx_370e/dir1_hw_ip_parsed.json`
- `tmp_bc250/recon/cezanne_a3mstx_370e/dir3_hw_ip_parsed.json`
- `tmp_bc250/recon/cezanne_a3mstx_370e/dir1_sec_gasket_12.parsed.json`
- `tmp_bc250/recon/cezanne_a3mstx_370e/dir3_sec_gasket_12.parsed.json`
- `tmp_bc250/recon/read_sec_gasket_policy_with_renoir_candidates_2026-08-25.out`
- `tmp_bc250/recon/cezanne_sec_gasket_banks_decoded.json`
- `tmp_bc250/recon/bc250_sec_gasket_banks_decoded.json`
- `tmp_bc250/recon/vcn_gasket_semantics.json`
- `tmp_bc250/recon/bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.json`
- `tmp_bc250/recon/bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.verify.json`
- `tmp_bc250/recon/bc250_sec_gasket_compaction.json`
- `tmp_bc250/recon/smn_vcn_gasket_unclamp.py`
- `tmp_bc250/recon/run_smn_vcn_gasket_unclamp.sh`
- `tmp_bc250/recon/smn_vcn_gasket_control_2026-08-26.json` (`954ca2a0…06684`)
- `tmp_bc250/recon/smn_vcn_gasket_full_2026-08-26.json` (`36d16561…be52f`)
- `tmp_bc250/recon/smn_vcn_gasket_full_2026-08-26.out` (`2f6a8511…a78d`)
