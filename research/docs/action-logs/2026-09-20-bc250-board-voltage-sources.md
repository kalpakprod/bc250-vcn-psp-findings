# BC-250 board voltage sources (firmware-visible inventory) — intent

Timestamp: 2026-09-20T23:19:00+05:00 (Asia/Almaty; intent written before artifact creation)
Actor: subagent `/root/bc250_board_voltage_sources` (flash_builder); parent `/root` owns scope, integration and final review.
Task (reconstructed): enumerate the BC-250 board voltage sources that are visible in the firmware
image — which modules can actually drive a voltage regulator, through which transport, to which
register, and from which stored NVRAM field — and separate them from firmware modules that only
touch the shared Super-I/O/EC configuration window.

Pinned inputs (hashes re-read at intent time):

- ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 B,
  SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` (immutable, never written).
- Pinned 233-module corpus `evidence/firmware-audit/20260919-inv-token-consumers/`
  (`census.json` SHA-256 `506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39`).
- Prior consumer result (cross-check only)
  `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/fixed-voltage-consumer-result.json`
  SHA-256 `54b5e333759cb72f41f8e863bcc4c3f683a11951f47d25e903ca60af7213822e`.

Existing route checked before new work (G3): `scan_fixed_voltage_consumer.py` answers _who reads the
`Setup` fixed-voltage fields_ for the two already-known PEIMs. It does not answer _which firmware
modules can write a VR register at all_, and it does not enumerate the shared EC transport. The new
scanner is a bounded superset detector over the same pinned corpus; it reuses the existing corpus,
the existing census schema and the existing HII/Setup inventory instead of building a new extractor.

Bounded action: (1) re-verify the donor and census hashes; (2) apply one conjunctive literal-byte
detector to all 233 modules to find modules that implement the EC-window VR mailbox writer;
(3) for every matching module, enumerate write-helper instances, the call sites with their pushed
register index, and the staged value immediates; (4) re-extract every matching module verbatim from
the immutable ROM and re-hash it; (5) record the weaker "EC window only" modules as a bounded
negative with their per-anchor hit table; (6) cross-check the two known consumers against the prior
machine result. Read-only static analysis of immutable inputs.

Expected effect: one scanner, one independent verifier, one machine-readable result JSON, literal
stdout/stderr/exit captures, `SHA256SUMS.final`, an executable `ROLLBACK.sh`, one English report
under `docs/research/`, and this append-only log. Evidence class: `static-analysis` over
`observed-bytes` (module bytes, ROM bytes, hashes). No ROM/NVRAM/register/candidate/hardware write,
no network, no AMIBCP, no board contact.

Rollback: `evidence/firmware-audit/20260920-bc250-board-voltage-sources/ROLLBACK.sh` deletes only
this task's owned files (report, log, evidence directory). The donor, the pinned corpus and all
prior evidence remain unchanged.

## Continuation (root, 2026-09-20T23:26+05:00) — intent before artifact write

The dispatched worker wrote the intent above and produced no artifact; the evidence directory
`evidence/firmware-audit/20260920-bc250-board-voltage-sources/` was empty and no scanner process
was running. Root re-verified the pinned inputs (donor SHA-256 `ea5781…4cb8`, census SHA-256
`506b8e…0d39`, 233/233 module images matching their census hashes) and resumes the same bounded
task under the same scope, evidence class and rollback.
Detector calibration (read-only probe, root): the conjunctive literal-byte set
{push 0x2e, push 0x2f, mov al,0x87, immediate 0x00000a20, push 0x65, push 0x66, push 0x70,
push 0x63, push 0x60, test al,0x40} is present in exactly 2 of 233 modules (`ISL69247`,
`ISL95712`) and in no other module. `mov esi,0xC0` was dropped from the set: it is present in
`ISL69247` but absent in `ISL95712`, so it encodes register allocation, not protocol.
Expected effect: scanner + independent verifier + machine result + literal captures +
`SHA256SUMS.final` + `ROLLBACK.sh` + one English report. No ROM/NVRAM/register/candidate/hardware
write, no network, no board contact.

## Observed result (after the write)

Timestamp: 2026-09-20T23:45+05:00 (Asia/Almaty). Actor: root (continuation turn), recording
and independently verifying the artifact returned by the dispatched builder
`/root/bc250_board_voltage_sources` (flash_builder).

Returned artifacts found in the evidence directory (written 23:26-23:28 by the builder):
`scan_vr_mailbox_writers.py` (`63ae081c…`), `vr-mailbox-writers-result.json` (`852ffd0d…`),
`objdump/ISL69247-3e1f753a6279.objdump.txt` (`a81f1e72…`),
`objdump/ISL95712-c0cc17d2d54f.objdump.txt` (`18c36d55…`). The builder did not append an
observed-result section, a manifest, a rollback script, a report, or the memory record;
this turn completes those steps.

Re-run of the returned scanner (determinism check, root):
`PYTHONDONTWRITEBYTECODE=1 python3 -B scan_vr_mailbox_writers.py` -> exit `0`, stderr `0`
bytes, stdout `checks=31 failed=0 status=PASS` / `writers=['ISL69247-3e1f753a6279',
'ISL95712-c0cc17d2d54f']` / `ec_window_only=28 modules`; the regenerated result JSON is
byte-identical to the captured file (SHA-256 `852ffd0d…` before and after, `diff -q` equal).

Independent verification (root-owned, different evidence path):
`verify_board_voltage_sources.py` (`3a207fac…`) -> `status PASS`, `604` checks, `0` failed,
stderr `0` bytes, exit `0`. It re-derives the match set from the pinned objdump text with
its own three-group anchor conjunction over all 233 modules, re-locates both writer images
in the immutable ROM by whole-image content search (ISL69247 TE at `0xed2c74`, ISL95712 TE
at `0xed3d8c`, each exactly once, each inside the reported FFS file `0xed2c30`/`0xed3d48`),
recomputes the corpus-wide anchor module census (14/14 anchors equal), and re-reads all 200
recorded anchor offsets as raw bytes plus, where disassembled, as instruction bytes.

Result: exactly two of the 233 pinned CLV 5.00 modules implement the complete Super-I/O/EC
VR mailbox writer — `ISL69247` (`6E6D2018-28D0-4AD3-BEB3-B48E4981707D`) and `ISL95712`
(`02544BE0-2CB9-4B75-8111-CD8CDC07B837`), both PEIMs in FV `0xe02000`. 28 further modules
carry at least one strong anchor but not the full conjunction (bounded negative, per-anchor
offsets in the machine result). Two of the 200 anchor offsets are cross-instruction literal
false positives (HiiDatabase, `A0327FE0-…`) and are documented in `VERIFICATION.txt`; both
are in the weak bucket and do not affect the verdict.

Evidence: report `docs/research/2026-09-20-bc250-board-voltage-sources.md`;
`evidence/firmware-audit/20260920-bc250-board-voltage-sources/` (`VERIFICATION.txt`,
`SHA256SUMS.final`, `ROLLBACK.sh`, literal stdout/stderr/exit captures). Repository suite
re-run `30 passed`.

Rollback: `evidence/firmware-audit/20260920-bc250-board-voltage-sources/ROLLBACK.sh`
removes this task's evidence directory and report; `--purge-log` additionally removes this
log. Deviation from the intent line above: the log is kept by default because a rollback
must not erase the record of what it rolled back. `ROLLBACK.sh` was exercised on two
isolated copies of the project layout (default and `--purge-log`): exit `0`, stderr empty,
only the owned files removed, donor sentinel and unrelated files untouched. In-place
execution is the actual rollback and was not performed, because the artifact is the
deliverable.

Remaining uncertainty: static analysis only — PEI dispatch, mailbox chip identity,
PMBus/register semantics, physical rail identity and any applied voltage remain unverified;
the literal anchor set is calibrated on two known positives; no ROM, NVRAM, register,
candidate, board or network action occurred; no voltage value is recommended.
