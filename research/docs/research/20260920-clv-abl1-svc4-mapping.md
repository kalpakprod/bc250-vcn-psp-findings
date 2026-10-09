# Exact CLV ABL1 SVC#4 mapping and address-space boundary

## Current

The exact CLV ABL1 helpers at payload offsets `0x6DA4` (read) and `0x6E70` (write) are not descriptor-only stack/object-field operations. Their observed caller contract is an SMN-page mapping sequence: split an encoded address into a 4-KiB-aligned high part and a low 12-bit offset, invoke `SVC #4`, use the returned `R0` as a mapped base, access `mapped + offset`, then invoke `SVC #5` with that returned base. The physical map/window destination and the on-die SVC handler remain unavailable in the BIOS image.

This resolves the service at the **caller-contract/static-analysis level**, not as a physical register or hardware claim.

## Exact input, ISA, and base

- Exact CLV ABL1 decompressed payload: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing: `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- ISA: little-endian ARM Thumb-2. All function addresses below are payload-relative offsets. The exact `$PS1` header records `load_address=0`; no nonzero execution base is assumed.
- The version-aligned historical source lead is `archives/imported/recon-evidence/legacy-tmp-bc250-recon/lorek123_psp/ABL1_decompiled.c`, SHA-256 `9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b`. It is not treated as a source-to-binary identity proof.

## Exact read helper `0x6DA4`

The current exact bytes and listing show:

|   Offset | Observed operation   | Effect                                              |
| -------: | -------------------- | --------------------------------------------------- |
| `0x6DCC` | `LSRS R0,R6,#0xC`    | prepare high address selector                       |
| `0x6DCE` | `UBFX R4,R6,#0,#0xC` | retain low 12-bit offset                            |
| `0x6DD2` | `LSLS R0,R0,#0xC`    | restore 4-KiB-aligned selector                      |
| `0x6DD4` | `SVC #4`             | request mapping; handler return is in `R0`          |
| `0x6DD8` | `MOV R6,R0`          | retain returned mapped base                         |
| `0x6E1A` | `LDR R3,[R6,R4]`     | type `R0=3` word read from mapped window            |
| `0x6E1E` | `STR R3,[R5]`        | copy read word to caller output pointer             |
| `0x6DFC` | `SVC #5`             | paired post-access service with mapped base in `R0` |

The helper's input shape is `R0=width/type`, `R1=encoded address`, and `R2=output pointer`; the prologue preserves the address in `R6` and output pointer in `R5`. The normal target path reaches it with type `3`.

## Exact write helper `0x6E70`

|   Offset | Observed operation   | Effect                                              |
| -------: | -------------------- | --------------------------------------------------- |
| `0x6EA6` | `LSRS R0,R5,#0xC`    | prepare high address selector                       |
| `0x6EA8` | `UBFX R6,R5,#0,#0xC` | retain low 12-bit offset                            |
| `0x6EAC` | `LSLS R0,R0,#0xC`    | restore 4-KiB-aligned selector                      |
| `0x6EAE` | `SVC #4`             | request mapping; handler return is in `R0`          |
| `0x6EB2` | `MOV R5,R0`          | retain returned mapped base                         |
| `0x6EE6` | `LDR R0,[R4]`        | load caller value for type `R0=3`                   |
| `0x6EE8` | `STR R0,[R5,R6]`     | word store to mapped window plus offset             |
| `0x6ED6` | `SVC #5`             | paired post-access service with mapped base in `R0` |

The write helper's input shape is `R0=width/type`, `R1=encoded address`, and `R2=value pointer`.

## SMN classification and structural source cross-check

The exact current ABL1 payload contains the strings:

- `~SMN R [0x%0x]` at payload `0x6E26`;
- `~SMN BW [0x%0x] = 0x%0x` at payload `0x6EF2`;
- `~SMN W [0x%0x] = 0x%0x` at payload `0x6F0E`;
- width diagnostics `0x%02x (8b)`, `0x%04x (16b)`, and `0x%08x (32b)`.

The version-aligned local decompilation labels the corresponding wrappers `FUN_00006EA4` (read) and `FUN_00006F70` (write), explicitly masks `param_2` as:

```c
uVar2 = param_2 & 0xfff;
param_2 = param_2 & 0xfffff000;
software_interrupt(4);
/* access param_2 + uVar2 */
software_interrupt(5);
```

It names the logging path `SMN R`, `SMN BW`, and `SMN W`. The current exact code entry is offset `-0x100` from the historical source label (`0x6DA4` vs `0x6EA4`); the corresponding current string locations are `-0xFE` (`0x6E26` vs source `0x6F24`, and `0x6F0E` vs source `0x700C`). These are structural alignment observations only. The current raw bytes, not the historical source, establish the operations above.

## Service/address-space conclusion

### SVC#4 — resolved caller contract

`SVC #4` is the map service used by these ABL1 SMN access wrappers. The caller supplies the high, 4-KiB-aligned portion of an encoded SMN address in `R0`; the low 12 bits remain in a caller register; the service returns a base in `R0`; and the caller accesses `R0 + low12`. Therefore the post-SVC memory operation is through a PSP-accessible mapped window, not directly through the descriptor object or stack frame.

This is enough to distinguish the target callback's normal path from a descriptor-only RMW: `0x6DA4` obtains a mapped word, the callback performs its local field merge, and `0x6E70` can write a mapped word back. It does **not** identify the selected SMN page or a physical register.

### SVC#5 — paired cleanup, handler unavailable

Both wrappers pass the SVC#4-returned base to `SVC #5` after the access. Release/unmap/cleanup is the strongly indicated role from this exact call shape, but the handler body is unavailable and the precise semantics are not claimed as observed.

### Missing handler boundary

The exact on-die PSP ROM SVC vector, handler body, and translation table are not part of the extracted BIOS ABL1/TOS images. The hash-pinned CLV type-`0x45` TOS security-policy body (`1504` bytes, SHA-256 `bafe168f7718e7729061ee2469a4871e3a237c9e22746175a920d3c60a75850b`) occurs at ROM offset `0x9CAC00` and contains no `DF 04` SVC#4 instruction. It therefore does not provide the missing SVC#4 handler; its absence is not evidence that the on-die handler does not exist.

## Target callback effect and limits

At target callback call sites, `0x9C2A` calls `0x6DA4` with type `3`, output `SP+0x14`, and descriptor candidate in `R1`; the high-index path at `0x9D96` calls `0x6E70` with type `3`, value pointer `SP+0x14`, and descriptor candidate in `R1`. This proves the candidate can participate in a mapped-register field read/modify/write sequence if its runtime context and descriptor are the active ones.

It does not prove:

- the active dispatcher object equals the initializer object;
- the runtime descriptor value selects an SMN address rather than another valid map class;
- the physical SMN/MMIO register, bridge, PLL, clock domain, units, or synchronization behavior;
- any hardware effect or `MCLK=UCLK=FCLK` relation.

The evidence class is **observed-bytes + static-analysis**. No firmware, hardware, ROM, settings, or global configuration changed.

## Reproduction and artifacts

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verify_svc4_mapping.py \
  > /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stdout \
  2> /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stderr
```

Observed: exit `0`; stdout status `PASS`, `59` checks; stderr empty.

- Machine result: `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/svc4-mapping-result.json`, SHA-256 `4b9fa6b22d418ee31f284025d2d5f84931e56d222a32e37cfd5d69e08ac39cf0`.
- Verifier: `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verify_svc4_mapping.py`, SHA-256 `f6973f508c66ffdd1c0c534b1be898a6302a56749cf48a3d394f93deb5003da7`.
- Literal stdout: `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stdout`, SHA-256 `4b9fa6b22d418ee31f284025d2d5f84931e56d222a32e37cfd5d69e08ac39cf0`.
- Literal stderr: `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verifier.stderr`, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Action log: `docs/action-logs/2026-09-20-clv-abl1-svc4-mapping.md`.

## Final boundary

**Resolved:** SVC#4 is the caller-visible SMN-page map operation returning a mapped base used with a 12-bit offset; the exact code path is mapped-register access, not a descriptor-only field RMW.

**Unavailable:** the on-die handler, translation-table destination, runtime descriptor/active binding, and physical register/clock semantics. The next decisive evidence would be an authorized PSP-ROM-level SVC handler recovery or an execution trace that captures the encoded descriptor and returned mapped base.
