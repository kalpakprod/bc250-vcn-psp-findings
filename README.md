# BC250 VCN / PSP findings

A public research handoff from **kalpakprod**: VCN enablement attempts, AMD PSP boot/signature policy, SMU mailbox reverse engineering, GASKET/DF/NBIO isolation, BIOS/DXE experiments and SPI TOCTOU work on AMD BC-250.

**No working BC250 VCN unlock or successful hardware PSP TOCTOU is claimed by this repository.** This is a research corpus, including failed experiments, rejected hypotheses and corrections—not a flash-ready BIOS or a tested installation kit. Snapshot: **2026-10-09**.

## Start here

1. [Current evidence and corrections](STATUS.md): what the records support, and what they do not.
2. [Research map](RESEARCH-MAP.md): VCN → power/isolation → SMU/PSP → signed policy → TOCTOU.
3. [Research index](research/INDEX.md), [code index](code/INDEX.md), [evidence index](evidence/INDEX.md).
4. [Source links and attribution](references/SOURCES.md), [local-input dependencies](references/DEPENDENCIES.md).
5. [Full path catalog](CATALOG.json) and [coverage/exclusions](references/COVERAGE.md). The catalog is large; use the readable indexes above or download it.

## Repository layout

```text
README.md                 English entry point and reading order
STATUS.md                 Evidence boundaries and superseded conclusions
RESEARCH-MAP.md           How the research directions fit together
CATALOG.json              Original paths, release paths, provenance and exclusions
research/                 Authored reports, chronology, plans and historical context
code/                     DXE/probe sources, analyzers, models, build scripts and tests
evidence/                 Sanitized recorded outputs, not fresh hardware verification
references/               Attribution, sources, missing inputs and disclosure decisions
REPLY.md                  Short English reply accompanying this repository
```

Original relative paths are retained under each section. For example, a script originally at `scripts/psp_ps1_verify.py` is under `code/scripts/psp_ps1_verify.py`. This allows provenance tracking without moving the private original workspace. Existing Markdown links were adapted; quoted historical paths remain historical. The layout is archival: some scripts need the original source layout and non-bundled BIOS inputs.

## What is included

The catalog records **59,113 individual source paths**: **3,552 included text/code records**, **55,561 individually explained exclusions**, plus **45 explicitly excluded source subtrees**. These numbers describe a topic/path inventory, not manual scientific validation of every file or every file in the entire private workspace.

- **VCN:** IP discovery/harvest observations, driver experiments, firmware-load outcomes, Linux patches, power/isolation hypotheses, failed probes and donor comparisons.
- **PSP / GASKET / APCB:** policy carriers, signature/key database structure, bootloader analysis, consumer/producer traces, signed versus mutable surfaces and discarded bypass ideas.
- **SMU / DXE:** mailbox/handler research, transport limits, firmware-window behavior, early-DXE/ReadyToBoot experiments and boot-versus-readback distinctions.
- **TOCTOU / Waveshare:** original research provenance, legacy rig audits, host-side SPI models, serve-map tooling, newer authored adapter code, response timing/reset/MISO ownership constraints.
- **History:** negative results, contradictions, source revisions where recorded, and corrections. CU/core-unlock and clock research is retained when connected to these firmware paths; unrelated DLSS/game research is not included.

The English summaries guide a largely **Russian-language original research corpus**. The source reports were not silently translated or rewritten into a new narrative. External community work is attributed, not presented as our own.

## Using this material

Read [STATUS.md](STATUS.md) before reusing a conclusion. A saved PASS, `EFI_SUCCESS`, compiler result, successful SPI readback or permissive IP-discovery entry is not a successful codec test. Historical scripts can write SMN/MMIO/flash and hang hardware: do not run them as passive diagnostics.

See [licensing and attribution](references/LICENSING.md). Original licences are retained where present; there is no blanket licence that overrides third-party rights. Original ROMs, complete vendor firmware bodies, private exports and secret stores are not bundled.

A related, separately maintained release repository is [amd-bc250-bios-unlock](https://github.com/kalpakprod/amd-bc250-bios-unlock). This research snapshot does not change that repository's release/readiness claims.
