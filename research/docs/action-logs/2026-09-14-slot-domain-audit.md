# Slot versus power-domain audit

## Consequence for unlock search

The next bounded dom6 field set is block `0x06D000`, repeated pairs at
`+0x054..+0x070` (`0x06900900`, `0xE8`) and single-bit candidates
`+0x044/+0x074/+0x084/+0x090/+0x098/+0x09C/+0x1D0`. These are observed
configuration values, not proven isolation controls. A write candidate must
be tied to a PMFW function and a measured transition before hardware use.
No blind register writes are authorized by this offline audit.

## Full-map follow-up intent

Root will preserve a machine-readable 27-slot/8-domain map in
evidence/firmware-audit/20260914-smu-address-trace/slot-domain-map.json.
Use direct table extraction, not hardware probes. Existing dump_domain_blocks.py
requires live hardware; it cannot provide a reproducible offline image map.
Add an offline hash-pinned extractor beside the output, compare its body
input with the exact D19 readback, and verify table offsets from disassembly.
Keep semantic clock names unknown pending an independent producer trace.

## Full-map result

PASS: extractor produced 27 bounded slot records and eight domain records,
verified exact body SHA and byte equality to D19 SPI slice 0x8FF100..0x93F100.
Output SHA-256 58a7042c863767db9f817b8b129f7cf440eaea732c9e195e7383871f55293dce.
Slots 22/23/24 program addresses 0x6D100/0x6D128/0x6D150 and share domain6.
This demonstrates the table relationship, not semantic identity as VCLK/DCLK.
The previous VCN-associated wording comes from historical experiment labels,
not an independently identified metrics producer or hardware naming source.
No exclusive bridge/isolation root cause is established by this table.

## Intent

2026-09-14, Asia/Almaty. Root rechecks the two table index spaces used by
0x2362C and 0x23B14. Preserve the measured mapping and independently compare
the extracted body against D19 readback. No hardware probes or image writes.
Existing disasm_xtensa.py is reused. Rollback: append corrections, preserve inputs.

## Initial static result

Body SHA-256 5c805026581ace101ba43ef4d0f6b34354f4a61461a1c78d2fa6a335a53d9936.
0x2362C multiplies its input by 28 and loads a byte at
[literal(0x178AC)+28*input+0x80]. That byte, NOT the original input, is
passed in a10 to 0x23B14 if the power state requires enabling.
The domain table is literal(0x17434)=0xF550, stride 72. Slot data begin
at 0xF790. Measured slot->domain: 14->2, 15->3, 17->4,
22/23/24->6. Thus calling 0x2362C with 14 does not establish power domain 14.
0x23BB8 iterates eight power records while inspecting 27 clock-slot records,
corroborating the separation. Semantic names of individual clocks are open.

## G7 correction

Retract the direct identification of 0x2362C(14) as PowerUpDomain(14).
The previous synthetic domain-14 doorbell addresses are unsupported by this
caller chain. Their timeouts remain real observations but cannot prove that
the actual VCN power-domain ACK was denied. Q3 0x5C has other arithmetic and
polling operations, so its hang location remains unobserved.
Image state bytes are static initial contents, not current hardware state.
