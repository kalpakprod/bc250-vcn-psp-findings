Thanks for the update. I've been working on BC250 VCN and the surrounding PSP/SMU firmware paths too, so I put my research together in a separate public repository:

https://github.com/kalpakprod/bc250-vcn-psp-findings

It includes the research history, code, sanitized evidence, donor comparisons, failed approaches and corrections, plus the PSP/SPI TOCTOU work and the sources behind it. The English README has a map and a reading order; much of the original detailed material is in Russian.

One data point that may be useful for the binning discussion: our recorded BC250 IP-discovery capture reported VCN 2.0.3 with harvest=0. That does not prove the VCN is physically healthy, or rule out defective parts, but it also is not enough to conclude that the block is permanently fused off. We have not demonstrated a working BC250 codec. Several earlier “VCN power” leads turned out to be GFX/clock paths, and those corrections are included.

For PSP TOCTOU, we have host-side models and image-specific tooling, not a confirmed hardware bypass on our board. MISO ownership/isolation, the actual read sequence and response timing are still unresolved.

Sharing it in case any of the findings help with the current VCN effort. The CU unlock, VRAM-temperature patch and BIOS governor progress sounds interesting too—this repository is a research handoff, not a replacement for that BIOS work.
