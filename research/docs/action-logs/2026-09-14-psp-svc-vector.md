# PSP SVC vector trace — 2026-09-14

## Intent

Root traces t02 vector and SVC dispatch from the fresh readback rather than
assuming an on-die implementation. Source body begins SPI0x8EAD00; use ARM
mode for vectors and Thumb for functions selected by odd pointers. No writes
to chip or firmware. Historical a7_t02_flow.txt is a lead only.

## Observations

ARM vector at body+8 branches to0x240 (imm24*4+PC+8); historical target0x128
was incorrect. Handler extracts SVC immediate from saved Thumb/ARM instruction,
loads pointer0x4445 from literal0x3CC and BLXes to Thumb0x4444 in this image.
0x4444 applies caller-state checks and routes service<=0xDF to0x45A0.
0x45A0 subtracts0x51 and uses a relative jump table starting0x45E4.
For0x7C index0x2B, entry0x4690 is0x744 -> target0x4D28. That branch sets
r3=0 and joins0x4D5E, loading saved argument words and calling0x5A88.

This establishes an in-image SVC dispatch path, conditional on this vector
table being active. It retracts claims that svc0x7C necessarily resides only
in on-die ROM. Actual vector-base activation and the downstream0x5A88 checks
remain to trace. Presence of code is not a bypass or proof of hardware reachability.

## Downstream handler

`0x5A88` stores the caller value using byte/halfword/dword width `1/2/4`
after calling address mapper `0x2FCC`; invalid width returns `5`, valid store
returns `0` after `DSB`. The `svc 0x7C` branch passes mapper arguments with
zero mode/selector values. This confirms a mapped register-write primitive in
the in-image SVC path, but does not bypass mapper or privilege checks. Next
resolve `0x2FCC` and the active vector-base setup before considering a PEI
candidate.

## Mapper result

### Immediate G7 correction to argument attribution

The paragraph below conflated SVC r1 (VALUE) with mapper r1 (SLOT).
0x5A88 saves incoming r1 in r5 and explicitly sets r1=0 before BL0x2FCC.
Therefore svc7C always selects mapper slot0 on the traced branch; the t28
value1 does NOT select slot1. Its local results are0x0100C004/0x0101F8A4.
No user-controlled mapper-slot vulnerability is established by svc7C.
The suggested slot0x14/VCN-frame route is withdrawn: numerical equality of
CPU address spaces across PSP/x86 is not proof of a physical alias either.
Further work must use caller argument flow, not matching register names.

0x2FCC validates the supplied SMN-like address against ranges around
0x03700000/0x03800000/0x03900000, extracts low20 bits, writes a selector
entry through table pointer literal0x3020, then returns
`0x01000000 + (caller_r1 << 20) + (address & 0xFFFFF)`. For the t28 call
`caller_r1=1`, `0x0900C004` becomes `0x0110C004` and `0x1F8A4` becomes
`0x0111F8A4`. A hypothetical r1=0x14 would map the same low offset into
`0x0240xxxx`, which is the VCN discovery frame, but no existing signed caller
was found that supplies an attacker-controlled r1. Such an input would also
write selector-table state before the store. This is an interesting boundary
condition, not a safe exploit or a flash-ready modification.
- The range checks apply to address, not an obvious upper bound on caller_r1;
  resolve the table size/ownership and all SVC callers before calling it an
  implementation defect. Modifying signed t28/t02 to use r1=0x14 remains
  signature-blocked by the verified carrier experiments.
