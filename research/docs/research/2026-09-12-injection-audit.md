# BC-250 Boot-Chain Injection Audit (2026-09-12)

> Historical competing model. The two-lock explanation and next-action list below are not current acceptance evidence or permission to flash. Compare the same-date unlock-paths map, which records a DFG grant already present in D-series experiments. Preserve both accounts rather than selecting a cause from wording alone.

Scope: enumeration of every boot-chain surface that can carry an injected
VCN unlock, with its verification status and evidence class. Sources:
VCN-LOCK-MECHANISM.md (§1-11), memory/firmware-audit.md (2026-09-12),
today's live experiments S2-L5b/L6/L7/L8/L9.

## G7 corrections first (two premature verdicts today)

1. "The dom14 config space is bus-isolated" (S2-L9) — WRONG PATH, not a dead
   region. My write used `smu.smn_write32` = the sec mem64 SMN write
   (msgs 0x2B/0x2C). The FIELD-PROVEN path to the 0x0900Cxxx bank is the
   Q3 msg 0x98 smn_write32 (VULN-1 PoC: all 56 bank records ACCEPTED with
   readback OK; VCN-LOCK-MECHANISM §A3). The S2-L9 wedge = the wrong
   transport, not the region.
2. "The runtime unlock is closed" — PREMATURE. It is closed ONLY for the
   mem64-transport writes into the VCN cluster. The two-lock model
   (§7.4) explains every wedge of the campaign WITHOUT a dead bus (see the
   unified theory below).

## The unified theory (fits every observed fact)

Lock 1 — GASKET APERTURE (the 0x0900Cxxx VCN bank, HWID 12):
programmable AT RUNTIME via the SMU Q3 msg 0x98 (VULN-1, field-proven).
The stock gasket never programs this bank; the donor's program is known
byte-exact (56 records). Our runtime gasket (59/59 xx234) covered only
the enable-bit family, NOT the aperture program.

Lock 2 — DFG POWER GRANT (the APCB DFG policy, PSP-applied at boot):
the DFG table grants per-master permissions; the VCN master falls under
the wildcard baseline perm 0x1f — WITHOUT bits 5/6 (the power/reset
grants; the explicit rows sub 06 -> 0x63 and sub 08 -> 0x23 HAVE them).
WITHOUT the grant, the power transaction to the VCN domain is DENIED —
it never completes. This matches the exact failure signature of
S2-L5b (the fw poll wedge), S2-L8 (the direct request: accepted, ack
never asserts), and the born-locked statuses (dom14 0x41, dom17
0x80000002).

Both locks must open. Today's experiments opened NEITHER at the right
place: the gasket work opened lock 1 partially (the enable bits, not the
aperture program), and nothing ever addressed lock 2 — the DFG grant.

## Injection surfaces, ranked

### S1. APCB DFG region — UNSIGNED, checksum-only — THE primary surface

- Status: NOT PSP-signed. Verification = a single u8 checksum @+0x10,
  the algorithm SOLVED and verified on 12/12 samples (§7.2), the tool
  exists (apcb_cks_brute.py). The APCB-only modified images BOOT
  (field-proven: the community mods and our own D3 builds treat the APCB
  as freely patchable; the board restored to APCB-only 6b1fe8ef boots).
- What it controls: the per-master permission table (the DFG types 5/6,
  §7.3). Patch candidates READY (§7.4): (i) the wildcard baseline
  `00 ff 1f 00` -> `00 ff 7f 00` (1 byte) or (ii) the explicit row
  `01 0c 63 00` (+8 bytes, SizeOfApcb +8). The sub=0x0C mapping to the
  VCN (HWID 12) is inferred, not hardware-verified — the D3-A flash
  test settles it.
- Flash images ALREADY BUILT AND VERIFIED: D3-A (the APCB patch alone,
  the control) and D3-B2 (the full combo) — 26/26 PASS, the manifests +
  the verifier shipped in recon/d3/package/.

### S2. x86 UEFI/DXE region — UNSIGNED, field-proven modifiable

- Status: NO RTM/signature entries in the PSP/BHD directories; the
  community mods change 1,005,160 bytes of FVMAIN in production (§11).
- What it can carry: a DXE driver executing at DRIVER_ENTRIES phase —
  our Bc250VcnUnlockDxe (built, validated PE32+ x64) or the ProbeApp v4
  (the zero-flash USB vehicle). It can fire the SMU Q3 msg 0x98 aperture
  program + the dom6/dom14 power requests PRE-BOOT, every boot,
  without any flash besides the DXE volume edit.
- This surface needs NO signature bypass — only a correct FFS/FV
  rebuild (the tools exist: uefi_ffs_hunt.py et al.).

### S3. SMU runtime transports — NO FLASH NEEDED, partially field-proven

- The Q3 msg 0x98 smn_write32 = the PROVEN writer of the 0x0900Cxxx bank
  (VULN-1). The msg 0x61 repoint = the proven execution vector. The dom6
  power + the clock slots = proven live (today).
- After the DFG grant exists (S1 or S2), the FULL unlock sequence is
  runtime-only: aperture (0x98, 56 records) -> dom6 (0x61/proven) ->
  dom14 request (0x1100084, the doorbell) -> the ack -> the BAR5
  arbiter.

### S4. The signed carriers (gasket 0x24, TOS policy 0x45) — BLOCKED, bypassable

- The $PS1 signature (RSA-2048, kid 96ea7cfe, the on-die verification,
  the offline verification not reproduced) = the hard blocker for the
  flash EDITS of these two blobs. The D3-B2 (the unsigned rebuilds)
  failed to boot to video twice — consistent with a hard reject (or the
  boot-time halt; the SSH-at-t+90s discriminator was never run).
- BYPASS: do not edit them. Lock 1 opens at RUNTIME via msg 0x98 (S3);
  the boot-time carrier edit is NOT required.

### S5. DEBUG_UNLOCK 0x13 / the PSP keys — CLOSED (unchanged)

- RSA-2048 vs the AMD key; the challenge/token protocol; A1-A6 closed.

## The resulting unlock plan (all evidence-backed, no signature blockers)

Stage F (flash, needs the programmer + the operator approval):
flash D3-A (the APCB DFG grant patch — 3 bytes + the checksum, the
control image, built and verified). The ONLY unsigned-surface edit.
Expected alone: no unlock (the aperture lock still closed) — it is
the grant layer.
Stage R (runtime, per boot, no flash):

1. the aperture program via Q3 msg 0x98 (the 56-record VULN-1 replay);
2. dom6 power + the clock slots (the proven 0x61/0x23b14 sequence);
3. the dom14 request doorbell (0x1100084 <- status|1);
4. the bounded ack read (0x1100085 bit8) — with the grant, the ack
   should assert; without it, the same wedge signature returns;
5. the BAR5 arbiter verdict.
   Order: R-only first (the current board state, if the mailbox survives a
   fresh boot: the msg 0x98 writes were ACCEPTED in VULN-1 without any
   DFG patch — the aperture alone may already change the dom14 picture),
   then F+R if the grant hypothesis holds.
   Risk: R = the proven classes only; the wedge signature may recur on the
   dom14 step (cold cycle). F = the reversible APCB edit with a verified
   rollback image.

## Open items

- The sub-number for the VCN master in the DFG table (0x0C = HWID 12 is
  inferred) — the D3-A flash test or a UART trace settles it.
- The dom17 bit31 marker decode.
- The D3-B2 SSH discriminator (only if a flash window happens anyway).
