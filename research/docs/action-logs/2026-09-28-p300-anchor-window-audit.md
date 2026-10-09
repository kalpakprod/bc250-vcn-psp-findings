# P3.00 anchor-window audit

## Intent

Date: 2026-09-28. Determine whether the legacy TOCTOU rig's 320-byte window
`0x9DB560..0x9DB6A0` differs between the exact P3.00 stock and
SteamOS-BlackOut images, and whether the legacy payload matches either input.
Compare bytes only; do not interpret key contents. Keep only hashes and
differences in the report.

Inputs:

- Stock image: `dump/2.bin`, 16 MiB,
  SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Candidate image:
  `/home/OWNER/Downloads/Firmware(1)/Firmware/BC250_3.00_MeiMeiDXEv3-SteamOS-BlackOut`,
  16 MiB, SHA-256
  `7c636c8fe043b383d17881655eefb78a92cd4a0fbdc5b7ae0fb2bbdf8d77dee6`.
- Legacy payload: `candidates/toctou-rig-v001/include/anchor_original.h`,
  320 bytes extracted from the declared array. The source comment labels it
  “stock BC250 5.00 CLV”; that lineage is not independently established here.

## Result

The P3.00 stock and SteamOS-BlackOut bytes at this window are identical:
320/320 bytes match, SHA-256
`db40c2770dda6de90ae7852b76d1181a7fa6429e0efa3aa286dadfffed0498a8`.
The legacy payload differs from each P3.00 window in 314 of 320 bytes.
No payload bytes are included in the report.

For this exact P3.00 pair, the legacy 320-byte window is not a stock-versus-
candidate difference. It therefore cannot select between these two images at
that address. The 5.00-labeled payload is also not interchangeable with the
P3.00 window based on these bytes. This does not determine whether the PSP
reads the window or what validation it performs.

Sanitized comparison JSON is in
`~/.cache/bc250-single-flash-emulator/p300-anchor-window-comparison-v2.json`,
SHA-256
`09930d12d568049712286fc3fd58eae417ccf86a0af13a779b6c6db1a1f6b326`.
The JSON contains hashes, byte counts, and paths, not the compared payload.

No source image or payload was modified. No firmware was built or uploaded.
No board was connected, signalled, reset, or flashed.
