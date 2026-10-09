# PMFW Queue3 domain/request trace — independent unit and selector review

## Conclusion

**Accepted, narrowly:** for Queue 3 message `0x1D`, the exact static path extracts the mailbox argument's low 16 bits, applies `ufloat.s` with its scale immediate set to zero, and stores that numeric value as a single-precision float in the indexed target array. The local Xtensa SLEIGH semantics define `ufloat.s` as `float(zext(A)) / 2^imm`; here `imm=0`, so this conversion preserves the low-16 numeric magnitude. This is a numeric conversion result, **not a physical unit**.

**Rejected:** neither this conversion nor the selectors in Queue 3 `0x1D` / raw Queue ID 4 message `0x07` identifies an input as physical `MCLK`, `UCLK`, or `FCLK`; proves a value is MHz; or establishes `MCLK:UCLK:FCLK=1:1:1`.

The Queue 3 high 16 bits are a **1-based index** (checked as 1..20) used to fetch a separate domain ID from a runtime table. The low 16 bits are a request value. The Queue ID 4 `0x07` path uses a selector word with high byte mode `0x01` and low byte P-state index, then consumes a static row from the DF-related table at `0xCF0C`. No trace in this evidence maps the domain IDs or table columns to the board's physical memory/UCLK/FCLK clock trees or a crossing/divider selector. The existing result correctly leaves these identities and the provider/caller join unresolved.

Evidence class: exact `observed-bytes` + existing `static-analysis`; a bounded `emulated-or-host-tested` numerical model of the documented SLEIGH conversion formula. **The extracted SMU helper itself was not executed** and there was no hardware, register, mailbox, NVRAM, or physical-clock measurement.

## Bound inputs and provenance

| Input                                                                                                                             | Identity                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plain CLV donor ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`                                                         | 16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`                                                                                                                                                                                               |
| Robin-5 PMFW body `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` | 262,400 bytes; SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`; byte-equal to CLV ROM slice at `0x8FEF00` in the retained verifier                                                                                                                    |
| Existing completed trace                                                                                                          | `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py`, SHA-256 `540e8be034cdbdc8a42f63d504c2a3d4c42e7ad4feabd9e8ad9bdfec59afe233`                                                                                                         |
| Existing trace result                                                                                                             | `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/source-consumer-result.json`, SHA-256 `08a30b4bc9f7153ff81f532ebf5203d355f27840c3aca59e58a51797b50f7b63`                                                                                                    |
| Existing exact disassembly                                                                                                        | `evidence/firmware-audit/20260919-oc-clock-provenance/ghidra-decompiles.txt`, SHA-256 `5f1f963f7139754e005b0bfb66a296a4a362b9b80f0e3d12591a471e54650112`                                                                                                                         |
| Prior byte verifier/result                                                                                                        | `evidence/firmware-audit/20260921-smu-clock-entrypoints-next/verify-clock-handlers.py` SHA-256 `620a4cf9b198c23a17b86712d2ecfc01601e899457104e77d77d8bd55e12fc79`; `clock-handlers-verification.json` SHA-256 `eb8f41d575ef1e931b96240054bad4271c03a90055dd311ae463a3b2b5363ffa` |
| Local instruction-semantics reference                                                                                             | `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/ghidra/xtensaInstructions.sinc`, SHA-256 `93b33680e0a1eeb844f632401d7374479a008ed5e2240e5b10b7d60cb1acf1c6`; repository commit `3f47768eace8ad8ad86c480a55637d14467cffcd`               |

The local SLEIGH file has a pre-existing working-tree modification flag, but `git diff --ignore-space-at-eol -- ghidra/xtensaInstructions.sinc` is empty and the `UFLOAT.S` block hashes identically to the committed version (`f1953913725dce53e3b40f43de37697829e711a8d61b57698d639c61d8829ebd`). I did not edit it. This source is used as a local instruction-semantics reference, not adopted as a dependency or treated as a hardware authority.

## Existing verifier execution, not restarted

The continuation log `docs/action-logs/2026-09-21-smu-clock-entrypoints-continuation.md` binds the existing command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py
```

That existing script was run once in a **disposable mirror** with the same input identities; its output directory was the copied evidence directory under `/tmp/bc250-smu-domain-review-aj32__3z/project/`. It was not run against or allowed to overwrite the project evidence directory.

The recorded template includes `PYTHONDONTWRITEBYTECODE=1`; the observed disposable invocation was:

```text
python3 -B /tmp/bc250-smu-domain-review-aj32__3z/project/evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py
```

`-B` retains the bytecode-write suppression while the script/output identity points into the disposable copy.

Observed event:

```text
EXIT_STATUS: 0
STDOUT_BEGIN
{"checks": 25, "preserved_clv_request": {"AmdSetup_offset": "0x316", "byte": "0x24", "label": "1800MHz", "rom_offset": "0x7E5"}, "pstate3": {"row": "0xCF84", "stored_plus_0x04": 1200.0, "stored_plus_0x10": 875.0, "stored_plus_0x14": 109.375, "stored_plus_0x18": 1750.0}, "source_edges": {"q3_0x1d": {"bulk_source": "0x2E9DC reads 0x7B5C+pstate*100+0x48 -> 0x14038", "consumer": "0x2E788 -> 0x23890 -> 0x235C8", "handler": "0x2EA08", "mailbox": "Queue ID 3 msg 0x1D", "setup_join": "not observed", "target_source": "low16 mailbox arg -> ufloat.s -> 0x1402C+index*12", "unit": "raw unsigned integer; no MHz/divider scale encoded"}, "q4_0x07": {"consumer": "0x23B7C/0x23BA8/0x23BF4 -> 0x23F18", "dispatch": "0x79E8/0x79EC", "handler": "0x1E720 -> 0x1E448", "mailbox": "raw Queue ID 4 msg 0x07", "selector": "high byte mode 0x01, low byte pstate index", "setup_join": "not observed", "table": "0xCF0C, 5 rows x 0x28", "unit": "fixed-point/DID arithmetic reproduces numeric stored floats; physical MHz identity unresolved"}}, "status": "PASS", "unresolved": "provider/caller join from native AmdSetup/ABL1/APOB to mailbox args; physical MCLK/UCLK/FCLK assignment and crossing selector"}
STDOUT_END
STDERR_BEGIN
STDERR_END
```

The retained and regenerated result files both hash to `08a30b4bc9f7153ff81f532ebf5203d355f27840c3aca59e58a51797b50f7b63`. This is a reproducibility check of the existing static verifier, not a new full-firmware consumer census.

## Semantics review

### Queue 3 request value

Existing disassembly has this local sequence:

```text
0002ea2f 30e0f4 extui a14,a3,0x0,0x10   ; low 16 bits of argument
0002ea35 000eda ufloat.s f0,a14,0x0    ; unsigned fixed -> single, fractional scale 0
0002ea38 d0cca0 addx4 a12,a12,a13       ; indexed state/target structure
0002ea3b 034c50 ssi f0,a12,0x140       ; store target float
```

The checked instruction semantics in the local Ghidra SLEIGH definition are:

```text
UFLOAT.S: tmp = zext(A); scale = 1 << immediate; F = int2float(tmp) / int2float(scale)
```

With immediate `0`, the scale is `1`. Therefore the low-16 request `0x0708` is represented as float `1800.0`; that conversion supplies no MHz annotation or clock-domain name. The helper then calls generic state/actuation paths; their later engineering-unit interpretation is outside this conversion slice.

### Queue 3 index and Queue ID 4 selector

- Queue 3 `0x1D`: high 16 bits produce a 1-based index; the code loads an ID from `0x13EF0 + index*4`, stores the request float at `0x1402C + index*12`, and calls the shared actuator loop. A numeric index and a lookup in a runtime domain-ID table are not a physical clock identity until the table entries are mapped to named physical domains.
- Queue ID 4 `0x07`: the decoded handler splits the selector into the high byte (mode; mode `0x01` branch) and low byte (P-state index), then reaches `0x1E448` and table `0xCF0C`. This is a P-state/table selector in the checked path, not a direct MCLK/UCLK/FCLK identity selector or synchronous-crossing status read.
- CLV `AmdSetup+0x316=0x24` at ROM `0x7E5` remains an observed stored request with the menu label `1800MHz`. This trace does not connect that Setup byte to either mailbox argument, prove the SMU received it, or measure a physical rate.

### Bounded host semantics test

No existing Xtensa executor was available in the bounded environment inventory: `qemu-system-xtensa`, `qemu-system-xtensaeb`, `qemu-xtensa`, `unicorn`, `pypcode`, `angr`, `capstone`, `rizin`, `rz-bin`, and `analyzeHeadless` were not available. The Ghidra MCP session reported the loaded program `/bin/true`, architecture `x86:LE:64`, and its exposed tools provide disassembly/P-code but no execution endpoint for this Xtensa image. Therefore this review did **not** claim an emulation of the extracted PMFW helper.

Observed bounded capability-check output:

```text
BIN qemu-system-xtensa: NOT_FOUND
BIN qemu-system-xtensaeb: NOT_FOUND
BIN qemu-xtensa: NOT_FOUND
BIN rizin: NOT_FOUND
BIN rz-bin: NOT_FOUND
BIN analyzeHeadless: NOT_FOUND
MODULE unicorn: NOT_FOUND
MODULE pypcode: NOT_FOUND
MODULE angr: NOT_FOUND
MODULE capstone: NOT_FOUND
```

Ghidra MCP metadata observed in this session:

```text
Program Name: true
Executable Path: /bin/true
Architecture: x86
Compiler: gcc
Language: x86:LE:64:default
Endian: Little
Address Size: 64 bits
```

Instead, a bounded host model applied the locally checked SLEIGH equation with immediate zero to representative inputs and tested the selector bit split. This verifies the mathematical implication of the conversion definition for the checked operands; it is not firmware execution.

Exact command:

```text
python3 -B - <<'PY'
from pathlib import Path
import hashlib,struct,sys
root=Path('/home/OWNER/orca/projects/bc250')
repo=root/'archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering'
spec=repo/'ghidra/xtensaInstructions.sinc'
listing=root/'evidence/firmware-audit/20260919-oc-clock-provenance/ghidra-decompiles.txt'
body=repo/'smu_fw/smu_fw_robin_5'
result=root/'evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/source-consumer-result.json'
s=spec.read_text(); d=listing.read_text(); r=result.read_text()
expected='''# UFLOAT.S - Convert Unsigned Fixed to Single, pg. 550.\n:ufloat.s fr, as, u4_4_7 is op2 = 0b1101 & op1 = 0b1010 & fr & as & u4_4_7 & op0 = 0 {\n\tlocal tmp:8 = zext(as);\n\tlocal scale:4 = 1 << u4_4_7;\n\tfr = int2float(tmp) f/ int2float(scale);\n}'''
assert expected in s
assert hashlib.sha256(body.read_bytes()).hexdigest()=='cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
assert '0002ea2f 30e0f4 extui a14,a3,0x0,0x10' in d
assert '0002ea35 000eda ufloat.s f0,a14,0x0' in d
assert '0002ea3b 034c50 ssi f0,a12,0x140' in d
assert '0001e74c 30a874 extui a10,a3,0x8,0x8' in d
assert '0001e755 661a1b bnei a10,0x1,0x0001e774' in d
assert '0001e75b 324416 s8i a3,a4,0x16' in d
assert 'high byte mode 0x01, low byte pstate index' in r
cases=[]
for n in (0,1,109,875,1200,1750,1800,65535):
    fp=struct.unpack('<f',struct.pack('<f',float(n)/(1<<0)))[0]
    assert fp==float(n)
    cases.append((n,fp))
arg=(1<<16)|1800
index=(arg>>16)&0xffff; request=arg&0xffff
assert (index,request)==(1,1800) and 1<=index<=20
sel=(1<<8)|3
mode=(sel>>8)&0xff; pstate=sel&0xff
assert (mode,pstate)==(1,3)
print('LOCAL_SLEIGH_SEMANTICS: ufloat.s -> int2float(zext(A)) / int2float(1<<imm)')
print('OPERAND_IMMEDIATE: 0; FRACTIONAL_SCALE: 1; MODELLED_OUTPUT: unsigned low16 unchanged as binary32')
for n,fp in cases: print(f'HOST_MODEL u16=0x{n:04X} -> f32={fp:.1f}')
print(f'Q3_WORD 0x{arg:08X} -> domain_index={index}, raw_request={request} (domain ID is loaded from a separate table)')
print(f'Q4_WORD 0x{sel:04X} -> mode=0x{mode:02X}, pstate_index={pstate}')
print('INFERENCE: units and physical MCLK/UCLK/FCLK identities are not encoded by these conversions/selectors')
print('LIMIT: host semantic model, not Xtensa instruction execution or hardware measurement')
print('SUMMARY: 8/8 conversion cases + 2 selector cases PASS; exit=0')
PY
```

Literal output:

```text
LOCAL_SLEIGH_SEMANTICS: ufloat.s -> int2float(zext(A)) / int2float(1<<imm)
OPERAND_IMMEDIATE: 0; FRACTIONAL_SCALE: 1; MODELLED_OUTPUT: unsigned low16 unchanged as binary32
HOST_MODEL u16=0x0000 -> f32=0.0
HOST_MODEL u16=0x0001 -> f32=1.0
HOST_MODEL u16=0x006D -> f32=109.0
HOST_MODEL u16=0x036B -> f32=875.0
HOST_MODEL u16=0x04B0 -> f32=1200.0
HOST_MODEL u16=0x06D6 -> f32=1750.0
HOST_MODEL u16=0x0708 -> f32=1800.0
HOST_MODEL u16=0xFFFF -> f32=65535.0
Q3_WORD 0x00010708 -> domain_index=1, raw_request=1800 (domain ID is loaded from a separate table)
Q4_WORD 0x0103 -> mode=0x01, pstate_index=3
INFERENCE: units and physical MCLK/UCLK/FCLK identities are not encoded by these conversions/selectors
LIMIT: host semantic model, not Xtensa instruction execution or hardware measurement
SUMMARY: 8/8 conversion cases + 2 selector cases PASS; exit=0
```

The reported command execution also returned process exit code `0` and empty stderr.

## Adjudication and limits

| Inference                                                                                         | Decision                                          | Evidence boundary                                                                                                               |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `ufloat.s` converts the low-16 request to a numerically equal float when immediate is zero        | **Accepted statically; host-model sanity passed** | Exact disassembly + local SLEIGH semantics + bounded IEEE-754 host model. Not an execution of the SMU binary.                   |
| The value has units of MHz                                                                        | **Rejected / unproven**                           | Neither opcode nor observed caller gives an engineering unit; scaling/interpretation in downstream actuator code is unresolved. |
| Queue 3 high-16 index names MCLK/UCLK/FCLK                                                        | **Rejected / unproven**                           | It is an array index followed by an ID lookup; physical-domain mapping is not supplied by this trace.                           |
| Queue ID 4 message `0x07` mode/P-state selector establishes FCLK identity or synchronous crossing | **Rejected / unproven**                           | It selects mode/P-state row; no physical clock name, common counter, divider state, or crossing-status observation is present.  |
| CLV stored request `0x24` proves a physical 1800 MHz clock or 1:1:1                               | **Rejected**                                      | Stored IFR-labelled byte only; no Setup→mailbox argument join or board measurement.                                             |

Unrun: runtime caller/provider construction for Queue 3 and Queue ID 4 arguments; semantic names/units of every PMFW domain/table field; how the actuator translates float targets to PLL/register values; exact mapping to BC-250 physical MCLK/UCLK/FCLK paths; synchronous crossing/divider status; PEI/ABL1/SMU runtime execution; hardware clock counters or memory latency/performance.

No source, imported firmware, ROM, board, NVRAM, register, or shared report was changed. The 1800-labelled Setup request was preserved. No HOB or heap test was run.
