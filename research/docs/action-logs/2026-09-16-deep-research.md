# Worker registry: deep-research workflow (inline, no saved workflow found)

Date: 2026-09-16 (UTC). Actor: root (Muse Code).
Task: find seed-similar projects for BIOS dev; inventory current BC250 BIOS;
recommend donor BIOS base (fastboot+TPM); define internet-combing method;
define dissect/rebuild method with excluded VCN block + fixes.
Project root: /home/OWNER/orca/projects/bc250.

## Dispatch
- Requested saved workflow "deep-research": NOT FOUND (registry empty).
- Fallback: inline Workflow API V1 script, 6 parallel researchers + critic +
  1 gap follow-up + synthesis (9 children total).
- Script: /home/OWNER/.local/share/muse/sessions/2026/09/16/01a0a958-5ff7-74d2-bb24-b47133f42ede/workflows/scripts/af7e9254-76f6-4bb1-9d98-f0ec043eee20.js
- Permissions: read-only inventory + web research. No repo/firmware/hardware writes by workers.
- Return artifact: compact complete/evidence/unresolved + ranked synthesis.
- Terminal: completed. Status: partial (nonempty unresolved + notes).

## Worker claims (UNVERIFIED except where noted)
- E1: dump/2.bin 16MiB 83c4e420 AptioV P3.00-lineage; PSP@8E0000 19ent OK APCB/BHD OK 234TE $PS1 kid96EA
- E2: BC250 Cezanne 1002:13FE VCN2.0.3 SMU0.58.6.0; W25Q128.V flashrom1.8/ch347; read-a/b=83c4e420
- E3: Fastboot PRESENT; TPM ABSENT; fTPM blocked, dTPM+EDK2 unproven
- E4: Constraint: D3-B2 no-boot, APCB-only boots; unsigned FV D5-D19 only; excl PSP/$PS1
- E5: MCP rank: r2-mcp PREFERRED > bethington253 > LaurieWired > linted249 > CutterMCP
- E6: UEFI rank: UEFITool > fiano > chipsec > edk2-ref > flashrom; coreboot no-Oberon
- E7: Donor: R1 P5.00 0d6f136c > R2 P3.00 07595ca3 > R3 MENU 48fbe5d3 > R4 AFU GPL; reject 4700S/coreboot/OVMF
- E8: Rebuild: DXE 0xAE0000-0xC30000 + APCB DFG->0x007FFF00 + NVRAM 316-39A; shell-first + readback

## Root verification (this session)
- PASSED: dump/2.bin exists, 16777216 bytes,
  sha256 83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0.
- UNRUN: all other worker claims (PSP/APCB parse, fastboot/TPM presence,
  donor hashes, tool ranks). Full synthesis text not delivered; only compact
  data surfaced via final_summary.

## Unresolved (carried from synthesis)
- dump/2.bin capture tool/log unrecoverable
- flash_archive 824M re-hash pending 3b6c5455
- bc250.rom f4b0f467 use unknown; on-chip today unknown (last 0914 c0f5f1c5)
- No version string; need FV decompress
- Robin5.00 a8ebd810 vs 0d6f136c; P5clv no hash
- GitLab body + gh/FTP listings unfetched
- LICENSE/rev review pending; 253-count + UEFI-grep missing
- OQ1/2/3/5: $PS1/$KDB/registry/host-cmd/TOS/dTPM open
- Ambiguous request phrase "excluded VCN block with conversation..." needs operator clarification.

## Rollback / risk
- No writes to firmware/hardware. This log file is the only repo change.
- Worker ranks and donor hashes must be rechecked against current repo + live
  sources before any consequential use (G9).

## Follow-up 2026-09-16: operator contests 4700S rejection, orders donor re-hunt
- Operator: take an already-working same-chip BIOS (4700S board, PS5 lineage,
  anything Ariel/Oberon in the open internet) as base; VCN must WORK,
  overclocking must WORK, plus FastBoot/TPM/modernity; validate by flash-and-test.
- G7: "excluded VCN block" was root's misread of garbled "с разгоном"
  (overclocking). Record: `memory/incidents/2026-09-16-vcn-exclusion-misread.md`.
- Prior "reject 4700S/coreboot/OVMF" rationale was never delivered by workers;
  4700S rejection is now contested and must be re-examined with evidence.
- Standing brief written: `docs/research/deepresearch-donor-bios-brief.md`.
  Trigger convention: operator message starting with `/deepresearch`.
