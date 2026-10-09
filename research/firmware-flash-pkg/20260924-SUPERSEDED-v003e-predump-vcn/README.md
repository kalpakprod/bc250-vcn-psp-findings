SUPERSEDED — DO NOT FLASH. # v003e — VCN hardware enable built on the board's OWN booted image

Candidate: SUPERSEDED-BC250_pre_dump_vcn_own_fv_v003e.bin
sha256 b67e59d7ce32dd977bf0fc16885ed46021f1851e0c5acbbcb57f45fea7155934

What it is:
- base = pre-v003c-read-a.bin (the image the board ran this morning,
  sha 64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a)
- change = ONE new DXE driver file (Bc250VcnUnlockDxe, GUID B6250780…)
  inserted before Bds.ffs in the BASE'S OWN inner FV (grown
  0x43D000 -> 0x441000, 193 -> 194 files, capsule recompressed).
- Everything outside the capsule window = the booted dump byte-for-byte,
  including the live APCB token block and NVRAM.

Why v003e after v003c: the v003c full write factory-reset the live APCB
tokens/NVRAM; v003e by construction cannot (diff is the capsule window
only). Preflight vs the actual booted dump: 9/9 GO
(evidence/firmware-audit/20260924-v003c-postmortem/preflight-v003e.json).

Rollback (exact prior state): evidence/programmer/reads/20260924-v003c/
pre-v003c-read-a.bin (64973ba364…), write via the same CH347 procedure.

Flash procedure (unchanged gates): chip identity -> fresh double-read
(a==b, sha recorded) -> package sha -> flashrom write -> independent
readback+cmp -> cold boot -> sudo python3
/home/OWNER/vcn_unlock/postflash_vcn_check.py.
STOP on any mismatch. Flash only with operator approval.
