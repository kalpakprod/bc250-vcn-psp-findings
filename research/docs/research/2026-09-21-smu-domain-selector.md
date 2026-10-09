# Queue 3 `0x1D` domain-selector to register boundary

## Conclusion

**PASS (observed-bytes + static-analysis; hardware unrun).** A fresh Ghidra 12.1.3 headless run on a copied exact Robin-5 project, with whole-program memory compared to the pinned CLV SMU body, establishes the previously missing selector bound and one complete selector-to-register path:

```text
Queue ID 3 / message 0x1D
  -> FUN_0002EA08: high16 selector 1..20; low16 request
  -> target[0x1402C + selector*12]
  -> FUN_0002E788 loop entry (selector-1)
  -> domain ID lookup at 0x13EF4 + (selector-1)*4
  -> domain descriptor at 0xF7A8 + domain_id*0x1C
  -> raw program offset at 0xF7BC + domain_id*0x1C
  -> FUN_00023890 -> FUN_000235C8
  -> SMU-window program/poll addresses
```

For selector `11`, the exact path is:

```text
selector 11 -> target/read slot 0x140B0
            -> domain ID 0x18
            -> internal Group 6
            -> raw program offset 0x6D150
            -> SMU-window program 0x0116D150
            -> poll 0x0116D174
```

The handler rejects mapped domain IDs `0x13` and `0x14` (selectors 12 and 13) with response data `0xFFFFFFFF` and status `1`; selector 14 maps domain `0x15` and passes those visible filters. The older `1..20` bound is therefore confirmed, not narrowed.

The low16 request is converted with `ufloat.s` immediate `0`, preserving its unsigned numeric magnitude. Later `FUN_0002E788` applies a literal `0.001f` through `0x23C78`, combines group U9.16 / `0.1f` / `256.0f` factors, and converts through the software float divider helper and `0x23ECC`. No explicit MHz label, physical clock name, or MCLK/UCLK/FCLK selector is encoded in this path. Do not infer MHz from round values.

## Bound object and evidence

- Exact plain CLV donor: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Embedded Robin-5 SMU: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`, 262,400 bytes, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`; byte-identical at ROM `0x8FEF00`.
- Preserved CLV request: `AmdSetup+0x316`, ROM `0x7E5`, raw `0x24` (`1800MHz` label).
- Ghidra: `/home/OWNER/tools/ghidra_12.1.3_PUBLIC/support/analyzeHeadless`, version `12.1.3`; copied OCConsumer project under `evidence/firmware-audit/20260921-smu-domain-selector/ghidra-project/`.
- Existing script reused unchanged: `evidence/firmware-audit/20260919-oc-final-consumer-pass/OcConsumerRead.java`, SHA-256 `e2cbf970afc422d31ee6651035a1f67132a5c4842801290fc3d60d5db408dd3b`.
- Action log: `docs/action-logs/2026-09-21-smu-domain-selector.md`.

The original OCConsumer project readback matched all copied source files; the source project `.gpr` and copied `.gpr` are both empty with SHA-256 `e3b0c442...`. No existing source, ROM, hardware, or shared report was modified.

## Exact selector and register derivation

### Handler filter and target write

Fresh aligned Ghidra rows, each byte-checked against the pinned body:

```text
0x2EA10  1C4C    movi.n a12,0x14
0x2EA14  A0A0F5  extui a10,a10,0x10,0x10
0x2EA17  A73C3F  bltu a12,a10,0x2EA5A
0x2EA1A  BCCA    beqz.n a10,0x2EA5A
0x2EA24  1C38    movi.n a8,0x13
0x2EA26  871B3A  beq a11,a8,0x2EA64
0x2EA29  C71B37  beq a11,a12,0x2EA64
0x2EA2F  30E0F4  extui a14,a3,0x0,0x10
0x2EA35  000EDA  ufloat.s f0,a14,0x0
0x2EA3B  034C50  ssi f0,a12,0x140
0x2EA41  65D4FF  call8 0x2E788
```

Thus `a12=0x14` bounds the high16 selector to `1..20`; a zero selector takes the status-`0xFF` path. The domain ID loaded from `0x13EF0 + selector*4` is independently compared against `0x13` and `0x14`, which are reject cases returning `0xFFFFFFFF` with status `1`.

For selector 11 (`loop_i=10`):

| Item                       |        Value |
| -------------------------- | -----------: |
| Target write and loop read |    `0x140B0` |
| Domain ID cell             |    `0x13F1C` |
| Domain ID                  |       `0x18` |
| Descriptor base            |     `0xFA48` |
| Internal group byte        |          `6` |
| Program pointer cell       |     `0xFA5C` |
| Raw program offset         |    `0x6D150` |
| SMU-window program         | `0x0116D150` |
| SMU-window poll            | `0x0116D174` |

`FUN_00023890` loads the descriptor's `+0x254` program offset and calls `FUN_000235C8`. `FUN_000235C8` uses mask literal `0x000FFFFF`, base literal `0x010FFE00` plus `0x200`, and second-core IPC bounds `0x5AFFF..0x5B7FF`. Selector 11's raw offset `0x6D150` is outside that IPC interval, so the observed path is the direct SMN-window store/poll path.

### Neighbor selectors

```text
selector 12 -> domain ID 0x13, Group 5, raw offset 0x6C900 -> handler rejects
selector 13 -> domain ID 0x14, Group 5, raw offset 0x6C928 -> handler rejects
selector 14 -> domain ID 0x15, Group 5, raw offset 0x6C950 -> visible filters pass
```

The dynamic Queue-3 ID array contains no direct DF-table descriptor IDs `0x0E..0x12` used by the separate raw Queue ID 4 P-state path. This is a namespace/selection observation, not a physical clock-domain naming proof.

## Request scaling boundary

The exact `FUN_0002E788`/helper listing establishes:

```text
0x2E7F6  l32r a8,0x18240
0x2E7F9  lsi f5,a2,0x14C
0x2E7FC  lsi f6,a8,0x0
0x2E7FF  mul.s f4,f5,f6
0x2E805  call8 0x23C78
0x2E821  call8 0x23890
```

Pinned literals show:

- `0x18240 -> 0x16F50 -> float 0.00100000005`;
- `0x17924 -> float 0.1`;
- `0x17928 -> float 256.0`;
- `0x17460 -> float 2^-16` for U9.16 decoding;
- `0x3ACF8` is a software floating divide routine;
- `0x23ECC` converts the resulting truncated value to an internal divider code.

These are firmware arithmetic constants, not enough to assign engineering units. The Group-6 static base word at `0xF718` is zero in the ROM image, so the runtime Group-6 coefficient remains unresolved; no numeric target is proposed.

## Physical-name search and bounded negative

A scoped exact-address search over local AMD BC250 docs, SMU sources, BC250 SMU API, and the retained address-bearing corpus found no symbol or source name for `0x0116D150`, `0x0116D1xx`, `0x0006D150`, or the related Group-6 program range. The prior hash-pinned Robin-3 slot map independently records slot 24 as domain index 6 / raw `0x6D150`, but its `semantic_name` is explicitly `null` and it is not exact Robin-5 physical-name authority.

The result is therefore a bounded negative: **internal Group 6 and SMN offsets are proven; physical MCLK/UCLK/FCLK/VCN naming is not recovered.** No hardware measurement, register read/write, mailbox command, or emulator execution occurred.

## Execution ledger

Fresh Ghidra command:

```text
/home/OWNER/tools/ghidra_12.1.3_PUBLIC/support/analyzeHeadless \
  evidence/firmware-audit/20260921-smu-domain-selector/ghidra-project OCConsumer \
  -process smu_fw_robin_5 -noanalysis \
  -scriptPath evidence/firmware-audit/20260919-oc-final-consumer-pass \
  -postScript OcConsumerRead.java \
  archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5 \
  evidence/firmware-audit/20260921-smu-domain-selector/q3-aligned-ghidra.txt \
  0x2ea08 0x2e788 0x23890 0x235c8 0x23c78 0x23ecc 0x3acf8
```

- Ghidra process exit: `0`.
- `q3-aligned-ghidra.txt`: SHA-256 `6c6816365ce7b9febf374a092908f3b88033cb3c7a4b2111490c3d458b62af52`; 301 listed instructions byte-matched.
- `direct-selector-measurements.txt`: SHA-256 `a50af42fce3ff8b6483b8a454c13b38595c1553dab524f415744569c7db55361`; exit `0`, stderr empty.
- `register-symbol-search.stdout`: empty, SHA-256 `e3b0c442...`; exit `1` means grep no-match only.
- Prior slot map: `evidence/firmware-audit/20260914-smu-address-trace/slot-domain-map.json`, SHA-256 `58a7042c863767db9f817b8b129f7cf440eaea732c9e195e7383871f55293dce`.

Three verifier-fixture failures are preserved in the action log. Per G6, no further reruns of that assertion harness were made after the third same-class failure; the final result uses direct exact Ghidra listing and arithmetic readback instead.

## First unresolved boundary

The next missing edge is the physical meaning of internal Group 6 / raw `0x6D150` and the runtime value of its group-base coefficient. Specifically unresolved:

1. whether `0x0116D150/174` controls MCLK, UCLK, FCLK, VCN, or another clock;
2. the external unit represented after the `0.001f`, U9.16, `0.1f`, and `256.0f` arithmetic;
3. the caller/provider that supplies Queue-3 requests and any native `AmdSetup`/ABL1/APOB join;
4. whether the internal divider code corresponds to a physical frequency or merely a firmware state.

No MHz, synchronization, or hardware claim follows. The `1800MHz` Setup byte remains preserved metadata only.

## Artifacts

- Report: `docs/research/2026-09-21-smu-domain-selector.md`
- Action log: `docs/action-logs/2026-09-21-smu-domain-selector.md`
- Evidence directory: `evidence/firmware-audit/20260921-smu-domain-selector/`
- No firmware, hardware, mailbox, NVRAM, network, or ROM write.
