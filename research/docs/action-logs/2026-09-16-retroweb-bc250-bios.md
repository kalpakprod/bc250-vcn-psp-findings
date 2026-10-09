# Action log: RetroWeb BC250 BIOS acquisition (P2.00/P3.00/P5.00/clv)

Date: 2026-09-16 (UTC). Actor: root. Trigger: operator-supplied URL
`https://theretroweb.com/motherboards/s/amd-bc-250` (board ID 20611).

## Intent (before download)
Donor-research synthesis ranked BC250-native P5.00-stock `0d6f136c...` the top
base pick but its bytes were missing; P5.00_clv was hash-unknown (Discord-only
per workers); P3.00-stock/MENU hashes needed byte confirmation. The RetroWeb
page lists 5 BIOS downloads. Plan: fetch page (obscura, read-only), download
zips to /tmp, hash + parser-verify, compare vs known hashes, then promote to
`evidence/donor/retroweb-20260916/` with a provenance manifest. No flash, no
candidate build. Expected effect: close the biggest byte gaps; rollback = delete
the new directory (originals remain on RetroWeb + /tmp copies).

## Page facts (observed 2026-09-16 via obscura --stealth)
- AMD BC-250, chipset "AMD BC-250 SoC", socket BGA2197 (same BGA number as
  4700S Cardinal — same-silicon corroboration, not proof).
- Form OEM/Proprietary, 340x145x32mm, 16 GB GDDR6 shared UMA, PCIe 8-pin PSU.
- Also known as: ASRock BC-250, ASRock 4U12G (confirms synthesis H4 sub-claim).
- I/O: 1x DisplayPort, 1x RJ-45, 2x USB2.0, 2x USB3.x; 1x M.2 M-key.
- Tabs: BIOS 5, Drivers 4 (Realtek LAN only), Documentation 0.
- Page carries a user-submission disclaimer (info may be incorrect).

## Downloads (all to /tmp/trw-bios, curl, 2026-09-16)
| File | Zip SHA-256 | Inner image | Inner SHA-256 |
|---|---|---|---|
| bc250-2-00-bin-...8426.zip | 71c22247...e5240b | BC250_2.00.bin (2025-03-19) | ee6150df...1083c NEW |
| bc250-3-00-bin-...96675.zip | cc23639f...902dd | BC250_3.00.bin (2025-03-19) | 07595ca3...9045c MATCH P3.00-stock |
| bc250-3-00-chipsetmenu-...0330.zip | 22ffccbd...f3c43 | BC250_3.00_CHIPSETMENU.bin (2025-03-19) | 48fbe5d3...40b5 MATCH R3 MENU |
| bc250-5-00-bin-...5322.zip | 32eab45c...5473 | BC250_5.00.bin (2022-05-03) | 0d6f136c...aa82 MATCH P5.00-stock top pick |
| bc250-5-00-clv-...559.zip | 27ce5d5b...d675 | BC250_5.00_clv.bin (2025-10-05) | ea578104...a4cb8 NEW first hash (was BLOCKED) |

## Parser verification (scripts/firmware_audit.py, own runs, PASSED)
- All five: 16 MiB, PSP 19 entries Fletcher32 PASS incl. types 0x24 AND 0x45
  (unlike 4700S donor), 4 FVs, 233 modules each, stock DFG 0x001FFF00.
- APCB sizes: 2.00=1160, 3.00=2916, MENU=2916, 5.00=1160, clv=2972 (all PASS).
- Ftpm/Tpm/Gop/Vbios modules: ZERO in all five (R4: P5.00 brings no fTPM;
  fTPM stays 4700S-donor-only). AGESA tag V9 in all five (numeric version
  still unresolved).
- Worker-hash confirmations: 0d6f136c / 07595ca3 / 48fbe5d3 all MATCH.

## Promotion (executed after this log's intent section)
- Copied 5 zips + 5 images + manifest.json to
  `evidence/donor/retroweb-20260916/`; re-verified hashes post-copy.
- License/provenance note: community redistribution of vendor firmware
  (uploader unknown, page disclaimed); scope = our own BC250 board research.
  Kept out of `candidates/` (not built, not reviewed, not flashable).

## Remaining uncertainty
- Whether P5.00 boots BC250-01 better than stock (R1 UNRUN for all).
- Numeric AGESA/SMU versions per image (need blob-string/PE review).
- P5.00-vs-P3.00 VCN-policy delta; clv variant meaning (custom mod?).
- 2.00-vs-3.00-vs-5.00 Setup/OC-menu diff (next analysis step).
