# External sweep 2026-09-17: guide 02, simpmix, Solarflare, Reddit thread

> Audit 2026-09-27: early hypothesis log. Read with 2026-09-17-t28-open-questions-workerA.md and 2026-09-17-staged-descriptor-hunt-workerC.md: later analysis corrects the write-value interpretation, computed error return and the existence of a flash pointer table. Historical commands and next steps below are not current authorization.

Provenance (skill research-provenance):

- katzzero/bc250-unofficial-community-guide @ `b6014e44` (2026-09-14), local
  clone `/tmp/bc250-unofficial-community-guide`, file `02-bios-and-firmware.md`
  § "VCN Hardware Video Decode" (lines ~574-601).
- simpmix/bc250-encoding-decoding-fix @ `c5a7942d` (2026-09-16), local clone
  `/tmp/bc250-encoding-decoding-fix`, `README.md`, `docs/hardware-notes.md`,
  `docs/vcn-registers.md`. GPL-3.0/GPL-2.0.
- Koloses/Solarflare @ `48ae555e` (2026-07-04), Sunshine fork + PyroWave
  Vulkan-compute codec; BC-250 named as canonical use case.
- Reddit r/BC250Gaming thread not fetched (network fetch deferred); guide
  section is the corroboration source for the same participants.

## F1 Findings

1. **Pivotal conflict — "eFused permanently" vs "harvest=0".** simpmix
   hardware-notes claims VCN is permanently eFused off and "cannot be
   unlocked" (single-source narrative; the repo is a Vulkan-compute
   encoder whose framing benefits from VCN being impossible). The guide
   (multi-participant, dated) states VCN 2.0.3 IP discovery shows
   **instance 0, harvest=0** — present, NOT harvested; the failure is a
   power-path/registration gap, not fused silicon. Per the evidence rules,
   observed IP-discovery bytes (harvest=0) outrank the eFuse narrative.
   Preserved as an unresolved contradiction; simpmix claim marked
   single-source.
2. **P5.00 (P5) base confirmation from community (mergeconflicted,
   02/09/2026):** on P5 BIOS, PSP reload files are ACCEPTED (a fix in P5
   changed the random values / CVE-related behavior), but the VCN clamp
   persists; active investigation = correcting/bypassing `saved_len` so a
   planted Navi VCN firmware restore completes. Independent support for
   operator's D25-adjacent interest in P5.00; ALSO relevant to clv (clv is
   built on 5.00).
3. **t28 decode corroboration (rukkusireland/daveconde, 24/08):** PSP t28
   blob fw_type 13 = VCN0; on working cards PSP writes 1 to SMN
   `0x0900C004` (UVD cold-reset) via `svc #0x7C`; on BC250 the fw_type-13
   load is rejected (`ITEM_NOT_FOUND`) — "best candidate yet for the root
   clamp release". Our loop run #1 static result (t28 five-domain program
   byte-identical in P5.00) is consistent: the clamp is not changed by the
   P5 recompile. VCN1 / type-58 = dead end (no 2nd IP-discovery entry).
4. **SMU surface:** th="0x1F/0x20/0x26" undocumented public cmds look
   non-VCN; PPSMC 0x8/0x9 (PowerDown/UpVcn) likely unimplemented in 11.8
   FW; rw_r_r_0644 claims full arbitrary SMU code execution via a message-
   handler bug (Cyan-Skillfish-only, missing bound check), with RPC patch
   in bc250-smu-unlock — matches our corpus repo.
5. **Firmware signing:** holde (14/08): VCN firmware signed by AMD, not
   Sony — corrects older Sony-key claims (incl. simpmix's doc).
6. **Fallback path (not unlock):** Solarflare + simpmix give working
   encode via Vulkan compute on the 40 CUs; simpmix auto-scales when the
   40-CU kernel unlock is active. Relevant to C1 only as a
   fallback-with-caveat, not as progress toward hardware VCN.

## Impact on campaign (C1-C3)

- C1 stays ALIVE: no observed-byte evidence of eFuse harvest; the missing
  piece remains the power-on/clamp-release chain (SMU message mapping /
  t28 fw_type-13 PSP acceptance), exactly our V1/V2/V3 targets.
- New V3 input to chase: `saved_len` bypass + P5 PSP reload acceptance
  (mergeconflicted thread); fw_type-13 `ITEM_NOT_FOUND` rejection point in
  t28 decode.
- C3 donor-exhaustion: adds simpmix docs/vcn-registers.md as a reference
  (with its eFuse conclusion flagged as contradicted), daveconde
  vcn2_register_map.md as a register map source.

## Gaps

- Reddit thread not fetched; guide quotes participants directly, treat
  thread as corroboration-only until fetched.
- rw_r_r_0644 "arbitrary SMU execution" is a participant claim (no local
  reproduction); bc250-smu-unlock already in corpus for verification.

## Follow-up decode (2026-09-17, root, capstone 5.0.7, t28 Thumb)

Inputs: /tmp/t28_old.bin (dump `ebd9a7d2`), /tmp/t28_new.bin (P5.00
`5b6828bf`), both extracted at PSP entry spi 0x984F00 + 0x200 wrapper.

F1. `svc #0x7C` is the SMN-write primitive: r0 = SMN address, r1 = value,
r2 = byte count (4). Confirmed by daveconde's report (PSP writes 1 to
0x0900C004 via svc #0x7C) reproduced in OUR t28 byte-for-byte.
F2. The clamp-release block exists in BOTH bodies and is structurally
IDENTICAL (old @0xFCC8, new @0xFD9C, shift +0xD4): - write 1 -> `0x0900C004` (literal @0xFCF8 old / 0xFCCC+ new) - write 1 -> `0x1F8A4` (literal @0xFCFC old) - loop i=0..4: svc #0x7C with (addr,value) from qword table pointer
literal 0xE188D8 -> body 0x188D8 (load base 0x00E00000); aborts on
nonzero status, `cmp r4,#5`.
The 0x1F8A4 + 0x1F8C4..D4 register set is the same five-domain program
found in loop run #1 — so run #1's "PSP boot program" and the
community's "root clamp release" are THE SAME code path.
F3. Table @0x188D8 qwords (old == new, byte-identical, 48B): first qwords
`7f2c3284 bc1debda ...` do NOT decode as (SMN addr,value) pairs;
either the load base assumption is wrong or the loop's r5 table is a
different structure. OPEN QUESTION OQ-V3a: resolve the table base and
entry semantics (dump 0x188D8: 7f2c3284 daeb1dbc 62 6a87b9 65c947f6
81a345a2 9a7d67e1 then zeros).
F4. No direct BL caller found to the block (0xFCC0..0xFCD2) — reached via
branch/tail-call. OPEN QUESTION OQ-V3b: map reachability from the
fw_type-13 load path and locate the `ITEM_NOT_FOUND` rejection site
(daveconde: fw_type 13 = VCN0 rejected on BC250). Anchor: 0xF8F0 call
site at 0xFBE2 handles fw_type branches (cmp #5 / #3).
Impact: the release program is present and unchanged in P5.00/clv — the
clamp persists not because the code is missing but because the path is
never taken (or the table is unresolvable). V3 target narrowed.

## OQ-V3b first pass (same run)

F5. fw_type dispatch table @0xE764 (old): cases 0x33, **0xD (13 = VCN0)**,
4, 8, 0x21, 0x22. The fw_type-13 case @0xE7BC DOES issue an
`svc #0x7C` SMN write: r0 = literal @0xE824 = **0x1F820** (inside the
0x1F8A4/0x1F8C4 five-domain register region), r1 = literal @0xE828 =
0x185103 (odd alignment — re-verify literal bounds), r2 = 4; then
status plumbing with r5=0xC22 (and 0x32/0x8022 for fw_type 0x33).
Interpretation: the fw_type-13 handler is present and CAN issue SMN
writes; the ITEM_NOT_FOUND rejection (daveconde) must occur BEFORE
this dispatch (catalog/descriptor lookup), not inside it.
Next: locate the descriptor/catalog lookup that returns ITEM_NOT_FOUND
for fw_type 13 (likely the caller of 0xE740-region function); verify the
r1 literal; then trace how the release block (F2) is gated.

## OQ-V3b second pass (same run)

F6. Verified: svc #0x7C call in fw_type-13 handler = write value 1 to SMN
0x1F820 (r1 literal bytecheck `03511800` = 0x00185103, still odd —
likely a pointer, semantic OQ-V3c).
F7. Dispatch function 0xE6A8 = service that (a) validates a 64-bit
descriptor from [r4], (b) reserves memory via 0x11460, (c) reads 4 B
via 0x17074, (d) dispatches on fw_type [r4+0x10]. Unknown fw_type ->
r7 = literal @0xE814 = **0xFFFF0006** (negative status — the
ITEM_NOT_FOUND-class rejection; daveconde's 0xffff0008 is adjacent).
F8. fw_type lookup table literal @0xE818 = 0xE18B70 -> body 0x18B70
(base 0xE00000): 12 consecutive u32 pointers 0x69D38 + i*8,
byte-identical old/new. Slot 13 -> 0x69DA0, which is OUTSIDE the t28
body (0x1A550) — PSP SRAM space. The descriptor chain for fw_type 13
resolves to memory NOT contained in the t28 blob.
CONSEQUENCE: the static trail leaves t28 here. The 0x69DA0 descriptor is
populated by another PSP component (or is an SRAM-built table). Next
decoder step (run #2+): sweep other PSP entries (types 0x30-0x34/0x44-0x51)
for the 0x69D38 pointer table builder, and decode r7=0xFFFF0006 callers to
find the exact rejection site seen on hardware.

## OQ-V3b third pass (same run)

F9. Full PSP sweep (all 19 P5.00 entries): literals 0x69D38/0x69DA0/
0xE18B70/0xE188D8 occur ONLY inside t28. No PSP-dir blob builds the
0x69D38 pointer table. The fw_type-13 descriptor at 0x69DA0 is PSP
SRAM/DRAM space populated outside the PSP directory — consistent with
the PSP "reload files" model (mergeconflicted): descriptors/firmware
are staged into SRAM from a non-PSP-dir source (UEFI FV / ABL path)
before dispatch. OQ-V3d (new): find the staging source — sweep UEFI FV
contents and ABL for the descriptor layout that lands at 0x69DA0.

## OQ-V3d first pass (same run)

F10. Whole-image sweep of P5.00 (16 MiB): literals 0x69D38 and 0x69DA0
occur NOWHERE outside the t28 body. The descriptor table at PSP SRAM
0x69D38 is not stored anywhere in flash as a pointer table — it is
built at runtime by PSP code (address arithmetic, not stored
literals), or delivered in an obfuscated/compressed staged blob.
Static conclusion: no simple flash-side pointer table exists to
patch; the runtime builder must be traced inside t28 itself (who
writes to 0x69D38-region) — OQ-V3e.
