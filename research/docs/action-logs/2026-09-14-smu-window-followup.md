# SMU window follow-up — 2026-09-14, Asia/Almaty

## Feature framework assessment

- The recorded feature callback table identifies feature 4 (`0x23C24`) as
  `PLL_POWER_DOWN`, not a VCN power-on handler; feature 21 (`0x2496C`) is
  `PROCHOT`, not a VCN domain handler. Both callbacks install periodic
  callbacks through `0x1B1E4` and return 1. Their earlier proximity to the
  power code was not sufficient evidence of VCN relevance.
- The central feature framework `0x1D940` reconciles 64 requested/current
  bits and invokes enable callbacks at table+0x10 or disable callbacks at
  table+0x110. It provides policy control, but no feature bit in the
  inspected table is identified as a VCN enable/isolation release.
- Therefore a speculative feature-mask sweep is not justified. The next
  promising evidence target is the actual register programming behind the
  native domain power callback, including the precondition registers and
  domain table semantics, rather than enabling every dormant feature.

## G7 correction: Q3 0x21 is not a power-domain command

The historic note that message `0x21` handler `0x249DC` calls `0x23B14`
is disproved by a fresh decode of the exact PMFW body. `0x249DC` only reads
the message argument through `0x0FFC`, calls `0x2494C`, then returns status 1;
`0x2494C` performs float/frequency arithmetic and stores a state value. No
call to `0x23B14` occurs. The earlier "sendable PowerUpDomain message 0x21"
lead is retracted. Q3 `0x5C` remains the statically confirmed frequency handler
that reaches the domain-14 power path; its hardware behavior is already
classified as a no-timeout wedge when the domain ACK is absent.

## Array-consumer investigation intent and coordinate correction

Root will trace the address array around body 0x150B0 using existing Xtensa
decoder and direct little-endian pointer reads. No hardware operation.
Direct scan of body SHA-256 5c805026... finds C230 at 0x150C0, not 0x151C0
(the latter was a wrapper-relative offset). It is array index 4 among
0x09003230, 0x09004230, 0x09005230, 0x0900B230, 0x0900C230, ... .
Thus absence of three exact scalars did not exclude a computed VCN recipe.
C230 is four bytes below C234, not C830 (difference to C830 is 0x600).
Previous source-exclusivity claims are retracted; the consumer remains to trace.

## Array consumer found: static-analysis

Pointer literal at 0x17390 equals 0x150B0. L32R instruction at 0x1DD7F
loads that pointer in function 0x1DD74. Full function [0x1DD74,0x1DD9B)
iterates 29 dwords, skips zero entries and writes zero to
0x00FFFE00 + (entry & 0xFFFFF) + 0x200. Literals 0x1711C=0xFFFFF,
0x1713C=0x00FFFE00 were read directly, little-endian.
For array index 4 (0x0900C230), the local store target is 0x0100C230.
This is a THIRD local access context, distinct from native 0x01100000 and
selectable window 0x02C00000. Do not assume the three windows alias hardware.
The existing every-byte direct-call scanner found no direct calls to 0x1DD74
in [0,0x3A000). Indirect registration or unused code remains possible;
execution timing and hardware meaning of the zero stores are not established.

## Array consumer refinement

- The 29-entry table enumerates many `0x090xxxxx230` values, not only C230:
  entries include C230, 04230, 05230, 0B230, 10230 and others. Function
  0x1DD74 masks each to a 20-bit offset and clears the corresponding
  `0x01000000`-window dword. It resembles a bulk per-block reset/clamp routine,
  not an obvious VCN enable routine.
- No direct code pointer or direct call to 0x1DD74 was found by existing scans.
  Its registration and timing remain unknown; do not treat it as an unlock.

## Follow-up intent and G7 correction: distinct call paths

Root rechecks the IPC caller and corrects the erroneous attribution below.
No hardware operations. Preserve disassembly and hashes in the existing evidence directory.

The section `Critical address-path correction` is RETRACTED. D19 Q3 0x2C
calls 0x2A74 directly; the decoded 0x2A74 calls 0x30B0 (cache maintenance),
not 0x233E8. There is no demonstrated edge connecting that write to 0x233E8.
The selector-based local window address 0x02C0C830 therefore remains the
supported local destination for D19, with selector low16=0x90; physical
target identity is unresolved. Even hypothetically applying the OTHER path's
formula yields 0x0110C830, not the incorrectly reported 0x0110CC30.
The native 0x233E8 special-range branch does not establish D19 core routing.
Also, 0x246F4 has a separate confirmed call at 0x24732 to 0x1B514;
the claim that the special-range branch is its only caller is retracted.

## IPC sender completed decode

Existing disasm_xtensa.py on the hash-identified body resolves 0x10D0:
base literal 0x01210600; payload dwords at +0x100/+0x104 (0x01210700/704),
command/status at +0x118 (0x01210718). It acquires a software state mask
0x20000 through 0x2268, checks status bit31, writes two payload dwords and
(operation&0xFF)<<16, then polls bit31 until set WITHOUT TIMEOUT. On
completion it copies back both payload dwords and returns status low16;
on initial busy it releases the state mask through 0x231C and returns 0xFF.
Byte flag 0x7AD4 tracks a pending request. This is sender-side protocol only:
the peer and receiver semantics are not independently verified here.

The helper 0x2268 is thus consistent with synchronization/state-mask handling;
its 0x400000 use in Q3 0x98 does not prove a VCN feature-enable operation.
Calling IPC blindly could hang SMU indefinitely even with a bounded host timeout.

Existing direct-call scanner over [0,0x3A000) returns two candidate callers
of 0x1B514: 0x2341C and 0x24732, both independently present in decoded code.
It returns ten call candidates for 0x10D0: 0x1B46B, 0x1B47F, 0x1B509,
0x1B520, 0x1F7C5, 0x1FA25, 0x278B2, 0x31128, 0x35E61, 0x35EB0.
Linear every-byte scanning can match data; uninspected callers are candidates,
not proof of reachable code. No hardware test or unlock claim is made.

## Intent

Root continues offline decoding of 0xFFC, 0x29F8, 0x2A74 and Q3 0x98.
Record exact input provenance and correct earlier interpretations before any
candidate design. No hardware operations. New evidence goes under
`evidence/firmware-audit/20260914-smu-address-trace/`.
Rollback: retain historical records and append corrections; original bytes remain untouched.

## Direct findings and corrections

- Input is the 262144-byte `recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body`,
  SHA-256 `5c805026581ace101ba43ef4d0f6b34354f4a61461a1c78d2fa6a335a53d9936`.
  It equals D19 SPI readback bytes starting at `0x8FF100`, not `0x8FF200`.
  The latter slice hashes to `f546f118...`. These coordinate systems differ by 0x100;
  do not interchange file offsets. Handler offsets here use the former body.
- 0xFFC reads an argument through a queue descriptor: descriptor base literal
  0x7000, stride 12, pointer field +0xC, dereference with MEMW.
- Q3 0x2B at 0x27D1C obtains the argument and stores it at 0x8B08+4.
- Q3 0x2C at 0x27D34 obtains the value and calls 0x2A74 with
  (high=0, low=[0x8B0C], value=argument, width=2).
- 0x2A74 is a window WRITE primitive; 0x29F8 is its READ counterpart.
  Width 0/1/2 selects byte/halfword/dword. Both mask local offset with
  0xFFFFF, but also replace the low 16 bits of selector register 0x03220038
  using SRC with shift 20. The local access address is
  0x02BFFF80 + (low & 0xFFFFF) + 0x80 = 0x02C00000 + offset.
  Therefore a low-20-bit mask alone does NOT prove upper address bits lost.
  For high=0, low=0x0900C830: selector low16=0x0090, local address=0x02C0C830.
  Physical meaning of the selected window is not established by this decode.
- Q3 0x98 at 0x280E0 reads an argument. For nonzero argument it calls
  0x2A74(0, argument, 0xFF, 2), then 0x29F8(0, argument, 2), and reports status 1.
  It is a FIXED-0xFF write followed by readback, not a general (address,value)
  primitive. The zero-argument branch calls 0x2268 twice with 0x400000;
  helper semantics remain unresolved. No hardware call is justified.
- RETRACT earlier description that 0x98 helpers merely modify a state table.
  D19 and the retained replay library use the same 0x2B/0x2C sequence;
  replacing that pair with 0x98 would change both the written value and add a read.
- The window routines mask interrupts locally but this is not proof of exclusion
  against a second SMU core or another bus master. Selector ownership, helper
  0x30B0 and alternate native SMN paths remain open.

## Second-core IPC decode

- `0x1B514` packages its two arguments into a stack pair and calls the internal
  IPC dispatcher `0x10D0` with message `0xFE`; it has no register-address check
  or local SMN store of its own.
- `0x1B4F8` is the retrying variant: it packs `(arg2 | arg3<<16)`, calls the same
  dispatcher with operation `0x08`, and retries while the return value is
  `0xFFFFFFFF`. This distinguishes the second-core path from the normal direct
  store in `0x233E8`.
- No existing Q3 handler table entry directly exposes `0x1B514`; the known path
  is reached internally from the power/domain code when an address falls inside
  the special range. A direct caller or message-0xFE payload layout is still
  required before any BIOS or hardware experiment can use it.

## Verification boundary

Static disassembly using existing disasm_xtensa.py and pypcode 4.0.0, plus
direct little-endian literal reads. L32R output has a spurious high address
prefix in this decoder; literal offsets are interpreted in the 32-bit image
and corroborated from instruction encoding. No codec or hardware acceptance claim.

## Helper decode follow-up

- `0x30B0` is a cache/write-buffer maintenance helper: it performs `dhwbi` over
  a length rounded to 16 bytes, then `dsync`. It does not select an SMN window.
- `0x2268` sets feature/state bit `0x400000` in a state word at `state+0x2C`
  and mirrors the bit into a secondary word at `state+0x68`; an existing bit is
  checked first and a notification call is made only when needed. This explains
  the zero-argument Q3 `0x98` branch as a feature-enable operation, not an SMN
  write primitive.
- The nonzero `0x98` branch remains a fixed-FF probe: write FF to the supplied
  window offset, read the same offset as a dword, and return success. It cannot
  express the donor values required by the VCN gasket.

## Critical address-path correction

- The complete `0x233E8` primitive shows the actual destination split. It first
  validates the access with `0x29CD4`; normal addresses are written directly to
  `0x10FFE00 + (addr & 0xFFFFF) + 0x200`. Only addresses in the range bounded by
  literals `0x5AFFF..0x5B7FF` are redirected through IPC call `0x1B514` to the
  second SMU core. `0x0900C830` is outside that range, so it follows the direct
  master path and resolves to `0x0110CC30` after masking and the `+0x200` command
  offset. The earlier text suggesting a generic `0x02C00000+offset` local
  destination is retracted: that was an incorrect interpretation of helper
  `0x2A74`'s selector arithmetic.
- This materially changes the next hypothesis: D19's C830 operation is a direct
  master-side store to the `0x0110CC30` register, while the special second-core
  routing is unavailable for this address class. The VCN unlock question now
  includes whether C830 must be issued through an alternate core/window path.

## PMFW caller scan and VCN relevance

## PMFW literal scan

- A little-endian scalar scan of the exact 262144-byte PMFW body finds no
  literals `0x0900C234`, `0x0900C830`, or `0x0900C834`. The body contains only
  the native window base `0x10FFE00`, range bounds `0x5AFFF/0x5B7FF`, and the
  selector literal `0x03220038`.
- This rules out a simple PMFW hardcoded VCN-bank recipe in this blob. The
  `0x0900Cxxx` addresses originate in x86/PSP gasket data or caller-supplied
  arguments, not from an obvious SMU firmware constant.

## Follow-up correction: nearby VCN control literal

- A second scan of every byte (not only aligned words) finds one PMFW literal
  `0x0900C230` at body offset `0x151C0`. This is four bytes before the D19
  target `0x0900C830` and may be a base/control selector, but the surrounding
  bytes do not decode as a valid function entry and no direct xref has been
  proven. Treat it as an observed-byte lead, not a VCN register assignment.
- Exact D19 target literals `0x0900C234/830/834` remain absent from PMFW. The
  x86/PSP gasket address set is still the confirmed source of those exact values.

- `0x1F038` is the frequency-apply handler previously associated with Q3 `0x5C`. It gates on driver-table byte `0xCEC8+0xF6`; after the gate opens it derives domain-14 parameters and calls `0x2362C` (PowerUpDomain(14)) when the requested value exceeds the current value. This is a real firmware-side VCN-cluster power route, but its domain ACK is hardware-denied on the board and the handler has no timeout.
- `0x24748` calls `0x246F4` for domains 19,20,21 and then powers domain 5 down; it is a cleanup/transition helper, not the VCN domain-14 route.
- The `0x10D0` sender has a software busy/status protocol and no timeout; its peer cannot be safely invoked without identifying the receiver and payload contract. No direct Q3 command exposing a user-controlled second-core VCN write was found.

## Current conclusion

The strongest exploitable defect remains the firmware's unbounded polling of hardware-denied domain power ACKs in `0x2362C/0x23B14`. It can turn a malformed or unauthorized VCN power request into an SMU wedge, but it does not itself provide an enable value. A successful unlock requires an earlier transition that releases the domain/isolation gate, or a valid boot-time policy accepted by PSP. Neither is established by this decode; no BIOS image is built or flashed in this step.
