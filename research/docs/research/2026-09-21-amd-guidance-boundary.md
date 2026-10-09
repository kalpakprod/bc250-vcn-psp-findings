# AMD voltage guidance boundary for BC-250

Date: 2026-09-21. Scope: the AMD Ryzen Master 2.9 Reference Guide and the pinned BC250-specific `bc250_smu_oc` README only. Evidence class: `external-primary` for AMD; `external-community-source` for the README. This is a source comparison, not hardware evidence or a recommendation to set a voltage.

## Finding

**No universal or BC-250-specific AMD recommendation for manual SoC `1.15 V` appears in the checked AMD guide.** AMD does publish a narrower starting point: the Ryzen Master 2.9 guide says **VDDCR SOC and CLDP VDDG should typically start at `1.1 V` for memory overclocking** in its Ryzen 3000-Series memory/fabric section. The same section describes DDR4 memory-clock arithmetic. That is a context-specific starting point—not a maximum, not `1.15 V`, and not a BC-250/GDDR6 setting. The guide's `SoC`, `CPU`, and APU `GFX` labels are distinct; do not substitute CPU-core VID or a GFX value for SoC voltage.

The BC-250 README gives CPU-core `Vid` examples and author cautions; it does not give a SoC voltage setting or a GFX voltage recommendation. Its CPU numbers are not AMD guidance and must not be reinterpreted as SoC values.

## Sources and identity

1. **AMD, Ryzen Master 2.9 Reference Guide (April 2022, body text), linked as the Quick Reference Guide from AMD's Ryzen Master product page.** Product page: <https://www.amd.com/en/products/software/ryzen-master.html>. Direct guide PDF: <https://www.amd.com/content/dam/amd/en/documents/products/software-tools/ryzen-master-quick-reference-guide.pdf>. Agent-Reach/Jina Reader snapshot: 51 pages, 45,037 bytes, SHA-256 `d850b95da8f0b48151ac9571f898300d741a48f495d1323fa8195c0cdaff1623`. **This is the hash of the extracted Markdown snapshot, not the original PDF bytes**; direct PDF retrieval failed with HTTP/2 curl error 92. Jina metadata labels the file “2.1 Reference Guide - Feb 2020,” while the document body identifies itself as “2.9 – Reference Guide [Public]” and “AMD Ryzen Master 2.9 Reference Guide | April 2022.” The current AMD User Guide is linked at <https://docs.amd.com/r/en-US/68886-ryzen-master-user-guide>, but only its dynamic portal shell/title was retrieved (snapshot SHA-256 `64ab959963b44ed3beb666898b064873264c7e990b7e06c79cec991042ee71fe`); its body is unavailable in this run and is not cited.
2. **BC250 community source, `bc250-collective/bc250_smu_oc`, `README.md`, pinned at commit `43d6b4c6e38c57bc9ec8908c44675ce7d5fd3d2f`** (latest commit metadata observed 2026-01-26; message `Updated readme to include stability testing`). Raw file URL: <https://raw.githubusercontent.com/bc250-collective/bc250_smu_oc/43d6b4c6e38c57bc9ec8908c44675ce7d5fd3d2f/README.md>. Exact file size `5,792` bytes; SHA-256 `7cd268ec3f7fc98f2fe75682380d09e35079d5238f6ad12fe2396e602a6fe9e3`. No license was established in this scoped README-only retrieval; no code was reused.

## What the sources actually say

### AMD guide: recommendation, control-mode maximum, and domain separation

- **Recommendation (p. 41, “Ryzen 3000-Series CPUs – Memory and Fabric Overclocking”):** “VDDCR SOC and CLDP VDDG should typically be start at 1.1V for memory overclocking.” On the same page the guide states that memory clock runs at half DDR4 speed and gives DDR4-3600 → 1800 MHz. This is a recommended starting point for that named memory/fabric context. The guide does not call `1.1 V` a maximum or a BC-250 limit.
- **Maximum wording (p. 20):** “CPU Core Voltage showing the current average core voltage and the maximum allowable voltage set by the present control mode.” This is a displayed, control-mode-specific **CPU core** value; it is not a universal electrical maximum for SoC, CPU, or GFX.
- **Domain labels (pp. 23–24):** the guide separately labels “SOC Voltage setting” and “CPU Voltage setting,” and identifies an “APU GFX Voltage” setting. It states that “The SOC Voltage setting drives the overclocking potential for the memory controller and, if an APU, for the APU Graphics (GFX),” and that APU GFX voltage is derived from SoC voltage. These are distinct controls/domains, not interchangeable names for CPU `Vid`.
- **General caution (pp. 3–4, 21):** AMD says its guide does not supersede published specifications, warns operation outside specifications/factory settings can damage components, and warns CPU voltage “must be applied carefully.” It does not provide a universally recommended manual SoC voltage of `1.15 V` for this custom board.
- **Scope boundary:** the numeric `1.1 V` statement is attached to Ryzen 3000-Series memory/fabric overclocking and the surrounding DDR4 discussion. It does not establish a valid value for BC-250 GDDR6. No Cezanne/Zen 3 recommendation is imported here; no cross-generation, DDR4-to-GDDR6, or SoC-to-GFX conversion is supported by these sources.

### BC-250 README: CPU-core VID claims and examples, not SoC advice

- The tool identifies itself as modifying “the BC-250s CPU Parameters via SMU”; the CLI help defines `--vid mV` as “CPU Core Voltage Limit in mV” (README lines 2, 35–45). This pins the following numbers to CPU core VID.
- **Community caution, not an AMD maximum:** “Always make sure that CPU core voltage (\"Vid\") does not exceed 1.325 V under any circumstances!” (line 9). Elsewhere the README says to “stay below 1300 mV Vid” (line 68). Those are the community author's CPU-VID cautions; neither is a manufacturer SoC limit or proof of a safe board-wide maximum.
- **Examples / author-reported result, not prescriptions:** it offers 4,000 MHz at 1,275 mV and says to try 1,300 mV if detection crashes (lines 63–68); gives a 3,500 MHz / 1,000 mV undervolt example and says stock core voltage at 3.5 GHz is “around 1180 mV” (lines 75–80); and labels 4.1 GHz @ 1.3 V under “Results on my system” (lines 125–133). These are CPU-core examples or one system's report, not SoC/GFX voltages and not universally stable points.
- Source commands (`bc250-detect`, `bc250-apply`, `systemctl`) were read only as text and **not executed**.

## Decision boundary

| Label                    |                                       Observed value | What it means here                                                                                 | What it does not mean                                            |
| ------------------------ | ---------------------------------------------------: | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| AMD typical start        |                                              `1.1 V` | VDDCR SOC + CLDP VDDG starting point for Ryzen 3000-Series DDR4 memory/fabric overclocking (p. 41) | Not a maximum, not `1.15 V`, and not a BC-250/GDDR6 prescription |
| AMD UI maximum           |      no universal number stated in the cited passage | Current CPU-core voltage’s “maximum allowable” in the present Ryzen Master control mode (p. 20)    | Not an absolute SoC/GFX rating                                   |
| BC-250 README admonition |          `1.325 V` CPU core Vid; `below 1300 mV Vid` | Community CPU-core warnings/guidance                                                               | Not AMD-published and not SoC                                    |
| BC-250 README examples   | `1275 mV`, `1300 mV`, `1000 mV`, `~1180 mV`, `1.3 V` | CPU-core VID examples/author-reported figures at stated frequencies                                | Not SoC, GFX, DDR4/GDDR6 memory voltage, or a BIOS target        |

## Limitations and unrun checks

- The exact AMD source content used is the 2.9 Reference Guide PDF linked by AMD. Its extracted-text snapshot is hash-pinned; the original PDF byte hash is **unavailable** because direct transfer failed.
- The separate current AMD User Guide page `68886` returned only a dynamic shell, not its body. Therefore this report makes a scoped conclusion about the fetched 2.9 guide, not an exhaustive negative claim about every AMD publication.
- The community README is not independently revalidated against a live BC-250, and its numerical claims remain community examples/cautions.
- No hardware, BIOS, ROM, NVRAM, register, or candidate operation was performed. No overclock command in the source was executed.
