# CLV MCLK/UCLK/FCLK frequency-unit discrimination — intent

## Intent (before evidence writes)

- Timestamp: 2026-09-20T12:00:00+05:00 (Asia/Almaty)
- Actor: delegated independent reviewer (`gpt-5.6-luna`, xhigh); root remains orchestration-only.
- Target evidence: exact-clv clock-control records and retained host-driver source `cyan_skillfish_ppt.c`; pinned ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Bounded task: identify which MCLK/UCLK/FCLK mapping is actually demonstrated, distinguish source-level software aliasing from firmware software-state queries and physical clocks, and execute one smallest host-only discriminating check using existing data. Do not repeat sysfs aliases as independent measurements, add dependencies, or infer a frequency/unit/sync profile.
- Existing evidence reused: `import/from-windows/Users/kukuruza/tmp_bc250/recon/cyan_skillfish_ppt.c`, `evidence/firmware-audit/20260919-oc-clock-provenance/clock-handlers-verification.json`, `fabric-domains-verification.json`, and `docs/research/oc-clock-actuator-chain.md`.
- Expected effect: one machine-readable result, one report, and this append-only action log. No firmware/hardware/settings/voltage/candidate/install/commit/child-agent action.
- Rollback: remove only this own evidence/report/log set and any later append-only integration section.

## Observed result

Timestamp: 2026-09-20T12:20:00+05:00 (+05:00).

The first verifier run exited `1` because one assertion used the wrong retained wording (`state index delta/count` versus the exact evidence phrase `state index delta, NOT a frequency measurement`). No result was accepted from that run. The assertion was corrected and rerun.

Final command exited `0` with `11/11 PASS` and empty stderr. Final hashes:

```text
d71b37619875e1fa44100a77a39dbec34ab37bd2770dc2547c30b716eaab29d8  evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency_unit_verify.py
6027fd54d8803fbd2a8b22f09c098ec5e9174ddbb143fd2b41f68a5575f7fb0c  evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency-unit-result.json
254c224c10e086db5fd5f71381d381e23e39c1180ff741fb53bd583028ba7a89  docs/research/2026-09-20-clv-sync-frequency-unit-discrimination.md
```

The check confirms only source-level driver aliasing and software-state handler semantics. It does not provide an independent physical clock or GDDR6 unit mapping. No firmware, hardware, settings, voltage, candidate, installation, commit, child-agent or live telemetry action occurred.

## Shared integration result

Timestamp: 2026-09-20T12:35:00+05:00 (+05:00).

Reviewed the `11/11` host-only discrimination result and integrated only its static qualification:

- `memory/oc-recheck.md` records that FCLK/MCLK/UCLK software exports alias `MemclkFrequency`, while Robin-5 queries expose internal state/counts rather than physical clock samples.
- `memory/decisions.md` contains `D34` exactly once.
- `specs/2026-09-20-clv-sync-development-plan.md` records the demonstrated alias/state mapping and keeps the field/token-to-consumer/unit/rate gate open.

Final shared hashes:

```text
59a566f2671e6787a73242473ccbfcc85540a8896b09c7564edb8310a75263e4  specs/2026-09-20-clv-sync-development-plan.md
ff0f39c0b1a0788669465d5ddc8286cbf228c6a5fd423d7531cf97074b374eb9  memory/oc-recheck.md
25e8ea24a75a3c0134090275f96cfcdb8322b75e66dc9cd5eb35c2ca3ad7dafe  memory/decisions.md
```

No live telemetry, firmware, hardware, settings, voltage, candidate, installation, commit, or child-agent action occurred. Phase-2 remains **PARTIAL**.

## Continuation intent — resolve serializer record ownership off-by-one

Timestamp: 2026-09-20T12:50:00+05:00 (Asia/Almaty).

Target: exact contiguous `CbsBasePei` and `AmdNbioSmuV10Pei` serializer instructions around the adjacent `0x1330..0x1333` records. The prior canonical matrix paired source loads by nearest address; this check will instead track destination pointer increments and `dest+0/+2/+3` stores. Preserve all superseded claims; do not update shared memory/plan until the direct store-pair trace passes.

## Continuation result intent — supersede nearest-header token pairing

The destination-pointer trace has shown that prior nearest-RVA/header pairing is invalid for the contiguous record stream. Before updating shared conclusions, extend the own matrix to require the destination `+0/+2/+3` store and pointer-increment trace, with `+0x6A3` ownership tested as token `0x1331` in both exact modules. Preserve the earlier `0x1332` claim as superseded evidence; no downstream semantic conclusion follows.

## Decisive ownership correction result

Timestamp: 2026-09-20T13:20:00+05:00 (Asia/Almaty).

The full contiguous destination-pointer trace was executed and passed `12/12` in both exact serializer modules:

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-record-ownership-correction/record_ownership_verify.py
```

Result SHA-256: `cab9dd7e18defabe1459537fe870a520c24602f1641bd44af5e78ad3e2b2aaf3`; verifier SHA-256: `828bb9fa479b447cf8cbfba69b4c22514b446f18f39c2424d73b7d0cea853043`.

Exact ownership is `+0x6A2 -> 0x1330`, `+0x6A3 -> 0x1331`, `+0x6A4 -> 0x1332`. This supersedes the previous nearest-header/preceding-load `+0x6A3 -> 0x1332` correction. Shared plan/memory/decisions were corrected to `0x1331`; earlier claims remain preserved as superseded history. No downstream or hardware claim follows.

Final shared hashes:

```text
ea94204ef6e75d495455a1a4877eb5812c00217efe0aac3d3a043013c0ce0ecc  specs/2026-09-20-clv-sync-development-plan.md
f69fab63288c3a67a707fc650f9301629036be3e85ec302a76b8fddb58af2c1c  memory/oc-recheck.md
f192872607fb2e7dce10e593ad2f97a1ef0c505688beccd7f481033f5666f730  memory/decisions.md
```

## Final integrity/provenance readback

Timestamp: 2026-09-20T13:35:00+05:00.

The own matrix now depends on byte-backed exact-module ownership evidence for `+0x6A3`, not historical token strings or nearest-address pairing. Current own result is `39/39 PASS`; direct ownership result is `12/12 PASS`. Historical canonical artifacts remain preserved and explicitly superseded.

Current key paths:

```text
/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-frequency-unit-discrimination.md
/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency-unit-result.json
/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-sync-frequency-unit-discrimination.md
/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-record-ownership-correction/record-ownership-result.json
```

No consumer closure, physical clock, training or hardware claim is made.

## Continuation intent — adopt corrected all-fields lifetime map

Timestamp: 2026-09-20T13:55:00+05:00.

Review the new all-fields cursor-lifetime result and Uclk semantics result. Replace superseded P-state/Phy token associations in the own matrix only after verifying their current hashes/manifests and preserve all prior mappings as corrected history. Canonical target map must include all requested fields and the independently traced FCLK_DPM ownership; no downstream consumer or hardware conclusion is implied.

## Final all-fields map/readback

Timestamp: 2026-09-20T14:20:00+05:00.

The current own matrix is `44/44 PASS` and now uses corrected all-fields lifetime evidence:

```text
+0x316 -> 0x11ED (u8)
+0x330 -> 0x1204 (u8)
+0x368 -> 0x1237 (u8)
+0x36D -> 0x123C (u8)
+0x6A3 -> 0x1331 (u8)
+0x703 -> 0x1373 (u8)
+0x704 -> 0x1374 (u16)
```

Final absolute role paths reopened:

```text
/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md
/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration-domain-matrix.json
/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-sync-frequency-unit-discrimination.md
/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all-fields-result.json
```

All-fields result: `29/29 PASS`, manifest `3/3 OK`; Uclk semantics result: `31/31 PASS`, manifest `8/8 OK`. The own matrix now supersedes old 39-check/FCLK-only output and old P-state/Phy token mappings. No downstream consumer, unit, ratio, training, physical clock, synchronization, or hardware acceptance claim follows.

Final shared hashes:

```text
4b37fd034b35fd26268699028304e87e00f6c644e4d5cbc2870b09c3dbe09d11  specs/2026-09-20-clv-sync-development-plan.md
0aa5c299a1647cf3d46a8b594dbd8aae7fc7a4e0f9647292f653a6c57f61460a  memory/oc-recheck.md
7f993acfaec045c93583d7263b6764121c27a0941aaa4ba33014cfb1636e2094  memory/decisions.md
```

## Final canonical seven-field readback

Timestamp: 2026-09-20T14:45:00+05:00.

The corrected all-fields artifacts and own matrix are now the canonical checkpoint:

- All-fields report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-record-lifetime-all-fields.md` (SHA-256 `7ea52e605142d020ecdf32a0889333472adc217d73dd98a3badc452d3b76dac7`); result SHA-256 `7f865e2a018c9be7f665e01286473593582967808963d8bb29c112514840fbbf`; `29/29 PASS`; manifest `3/3 OK`.
- Uclk semantics report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-uclk-semantics.md`; result SHA-256 `17cba83251f50a108341aa40bbe0d48aa758ff008000436570975428bbdb5059`; `31/31 PASS`; manifest `8/8 OK`.
- Own matrix result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration-domain-matrix.json`; current `44/44 PASS`, uses all-fields lifetime plus direct FCLK ownership evidence.

Canonical map is now `316->11ED`, `330->1204`, `368->1237`, `36D->123C`, `6A3->1331`, `703->1373`, `704->1374`. Prior `1238/123D/1332` assignments are superseded history. No downstream/hardware claim follows.
