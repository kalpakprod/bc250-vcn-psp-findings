# CLV DF override consumer boundary — 2026-09-21

## Conclusion

A pinned, read-only disassembly test confirms the exact DF field serializers but does **not** establish that `$INV` records `0x1373/0x1374` reach the separate ABL1 FCLK request or a clock actuator.

- `AmdSetup+0x703` is copied as one byte into record ID `0x1373`.
- `AmdSetup+0x704` is copied as a little-endian u16 into record ID `0x1374`.
- The same byte-backed serializer chain is present in `CbsBasePei` and `AmdNbioSmuV10Pei`; an independent `AmdFabricAriPei` window emits `0x1374` and copies `[Setup+0x704]`.
- The exact ABL1 payload has a separate FCLK-named request path: selector `R1==0x0F` constructs descriptor halfwords `0x015F` and `0x0160`, calls generic reader `0x1FB4`, and writes the returned halfword through caller `R5`. The adjacent exact string is `"\n\tOverride Fclk: %d\n"` at payload `0x469C`.
- No byte-backed join was found between `$INV` IDs `0x1373/0x1374` and ABL1 descriptor keys `0x015F/0x0160` in this bounded trace. No MHz/unit conversion, FCLK/UCLK order comparison, Memory-P-state check, physical limit, runtime invocation, divider/PLL writer, or hardware effect is proven.

The native sentence **“When you try to override FCLK, please make sure FCLK > UCLK and Memory P-state is disabled.”** is confirmed as HII help text for QIDs `0x37D` (`+0x703`) and `0x37E` (`+0x704`). In the checked serializer and ABL1 FCLK windows, no executable `FCLK > UCLK` or Memory-P-state enforcement is observed. Global enforcement remains unresolved; the sentence cannot be promoted from guidance to code behavior.

## Pinned inputs and baseline

Target: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`

- Size: `16,777,216` bytes.
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- `AmdSetup` body base: `0x4CF`.
- Native memory request retained: `+0x316` at ROM `0x7E5` = `0x24` (IFR label `1800MHz`; stored enum, not a measured clock).
- DF control: `+0x703` at ROM `0xBD2` = `0x01` (`Manual`).
- DF value: `+0x704` at ROM `0xBD3..0xBD4` = bytes `8C 05`, u16 LE `1420` (stored request, not a measured clock).

Other exact inputs were hash-checked by the verifier:

- `CbsBasePei-6ff112922ad8.bin`: `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`.
- `AmdNbioSmuV10Pei-905b8be68afd.bin`: `905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80`.
- `AmdFabricAriPei-c5b99650a442.bin`: `c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78`.
- `ABL1-clv-decompressed.bin`: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- `ABL1-exact.o`: `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Existing HII result `evidence/firmware-audit/20260920-df-init-route/menu-result.json`: `6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a`.

## Exact static edges

### DF serializer: control and u16 request

The direct GNU `objdump` windows were run against existing extracted TE bodies. Address conversion is the retained TE mapping: raw offset = RVA minus `0x190` for `CbsBasePei`/`AmdNbioSmuV10Pei`, and minus `0x198` for `AmdFabricAriPei`.

`CbsBasePei`:

- RVA `0xE706`: `mov edx,0x1373`.
- RVA `0xE726`: `mov al,BYTE PTR [edx+0x703]`.
- RVA `0xE72C`: `mov BYTE PTR [ecx+0x3],al`.
- RVA `0xE738`: `mov edx,0x1374`.
- RVA `0xE74C`: type bits set with `or dl,0x1`.
- RVA `0xE75B`: `mov ax,WORD PTR [edx+0x704]`.
- RVA `0xE762`: `mov WORD PTR [ecx+0x3],ax`.
- RVA `0xE769`: record cursor advances by `0x5` bytes.

`AmdNbioSmuV10Pei` mirrors this at RVA `0x10786/0x107A6` and `0x107B8/0x107DB`; `AmdFabricAriPei` independently has `0x11C98: mov edx,0x1374`, `0x11CBB: mov ax,[edx+0x704]`, and `0x11CC2: mov [ecx+3],ax`.

These windows perform typed record construction only. They contain no arithmetic conversion, FCLK/UCLK comparison, Memory-P-state read, PLL/divider write, or direct port/MMIO operation.

### Separate exact ABL1 FCLK request path

At ABL1 payload `0x463C..0x4695`:

- `0x4648`: `cmp r1,#0xF`; all other selectors leave through `0x4684`.
- `0x464E`: `movw r0,#0x15F`, stored at `SP+0x10` (`0x4652`).
- `0x4656`: increments to `0x160`, stored at `SP+0x12` (`0x465E`).
- `0x466A`: `bl 0x1FB4` (generic reader).
- `0x4670`: loads returned halfword from `SP+0x8`.
- `0x4678`: ADR points to payload `0x469C`.
- `0x467E`: reloads returned halfword.
- `0x4682`: `str r0,[r5]`, through the caller-supplied output pointer.
- `0x469C`: exact bytes `0A 09 4F 76 65 72 72 69 64 65 20 46 63 6C 6B 3A 20 25 64 0A 00` (`"\n\tOverride Fclk: %d\n"`).

At `0x1FB4`, the generic reader calls helper `0x4800`; it loads the provider result from `SP+0x8`, accepts a type byte `1` in the first bounded branch, and otherwise dispatches typed-result handling. The provider/request-object provenance is not connected to `AmdSetup`/`$INV` by this test.

A separate ABL1 context consumer at `0x107E4` loads `[R4+0x78]`, compares raw values `0x3E8` at `0x107EC` and `0x4B0` at `0x107F2`, then selects callback codes. These constants have no established unit relation to `+0x704=1420` or to keys `0x015F/0x0160`.

## Enforcement, conversion, limits, runtime

| Question                                       | Result           | Evidence boundary                                                                                                                                                                                        |
| ---------------------------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Does `+0x703`/`+0x704` serialize?              | **PASS**         | Exact x86 bytes above; verifier anchors and decoded instruction bytes all match.                                                                                                                         |
| Is `+0x704` converted to MHz or a divider?     | **UNRESOLVED**   | Serializer copies raw u16; no conversion appears in the checked windows. No token-to-ABL1/PMFW join is proven.                                                                                           |
| Is `FCLK > UCLK` code-enforced here?           | **NOT OBSERVED** | HII text is present, but checked serializer/ABL1 FCLK windows compare selector/state values only; no FCLK-vs-UCLK compare. Global search/indirect runtime enforcement remains outside this bounded test. |
| Is Memory P-state disabled code-enforced here? | **NOT OBSERVED** | No Memory-P-state field read or branch occurs in the checked serializer/ABL1 FCLK windows. Global enforcement remains unresolved.                                                                        |
| Is `[0,2000]` a physical FCLK limit?           | **NO**           | It is exact IFR numeric metadata for QID `0x37E`, not a validated actuator or physical range.                                                                                                            |
| Is there a runtime consumer/clock writer?      | **UNRESOLVED**   | `$INV` receiver after serializer cursor advance is not joined to the ABL1 request/provider or PMFW actuator. No runtime/hardware action was performed.                                                   |

Prior static PMFW evidence maps an internal row/state path through `0x1E170`, `0x1E1D0`, `0x1E260`, and `0x1EF18` to firmware-visible apertures, but it does not establish that the CLV Setup tokens feed those rows or that the apertures are FCLK/UCLK/MCLK registers. That prior path remains a qualified lead, not a consumer result.

**First unresolved instruction boundary:** after the serializer emits typed `$INV` records and advances past record `0x1374`, the receiving/provider instruction that would consume `0x1373/0x1374` as the ABL1 FCLK keys `0x015F/0x0160` is not identified. Independently, ABL1 `0x1FB4 -> 0x4800` is the next provider/value-origin boundary. No frequency-unit conversion, physical limit, training relation, synchronization, or hardware behavior follows.

## Reproduction

New verifier (no new dependency):

```text
python3 -B evidence/firmware-audit/20260921-df-consumer-next/verify_df_consumer_trace.py
```

Literal final stdout:

```json
{
  "status": "PASS",
  "checks_passed": 34,
  "checks_failed": 0,
  "memory_request": "AmdSetup+0x316=0x24 (1800MHz label), preserved",
  "df_serializer": "AmdSetup+0x703 u8->$INV 0x1373; +0x704 u16 LE->$INV 0x1374",
  "fclk_path": "ABL1 0x463C -> descriptors 0x015F/0x0160 -> reader 0x1FB4 -> output [R5]",
  "help_text_enforcement": "NOT_OBSERVED_IN_CHECKED_PATHS; GLOBAL_ENFORCEMENT_UNRESOLVED",
  "first_unresolved": "token 0x1373/0x1374 receiver-to-ABL1 FCLK-key join; ABL1 helper/provider request data origin"
}
```

Observed final status: exit `0`; stderr empty. The initial corrected-test attempt is preserved: exit `1` after `31` checks, due solely to an incorrect expected ABL1 address (`0x1080A` instead of observed `0x107F2` for `cmp.w r0,#0x4B0`). The verifier was corrected and rerun; no input bytes changed.

Exact command/output artifacts are under:

`/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-df-consumer-next/`

- `verify_df_consumer_trace.py`
- `result.json`
- `commands.txt`
- `cbs_1373_1374.stdout/.stderr/.exit`
- `smu_1373_1374.stdout/.stderr/.exit`
- `fabric_1374.stdout/.stderr/.exit`
- `abl1_fclk_request_463c.stdout/.stderr/.exit`
- `abl1_generic_reader_1fb4.stdout/.stderr/.exit`
- `abl1_context_selector_107e4.stdout/.stderr/.exit`

No ROM, NVRAM, register, hardware, network, installation, candidate or shared memory change occurred. Hardware/runtime verification is **UNRUN**.
