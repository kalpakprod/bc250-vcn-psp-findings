# CLV ABL1 indirect entry to 0x7378 table — AF58 target trace

Date: 2026-09-21

## Conclusion

The distinct pointer table used by the bounded function around ABL1 RVA `0x1B24` has conditional table VA `0x6E1C8` and invokes record field `+0x8` at `BLX R1` RVA `0x1B56`. Under the prior conditional base `0x57100`, record 0's populated callback is `0x62059`, mapping to RVA `0xAF58`; record 1's callback field is zero. The exact AF58 body was decoded through its return.

AF58 does **not** directly call `0x7378` or `0xAF90`. It saves incoming `R0` in `R4`; on zero incoming `R0` it calls `0x64C8`; then it calls `0x5CBE` with `R0=SP` and `R1=the saved incoming R0`, calls `0xFE60` with `R0=SP`, and conditionally clears three bytes at offsets `0x739`, `0x75F`, and `0x760` of the object reached through `[R4+0x28]`. It returns at `0xAF8A`. `0x5CBE` and `0xFE60` are opaque boundaries for this task. No direct clock-policy identity or clock-register operation is established.

## Inputs and focused execution

- Objective attachment reopened: `/home/OWNER/.codex/attachments/9d7bcc99-0793-46b7-a070-9d0a73377101/pasted-text-1.txt`.
- Raw ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`; size `94624`; SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- ABL1 ELF: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o`; SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`.
- Focused command: `llvm-objdump -D --triple=thumbv7m-none-eabi --start-address=0xaf58 --stop-address=0xaf8c /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o`; exit `0`; stderr empty. Exact command/output/status are in the evidence run.
- Machine verifier: `/usr/bin/python3 -B evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/check_af58_body.py`; exit `0`; literal stdout `PASS`, `23/23`; stderr empty.

## Bounded table termination

The same exact raw payload gives count pointer `0x6E200 -> conditional RVA 0x17100`, whose byte is `2`. With table base `0x6E1C8 -> RVA 0x170C8` and record stride `0x24`, record 0 callback field at RVA `0x170D0` is `0x62059`, while record 1 callback field at RVA `0x170F4` is `0`. Thus the two permitted iterations invoke only the first populated callback; the second has no `BLX`, and later records are not interpreted by this count-bounded loop.

## Evidence and limits

- Evidence class: `observed-bytes` + `static-analysis`.
- Unique evidence run: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/`.
- Machine result: `af58-body-result.json`, status `PASS`, `23/23`.
- No runtime execution, indirect callee semantics, loader-base proof, clock-policy interpretation, hardware action, ROM/NVRAM/register write, network action, or installation occurred.
- No generic table scan was repeated after the initial targeted query. This trace does not overlap the separately owned `memory_clock_units` `0x7378 -> 0xAF90 -> 0xB0C4` initializer or `0x10958` consumer semantics; it reports only the distinct `0x6E1C8` table's callback to `0xAF58`.

Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-abl7378-indirect-entry.md`

## Final evidence ledger

- `af58-body-result.json`: `PASS`, 23/23; direct links to `0x7378` and `0xAF90`: false; opaque boundaries: `0x5CBE`, `0xFE60`.
- Final manifest: `evidence-manifest.sha256`, 49 entries, SHA-256 `3a2090091bd7b161e57aa81ec68ff3de1727e7092bc15b619fdedd71420484f3`; absolute-path `sha256sum -c` exit `0` with 49/49 verified.

## Bounded helper contracts

The exact direct callees from AF58 were decoded in narrow windows. `0x5CBE` writes `u16 [R0]=2` and `u16 [R0+2]=1`, ignores AF58's saved-R0 value in `R1`, returns `1`, and returns via `BX LR`. `0xFE60` reads those halfwords, shifts the first by 30 and the second by 31, and returns `1` only when original bit 1 of the first and original bit 0 of the second are set; otherwise it returns `0`. Therefore the exact AF58-produced `[2,1]` buffer makes `0xFE60` return `1`, so AF58's three conditional cleanup stores are statically taken for that helper contract.

No direct clock-policy literal or clock register operation occurs in either exact helper body. The helper trace establishes no call to `0x7378` or `0xAF90`; no indirect/external boundary exists inside these two bodies. Their first caller-level semantic boundary remains the object-relative AF58 cleanup and the unresolved meaning of offsets `0x739`, `0x75F`, and `0x760`.

Corrected machine result: `helper-contract-result-corrected.json`, `PASS`, `22/22`. The first incorrect source-bit model is retained as `failure1-*` and is not used.

## G7 correction — 0x1B24 reader stride and candidate field

This report's earlier statement that the 0x1B24 loop uses a 0x24 (36-byte) stride, and that row1+8 is at RVA 0x170F4, is withdrawn and superseded. A fresh exact Thumb listing at RVAs 0x1B40..0x1B62 (exit 0, stderr empty) shows RSB r0,r4,r4,LSL #3 followed by ADD r0,r6,r0,LSL #2: (8*i-i)*4 = 28*i, so the record stride is 0x1C. The only record-member load in the loop is [record+0x8]; the separate count byte is read through the count pointer.

With the unproven conditional base 0x57100, the table base literal 0x6E1C8 maps to RVA 0x170C8. Direct little-endian reads from the pinned ABL1 show count pointer 0x6E200 -> RVA 0x17100 = 2; row0+4 at 0x170CC is 0x5E479; row0+8 at 0x170D0 is 0x62059; and the actual row1+8 at 0x170EC is 0. Thus 0x5E479 is present in row0 data but is not consumed by this reader. The former 0x170F4 offset is not row1+8 under the decoded arithmetic.

This 0x1B24 reader is not the separate requested stride-24 table reader. No global absence conclusion is made; exact target reader/table identity remains unresolved. These are observed-byte/static-analysis results only; the candidate base and runtime relocation are unproven.

### Correction evidence paths

- Fresh reader listing: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-reader-stride-correction/run-20260921T213700+0500/reader.stdout (SHA-256 5b3973c094d05fc438158273ea99792fad247d2bdf40498b6100a1c3619cb5fd); exit 0; stderr empty.
- Raw-field check: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-reader-stride-correction/run-20260921T213700+0500/raw-fields.stdout (SHA-256 adb62d1acfa446c5bab38ac52d3970b9b09de9d6bd4fe00855b2ac6c0c26128c); exit 0; stderr empty. Reusable check source: raw_fields.py.
- Evidence manifest: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-reader-stride-correction/evidence-manifest.sha256; SHA-256 3e660f7647551a5eade8a23f3a7fdef8723f725978701e7dd44f38275ebb3980. Manifest readback verified all 14 entries.
- Pinned raw ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a; pinned ELF SHA-256 adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6. No input mutation.
- The first verifier attempt remains in the same evidence directory with status FAIL (13/18) due only to its text-column parser. It is excluded from accepted correction evidence; see the linked G7 incident and task log.

### G7 correction — evidence manifest count

The preceding correction-evidence paragraph said the manifest verified 14 entries. Fresh readback of the manifest line count and file count returned 15 for each, and the checksum pass reported all 15 entries OK. The count is 15; all hashes and conclusions are unchanged.
