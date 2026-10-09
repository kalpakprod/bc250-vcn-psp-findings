# v004 — VCN driver WITH DEPEX, on the board's own booted image

Candidate: BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.bin
sha256 98b9c2bd0bd0324f5642d76b105fb7a1ba851ec16c5c89046b0bf585a5765ab8

Fix vs v003e (which hung early DXE): the driver FFS now carries a real
DEPEX section (TRUE, bytes 06 00 00 13 06 08) so DxeCore schedules it in
the normal dependency queue after PCI/AGESA, not the earliest no-DEPEX pool.

Base = pre-v003c-read-a.bin (the image that booted this morning,
sha 64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a).
Change = ONE new driver file (Bc250VcnUnlockDxe, GUID B6250780…) inserted
before Bds.ffs in the BASE'S OWN inner FV (0x43D000 -> 0x441000, 193 -> 194
files, capsule recompressed). Everything outside the capsule window is the
booted dump byte-for-byte (live APCB + NVRAM intact).

Verified:
- preflight 9/9 GO vs the booted dump: evidence/firmware-audit/
  20260924-v003c-postmortem/preflight-v004.json
- final FV sections = [0x10 PE32, 0x13 DEPEX TRUE], PE code byte-identical
  to the OVMF-validated driver (.efi loads, entry returns 0).

Rollback (exact prior working state): evidence/programmer/reads/
20260924-v003c/pre-v003c-read-a.bin (64973ba364…).

Flash procedure (unchanged gates): chip identity -> double read a==b ->
package sha -> flashrom write -> independent readback+cmp -> cold boot ->
sudo python3 /home/OWNER/vcn_unlock/postflash_vcn_check.py.
STOP on any mismatch. Flash only with operator approval.
