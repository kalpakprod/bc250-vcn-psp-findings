# Saved firmware provenance reconciled with live metadata

Scope: reuse local saved images, no new board access, flash or dump. Development TARGET remains clean5.00CLV.

## Newer saved image found

`evidence/programmer/reads/20260922/live-internal-0318.bin`,16MiB, SHA256 `3c34096349860a1694b4688fd8d2ec939354613f3924e3d29a8ddabc2e90f6d7`.

This file is newer in retained directory/date than W11. September21 reports that called W11 the latest saved image predate it. No raw capture command/exit log was located in the scoped September22 action-log search, so filename/date is not independently verified acquisition provenance or current-chip proof.

## Byte comparison executed

Existing `scripts/firmware_audit.py` executed on the saved image, cleanCLV500 and two P3 references, exit0, stderr empty. All selected PSP directory Fletcher checks match. Compared each declared PSP payload hash by type/subprogram:

- P3.00 donor SHA07595ca3aecf8a4caa28a397b5298f3946a1b769f87b16f67adc369c3f69045c:19/19 payloads identical to saved image.
- P3.00_CHIPSETMENU donor SHA48fbe5d366e6a56e2fdffdca848426216ba1f083610dab63db89d2f4e6c940b5:19/19 identical.
- Clean5.00CLV SHAea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8:8/19 identical,11 differ, including SMU and ABL0..4.

Saved image is not byte-identical to either P3 donor. Different64KiB blocks against both P3 references are0x0,0x10000 and0xAE0000..0xC30000. Therefore describe it as having a P3-identical PSP/SMU/ABL set with differences elsewhere, not pristineP3 or identified named community release. Full diff map and payload hashes in saved-provenance-result.json.

## Relation to running board

Today's independently executed Stage1 metadata reports P3.00,12/09/2021,1002:13fe. September21 takeover log and memory/project-state.md437..465 already recorded P3/all-Auto and an unresolved operator claim of installedCLV. New metadata is consistent with the saved P3 payload set but does not prove exact currentROM hash or unchanged chip since September22.

Do not say a mere stale P3 string is established: a saved image also has different executable SMU/ABL bodies from CLV. Conversely, do not infer that this saved image is certainly still installed.

## Decision

Hardware results gathered now must be labelled currentP3-reported baseline with unresolved full-image identity, not a HARDWARE-PASS of5.00CLV. CleanCLV remains immutable development base. No need to demand a new dump for unrelated offline analysis. Do not switch to P3 development or automatically flash CLV to resolve this identity gap.

Evidence extends the same diagnostic transaction roles in evidence/firmware-audit/20260923-diagnostic-preparation/: saved-image-inventory.json, p3-reference-inventory.json, saved-provenance-result.json. No firmware modified.
