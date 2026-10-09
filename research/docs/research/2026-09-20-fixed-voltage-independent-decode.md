# CLV fixed-voltage consumer — independent instruction-level decode

Current: pinned CLV donor / two PEIMs decoded by GUID from the ROM / prior findings confirmed, three
byte-assertion labels contradicted / static only / no voltage recommendation.

## Conclusion

The fixed-voltage Setup consumer path reported in
`docs/research/2026-09-20-clv-fixed-voltage-consumer.md` decodes as claimed in substance, but three
of its byte-pattern "meanings" do not survive decoding, and one of them (the enable test) is printed
in that report at a wrong RVA:

| #   | Prior text                                                                                                                                                             | Decoded reality                                                                                                                                                                                          | Verdict                                           |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| C1  | report table line for `0x1c9`: "`cmp` vs 0 @`0x30A` block"; scanner label "enable test: cmp Setup+0x1c9 vs 0 selects Setup mV vs default 900" asserted at RVA `0x030A` | `0x30A` = `push 0x21` (the register index). The enable test is `0x30F: cmp BYTE PTR [ebp+0x51],bl` with `bl==0` from `xor ebx,ebx` at `0x27C`                                                            | **CONTRADICTED** (substance right, address wrong) |
| C2  | scanner label "write helper reads a u16 little-endian value from [edi]" at RVA `0x0709`                                                                                | `0x709` = `movzx eax,BYTE PTR [edi]`; the second byte is read at `0x714` (`movzx eax,BYTE PTR [edi+0x1]`) and staged to mailbox register `0x71`. The 2-byte little-endian staging at `0x70/0x71` is real | **CONTRADICTED label** (byte read, not word read) |
| C3  | scanner labels "transport uses x86 config port 0x2E" asserted as the 2-byte pattern `2e 59` at RVA `0x0566`                                                            | `0x566` is one byte inside `0x565: push 0x2e`; the window straddles `push 0x2e` (`6a 2e`) and `pop ecx` (`59`) at `0x567`. Port `0x2E` itself is correct                                                 | **MISALIGNED**                                    |

Three further assertions are strict prefixes of the instruction they describe, so the claimed
immediate is not covered by the pattern even though the decoded value is correct:
`0x2AC` (`c6 45 54` prefix of `mov BYTE PTR [ebp+0x54],0x2`), `0x2B3` (`c6 45 58` →
`...,0x2`), and ISL95712 `0x270` (`c6 45 f2` → `mov BYTE PTR [ebp-0xe],0x1e`). Likewise `0x2E8`
is the pushed value `3`; the register index `0x62` is pushed at `0x2EA`.

Everything else in the prior report decodes as written, including the two-module attribution, the
Setup field→register mapping, the loadline table, the `0xF0` read-modify-write, the write/read helper
shapes and the Super-I/O/EC mailbox transport. No prior claim about hardware behavior is promoted:
dispatch, mailbox chip, PMBUS semantics, rail identity and applied voltage remain unverified.

## Method (independent of the prior scanner)

1. FFS/FV walk of the immutable donor by file GUID (structural validation) — the two PEIMs are
   obtained without using the pinned census for selection.
2. GNU objdump 2.47 disassembly of the extracted TE images as flat binaries
   (`-D -b binary -m i386 -M intel --adjust-vma=0x198`), so decoded addresses equal the RVAs the
   prior artifact uses. The `0x198` mapping is independently confirmed by reading the data the code
   references (Setup GUID at `0x9ED36C4`, UTF-16 `Setup` at `0x9ED36D4`, Read-Only Variable2 PPI GUID
   `2AB86EF5-ECB5-4134-B556-3854CA1FE1B4` at `0x9ED341C` and `0x9ED42B4`).
3. The prior assertion table is loaded programmatically from the cited scanner (no manual
   transcription) and every entry is re-derived from the decoded instruction at that RVA.

Observed: exit `0`, stderr `0` bytes, stdout byte-identical on re-run
(SHA-256 `3da15d4a281cbbd3d5c05f97e3ea74cdaea547d6114503af1bbd29c55785fe3f`).
`28` decoded semantic checks: `26 SUPPORTED`, `2 CONTRADICTED`; `4` assertion windows are not whole
instructions. No ROM, NVRAM, register, candidate, board or network action.

## Module identity (re-derived from the donor)

| Module     | FFS GUID                               | FFS file   | TE section data | Size | SHA-256                                 |
| ---------- | -------------------------------------- | ---------- | --------------: | ---: | --------------------------------------- |
| `ISL69247` | `6E6D2018-28D0-4AD3-BEB3-B48E4981707D` | `0xED2C30` |      `0xED2C74` | 4264 | `3e1f753a627922d1…b6421e34` (== census) |
| `ISL95712` | `02544BE0-2CB9-4B75-8111-CD8CDC07B837` | `0xED3D48` |      `0xED3D8C` | 3624 | `c0cc17d2d54f9cde…a95d43a9` (== census) |

Both match the offsets and hashes recorded by the prior artifact. The walk also re-derives the
consumer selection inside its own scope: of `67` structurally valid outer FFS files, exactly
`ISL69247` and `ISL95712` carry the Setup variable GUID immediately followed by the UTF-16 name
`Setup`; `7` further files carry the GUID without the name pair. `CpuDxe` (a nested GUIDed PE32,
`fv_base 0x10`) is outside this scan scope, so the prior "exactly three consumers" sentence is
neither re-derived nor contradicted here.

## Fixed-voltage path as decoded (ISL69247, RVAs)

- Setup read: `mov DWORD [ebp+0x5c],0x1d3` (`0x2A2`), buffer `lea eax,[ebp-0x178]` (`0x2C1`),
  locate call `call DWORD PTR [ecx+0x20]` (`0x2B7`) with the Read-Only Variable2 PPI GUID, then
  `call DWORD PTR [eax]` (`0x2DB`) = interface slot `+0x00` (GetVariable) with the Setup GUID/name.
- Defaults: `xor ebx,ebx` (`0x27C`) → `[ebp+0x51]`/`[ebp+0x55]` (Setup `0x1c9`/`0x1cd`) = 0;
  `mov esi,0x384` + `mov ecx,esi` (`0x287`/`0x28C`) → `[ebp+0x52]`/`[ebp+0x56]`
  (Setup `0x1ca`/`0x1ce`) = 900; `mov BYTE [ebp+0x54],0x2` / `[ebp+0x58],0x2` (`0x2AC`/`0x2B3`).
- Loadline table `[ebp+0x60..0x6a]` = `{0,20,30,40,50,60}` (`0x25B`…`0x283`), indexed by
  `movzx eax,WORD [ebp+eax*2+0x60]` (`0x36F`) and written to register `0x28`.
- VCORE/GFX blocks: enable tests at `0x30F` / `0x3AD`; enabled path writes the Setup mV word to
  register `0x21` (`0x30A`, `0x314`), disabled path writes `0x384` (VCORE reuses `esi`, GFX uses an
  explicit immediate at `0x3D4`); register `0x23` ← 0; register `0xF0` read-modify-write with
  `or …,0x30` (`0x335`) / `and …,0xffcf` (`0x35B`) using read helper `0x653`
  (`0x63`←`0x83`, returns mailbox `0xB0`/`0xB1`).
- Loadline consequence: helper `0x4D2` writes `0xC7` ← `0xEA0B`/`0xEA8B` and `0xC5` ← `0x0B`
  (`loadline==2`, `0x381`) else `0x08`.
- Write helper `0x6ED`: `0x65`←`0xC0`, `0x66`←register, `0x70`←byte0, `0x71`←byte1, `0x63`←`3`,
  `0x60`←`0xC0`, then `test al,0x40` polling with `cmp bl,0xa` (≤10 retries) and `0x60`←`8`.
- Transport: low-level writer `0x565` (`push 0x2E`/`0x2F`, `mov al,0x87` + two `out dx,al`,
  `mov ecx,0xA20`), sending `[esp+4]`→`0xA21` (index) and `[esp+8]`→`0xA22` (value); `0xA20` is the
  command window written `0xFF`/`4`.
- ISL95712: defaults `0x1d1`=0, `0x1d2`=`0x1E` (1.35 V); enabled path `0xDF`←stored enum then
  `or …,1`; disabled path `0xDF`←`0x1E` then `and …,0xFE`; both branches also write register `0xDE`;
  follow-up helper stages `0x65`←`0x9E`, `0x66`←`0xDE`, `0x63`←`0x82`, `0x60`←`0xC0`.

## Limits and what would settle the rest

- The observed call is a 5-argument indirect call through `[*(PeiServices)+0x20]` with a PPI GUID.
  In the local EDK II `PiPeiCis.h` IA32 layout, the 24-byte `EFI_TABLE_HEADER` is followed by
  `InstallPpi` at `+0x18`, `ReInstallPpi` at `+0x1C`, and `LocatePpi` at `+0x20`.
  The former `+0x08` remark counted from the PPI-function block rather than the full service
  table. This supports the static ABI name, not a runtime call trace or PEI dispatch proof.
- Evidence class: `static-analysis` over `observed-bytes`. No execution, emulation, board contact,
  NVRAM read or write. PEI dispatch, mailbox chip identity, PMBUS register semantics, physical rail
  identity and any applied voltage stay unverified. No voltage value is recommended.
- Decisive next step is unchanged: a runtime trace of the mailbox ports on a board that boots with a
  modified Setup variable, or a register readback of the VR controller at Enabled vs Disabled.

## Evidence and rollback

- Decoder: `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/decode_fixed_voltage.py`
- Machine result (== verifier stdout): `…/independent-decode-result.json`
- Literal captures: `…/verifier.stdout`, `verifier.stderr`, `verifier.exit`
- Disassembly listings: `…/ISL69247.disasm.txt`, `…/ISL95712.disasm.txt`; extracted TE images under `…/extracted/`
- Verification record + manifest: `…/VERIFICATION.txt`, `…/SHA256SUMS.final`
- Action log: `docs/action-logs/2026-09-20-fixed-voltage-independent-decode.md`

Rollback: `…/ROLLBACK.sh` (dry run by default, `--apply` removes this task's evidence directory,
this report and its log; the memory G7 note is removed manually and the superseded text is kept).
The donor, the pinned corpus and all prior artifacts were not modified.
