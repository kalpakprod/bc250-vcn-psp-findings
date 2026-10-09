# Root review of indirect consumer findings

## Intent and evidence — 2026-09-20T01:31:59+05:00

Root read the whole new report and verifier and executed `python3 scripts/verify_df_indirect_consumer.py` successfully. The script checks three serialization sites, selected dispatch tables and absence of two literal pointer encodings in a selected suffix, NOT all indirect edges. Report category counts disagree with enumerated sites, and universal no-consumer wording exceeds coverage. Proposed FirstMarker ROM offset 0x01FC0000 exceeds the 16 MiB image; no capture capability is established by a dispatch marker. Proposed 1500/1600 test raises clocks without required provenance and is withdrawn.
Procedure: append memory correction, replace unsupported coverage and experiment sections with bounded conclusions and prerequisites. No binary/code/hardware changes. Rollback: retain this correction alongside original worker log; reverse only documentation edits if disproven. Root retains integration, delegated worker result is not release review.

## Result

Memory correction appended and report narrowed. Root readback assertions passed; `python3 -m unittest discover -s tests -q` passed 11 tests (1.764s). Byte verifier passed as recorded above, but exhaustive consumer analysis remains incomplete. No firmware or hardware changed. Next work must verify a stock read-only capture route before proposing a changed-clock board experiment.
