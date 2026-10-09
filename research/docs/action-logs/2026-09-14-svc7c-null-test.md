# SVC7C mapper rejection test

## Caller scan correction

The earlier raw ABL scan searched bytes DF7C, but Thumb SVC0x7C is encoded
7CDF in little endian (confirmed by t28 at0xFED0). Its negative result is
invalid and must not support caller absence. Likewise a linear pass stopping
at headers is not full executable coverage. Corrected t28 scan identifies
table-driven stores (e.g.0xA676,0x10004) as candidates to trace from entry
and input provenance; raw matches alone are not caller reachability.
The emulated missing NULL check remains valid independently of this scan.

## Intent

Root tests exact body3b52b28e... sliced at fresh SPI0x8EAD00, length82512.
Reuse isolated uv/Unicorn for bounded ARM Thumb instruction execution. Original
image untouched. Entry0x5A88, returning through sentinel; map scratch stack,
image and synthetic register-window storage. Hook hardware-only0x42D8 as a
no-op for accepted-path control, recording the hook; rejection paths never
reach it. Compare valid address, denied-range address and overflow, widths1/2/4
and invalid3. Memory writes captured; no board, network or programmer access.
Output script/report under evidence/firmware-audit/20260914-svc7c/.
Rollback: retain failed runs/corrections; no hardware rollback required.
An emulated null write does not establish writable real address0, an exploitable
caller, or VCN enablement. Those are distinct unrun requirements.

## Result

PASS16 exact-code cases using Unicorn2.1.4: normal0x0900C004 maps to
0x0100C004; rejected0x03700000/0x03900000/0xFFFFFFFC return NULL from
mapper and wrapper attempts store at0 for each valid width1/2/4, then
reports success0 in synthetic writable-zero memory. Invalid width3 returns5
without a store. Rejected paths do not execute the hardware-selector stub.
This reproduces a missing mapper-return check in0x5A88. Live address-zero
mapping, caller reachability, privilege and VCN usefulness are UNRUN.

## Caller reachability

The preserved ABL0..ABL4 bodies contain no decoded SVC0x7C instruction in
the bounded linear pass; raw immediate-byte scan also finds no `DF7C`
sequence. The confirmed callers are in t02 and t28. Therefore a direct
ABL-controlled path to this mapper defect is not established. Any BIOS
candidate must first show a caller that can pass the denied address/value
without editing a signed PSP body. No candidate image is justified yet.
