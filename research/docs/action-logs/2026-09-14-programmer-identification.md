# Programmer identification — 2026-09-14 15:49 +05:00

## Intent

Operator connected the programmer after the power-off/clip instructions.
Root performs read-only chip identification and two full reads; no flash write.
USB identifies CH347T 1a86:55db. Restore the previously verified Arch flashrom
1.8.0-1 package in an isolated temporary prefix, requiring package SHA-256
b3804df8cf3a44461deb03bd0ac2edc37d616edc28eb95a9a0d3b3c16cc48316 and
binary SHA-2565ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c.
Read procedure: flashrom -p ch347_spi:spispeed=1.875M -r <new read-a/read-b path>.
Outputs: evidence/programmer/reads/20260914-identification/. Compare hashes,
bytes and known D10R/D19/stock; parse structure after matching reads.
Rollback: none required for chip reads. Preserve all captures; no original overwritten.

## Result

PASS: package and binary hashes match recorded approved flashrom1.8.0.
Tool restored at /tmp/bc250-flashrom-read-qWZxCK/usr/bin/flashrom.
CH347T detects Winbond W25Q128.V 16MiB at1.875MHz. Two sequential reads
exit0, each16777216 bytes, cmp exit0; SHA-256
c0f5f1c59cd0503d99cec9fffc5b95c8897a2deabfa42dd389c924d6be6cc4de.
libusb logged ignored udev action-change messages; reads nonetheless completed
and matched byte-for-byte. Raw logs retained beside captures.

Read-a differs from d20-restore/postwrite-d10r.bin in335 bytes, all below
0x20000, last difference0x1B8C. All bytes from0x20000 onward match restored
D10R, not D19. Firmware/APCB parsers pass PSP/BHD/APCB checksums and four FVs;
DFG words are0x007FFF00. Difference content is classified NVRAM-region drift,
not evidence of which setting or boot caused it. No SPI write performed.
Bootability today and VCN function remain unrun. Next operator step is detach
programmer with board power off, then normal mode1 boot for file retrieval.
