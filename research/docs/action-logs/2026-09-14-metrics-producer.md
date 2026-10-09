# Metrics producer trace — 2026-09-14, Asia/Almaty

## G7 correction: VCN firmware header parser offsets

The existing `enable_vcn.py` parser is wrong for Linux `common_firmware_header`:
it treats offset 0 as `hdr_size`, offset 4 as version, and offset 12 as a
64-bit ucode version. The public structure is `u32 size_bytes, u32 header_size,
u16 header_version_major/minor, u16 ip_version_major/minor, u32 ucode_version,
u32 ucode_size_bytes, u32 ucode_array_offset_bytes, u32 crc32`.
For the exact `navi10_vcn.bin` (404544 B, SHA-256
`ac5f2182b0ddee7a2886bf1239a47b4027becd0c37a1b0b6cac1f335393302c9`), correct
fields are size=404544, header_size=32, header=1.0, IP=2.0,
ucode_version=0x08118009, payload_size=404288, payload_offset=256,
CRC32=0xE99D512A (verified over payload). The old parser printed a spurious
64-bit version because it was shifted by four bytes. Any prior direct-load
claim relying on its displayed version is retracted; payload extraction itself
used the correct offset/size constants by coincidence and must be rechecked.

## Archived clock-state comparison intent/result

Root reads native_domain6_cycle.py, native_cycle_clock_enable_2026-08-25.out,
and clock_enable_direct_load_after_coldboot_2026-08-25.out. No re-execution.
The first log shows slot23 divider 0->32 and status 0x00090053->0x02090053.
After enable engagement its status is 0x02090050; slot22 remains divider18,
status0x01290050. Readback low status bits change 3->0; bit16 remains set.
This corroborates a clock-register transition, not codec function.

Neither native_domain6_cycle.py snapshot nor these textual snapshots collect
control+0x20 (source selector) or metrics slot record+8. They collect +0,
+8, +0x24; the verbose tool additionally prints +0x14. Therefore the newly
identified source-mode bits cannot be reconstructed from this evidence alone.
Do not claim full source-mode/divider consistency from these snapshots.

The direct-load log reports firmware header version32.0 and a 64-bit
ucode_version 0x0811800900000002, indicating a possible header field-width or
offset interpretation error; verify its parser before treating that stage as
validated. This is distinct from the earlier all-ones MMIO observation.

## Slot-source fields follow-up intent/result

Root follows source-selection fields using the isolated decoder trial.
No hardware changes; preserve scope to the identified functions.
0x2387C reads the slot control register at programming_address+0x20;
bits[2:0] become slot record+0x18 and bits[17:16] become record+0x19.
The base literal 0x17154 must be retained separately from the host SMN view.
It reads programming_address+0x24 bits[26:20] into record+2 and refreshes
metrics through 0x23CB4 for all slots in the selected domain.
0x2375C writes the same source selector at programming_address+0x20 and
updates record+0x18/+0x19; its source switch also contains a divider-status
poll at programming_address+0x24 bit16, without timeout in this path.
0x2362C writes its divider argument to record+2 and calls 0x23CB4.
Thus metrics zero is gated by source mode and divider state, not simply
the software power-state byte of domain6. Changing metric storage alone
cannot turn on clocks. Capturing the correct source-mode and divider state
is required to judge the previous clock operations.

## Interface comparison and slot binding

Intent: read the missing public driver header (no execution of external code),
derive layout, and compare field source addresses to the hash-pinned slot map.
Source retrieved 2026-09-14:
https://raw.githubusercontent.com/torvalds/linux/v6.8/drivers/gpu/drm/amd/pm/swsmu/inc/pmfw_if/smu11_driver_if_cyan_skillfish.h
Copyright AMD 2021, permissive license in header; MP1_DRIVER_IF_VERSION=8.
This is a public comparison interface, not verified current-board interface identity.

Its standard fixed-width layout places GfxclkFrequency at +0x44, GfxTemperature
at +0x46, SocclkFrequency at +0x48, VclkFrequency at +0x4A, DclkFrequency
at +0x4C, MemclkFrequency at +0x4E; Current and Average each occupy 116 bytes,
with 12-byte trailer for 244 total. This agrees with the retained export length
and the PMFW store widths/offsets, but exact live interface-version validation
has not been repeated in this run.

Combining the decoded producer and the independently extracted slot table:
- VclkFrequency <- float[0xFA1C]*1000, slot23 (0x17), record+8, domain6.
- DclkFrequency <- float[0xFA00]*1000, slot22 (0x16), record+8, domain6.
- SocclkFrequency <- float[0xF904]*1000, slot13 (0x0D), record+8, domain1.
- Slot24 (0x18) is still not named by these two video fields.

This is a corroborated static semantic binding, not measured current clocks or
codec success. Producer writes are decoded; the writer of slot record+8 remains
to trace. Existing pypcode stops at 0x23CCB in 0x23CB4; do not skip undecoded
instructions and infer their effects. Restore the documented Xtensa opcode
support or use an independent decoder before assigning writer semantics.

## Intent

Root traces table-6 export in hash-pinned PMFW 5c805026... using the existing
Xtensa decoder. Preserve a disassembly under the current SMU evidence directory.
No hardware accesses. Match metric field offsets only after inspecting the
exact driver-interface structure. Rollback consists of append-only corrections.

## Result

Q0 0x06 handler 0x1BA5C computes descriptor fields with stride36 using
literal 0x170F8=0xCA38, base-minus16=0xCA28. For table6 its callback field
is at 0xCA28+6*36+0x34=0xCB34, containing 0x29AEC. The callback path is
conditional on descriptor readiness (0x398FC) and the queue permission mask.

0x29AEC uses metric buffer base literal 0x17F24=0xCB54. Stores include:
- buffer+0x44 <- trunc(float[0x104C4+0x3A0] * 1000)
- buffer+0x48 <- trunc(float[0xF750+0x1B4] * 1000)
- buffer+0x4A <- trunc(float[0xF750+0x2CC] * 1000)
- buffer+0x4C <- trunc(float[0xF750+0x2B0] * 1000)
- buffer+0x4E <- trunc(result of 0x1E708(driver-state byte+0xD))
The 1000.0f literal is 0x447A0000 at 0x17284. Values are source state
converted into 16-bit exported fields, not necessarily physical measurements.

Current local cyan_skillfish_ppt.c consumes named Current.VclkFrequency and
Current.DclkFrequency, but its included smu11_driver_if_cyan_skillfish.h was
not found in the bounded project filename inventory. Do not assign names
to offsets 0x48/0x4A based on ordering alone. Exact interface layout and
writers of 0xF904/0xFA1C/0xFA00 remain next source-level targets.

This identifies a concrete metrics producer and its source addresses. VCN
clock names, actual power and codec operation remain unverified.
