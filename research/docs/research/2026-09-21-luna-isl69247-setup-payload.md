# ISL69247 BIOS Setup payload and fixed page sequencing

Date: 2026-09-21 (Asia/Almaty)
Scope: exact CLV `ISL69247` PEIM disassembly only. Determine whether VCORE/GFX Setup u16 values are transformed before mailbox staging, and whether command/register `0x21` is selected on page 0/1 conditionally or through fixed sequencing. Do not equate register indices with physical PMBus semantics or rail voltage without hardware evidence.

## Conclusion

**The Setup VCORE/GFX u16 is preserved numerically in the decoded firmware path; no scale, offset, divider, multiply, or unit conversion is observed before the mailbox byte split.**

- VCORE stored Setup offset `0x1CA` is loaded with `movzx eax, WORD PTR [ebp+0x52]` at RVA `0x314`, then copied directly to `[ebp+0x74]` at `0x318`.
- GFX stored Setup offset `0x1CE` is loaded with `movzx eax, WORD PTR [ebp+0x56]` at `0x3B2`, then copied directly to `[ebp+0x74]` at `0x3B6`.
- The only transformation in these instructions is zero-extension from u16 to the 32-bit local. The common helper `0x6ED` takes the local pointer in `EDI`, stages byte 0 to mailbox `0x70` and byte 1 to mailbox `0x71`, preserving little-endian 16-bit representation. It does not perform arithmetic.
- The `Fix Voltage` flag changes **which value** reaches command `0x21`: nonzero flag → stored Setup u16; zero flag → default `0x384` (900 decimal) in both VCORE and GFX paths. Both arms still call the same write helper.

**Page sequencing is fixed, not selected conditionally by the Setup value.** The PEIM calls helper `0x5D3` unconditionally with page payload `0` before the VCORE block, then unconditionally with page payload `1` before the GFX block. Helper `0x5D3` stages target command/index `0x00` and the one-byte payload through the mailbox. The command `0x21` write follows each fixed page selection. There is no branch on page value or on VCORE/GFX flag guarding the page-select calls in this bounded entry function.

This is `static-analysis` over `observed-bytes`, not proof that `0x00` is a PMBus PAGE command, `0x21` is VOUT_COMMAND, or Setup values are physical mV at the controller. The prior report's labels “page/rail select” and “register 0x21 (mV)” are useful hypotheses/inference, not hardware-verified semantics. No voltage is recommended.

## Exact pinned input and evidence

- Immutable CLV donor identity retained by prior evidence: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Independent extracted TE disassembly: `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/ISL69247.disasm.txt`, SHA-256 `cb15e09a6b7c35bb6dff13c40f61b3b076c999f3ce60c62b99476bbb1db34aab`.
- Machine result from independent decoder: `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/independent-decode-result.json`, SHA-256 `3da15d4a281cbbd3d5c05f97e3ea74cdaea547d6114503af1bbd29c55785fe3f`.
- Independent decoder report: `docs/research/2026-09-20-fixed-voltage-independent-decode.md`, SHA-256 before this task `a3b3cb0f90a392cb3be97a305a310ed3b23d5c3405ecfdc99d7cda810f071edd`.
- Existing fixed-voltage consumer report: `docs/research/2026-09-20-clv-fixed-voltage-consumer.md`, SHA-256 before this task `6bb851ec32ec8fe963bf50e4070563944bf98c2657a703d2fd696ce960bb3791`.

## Decoded flow and values

### Setup read and defaults

The PEIM reads the 0x1D3-byte `Setup` variable into a stack buffer (`ISL69247.disasm.txt:0x2A2`, `0x2C1-0x2DB`). Before the variable call, the decoded defaults include:

- `EBX=0` at `0x27C`; VCORE/GFX fixed-voltage enable bytes are initialized to zero at `0x2A9` and `0x2B0`.
- `ESI=0x384` at `0x287`; VCORE/GFX default voltage words are initialized to `0x384` at `0x28F`/`0x293`.
- VCORE/GFX loadline selector bytes default to `2` at `0x2AC`/`0x2B3`.

The Setup fields used by the two VOUT blocks are:

| Function                 | Setup offset | Local slot   | Enabled path        | Disabled path   |
| ------------------------ | -----------: | ------------ | ------------------- | --------------- |
| VCORE fixed-voltage flag |      `0x1C9` | `[ebp+0x51]` | selects stored word | default path    |
| VCORE voltage word       |      `0x1CA` | `[ebp+0x52]` | `movzx` u16 → local | default `0x384` |
| GFX fixed-voltage flag   |      `0x1CD` | `[ebp+0x55]` | selects stored word | default path    |
| GFX voltage word         |      `0x1CE` | `[ebp+0x56]` | `movzx` u16 → local | default `0x384` |

### VCORE: fixed page-0 sequence and value branch

At `0x2F6-0x2FD`, the code sets `[ebp+0x73]=0` and calls helper `0x5D3`. The helper body (`0x5D3-0x64E`) stages:

- `0x65 <- 0xC0`;
- `0x66 <- 0x00` (target command/index);
- low byte of the helper's page pointer (`0`) to `0x70`;
- `0x63 <- 0x02`, `0x60 <- 0xC0`, then polls status through the same mailbox transport.

At `0x30A-0x33E`:

1. The target command/index `0x21` is pushed before the flag test (`0x30A`).
2. The corrected enable test is `cmp BYTE PTR [ebp+0x51], bl` at `0x30F`, with `BL=0` from `0x27C`.
3. If VCORE Fix Voltage is nonzero, `movzx eax, WORD PTR [ebp+0x52]` (`0x314`) and `mov DWORD PTR [ebp+0x74], eax` (`0x318`) copy the stored Setup u16 without arithmetic; helper `0x6ED` is called at `0x31B`.
4. If the flag is zero, control jumps to `0x33B`; `ESI` is still the earlier `0x384`, and `mov DWORD PTR [ebp+0x74], esi` supplies the default 900 decimal; helper `0x6ED` is called at `0x33E`.
5. The following `0x23`, `0xF0`, `0x28`, `0xC7`, and `0xC5` operations configure other values; they do not transform the VOUT word before the `0x21` call.

### GFX: fixed page-1 sequence and value branch

At `0x39A-0x3A2`, the code sets `[ebp+0x73]=1` and calls the same helper `0x5D3`, before the GFX block. At `0x3A8-0x3DB`:

1. Target command/index `0x21` is pushed at `0x3A8`.
2. The corrected enable test is `cmp BYTE PTR [ebp+0x55], bl` at `0x3AD`.
3. If GFX Fix Voltage is nonzero, `movzx eax, WORD PTR [ebp+0x56]` (`0x3B2`) and `mov DWORD PTR [ebp+0x74], eax` (`0x3B6`) copy the stored Setup u16; helper `0x6ED` is called at `0x3B9`.
4. If the flag is zero, `mov DWORD PTR [ebp+0x74], 0x384` at `0x3D4` supplies the default; helper `0x6ED` is called at `0x3DB`.
5. The GFX loadline/configuration operations follow and do not scale the VOUT word before the `0x21` helper call.

### Shared write helper: byte preservation

`0x6ED` (`ISL69247.disasm.txt:0x6ED-0x776`) receives the target register/index as the caller stack word and uses `EDI` as the pointer to the prepared payload local:

- `0x6FE`: `push DWORD PTR [esp+0x14]` and `0x702`: `push 0x66` pass the caller's target command/index to the lower mailbox writer.
- `0x709`: `movzx eax, BYTE PTR [edi]`; `0x70D`: `push 0x70`; the low payload byte is staged to mailbox register `0x70`.
- `0x714`: `movzx eax, BYTE PTR [edi+0x1]`; `0x719`: `push 0x71`; the high payload byte is staged to mailbox register `0x71`.
- `0x720-0x72E`: `0x63 <- 0x03` and `0x60 <- 0xC0` trigger the mailbox transaction, followed by status polling and completion value `0x08`.

The helper's byte split means a stored Setup word `W` is staged as `W & 0xFF` at `0x70` and `(W >> 8) & 0xFF` at `0x71`. This is a representation statement derived from instructions, not a voltage-unit statement. For example, the code path would preserve `0x0480` as bytes `0x80,0x04`; this example is a host-side arithmetic illustration, not a board read/write or recommendation.

## Answer to the page/conditional question

- **Page-select command/index `0x00`:** fixed sequence, page payload `0` then page payload `1`; helper calls at `0x2FD` and `0x3A2` are not conditional on VCORE/GFX fixed-voltage flags.
- **VOUT-like command/index `0x21`:** one call in each page block, and both flag outcomes call it. The flag only chooses stored Setup u16 versus default `0x384`; it does not choose page 0 versus page 1.
- **Observed conditionality:** Setup `0x1C9` controls VCORE value selection; Setup `0x1CD` controls GFX value selection. Loadline selectors `0x1CC`/`0x1D0` independently index a table and configure command `0x28`.
- **Not observed:** any arithmetic scaling from Setup u16 to the `0x21` mailbox payload, a conditional page branch, a decoded physical rail identity, PMBus page semantics, or a physical voltage.

## Limits and evidence class

- `observed-bytes`: exact disassembly bytes, instruction addresses, donor/module hashes, and machine result hashes.
- `static-analysis`: control-flow interpretation of the VCORE/GFX branches and helpers.
- Not established: PEIM dispatch on a live boot, execution of the Setup path, mailbox controller identity, PMBus register semantics, whether register `0x21` is a VOUT command on this hardware, physical rail identity, raw-to-mV mapping at the controller, applied voltage, thermal/current margin, or safety.
- No BIOS image, NVRAM variable, firmware, I/O port, SMBus/I2C bus, register, or hardware state was modified or read.
