# CLV fixed-voltage consumer: independent instruction-level decode — intent

Timestamp: 2026-09-20T23:33:00+05:00 (Asia/Almaty; intent written before artifact creation)
Actor: subagent `/root/fixed_voltage_independent_decode`; parent `/root` owns scope, integration, final review.
Scope: the open review item recorded in `memory/project-state.md` ("Independent review of misleading
byte-assertion labels remains incomplete") attached to
`docs/research/2026-09-20-clv-fixed-voltage-consumer.md` and
`evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/`.
Question: do the byte-pattern "meanings" asserted by `scan_fixed_voltage_consumer.py` match the real
decoded instructions at those RVAs, and does the fixed-voltage consumer path decode as claimed?

Method (independent of the prior scanner): (1) parse the PEI FV at `0xE02000` of the immutable donor
and walk its FFS chain to obtain the two PEIMs by file GUID (no census dependency); (2) disassemble
the extracted TE images with GNU objdump 2.47 `-b binary -m i386 -M intel --adjust-vma=0x198` so
decoded addresses equal the report's RVAs; (3) parse objdump output into an instruction list and
answer every prior claim from the decoded instructions plus the referenced data bytes.

Inputs: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
(SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, 16,777,216 bytes);
prior assertion table read programmatically from the cited scanner (no manual transcription).

Expected effect: a new evidence directory with the decoder, machine result, literal stdout/stderr/exit,
bounded disassembly listings, `SHA256SUMS.final`, `ROLLBACK.sh`, plus one English report and this log.
No ROM/NVRAM/register/candidate/hardware write, no network, no board contact, no edit of prior artifacts.

Rollback: delete only `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/`,
`docs/research/2026-09-20-fixed-voltage-independent-decode.md` and this log file; donor, corpus and prior
evidence stay unchanged.

## Observed result

Timestamp: 2026-09-20T23:43:00+05:00 (Asia/Almaty). Actor: subagent `/root/fixed_voltage_independent_decode`.

Command:
`PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-fixed-voltage-independent-decode/decode_fixed_voltage.py > verifier.stdout 2> verifier.stderr; printf '%s\n' "$?" > verifier.exit`

Observed: exit `0`; stderr `0` bytes; stdout SHA-256
`3da15d4a281cbbd3d5c05f97e3ea74cdaea547d6114503af1bbd29c55785fe3f`; re-run byte-identical
(`cmp -s` equal). `status PASS`, `decode_status PASS_WITH_CONTRADICTED_LABELS`,
`label_status MISLEADING_LABELS_FOUND`; `28` decoded semantic checks, `2 CONTRADICTED`,
`4` assertion windows that are not whole instructions.

Method facts: FFS walk of the donor by file GUID (no census dependency) re-locates the two PEIMs
(`ISL69247` file `0xED2C30` / TE `0xED2C74` / SHA-256 `3e1f753a…b6421e34`; `ISL95712` file `0xED3D48` /
TE `0xED3D8C` / SHA-256 `c0cc17d2…a95d43a9`); objdump 2.47 flat-binary i386 disassembly with
`--adjust-vma=0x198` puts decoded addresses on the report's RVAs; the prior assertion table was loaded
from the cited scanner (`e67ded12…`) rather than transcribed. Data checks: the pushed VAs hold the Setup
GUID / UTF-16 `Setup` / Read-Only Variable2 PPI GUID `2AB86EF5-ECB5-4134-B556-3854CA1FE1B4`.

Findings (G7 corrections to the prior artifact's labels, not to its substance):

1. RVA `0x030A` decodes as `push 0x21`; the "enable test cmp Setup+0x1c9 vs 0" asserted there is wrong -
   the compare is `0x30F: cmp BYTE PTR [ebp+0x51],bl`. The report table's "cmp vs 0 @0x30A block" is to be
   read as `0x30F`.
2. RVA `0x0709` is `movzx eax,BYTE PTR [edi]`, not a u16 read; the second byte comes from `0x714`
   (`[edi+0x1]`) staged to mailbox register `0x71`.
3. The `2e 59` window at `0x0566` starts one byte inside `0x565: push 0x2e` (it straddles `push 0x2e`
   and `pop ecx`); the port `0x2E` claim itself is correct.
4. `0x2AC`, `0x2B3` (ISL69247) and `0x270` (ISL95712) are 3-byte prefixes of 4-byte stores, so the
   claimed immediates are not covered by the pattern though the decoded values (`2`, `2`, `0x1e`) are right.

Everything else the prior report states decodes as written (defaults 0/900/2, loadline table
`{0,20,30,40,50,60}` -> register `0x28`, mV -> `0x21`, `0x23`=0, `0xF0` read-modify-write of bit `0x30`,
helper `0x4D2` -> `0xC7`/`0xC5` with `0xEA0B`/`0xEA8B`, writer `0x6ED` staging + `test al,0x40` + <=10
retries + `0x60`<-8, ports `0x2E`/`0x2F` with `0x87,0x87` and mailbox `0xA20`/`0xA21`/`0xA22`,
ISL95712 `0xDF`/`0xDE` writes and the `0x9E/0xDE/0x82/0xC0` follow-up helper).

Evidence and hashes: report `docs/research/2026-09-20-fixed-voltage-independent-decode.md`
(`a3b3cb0f…`); `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/` with
`decode_fixed_voltage.py` (`24c68c2a…`), `independent-decode-result.json` / `verifier.stdout`
(`3da15d4a…`), `verifier.stderr` (0 B), `verifier.exit`, `ISL69247.disasm.txt` (`cb15e09a…`),
`ISL95712.disasm.txt` (`10d0e762…`), `extracted/*.te.bin` (hashes above), `VERIFICATION.txt`,
`SHA256SUMS.final` (11/11 `sha256sum -c` OK), `ROLLBACK.sh` (dry-run exercised, exit `0`).

Rollback: `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/ROLLBACK.sh --apply`
removes this task's evidence directory, report and log; the appended memory note is removed manually.
Donor, pinned corpus and prior artifacts unchanged. No ROM/NVRAM/register/candidate/hardware action;
board `BC250-01` was not contacted.

Remaining uncertainty: `LocatePpi at PEI_SERVICES+0x20` is an inference about the firmware's PEI services
table (the decoded call shape and GUID are observed); nested/compressed images and other volumes are not
enumerated by this scan, so the `CpuDxe` third-consumer sentence is unrun here; runtime dispatch, mailbox
chip, PMBUS semantics, rail identity and applied voltage remain unverified.
