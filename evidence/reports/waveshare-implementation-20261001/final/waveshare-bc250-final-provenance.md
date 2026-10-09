# Waveshare BC-250 final guide: provenance and limits

The companion HTML is an offline presentation, not a wiring authorization.

## Project evidence

- `evidence/boardview/bc250-connector-map.json` records CAD-derived roles and nets for J4004, J5, and TPMS1. Its source CAD and parse hashes are retained in the JSON.
- `docs/action-logs/2026-09-30-waveshare-status.md` records the corrected J5 direction: pin 3 `U_TX` reaches UIO1 RXD1 through R9557; pin 4 `U_RX` reaches UIO1 TXD1 through R9558. It also records that design voltage and physical population are not measured acceptance.
- Local TOCTOU notes and candidate reports describe a two-flash concept; they do not establish safe live isolation or complete-ROM acquisition for this adapter.

## Article/reference evidence

The mirrored pages in `docs/reference/amd-bc250-docs/` provide a public pinout summary (TPMS1 LPC, J4004 SPI, and the warning about BIOS versus SIO flash). Those pages are treated as article evidence only. They are not proof of the connector orientation, population, voltage, or chip identity on this board.

## Explicit unresolved identity

Physical pin-1/orientation and population of J4004, J5, and TPMS1; J4004 pin 7; measured idle/high levels; BIOS_A1 versus SIO1_R selection; `PROGRAM#` reset coupling; and dual-flash chip-select/power isolation remain UNKNOWN. The guide therefore labels these paths conditional or DO NOT CONNECT and keeps USB-only as the first mode.
