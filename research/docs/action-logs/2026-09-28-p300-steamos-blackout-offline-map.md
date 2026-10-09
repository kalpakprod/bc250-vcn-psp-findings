# P3.00 SteamOS-BlackOut offline map

## Intent

Date: 2026-09-28. Compare the owner-selected SteamOS-BlackOut P3.00 image
against the exact preserved P3.00 stock dump and produce a synthetic host-model
map. Inputs must match their recorded SHA-256 values before analysis. Reuse
the existing byte-diff merge helper and firmware parsers; preserve both source
images unchanged.

Inputs:

- Stock: `dump/2.bin`, 16 MiB,
  SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Candidate:
  `/home/OWNER/Downloads/Firmware(1)/Firmware/BC250_3.00_MeiMeiDXEv3-SteamOS-BlackOut`,
  16 MiB, SHA-256
  `7c636c8fe043b383d17881655eefb78a92cd4a0fbdc5b7ae0fb2bbdf8d77dee6`.

The proposed map is explicitly synthetic: default to the candidate and select
stock for merged changed ranges on read index 0. Verify every merged range at
its start and end with the host model, then verify read index 1 returns the
candidate. This does not assert that the BC-250 reads those addresses in this
order, nor that the legacy PIO can act on the same transaction.

Write only generated JSON and logs to
`~/.cache/bc250-single-flash-emulator/`. No firmware or BIOS image changes,
board connection, signalling, reset, upload, or flash operation.

## Result

Both inputs were 16 MiB and matched the pinned hashes. The existing
64-byte-gap diff merger found 1,440,179 changed bytes in 10,867 contiguous
byte-difference ranges, merged into 11 serve ranges covering 1,453,608 bytes.
PSP directories had matching checksums and 19 entries on each side, with no
entry-body or size differences. BHD checksums matched on both sides; one
type-`0x60` entry body differed. APCB checksums matched; sizes were 2,928 bytes
for stock and 2,916 bytes for the candidate.

The cache-only JSON map at
`~/.cache/bc250-single-flash-emulator/p300-steamos-blackout-serve-map.json`
pins both input paths, sizes, and hashes; records all 11 merged ranges and
parser results; and labels its `0x03` read-index choice as synthetic. Its
SHA-256 is `df948fb3cd292a6e944030c8d9edb6d6db931993b989b4ae536a81d31a1736eb`.
An independent boundary pass checked the first and last byte of every merged
range against both configured images: 44 assertions passed, exit code 0. The
model returned stock for read index 0 and candidate for index 1.

A stronger host check then compared every byte in all 11 merged ranges, both
read indices: 22 synthetic transactions and 2,907,216 byte comparisons passed,
exit code 0. This verifies the configured host map across its entire served
coverage, not the RP2350 PIO implementation.

Evidence class: byte inventory is direct offline comparison; the read-index
result is `emulated-or-host-tested`. Neither establishes PSP transaction
order, correct TOCTOU target semantics, PIO readiness, or hardware behavior.
No image was written or modified. No firmware was built or uploaded, and no
board was connected, signalled, reset, or flashed.
