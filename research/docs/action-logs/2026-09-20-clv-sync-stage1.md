# Stage 1 — Historical SYNC candidate reconciliation

## Intent (recorded before extraction/report writes)

- Timestamp: 2026-09-20T03:59:05+0500 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`, xhigh)
- Target: operator-supplied archive tree `/home/OWNER/Downloads/AyuGram Desktop/ChatExport_2026-09-20`; immutable donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`)
- Procedure: inventory archive members without execution; bounded extraction of ROM members into disposable/stage evidence only; hash and compare loose and archived revisions; reuse read-only `scripts/nvar_audit.py` and existing APCB/UEFI parsers; classify differences into NVRAM/defaults/APCB/code/checksum regions.
- Rationale: execute phase 1 of `specs/2026-09-20-clv-sync-development-plan.md` and replace filename/claim-based attribution with measured structural evidence.
- Expected effect: no source/archive mutation, no firmware modification, no hardware action; only new machine-readable stage report, copied evidence members, and append-only action log.
- Rollback: delete only the newly created stage-1 evidence directory and report/log additions; source archives and donor remain untouched.
- Safety: archive contents are treated as data; no attached executable or firmware is run/flashed. Security-like NVRAM names and raw chat/credentials/access links are excluded.

## Read-only discovery already completed

- Plan, contract, memory index/task memory, focused skills, prior `chat-attachment-audit.json`, existing NVAR/APCB/UEFI tools, and archive member inventories were read before bounded extraction.

## Observed extraction result

- Bounded extraction command exited `0`; stdout was `stage=evidence/firmware-audit/20260920-clv-sync-stage1`, `extracted_files=17`, `status=0`; stderr was empty (no attached code executed).
- `files.zip` inventory: `README.md` (4379 B uncompressed), four 16 MiB ROM members (`dfg_idx06_up_130`, `dfg_idx06_down_70`, `dfg_idx08_up_50`, `dfg_idx08_down_20`).
- `oc_profiles.rar` and `oc_profiles (1).rar` each contain three 16 MiB SYNC members; `03_BC250_ULTIMATE_LOW_LATENCY_StockCPU.rar` contains one 16 MiB ROM.
- Loose SYNC SHA-256: `01=6a8c0d01b7df41ca67e10747add43c59374012cf64efcbafa0d59aea9d19f9f9`, `02=f96552bf7b5d3e81a8d101c200d5b4c9cbd0b8dc1ac45ff1448d304388b248fc`, `03=71d1988db4b7b149e1b8f1efda970c37c1a5a9e3ade0867a83ce66122d159b9a`.
- Both loose duplicate `dfg_idx08_down_20_ckfix(1)*` files are SHA-256 `632e222666abbf88bf0260d8bf3daab7a1a6ea2504548bde172c4d4610b95885`.

## Observed reconciliation and verification result

- `scripts/nvar_audit.py` was run read-only against donor, loose SYNC, DFG copies, archived SYNC revisions and ULTIMATE with `--store-offset 0 --store-length 0x20000`; every invocation exited `0` and selected `AmdSetup`. Three SYNC images report three later opaque/unterminated NVAR records; relevant AmdSetup fields decoded successfully and raw bodies were not emitted.
- Local path-parameterized `scripts/firmware_audit.py` exited `0` on 14 image entries / 13 unique SHA-256 contents, stdout exactly `{"output": "evidence/firmware-audit/20260920-clv-sync-stage1/firmware-audit.json", "images": 14, "extracted": 0}`; stderr empty. `scripts/apcb_detail.py` exited `0` on 14 image entries / 13 unique SHA-256 contents, stdout exactly `{"output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage1/apcb-detail.json", "images": 14, "failed": false}`; stderr empty.
- Executable extraction on donor, SYNC03 and ULTIMATE exited `0`; each produced 233 executable module records, and ordered module body SHA-256 sequences were identical to donor.
- `scripts/psp_ps1_verify.py` exited `1` for baseline and all candidates: 14 signed containers PASS, 2 external-key records unresolved, 3 non-containers. No candidate-only PSP failure appeared; this is an unresolved-key status, not a hardware acceptance claim.
- DFG checksum result: uncorrected variants calculated `0xFA`, `0x82`, `0xDE`, `0xA2` against stored `0xC0` (FAIL); ckfix pair changed `0xAB1014` `00->1E` and calculated `0xC0` (PASS). `scripts/firmware_audit.py` reports PSP/BHD matches for all images.
- All generated machine/human reports were reopened and parsed; exact report paths and hashes are in `stage1-report.json` and final hash manifest.

## Stage-1 conclusion and next action

- Completed checks: archive inventory/extraction coverage; loose-vs-archive deduplication; NVRAM/default field attribution; APCB range/checksum attribution; executable/UEFI code immutability check; PSP/BHD structural check; message-ID correlation.
- Not completed and not claimed: board boot, training, physical clock synchronization, voltage/rail measurement, PSP acceptance of modified APCB, performance, or flash acceptance.
- Next concrete consumer target: phase-2 static trace of native `AmdSetup` fields at body offsets `0x316`, `0x330`, `0x6A3`, `0x703`, `0x704` through `CbsSetupDxe`/`AmdFabricAriPei` and downstream divider/clock/training consumers. Historical DFG variants are not forwarded without a verified consumer and checksum rationale.
- Primary machine report: `evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.json`.
- Primary human report: `evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.md`.

## Plan progress update intent and result

- Intent: mark only phase-1 checklist checks completed by the observed report; do not mark any phase-2/hardware item.
- Target: `specs/2026-09-20-clv-sync-development-plan.md`, section `1. Reconcile historical candidates (offline)`.
- Expected edit: three phase-1 boxes become checked; decision log D4 remains unchanged; no scope expansion.
- Rollback: restore the three checklist markers to `[ ]` without touching evidence.
- Result: checklist markers updated exactly for the three completed phase-1 checks; phase-2 and hardware boxes remain unchecked.

## Memory append intent

- Intent: append durable, sanitized phase-1 findings to `memory/firmware-audit.md` only after report/readback verification.
- Scope: hashes, changed ranges, decoded non-secret AmdSetup fields, APCB checksum status, archive coverage, and explicit unrun hardware checks.
- Exclusions: no raw chat, credentials, access links, security-like NVRAM bodies, private keys, or unredacted personal export.
- Rollback: remove only the appended dated section if a later correction supersedes it; preserve the correction record.
- Result: dated sanitized section appended to `memory/firmware-audit.md`; file reopened to its end. No secrets, raw chat, security-like NVAR bodies, keys, credentials or access links copied. Current memory SHA-256 (pre-Q1 wording correction; superseded below): `5ac1f08591a20c6c029f2c96482eec2f720f42f8d2c6ec40db99bd0ac5dacff2`.
- Report path correction: machine report now points to `SHA256SUMS.final` (not the intermediate command manifest). Final machine report SHA-256 (pre-Q1 wording correction; superseded below): `2a0cb0cd4133ec9671eb59b8645d51b6d566bfc4468691f3a22ce63025cd12a6`; pre-Q1 manifest had 836 entries excluding itself.

## Independent review correction intent (Q1)

- Review source: `docs/action-logs/2026-09-20-clv-sync-stage1-independent-review.md`, verdict PASS with Q1 wording correction.
- Correction: replace inaccurate `14 unique contents` wording with `14 image entries / 13 unique SHA-256 contents`; the two ckfix image entries share SHA-256 `632e222666abbf88bf0260d8bf3daab7a1a6ea2504548bde172c4d4610b95885`.
- Targets: `stage1-report.json`, `stage1-report.md`, this action log, and the matching durable memory sentence. No byte findings, plan status, or hardware claims change.
- Expected effect: wording-only correction; regenerate and verify `SHA256SUMS.final`.
- Rollback: restore the previous wording only if a later evidence correction requires it; preserve this review correction record.

## Independent review correction observed result

- Q1 wording corrected in `stage1-report.json`, `stage1-report.md`, this action log, and the matching memory sentence: `14 image entries / 13 unique SHA-256 contents`; the ckfix pair is duplicated by hash `632e222666abbf88bf0260d8bf3daab7a1a6ea2504548bde172c4d4610b95885`.
- No bytes, candidate attribution, plan status, hardware status, or acceptance claim changed.
- Corrected readback: machine report SHA-256 `07d95e48080558434ff4cd0928416f0ae54cd421939c15b2accf64200b57d39f`; human report SHA-256 `b9eb05600e5c288fc0d18be0a2717b8d948f174f986ff4f7db9e7548c622cd36`; final manifest SHA-256 `adc0fa2d4e476d53035838d220d0a1bd90d0863c37c0a4f75e6ab7a8124db1fd`, with 838/838 readback entries `OK`; corrected memory SHA-256 `98c1687fea918f76a60f0e67bb77dbb876c7588b936cc2b89369dd219b8371df`.
