# ABL1 `0x7378` table-xref independent review

## Result

The newest local `0x7378` artifact does **not** establish a caller/object identity for
any stride-24 table reader. Its machine result explicitly says
`PASS_BOUNDED_STATIC_WITH_CALLER_IDENTITY_UNRESOLVED`; the `exact_missing_input` is
the constructor or indirect invocation supplying `R0` at `0x7378`, or a bounded runtime
address trace comparing that initializer root with the `R0` consumed by `0x10958`.

The only new bounded check performed here is conditional pointer arithmetic plus exact
Thumb decoding of the known `0x7378` function:

```text
0x5E479 & ~1 = 0x5E478
0x5E478 - 0x57100 = 0x7378
0x5E479 bit0 = 1 (Thumb)
```

That establishes only a **conditional mapping** under candidate base `0x57100`. The
exact function begins:

```text
0x7378: PUSH.W {R4,R5,R6,R7,R8,R9,LR}
0x737C: MOV   R5,R0                    ; root/object pointer saved in R5
0x737E: LDR.W R0,[R1,#0x3C4]
0x7384: MOV   R6,R1                    ; input/context pointer
0x7388: MOV   R8,R2
0x738A: MOV   R4,R3
...
0x739E: STR   R6,[R5]
```

This confirms the local initializer's R0 role as a root/object pointer and does not
identify a table reader or caller. The prior action log correctly records that the
first selected `0x1FB4` reader was unrelated and that no stride-24 reader output was
available; this review does not rerun it.

## Exact execution event

Inputs were copied to a unique disposable directory:

- Object: `evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o`, SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`.
- Payload: `evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Command: `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x7378 --stop-address=0x73a0 <copied-object>`; exit `0`, stderr empty.
- Command: `od -An -v -tx1 -j 0x7378 -N 0x28 <copied-payload>`; exit `0`, stderr empty.
- Temporary output: `/tmp/bc250-7378-conditional-pointer-b51137g5/`.

Literal disassembly output:

```text
7378: e92d 43f0  push.w {r4, r5, r6, r7, r8, r9, lr}
737c: 4605       mov r5, r0
737e: f8d1 03c4  ldr.w r0, [r1, #0x3c4]
7382: b08d       sub sp, #0x34
7384: 460e       mov r6, r1
7386: 305e       adds r0, #0x5e
7388: 4690       mov r8, r2
738a: 461c       mov r4, r3
738c: f7fe fc97  bl 0x5cbe
7390: f8d6 03c4  ldr.w r0, [r6, #0x3c4]
7394: 305e       adds r0, #0x5e
7396: f008 fd63  bl 0xfe60
739a: 2800       cmp r0, #0
739c: d05e       beq 0x745c
739e: 602e       str r6, [r5]
```

The only currently available machine status for the related artifact remains:
`PASS_BOUNDED_STATIC_WITH_CALLER_IDENTITY_UNRESOLVED`; it contains no table-reader
caller/object identity and no physical-clock implication.

## Current adjacent table output is distinct

The newest completed related report,
`docs/research/2026-09-21-abl7378-indirect-entry.md` (SHA-256
`c15b43356e66dcdad621e0cf2f89a61af43dc00d84b32d8a8b15fc1bb79952c8`), is a
separate bounded table at conditional VA `0x6E1C8`/payload RVA `0x170C8`, stride
`0x24`, reached by code around RVA `0x1B24`. Its record-0 callback word is
`0x62059` (conditional payload entry `0xAF58` under base `0x57100`); record 1's
callback is zero. Its exact bounded result says AF58 does not directly call
`0x7378` or `0xAF90`. Machine result
`evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/af58-body-result.json`
has SHA-256 `db6cb72a620818c23aae2abab2e5949dbec12850407971ba958c924a0450dce7`.
This is a completed pointer-table result, but it is **not** a reader/caller for
the `0x5E479` candidate or initializer `0x7378`; it does not close the missing
caller/object identity.

## Adjudication

| Question                                                                      | Decision                                                                                                      |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Does current artifact establish a `0x7378` caller/object identity?            | **No.** The initializer root R0/R5 role is observed; the supplying constructor/indirect caller is unresolved. |
| Does `0x5E479` prove an absolute runtime function address?                    | **No.** It maps to RVA `0x7378` only under conditional base `0x57100`, with Thumb bit set.                    |
| Does this identify a stride-24 table reader or active table object?           | **No.** No reader output or caller/object join is present.                                                    |
| Does it establish clock units, MCLK/UCLK/FCLK identity, or hardware behavior? | **No.** None is observed in this local initializer check.                                                     |

Evidence class: `observed-bytes` + `static-analysis`; no runtime execution, hardware,
network, ROM, NVRAM, register, HOB, heap, or float test.

## G7: newer completed table output and stride correction

The author report was reopened after the preceding hash check. Its current SHA-256 is
`d9b70067eb560bee535087f86167c3f13cdcb631655cc91ac0913afc2b0608cd`, superseding the
previous `c15b...` report snapshot. Its appended G7 section corrects the earlier table
stride `0x24` to `0x1C`: Thumb instructions at `0x1B48`/`0x1B4C` compute
`R6 + ((8*i-i) << 2)`, and `0x1B50` loads only `[row+8]`; `0x1B52` skips the `BLX`
when that loaded word is zero. With the conditional table base `0x6E1C8 -> RVA 0x170C8`,
`row0+4` is `0x5E479` (candidate Thumb entry `0x7378` under base `0x57100`), whereas
the consumed `row0+8` is `0x62059` (candidate `0xAF58`); `row1+8` is zero at `0x170EC`.
This bounded reader does not consume `0x5E479`. The changed report remains a different,
known table reader, not a caller/object-identity proof for the initializer.

Current related hashes: action log
`docs/action-logs/20260921-abl660-entry7378-table-xref.md` SHA-256
`e537c997d3997f8d6f93043380e3089f7de7581fbc473a0cfa88374106e9dad7`; machine result
`evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/af58-body-result.json`
SHA-256 `db6cb72a620818c23aae2abab2e5949dbec12850407971ba958c924a0450dce7`.

## Independent raw table arithmetic command

The check is restricted to the two literal addresses, the reported conditional base,
the two permitted rows, and the candidate Thumb entry. It does not scan tables or rerun
the author verifier.

```text
python3 -B - <<'PY'
from pathlib import Path
import hashlib,struct,tempfile,sys
p=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin')
data=p.read_bytes()
expected='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
checks=[]
def ck(n,ok,d): checks.append((n,bool(ok),d))
def u32(o): return struct.unpack_from('<I',data,o)[0]
ck('size',len(data)==94624,len(data))
ck('sha256',hashlib.sha256(data).hexdigest()==expected,hashlib.sha256(data).hexdigest())
base=0x57100
bt=u32(0x1bac); cp=u32(0x1bb0)
ck('table_va',bt==0x6e1c8,hex(bt)); ck('count_va',cp==0x6e200,hex(cp))
tr=bt-base; cr=cp-base
ck('conditional_table_rva',tr==0x170c8,hex(tr)); ck('conditional_count_rva',cr==0x17100,hex(cr))
count=data[cr]; stride=(8-1)*4
ck('count_byte',count==2,count); ck('reader_stride',stride==0x1c,hex(stride))
r0=tr; r1=r0+stride
p04=u32(r0+4); p08=u32(r0+8); p18=u32(r1+8)
ck('row0_plus4',p04==0x5e479,hex(p04)); ck('row0_plus8',p08==0x62059,hex(p08)); ck('row1_plus8',p18==0,hex(p18))
thumb=p04&1; rva=(p04&~1)-base
ck('candidate_pointer_decode',thumb==1 and rva==0x7378,(hex(rva),thumb))
ck('known_thumb_entry_bytes',data[rva:rva+4]==bytes.fromhex('2de9f043'),data[rva:rva+4].hex())
passed=sum(ok for _,ok,_ in checks)
for n,ok,d in checks: print(f'{n}: {"PASS" if ok else "FAIL"} ({d})')
print(f'SUMMARY: {passed}/{len(checks)} PASS; exit={0 if passed==len(checks) else 1}')
out=Path(tempfile.mkdtemp(prefix='bc250-7378-table-raw-check-'))
(out/'result.stdout').write_text('\n'.join(f'{n}: {"PASS" if ok else "FAIL"} ({d})' for n,ok,d in checks)+f'\nSUMMARY: {passed}/{len(checks)} PASS; exit={0 if passed==len(checks) else 1}\n')
(out/'result.stderr').write_text('')
(out/'result.exit').write_text(str(0 if passed==len(checks) else 1)+'\n')
print('DISPOSABLE_OUTPUT_DIR:',out)
if passed!=len(checks): sys.exit(1)
PY
```

Observed process exit `0`, stderr empty, `SUMMARY: 13/13 PASS`; outputs are in
`/tmp/bc250-7378-table-raw-check-dt94zvvh/`. The earlier ad-hoc checker printed a
hard-coded, incorrect “10/10” summary after eight assertions; this counted-output
rerun supersedes that label and preserves the actual 13 checks.

## Latest checkpoint readback (shared-workspace update)

After the bounded raw check, the current author report and action log were reopened again.
The report now has SHA-256
`af4dd43d5b886371a5e1d39447c4204f40830d9dd64306760f9e215d4a2954be`, superseding the
previous `d9b7...` snapshot; the appended text only corrects its evidence-manifest count
to 15/15, with no change to the `0x1B24` stride/field result. The current status log
`docs/action-logs/20260921-abl660-entry7378-table-xref.md` has SHA-256
`ba561f2e9636b3e3e5e634923af630c82a60d4ede02b9bf361c796d381fda5df`; its newest
`0x1B1C/0x1BAC/0x1BB0/0x1BB4/0x1BB8` literal-xref work is **intent only**, with no
observed command/result appended at this readback. I did not duplicate that pending
range or restart `memory_clock_units`.

Current conclusion remains bounded: the completed `0x1B24` reader loads row `+8`, not
row `+4`; under conditional base `0x57100`, row0+4 `0x5E479` decodes to Thumb RVA
`0x7378`, but is not consumed by this reader. The separate current AF58 table output
is not a `0x7378` caller. **No current artifact establishes a `0x7378` caller/object
identity**, and no global-absence claim follows.
