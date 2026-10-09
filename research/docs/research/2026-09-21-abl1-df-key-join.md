# Exact CLV ABL1 FCLK selector-to-provider key join — 2026-09-21

## Conclusion

A fresh exact-byte/dataflow trace resolves one new edge beyond the prior `0x1FB4 -> 0x4800 -> 0x49CC` boundary:

```text
caller 0x5FAE: R1=0x0F, R0=SP+0x04, local default 0x4B0
  -> FCLK handler 0x463C (selector check, descriptors 0x015F/0x0160)
  -> reader 0x1FB4 (R1 preserved in R8)
  -> helper 0x4800 (R2=0x0F provider context; R1=current token)
  -> provider 0x49CC selector case 0x0F
  -> fixed provider literal 0x1707 and HEAP lookup key 0xA04E
  -> lookup 0x6374, typed output-width byte returned through provider stack arg0
  -> caller output local and context+0x78 at 0x5FBA
```

The FCLK token candidates `0x015F`/`0x0160` are passed to `0x4800` as provider `R1`, but in provider selector case `0x0F` the subsequent path loads a table pointer at `0x49DC`, prepares literal `0x1707` at `0x4A1E`, and replaces the lookup key with fixed `0xA04E` at `0x4B1A`. Thus this trace does not map `0x015F`/`0x0160` to an FCLK frequency or to native `$INV` `0x1373/0x1374`; it shows a selector-specific key transformation into an ABL1 HEAP/APCB-style lookup.

The exact APCB parser independently reports CBSG group ID `0x1707` (subgroup instances 13 and 15). This is a static numeric correspondence and address-ownership lead for the APOB/ABL handoff, not proof that ABL1's literal is backed by this flash group at runtime. No schema/runtime join between CBSG `0x1707`, ABL1 key `0xA04E`, FCLK keys `0x015F/0x0160`, or native `$INV` `0x1373/0x1374` is established.

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, size `16,777,216`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact object: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`, SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Existing parsed APCB detail: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-detail.json`, SHA-256 `503e4f525f4372903b23ea9320c77f7b0b39250f310d80a1b7565eb98b39f394`.

Prior reports/results were reused for context only; no prior serializer or 42/36/71-check inventory was repeated.

## Exact dataflow

### Caller buffer and selector provenance

At ABL1 payload addresses:

- `0x5E70`: `MOV R5,R0`, preserving the caller's context object.
- `0x5FA4`: `MOVW R0,#0x4B0`; `0x5FA8`: stores it at `[SP+0x4]`.
- `0x5FAA`: `MOVS R1,#0x0F`.
- `0x5FAC`: `ADD R0,SP,#0x4`, passing the local halfword output address.
- `0x5FAE`: `BL 0x463C`.
- `0x5FB2`: reloads `[SP+0x4]`; `0x5FBA` stores the halfword to `[R5+0x78]`.

The output/context edge is therefore byte-backed: FCLK handler output local -> `context+0x78`. The input `R1=0x0F` is the FCLK selector entering `0x463C`.

### FCLK descriptor and reader input

At `0x463C..0x466A`:

- `0x4648`: `CMP R1,#0x0F`.
- `0x464E`: constructs `0x015F`; `0x4656` increments to `0x0160`; the zero terminator is at the third halfword.
- `0x466A`: calls `0x1FB4` without rewriting `R1`; the selector remains `0x0F`.

At reader `0x1FB4`:

- `0x1FBE`: `MOV R8,R1` preserves the selector.
- `0x1FD2`: forwards the caller stack value in `R9` to the helper stack argument.
- `0x1FDE`: `MOV R1,R8`, restoring `0x0F` before `BL 0x4800` at `0x1FE0`.

### Helper/provider argument transformation

At `0x4800`:

- `0x4804`: saves reader `R1` (`0x0F`) in `R5`.
- `0x4810`: sets provider selector `R0=0x0F`.
- `0x4818`: `MOV R2,R5`, passing `0x0F` as provider context argument.
- `0x481A`: `MOV R1,R4`, passing the current FCLK token (`0x015F` or `0x0160`) as provider `R1`.
- `0x481C`: calls provider `0x49CC`.

This is the new positive edge: caller selector `0x0F` reaches provider `R2`, while candidate FCLK tokens reach provider `R1`; they are distinct namespaces/arguments.

### Selector-specific provider transformation

At provider `0x49CC`:

- `0x49DC`: loads the table pointer literal, replacing the incoming token register `R1` before selector-case work.
- `0x4A1E`: prepares literal `0x1707`.
- `0x4B0E`: selector case `0x0F` reasserts `R2=0x0F`.
- `0x4B1A`: prepares fixed key `0xA04E` in `R6`.
- `0x4B1E`: stores the selector/`0x1707` pair into the provider's request frame.
- `0x4B34..0x4B3A`: writes fixed key `0xA04E` into a lookup descriptor and calls `0x6374`.
- `0x4BF0..0x4BFA`: loads the provider stack type pointer, extracts a width/type value, and writes the returned type byte through that pointer.

At `0x6374`:

- `0x637C`: reads the HEAP header pointer and verifies the `HEAP` tag.
- `0x6394`: reads requested key from the descriptor (`0xA04E` in the selected case).
- `0x6396..0x6398`: reads and compares each linked node key.
- `0x63A8..0x63AE`: on match, reads metadata and stores payload pointer/length into descriptor `+8/+4`.

No direct clock register, divider, PLL, `$INV`, or `AmdSetup` access occurs in these ABL1 slices.

## APCB namespace correspondence

The exact parsed APCB contains:

- CBSG group `gid=0x1707`, two subgroups (`instance=13`, `instance=15`).
- Subgroup instance 15 body offset `0x160`: `u8_0=1`, `u8_1=189`, `u16_le=96`.

This only shows a matching numeric CBSG identifier and an observed APCB row. It does not establish that the ABL1 `0x1707` literal selects this subgroup, that `0xA04E` is encoded in it, or that native `$INV` `0x1373/0x1374` are transformed into this HEAP node.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260921-abl1-df-key-join/verify_abl1_df_key_join.py
```

Observed final stdout:

```json
{
  "status": "PASS",
  "checks_passed": 66,
  "checks_failed": 0,
  "new_edge": "caller 0x5FAE R1=0x0F -> reader 0x1FB4 -> helper 0x4800 R2=0x0F -> provider case 0x0F -> fixed HEAP key 0xA04E; APCB literal correspondence 0x1707 observed",
  "first_unresolved": "HEAP 0xA04E producer and INV 0x1373/0x1374 bridge"
}
```

Final exit status: `0`; stderr empty. The verifier used six fresh exact `llvm-objdump` windows and compared every decoded Thumb instruction against the pinned ABL1 bytes. The two earlier verifier exits (`1`, then `1`) were test-oracle endianness errors and are preserved in the action log; the method was then changed to display-order Thumb parsing plus byte reconciliation.

Evidence directory:

`/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl1-df-key-join/`

No firmware, ROM, NVRAM, register, hardware, network, installation or candidate write occurred. Runtime execution, loader/base, physical clocks and hardware behavior remain **UNRUN**.
