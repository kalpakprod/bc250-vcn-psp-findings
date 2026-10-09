# BC250 VCN / PSP findings

I've collected our AMD BC-250 VCN research here so other people working on the problem can use it. The repository covers PSP boot and signature policy, SMU mailboxes, GASKET/DF/NBIO isolation, BIOS/DXE experiments and SPI TOCTOU. It includes the approaches that failed and the conclusions we later corrected.

We have not demonstrated a working BC250 VCN codec or a successful hardware PSP TOCTOU run. These are research records from **kalpakprod**, dated **2026-10-09**. They are not a flash-ready BIOS or a tested installation kit.

## Where to start

1. Read [STATUS.md](STATUS.md) for the evidence behind the findings and the corrections to earlier claims.
2. Follow [RESEARCH-MAP.md](RESEARCH-MAP.md) through VCN power and isolation, SMU/PSP policy and TOCTOU.
3. Browse the [research](research/INDEX.md), [code](code/INDEX.md) and [evidence](evidence/INDEX.md) indexes.
4. Check [sources and attribution](references/SOURCES.md) and [missing local inputs](references/DEPENDENCIES.md) before trying to reproduce an experiment.
5. Download [CATALOG.json](CATALOG.json) for every cataloged path, or read [coverage and exclusions](references/COVERAGE.md). The catalog is too large for comfortable browsing on GitHub.

## Repository layout

```text
README.md                 Introduction and reading order
STATUS.md                 Findings, limits and corrections
RESEARCH-MAP.md           Connections between the research directions
CATALOG.json              Original paths, public copies and exclusions
research/                 Reports, experiment history, plans and context
code/                     DXE/probe sources, analyzers, models, builders and tests
evidence/                 Sanitized outputs from recorded experiments
references/               Sources, attribution, licences and missing inputs
```

The folders retain the original relative paths. For example, `scripts/psp_ps1_verify.py` is now at `code/scripts/psp_ps1_verify.py`. The private originals stayed in place. Markdown links point to the public copies where available, while quoted paths keep their historical names. Some scripts still need the original workspace layout and BIOS inputs that are not included here.

## What's here

The catalog lists **59,113 source paths**. We published **3,552 text and code records**, recorded a reason for each of **55,561 individual exclusions**, and listed **45 excluded source subtrees**. Those counts describe the collection, not a manual scientific review of every file in it or in the private workspace.

- VCN discovery and harvest observations, driver experiments, firmware-load results, Linux patches, failed probes, donor comparisons and power/isolation hypotheses.
- PSP, GASKET and APCB policy carriers, signature/key database structure, bootloader analysis, producer/consumer traces, mutable versus signed inputs and discarded bypass ideas.
- SMU mailbox handlers, transport limits, firmware windows and early-DXE/ReadyToBoot experiments, including the difference between a successful readback and a booting board.
- TOCTOU and Waveshare work, from external research and legacy-rig audits to host-side SPI models, image-specific serve maps and newer adapter code. Response timing, reset behavior and MISO ownership are still part of the open hardware questions.
- Negative results, contradictions, source revisions where recorded and later corrections. CU/core-unlock and clock work appears where it connects to these firmware paths. Unrelated DLSS and game work is excluded.

The introductions are in English. Most detailed reports are in Russian and remain in their original wording, rather than being translated or rewritten. Community research is credited to its authors.

## Before running anything

A saved PASS, `EFI_SUCCESS`, a successful build, SPI readback or an IP-discovery entry does not establish that a codec can encode or decode. Read [STATUS.md](STATUS.md) before relying on an old conclusion. Some scripts write SMN/MMIO or flash and can hang the board. They are not passive diagnostic tools.

[Licensing and attribution](references/LICENSING.md) explains the permissions recorded for the sources. Existing licences remain in place, and no blanket licence overrides third-party rights. Original ROMs, complete vendor firmware bodies, private exports and secret stores are not included.

[amd-bc250-bios-unlock](https://github.com/kalpakprod/amd-bc250-bios-unlock) is our separately maintained release repository. The findings here do not change its release or readiness claims.
