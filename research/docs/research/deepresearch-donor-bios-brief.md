# Deep-research brief: donor-BIOS hunt for Ariel/Oberon-family silicon

Standing brief. Trigger: an operator message starting with `/deepresearch`
(optionally with a focus suffix, e.g. `/deepresearch 4700S BIOS versions`).
On trigger, root reads this brief plus the task-relevant `memory/` files to
their end, then runs an inline Workflow API V1 deep-research (no saved
workflow exists in this harness) with the angles below.

## 1. Objective
Find, in the open internet, every usable BIOS/firmware image and related
material for the SAME chip family as the AMD BC250 (Ariel/Oberon lineage:
BC250 itself, AMD 4700S "Cardinal", PlayStation 5 "Oberon/Prospero", and any
other Ariel/Oberon-based board), and recommend which BIOS to take AS THE BASE
for a new, more working, more modern BC250 image.

Target base requirements (operator-set, 2026-09-16):
- R1: boots the BC250 board (flash-and-test loop available, recovery mandatory).
- R2: VCN block WORKING (enablement, not exclusion).
- R3: overclocking block WORKING (memory/GFX clocks; voltage/power where provable).
- R4: FastBoot present; modern AGESA; TPM route (fTPM or discrete, proved not assumed).
- R5: newer / more functional than current stock `dump/2.bin` (Aptio V P3.00-lineage).

## 2. Background (verified baseline)
- Stock control: `dump/2.bin`, 16 MiB, SHA-256
  `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Board BC250-01: UP, boots Linux, gaming-observed; flash history (D-candidates,
  APCB-only boots, D3-B2 no-boot) in `memory/project-state.md`.
- Prior synthesis (2026-09-16, worker claims, rationale NOT delivered):
  "Donor: R1 P5.00 0d6f136c > R2 P3.00 07595ca3 > R3 MENU 48fbe5d3 > R4 AFU GPL;
  reject 4700S/coreboot/OVMF". The 4700S rejection is CONTESTED, see section 3.

## 3. Hypotheses to confirm or deny with inspected evidence
- H1 (operator): the AMD 4700S Desktop Kit uses the same Ariel die
  ("Cardinal") and ships an AMI Aptio V BIOS with public updates; it is the
  closest possible donor and its rejection must be re-examined. Find exact
  board/BIOS versions, download sources, AGESA/PSP/SMU versions, memory-training
  deltas vs BC250 (GDDR6 config), and board-specific risks.
- H2: PlayStation 5 system software (encrypted PUP, Sony secure-boot chain,
  no AMI/UEFI) CANNOT serve as a bootable x86 base, but PS5 silicon research
  (fail0verflow Linux port, Ariel/Oberon RE, SMU/PSP notes) is usable REFERENCE.
  Confirm/deny each half; collect reference links with retrieval dates.
- H3: coreboot (no Ariel/Oberon port) and OVMF (no hardware init) are correctly
  rejected as a DIRECT bootable base; EDK2 remains the DXE-module/source route.
- H4: there may exist other Ariel/Oberon-based products (devkits, embedded,
 ESBC/mining boards) with leaked or public firmware — sweep for them.

## 4. Research angles (one workflow child each)
1. `local-baseline`: recap current BC250 BIOS + board state from memory and the
   repo (hashes, versions, boot history, VCN/SMU state). Read-only.
2. `4700S-hunt`: all 4700S BIOS versions, sources, hashes, changelogs, AGESA;
   board differences (PCIe layout, GDDR6, no iGPU video); transplant risk map.
3. `same-silicon-sweep`: PS5 firmware + research corpus; any other Ariel/Oberon
   product firmware; Ariel vs Cezanne vs green_sardine identity evidence.
4. `modern-base-hunt`: modern AMI Aptio V / EDK2-based donor candidates that
   satisfy R1-R5; version/TPM/FastBoot/OC-menu comparison.
5. `internet-combing`: reproducible query sets and source list (vendor support,
   BIOS DBs, GitHub, archive.org, forums) with exact strings tried and dates.
6. `flash-test-rebuild`: base-image adaptation playbook (DXE/APCB/NVRAM edit
   points, PSP/$PS1 no-touch boundary), staged variants, flash-and-test loop
   with recovery + exact-approval form, UEFI-Shell-first validation.

## 5. Deliverables (synthesis)
- Ranked donor-base list: version, source URL + retrieval date, SHA-256,
  AGESA/PSP/SMU, FastBoot/TPM/OC-menu/VCN status, legal scope note.
- Compatibility matrix vs R1-R5 with evidence class per cell
  (observed-bytes / static-analysis / emulated-or-host-tested / hardware-verified).
- Explicit verdict on H1-H4 with the evidence that decided each.
- Flash-and-test runbook stub (recovery, one variable, expected signal, stop rule).
- Unresolved list + omitted scope (unfetched listings, unreviewed licenses).

## 6b. Browser tooling (verified 2026-09-16, use instead of plain fetch on 403s)
- Primary: OpenCLI bridge (`opencli browser main ...`), daemon 127.0.0.1:19825,
  extension connected. Rules: work in NEW tabs (`tab new <url>`), never touch
  the user's current tab; `state` to check load; `eval document.body.innerText`
  for table-heavy pages (`extract` fails on them); `screenshot` to /tmp when
  layout matters; `wait time/text` after navigation; close own tabs when done.
- Fallback: `obscura --stealth fetch --dump markdown <url>` (beats hard-403,
  stops at interactive CAPTCHAs). `web_search` for discovery, browser for pages.
- Record per research-provenance: URL + retrieval date + exact claim + file
  hash when a download is involved. Compare downloaded bytes against corpus
  (`bb2cf51d...` C0A, `e8fa745b...` vendor C0A, `26863de9...` C08) before
  claiming novelty. Downloads land in /tmp first; promotion into the repo only
  after hash + parser + license/provenance check.

## 6c. Evidence already in hand (do not re-do, build on it)
- 4700S C0A-STOCK = `bb2cf51d...` (corpus file, TRUE stock): 18-entry PSP,
  4 FVs, 245 modules, no 0x24/0x45, no GOP/VBIOS, fTPM PRESENT, AGESA V9,
  APCB 0x488 stock DFG. The 09-14 donor audit analyzed THIS file.
- C0A-MOD = `e8fa745b...` and C08-MOD = `26863de9...` (~/Downloads zips):
  AMIBCP-unhide MODS, REFERENCE ONLY, never a flash base. Proven by root
  byte diff: Setup 35 sparse bytes ALL ->0x47, AMITSE 35 B, rest identical.
  (G7 2026-09-16: earlier "vendor stock" label retracted, see
  `memory/incidents/2026-09-16-c0a-c08-mods-not-stock.md`.)
- C08-STOCK `ef32de2f...`, C09 `70429266...`, C07 `87ce2ebc...`,
  C06 `dc62f7b6...`: worker hashes, bytes NOT in hand, UNVERIFIED.
- P5.00-stock `0d6f136c...` (BC250-native): synthesis top base pick, NOT in
  repo, NOT downloaded — highest-value missing bytes.
- TPU primary source: 8C/16T, 65 W, 3.6/4.0 GHz, Cardinal, BGA 2197, Zen 2,
  8 MB L3, TSMC 7 nm, GDDR6, ext PCIe Gen 2, no iGPU, locked multiplier.
  TPU-vs-Ariel taxonomy discrepancy OPEN.
- Full records: `docs/action-logs/2026-09-16-4700s-vendor-bios.md`,
  `docs/research/2026-09-16-browser-stack-evaluation.md`.

## 6. Constraints
- Owned/authorized assets only; stop and ask if authorization is unclear.
- Read-only first; immutable originals; new output paths; hashes everywhere.
- PSP/$PS1 signed regions: no-touch unless a dedicated experiment with a
  physical recovery plan; never call a modified signed blob safe from a parser.
- Provenance per candidate: origin, revision/hash, license, local mods,
  code-vs-compare-vs-docs use (`research-provenance` skill before collecting).
- MCP binds 127.0.0.1 only, read-only default (per project stack policy).
- No secrets/tokens/keys in outputs (G5). English artifacts; root reports Russian.
- Worker claims are not findings: root re-runs the cheapest decisive check
  (hashes, URL liveness, parser pass) before relying on them (G2/G8/G9).
