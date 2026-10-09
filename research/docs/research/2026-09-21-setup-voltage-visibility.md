# Exact-CLV Setup voltage form: IFR visibility and native navigation

## Conclusion

**The exact CLV HII package contains a normal Setup → Advanced → Voltage Configuration route, and the Advanced-to-voltage REF is under a well-formed `SUPPRESS_IF(FALSE)` record.** At the static IFR level, this link is not suppressed; AMIBCP is not needed to create the form or REF in that package. The VCORE/GFX numeric questions have well-formed `EQ_ID_VAL` suppress predicates tied to their corresponding enable toggles. However, the enclosing voltage-form `GRAY_OUT_IF` and MEMIO selector each use a noncanonical six-byte `FALSE` opcode record. Their exact handling by the board's AMI TSE is unknown; do not claim those fields are definitely ungrayed/visible at runtime from these bytes alone.

This is **static package interpretation**, not proof the board's live AMI TSE registers/displays this form or reevaluates questions interactively. Thus “reachable without AMIBCP” is **supported by the encoded navigation route under standard IFR semantics, but not live-verified on this BIOS**. No Setup UI, BIOS, NVRAM, firmware, register, or hardware action occurred. Do not interpret this UI evidence as a recommendation or as proof of any applied voltage/rail.

## Pinned source and parser

- Exact CLV ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact Setup PE32 from the pinned ROM's existing census: `evidence/firmware-audit/20260919-inv-token-consumers/Setup-10cc728ae3f8.bin`, 169,056 bytes, SHA-256 `10cc728ae3f8abec5bdf206b272eb3806ef4b7f90f2bc3f887b33c02c30da152`. Census `evidence/firmware-audit/20260919-inv-token-consumers/census.json` records ROM SHA above and Setup module at FV `0x10`, FFS `0x105730`, PE32 section offset `0x60`.
- Existing flattened decode: `evidence/firmware-audit/20260920-df-init-route/menu-Setup.txt`, SHA-256 `18791e3a2a50b89cf8997ec4bebfd944e3abe7a25a9ee03ba3119de0a562c5ed`; package metadata `menu-Setup-packages.json`, SHA-256 `a9be0a7224c5365abbb678781bda1f632a45b048a063882762c6da3aced814cc`.
- Reused parser `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py`, SHA-256 `480aa6fc70ed12e8d1dbec2c32dfb45ddadcd7c2f9075ceac6dad6486bc50ebb`. It found Forms package at module offset `0xFB54`, declared package length `0x3C26` **including its 4-byte header**; correct IFR payload is 15,394 bytes and 2,468 IFR records. The one-off verifier slices `[package_offset+4 : package_offset+package_length]`.

The flattened report labels nested questions `HIDDEN`/`GRAY` based on scope. Those labels are not expression evaluation: the report records empty `expr=` strings and does not print/evaluate the following IFR expression opcodes. Therefore its `HIDDEN`/`GRAY` text alone cannot decide runtime visibility.

## Exact IFR records

Offsets in the first column are relative to the IFR body. Corresponding file offsets are `Setup-10cc728ae3f8.bin` + `0xFB58` + IFR-relative offset. Condition opcode encoding uses the standard IFR expression opcodes (`SUPPRESS_IF=0x0A`, `GRAY_OUT_IF=0x19`, `EQ_ID_VAL=0x12`, `FALSE=0x47`).

| IFR body offset | Raw IFR bytes             | Meaning from exact opcode operands                                                                                                                                        | Result under normal IFR expression semantics                                                                                                                                                                                                                                |
| --------------: | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|        `0x07B8` | `0A 82 47 02`             | Advanced-page `SUPPRESS_IF`, followed by `FALSE`; active REF QID `0x1F` at `0x07E9` targets Form `0x28EA`.                                                                | `FALSE` does not suppress the REF.                                                                                                                                                                                                                                          |
|        `0x2321` | `19 82 47 06 EC 00 01 00` | `GRAY_OUT_IF` scope; following opcode is `FALSE` (`0x47`) but encoded with noncanonical length `6` rather than the two-byte IFR constant record.                          | EDK2 source maps opcode `0x47` to false and would not gray it; exact AMI TSE handling of this noncanonical record is **unresolved**. Do not treat the flattened parser's `GRAY` tag as proof of a live gray state, nor declare runtime ungrayed from this malformed record. |
|        `0x234A` | `0A 82 12 06 73 00 00 00` | QID `0x74` is suppressed when `EQ_ID_VAL(QID 0x73, 0)` is true. QID `0x73` is `VCORE Fix Voltage`, `Setup+0x1C9`; QID `0x74` is its numeric `Voltage(mV)`, `Setup+0x1CA`. | Numeric VCORE field is hidden while VCORE Fix Voltage is `Disabled` (`0`); expression permits it when the toggle is nonzero/enabled.                                                                                                                                        |
|        `0x23CF` | `0A 82 12 06 76 00 00 00` | QID `0x77` is suppressed when `EQ_ID_VAL(QID 0x76, 0)` is true. QID `0x76` is `GFX Fix Voltage`, `Setup+0x1CD`; QID `0x77` is its numeric `Voltage(mV)`, `Setup+0x1CE`.   | Numeric GFX field is hidden while GFX Fix Voltage is `Disabled` (`0`); expression permits it when the toggle is nonzero/enabled.                                                                                                                                            |
|        `0x2454` | `0A 82 47 06 79 00 00 00` | QID `0x7A`, `Setup+0x1D2` (“Voltage”), is under `SUPPRESS_IF`; its child is `FALSE` (`0x47`) with noncanonical length `6`, not an `EQ_ID_VAL` against QID `0x79`.         | The standard EDK2 source treats opcode `0x47` as false; exact AMI TSE handling of this noncanonical record is **unresolved**. The raw bytes do not support a MEMIO-enable predicate, but they are insufficient to claim live visibility.                                    |

The other controls in that form—QID `0x75` VCORE Loadline (`Setup+0x1CC`), `0x76` GFX Fix Voltage (`+0x1CD`), `0x78` GFX Loadline (`+0x1D0`), and `0x79` MEMIO Fix Voltage (`+0x1D1`)—are not nested under a `SUPPRESS_IF` in the decoded IFR. They are nested under the noncanonical `GRAY_OUT_IF` record above, whose exact AMI TSE runtime effect is unresolved. IFR question flags are metadata (`0x10` for toggle questions and MEMIO selector; `0x14` for numeric VCORE/GFX); none is the IFR read-only bit (`0x01`).

The existing flattened decode marks QIDs `0x73`–`0x7A` as `GRAY` and `0x74`, `0x77`, `0x7A` as `HIDDEN` because they are structurally nested. That annotation is not itself a live visibility verdict. The valid q74/q77 predicates show they are suppressed while the respective toggle is zero under standard IFR semantics. The disabled options for QIDs `0x73` and `0x76` carry the IFR option-default flag; this is a declared IFR default, not a readback of live platform `Setup` NVRAM. The current on-board `Setup` values were not read. The noncanonical false records at the form grayout and QID `0x7A` must remain runtime-unresolved.

## Semantic cross-check and limits

The local imported EDK2 checkout at revision `04679c85b43cd11bd076a9196b77864fde2091b7` was read as a semantic reference, not treated as the board's AMI implementation:

- `MdeModulePkg/Universal/SetupBrowserDxe/IfrParse.c:1585-1587` maps `EFI_IFR_FALSE_OP` to Boolean false.
- `Expression.c:2659-2678` evaluates `EQ_ID_VAL` against the referenced question value.
- `Expression.c:3835-3859` only raises `ExpressSuppress`/`ExpressGrayOut` for expressions whose result is true.
- `Presentation.c:326-331,615-624` grays only `ExpressGrayOut` statements and skips statements when the result is above grayout (suppress/disable).

For the well-formed `SUPPRESS_IF(FALSE)` on the Advanced REF and valid q74/q77 `EQ_ID_VAL` records, this agrees with direct IFR interpretation. The Setup HII package statically contains navigation and question records; it does **not** establish that this exact platform's AMI TSE registers the package, treats noncanonical `FALSE` records like EDK2, refreshes a dependent question immediately after toggling, or exposes the page under the current access level. Live TSE reachability remains **UNRUN**; no AMIBCP operation was attempted.

## Reproduction command

The first exploratory walker incorrectly added four bytes to the HII package's declared total length and stopped at the trailing overread (`IFR-relative 0x3C22`, exit 1). The corrected command below treats `PackageLength` as including its header, validates the entire IFR payload and the selected raw records; it exits 0 with empty stderr:

```sh
python3 -B - <<'PY'
from pathlib import Path
import hashlib, importlib.util, json, struct
rom=Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes()
module=Path('evidence/firmware-audit/20260919-inv-token-consumers/Setup-10cc728ae3f8.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest()=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
assert hashlib.sha256(module).hexdigest()=='10cc728ae3f8abec5bdf206b272eb3806ef4b7f90f2bc3f887b33c02c30da152'
p=Path('archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py')
s=importlib.util.spec_from_file_location('ifr',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
packages=m.find_packages(module);fo,typ,plen=next(x for x in packages if x[1]==2)
ifr=module[fo+4:fo+plen]  # PackageLength includes the 4-byte HII header.
records=[];i=0
while i<len(ifr):
    op=ifr[i];n=ifr[i+1]&0x7f
    assert n>=2 and i+n<=len(ifr),(hex(i),op,n)
    records.append((i,op,ifr[i:i+n]));i+=n
assert i==plen-4==15394
check={0x07b8:'0a824702',0x07e9:'0f0fcf06cf061f000000ffff00ea28',
       0x2321:'19824706ec000100',0x234a:'0a82120673000000',
       0x23cf:'0a82120676000000',0x2454:'0a82470679000000'}
for off,h in check.items():
    assert ifr[off:off+len(bytes.fromhex(h))].hex()==h
questions={0x73:(0x2329,0x1c9),0x74:(0x2352,0x1ca),
           0x76:(0x23ae,0x1cd),0x77:(0x23d7,0x1ce),
           0x79:(0x2433,0x1d1),0x7a:(0x245c,0x1d2)}
found={}
for off,op,b in records:
    if op in (5,6,7):
        _,_,qid,vs,voff,flags=struct.unpack_from('<HHHHHB',b,2)
        if qid in questions:
            assert questions[qid]==(off,voff),(hex(qid),hex(off),hex(voff))
            found[hex(qid)]={'ifr_offset':hex(off),'var_offset':hex(voff),'flags':hex(flags)}
assert len(found)==6
print(json.dumps({'PASS':True,'forms_package_offset':hex(fo),
 'package_length_including_header':plen,'ifr_bytes_walked':i,
 'ifr_records_walked':len(records),'raw_conditions':{hex(k):v for k,v in check.items()},
 'voltage_questions':found},indent=2))
PY
```

## Check status

- **PASS — observed bytes:** exact source ROM and Setup PE32 hashes; HII package header/offset; complete 15,394-byte IFR body walk; six QID/VarStore offsets; all six selected raw IFR records.
- **PASS — static interpretation:** well-formed Advanced REF suppression is `FALSE`; q74/q77 use valid `EQ_ID_VAL` suppression predicates.
- **INCONCLUSIVE — noncanonical IFR records:** outer `GRAY_OUT_IF` and MEMIO `SUPPRESS_IF` have six-byte `FALSE` opcodes; exact AMI TSE handling was not inspected or executed.
- **INCONCLUSIVE — static platform integration:** package bytes contain the Advanced → Voltage Configuration path; exact AMI TSE integration/access policy was not inspected or executed.
- **UNRUN — live reachability:** actual BIOS Setup/TSE page display, dynamic redraw after enabling VCORE/GFX switches, current Setup NVRAM state, AMIBCP comparison, hardware or voltage behavior.
- **No-change check:** ROM, extracted PE32, parser and prior menu outputs were read only; no candidate or rollback image exists or was required.

Evidence class: `observed-bytes` + `static-analysis`; no `hardware-verified` claim.
