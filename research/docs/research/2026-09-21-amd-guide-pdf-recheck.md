# AMD Ryzen Master guide PDF — bounded text and retrieval recheck

Date: 2026-09-21. Scope is limited to the official AMD Quick Reference PDF and its already retrieved Agent-Reach/Jina text snapshot. No BIOS or hardware changes.

## Result

**The original PDF could not be retrieved by either direct method attempted here; the exact printed spelling and the VDDG/SoC electrical relationship remain unverified.** Do not silently correct `CLDP` to `CLDO`, or call it an AMD typo based on the extracted text alone.

The Jina text snapshot (SHA-256 `d850b95da8f0b48151ac9571f898300d741a48f495d1323fa8195c0cdaff1623`) places this extracted wording on printed p. 41:

> VDDCR SOC and CLDP VDDG
> should typically be start at 1.1V
> for memory overclocking

The same extracted page immediately above states “Memory Clock frequency operates at half the DDR4 speed” and gives `DDR4-3600 = 3600/2 = 1800 MHz Memory Clock`. The next printed page, p. 42, is headed “RYZEN 3000-SERIES CPUS – MEMORY AND FABRIC OVERCLOCKING”; its text identifies Ryzen 3000-Series CPU Zen2 and discusses Infinity Fabric and memory-clock coupling. Thus the **extracted** `1.1V` line is on p. 41 with DDR4 memory-overclocking context, immediately before the p. 42 Zen2 section. The earlier report's p. 41 parenthetical that presented that section heading as though it were on p. 41 is narrowed by this addendum; the earlier file remains unchanged.

The extraction co-lists `VDDCR SOC` and `CLDP VDDG` before a shared `1.1V` phrase. It does **not** state that VDDG equals SoC, is derived from SoC, or is the same rail; it does not explain their physical/electrical relationship. Elsewhere, the same extraction discusses APU GFX as SoC-referenced, but that is not a VDDG claim and must not be conflated with one.

Because Jina's text can misrecognize glyphs and the source PDF was not obtained, the following remain **inconclusive**: whether the PDF itself prints `CLDP` or `CLDO`; whether the source wording is `start at` or another phrase; and whether the extracted combined starting-value sentence accurately represents both named quantities. The earlier `1.1V` quotation should be described as Jina-extracted text, not as independently verified PDF typography.

## Download attempts and exact failure

1. `curl --http1.1` to the exact AMD PDF URL timed out after 40 seconds without receiving bytes: HTTP status `000`, size `0`, curl exit `28`; no output PDF.
2. `wget --timeout=20 --tries=1` to the same URL connected to `23.197.224.142:443`, sent the request, then timed out while awaiting response headers; wget exit `4`; no nonempty PDF.

No third retrieval attempt was made. The prior HTTP/2 curl error (`92`, stream reset) is preserved in `docs/action-logs/2026-09-21-amd-guidance-boundary.md`. No alternate search/source was used. The exact missing source is the original AMD PDF at <https://www.amd.com/content/dam/amd/en/documents/products/software-tools/ryzen-master-quick-reference-guide.pdf>; its raw bytes and SHA-256 remain unavailable.

## Evidence status

- `PASS`: existing Jina extraction hash rechecked; page 41/42 layout context and sole `CLDP VDDG` occurrence verified in that extracted text.
- `FAILED`: original PDF fetch by `curl --http1.1` and `wget` (network header/response timeouts).
- `INCONCLUSIVE`: original PDF spelling/wording, and any dependency/equality between VDDG and VDDCR SOC.
- `UNRUN`: PDF visual inspection and raw-byte hashing, because no PDF bytes were received.
- `UNRUN / not authorized here`: any hardware, BIOS, voltage, or register operation. No commands from the community README were run.
