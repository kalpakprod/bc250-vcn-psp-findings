I've put our BC250 VCN and PSP/SMU research in a public repository to share with people working on the same problem:

https://github.com/kalpakprod/bc250-vcn-psp-findings

It has the research history, code, sanitized evidence, donor comparisons and sources, including the failed approaches and corrections. The PSP/SPI TOCTOU work is there too. The README is in English and has a map and reading order, though most detailed reports are in Russian. Thanks for the update.

For the binning discussion, our recorded IP-discovery capture reported VCN 2.0.3 with harvest=0. That doesn't prove the block is physically healthy or rule out defective parts. It also isn't enough to conclude that VCN is permanently fused off. We haven't demonstrated a working BC250 codec, and some earlier “VCN power” leads turned out to be GFX/clock paths. I've kept those corrections in the repo.

The TOCTOU work has host-side models and image-specific tooling, but we haven't confirmed a hardware bypass on our board. MISO ownership/isolation, the actual read sequence and response timing are still unresolved.

I hope some of it is useful for the current VCN effort. The CU unlock, VRAM-temperature patch and BIOS governor work sounds interesting too. I'm sharing the research, not proposing a replacement for that BIOS work.
