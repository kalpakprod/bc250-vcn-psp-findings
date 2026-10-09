# CLV fixed-voltage Setup consumer trace — intent

Timestamp: 2026-09-20T22:40:06+05:00 (Asia/Almaty; intent written before artifact creation)
Actor: subagent /root/fixed_voltage_consumer_v2 (flash_builder); parent owns scope and integration.
Target: immutable CLV donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`) and the pinned extracted 233-module corpus `evidence/firmware-audit/20260919-inv-token-consumers/` (`census.json` input SHA-256 `ea578104…ca4cb8`).

Question (bounded): who reads the **fixed VCORE/GFX/MEMIO voltage fields** that live in the separate `Setup` VarStore (`EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9`, size `0x1d3`, form `0x28EA` "REF Voltage Configuration"), as opposed to the CBS offset path (`AmdSetup+0x6E5/0x6E6`)? Which exact Setup offsets does each consumer read, and what does it do with the value?

Existing route checked: `docs/research/2026-09-20-clv-voltage-control-inventory.md` already mapped the 8 Setup fixed-voltage/loadline fields (QIDs `0x73`-`0x7a`, offsets `0x1c9`-`0x1d2`) but explicitly left the consumer unknown. The pinned 233-module corpus already carries objdump disassembly plus structured `instructions.json`, so no new extractor or disassembler is built; the new scanner is a bounded join over those existing artifacts.

Bounded action: (1) re-verify the donor and corpus hashes; (2) locate every module that carries the `Setup` variable GUID immediately followed by the UTF-16 name `Setup` (the canonical `GetVariable("Setup", …)` pair); (3) for each such module assert the literal Setup-read call site (size `0x1d3`) and every literal instruction that consumes Setup offsets `0x1c9`-`0x1d2`; (4) emit a machine-readable field→instruction→action map. Read-only static analysis of an immutable input; no ROM/NVRAM/register/hardware write, no candidate, no network, no AMIBCP.

Expected effect: one scanner, one machine-readable result JSON, literal stdout/stderr/exit capture, one English report under `docs/research/`, and this append-only log. Evidence class: `static-analysis` over `observed-bytes` (module bytes and hashes). Expected outcome: a concrete consumer module pair plus the exact offset→register mapping, or an explicit bounded negative.

Rollback: delete only this log, the report, and `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/`. The donor, the corpus, and all prior evidence remain unchanged.

## Observed result

Timestamp: 2026-09-20T22:55:00+05:00 (Asia/Almaty)

Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py > verifier.stdout 2> verifier.stderr; printf '%s\n' "$?" > verifier.exit`

Observed: exit `0`; stderr `0` bytes; machine result `status=PASS`, `350/350` checks passed, `0` failed.

Result: the fixed VCORE/GFX/MEMIO Setup fields are consumed in PEI by two vendor VR-controller PEIMs.

- `ISL69247` (file GUID `6E6D2018-28D0-4AD3-BEB3-B48E4981707D`, PEIM/TE in PEI FV `0xE02000`, TE image at ROM `0xED2C74`, SHA-256 `3e1f753a627922d16e5a638a527e39f4dd26242144edae25b0ac849db6421e34`) reads Setup offsets `0x1c9/0x1ca/0x1cc` (VCORE Fix Voltage, Voltage mV, Loadline) and `0x1cd/0x1ce/0x1d0` (GFX) and stages them as VR register writes (`0x21` = mV, `0x28` = loadline table value, `0x23` = 0, `0xF0` read-modify-write of bit `0x30`, `0xC7` = `0xEA0B`/`0xEA8B`, `0xC5` = `0x0B`/`0x08`).
- `ISL95712` (file GUID `02544BE0-2CB9-4B75-8111-CD8CDC07B837`, PEIM/TE in PEI FV `0xE02000`, TE image at ROM `0xED3D8C`, SHA-256 `c0cc17d2d54f9cde65f471d2971596837b024d4764a28b33286032cfa95d43a9`) reads Setup offsets `0x1d1` (MEMIO Fix Voltage) and `0x1d2` (MEMIO Voltage enum) and writes the stored enum code to VR register `0xDF`.
- Both read the `0x1d3`-byte `Setup` variable through the PEI Read-Only Variable2 PPI (`2AB86EF5-ECB5-4134-B556-3854CA1FE1B4`).
- `CpuDxe` is the only other module that calls `GetVariable("Setup", …)`; it reads the `0x1d3`-byte variable but never accesses `+0x1c9`..`+0x1d2`.

Independent path: both consumer TE images were re-extracted directly from the immutable ROM (offsets `0xED2C74`, `0xED3D8C`) and re-hashed to the corpus module hashes; the Setup call-site and field-consumption bytes were re-asserted there (part of the 350 checks).

Evidence paths and hashes:

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-fixed-voltage-consumer.md`, SHA-256 `6bb851ec32ec8fe963bf50e4070563944bf98c2657a703d2fd696ce960bb3791`.
- Scanner: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py`, SHA-256 `e67ded127c9e00f0532f8aa41431b13ab08468619189252e01bb3fbbfcf72ea3`.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/fixed-voltage-consumer-result.json`, SHA-256 `54b5e333759cb72f41f8e863bcc4c3f683a11951f47d25e903ca60af7213822e`.
- Manifest: `SHA256SUMS.final`, SHA-256 `4cc1da09b4412168569614cb5aadd9602ce627170cba227fefa31a707d68f0bb`; `sha256sum -c` exit `0`, all five entries `OK`.

Limits: static analysis only. Runtime PEI dispatch, the mailbox transport chip identity, PMBus-style register semantics, physical rail identity, and any applied voltage are unverified. No ROM, NVRAM, register, candidate, or hardware action occurred. No voltage value is recommended.

Rollback: delete only this log, the report, and `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/`; donor, corpus, and prior evidence unchanged.

## Memory recording of the fixed-voltage consumer result — intent

Timestamp: 2026-09-20T23:15:10+05:00 (Asia/Almaty; written before the memory write).
Actor: root. Target: `memory/project-state.md` (one appended section) and
`memory/oc-recheck.md` (one appended section).
Reason: the fixed-voltage Setup consumer trace finished at 22:44-22:45 with report, scanner,
machine result and manifest, but the workflow's durable memory step was not performed; `memory/`
contained no `fixed-voltage` reference (verified by grep before this write).
Expected effect: both memory files gain a dated, evidence-classified record of the two PEI
VR-controller consumers, the observed mailbox/port transport, the limits, and the rollback.
Pre-write independent re-verification (this session, before the memory write):

- scanner re-run `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py`
  -> exit `0`, stderr `0` bytes, stdout SHA-256 `54b5e333759cb72f41f8e863bcc4c3f683a11951f47d25e903ca60af7213822e`
  (byte-identical to the recorded `verifier.stdout`), machine result `status=PASS`, `350/350` checks.
- `sha256sum -c SHA256SUMS.final` in the evidence dir -> 5/5 `OK`, exit `0`.
- `/home/OWNER/.local/bin/pytest -q tests/` -> `30 passed in 1.52s`.
- Pre-write hashes: `memory/project-state.md` `fb221e1213059988fa3e27816ee47428fab9c32c7b337bbebb78596066a398d2`,
  `memory/oc-recheck.md` `f6546a83435be7f8581355d314e4e0c52b6c62773492f11821482eb5e05fb82a`,
  this log `aeed724a7daac0212b3072db3babba4bcd817eadec0e327d47f168c2f4a5ae5d`.
  Rollback: delete only the two appended memory sections and this log section; the evidence
  directory, the report, and all prior memory sections stay unchanged.

## Memory recording of the fixed-voltage consumer result — observed result

Timestamp: 2026-09-20T23:15:53+05:00 (Asia/Almaty). Actor: root.
Observed: both sections were appended and reopened. `memory/project-state.md` gained 3,273 chars
(section "CLV fixed-voltage Setup consumer trace - VCORE/GFX/MEMIO consumed in PEI (2026-09-20,
offline static)"); `memory/oc-recheck.md` gained 1,603 chars (section "CLV fixed-voltage Setup
consumers in PEI - recorded after the fact (2026-09-20, root verification)").
`grep -c fixed-voltage memory/project-state.md memory/oc-recheck.md` -> `13` and `5`.
Post-write hashes: `memory/project-state.md` `ac05de2674eb486d9e6d1d2aadc717a791d8b40897f7543e18e1bc4b2de10b74`,
`memory/oc-recheck.md` `83373af783b8844ca43dd7704832cff68d8dda74ed8e4a80fb89c42a3db4e761`.
This log's own hash changes with this append and is therefore not quoted here.
Re-verification in the same session against unchanged inputs: scanner stdout
`54b5e333759cb72f41f8e863bcc4c3f683a11951f47d25e903ca60af7213822e` (exit `0`, stderr `0` bytes,
`status=PASS`, `350/350`); `sha256sum -c SHA256SUMS.final` 5/5 `OK`; `pytest -q tests/`
`30 passed`.
Remaining uncertainty: the recorded finding stays static-analysis only (no PEI dispatch proof, no
mailbox chip identity, no PMBus semantics, no rail identity, no applied voltage). No board, ROM,
NVRAM, register, candidate or hardware action occurred in this recording step.
Rollback: delete only the two appended memory sections and this log section.

## G7 correction — duplicate memory section detected and consolidated

Timestamp: 2026-09-20T23:18:05+05:00 (Asia/Almaty). Actor: root.
Discovery: while verifying the append, `memory/project-state.md` was found to already carry a
record of the same finding - "CLV fixed-voltage Setup consumer trace - PEI VR drivers identified",
appended by the concurrent project writer at 2026-09-20T18:14:35Z (= 23:14:35+05:00) - followed by
"G7 correction: rejected fixed-voltage reviewer identities", which withdraws that section's
mismatched identities (VddPei/VddMemPei, ISL69269) and restates the cited ones (`ISL69247`
`6E6D2018-28D0-4AD3-BEB3-B48E4981707D`, `ISL95712` `02544BE0-2CB9-4B75-8111-CD8CDC07B837`,
fields `0x1c9`-`0x1d2`). My own section, appended at 23:15:37+05:00, duplicated that record.
Correction: the duplicate `##` section was removed from `memory/project-state.md`. What remains is
one compact `### Independent re-verification and transport detail` addendum under the existing
record, carrying (a) the byte-identical scanner re-run, (b) the `sha256sum -c` 5/5 result,
(c) `pytest -q tests/` `30 passed`, and (d) the transport detail (mailbox staging plus x86 ports
`0x2E`/`0x2F`, `0xA20`-`0xA22`, `0x87,0x87` unlock). `memory/oc-recheck.md` keeps a single
section, reworded to state that the `project-state.md` record was appended concurrently rather
than missing. No evidence, report, scanner, result or manifest byte was touched.
Observed after the rewrite: `grep -c "VCORE/GFX/MEMIO consumed in PEI" memory/project-state.md`
-> `0`; `grep -c "recorded after the fact" memory/oc-recheck.md` -> `1`; headers now
`249 ## ... PEI VR drivers identified`, `272 ## G7 correction: rejected fixed-voltage reviewer
identities`, `275 ### Independent re-verification and transport detail`.
Post-correction hashes: `memory/project-state.md`
`a49478e2573e730b8f9b1f440641d90c1032fe7185d6e1a35824c798c357294a`; `memory/oc-recheck.md`
`bb0174d7e0d1e9e8775a018b1af059e28c4b51d5a31eed3fb5902584f21643ca`.
Rollback of this correction: delete the `### Independent re-verification and transport detail`
addendum and the `oc-recheck.md` section; the superseded `##` section and its G7 correction stay
as project history.
Remaining uncertainty: the withdrawn identity summary at `memory/project-state.md` line 249 is
preserved by project convention as superseded history and must not drive patches or voltage
recommendations; the finding itself stays static-analysis only (no PEI dispatch, mailbox chip,
PMBus semantics, rail identity or applied voltage).
