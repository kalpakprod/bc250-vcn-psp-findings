# BC-250 public voltage-output netlist lead — bounded source follow-up

Current: Agent Reach surfaced the community-hosted GenCAD 1.4 boardview publicly, but reconciliation showed it is a byte-for-byte copy of the already imported local artifact with only one Jina-added trailing LF. Its existing netlist links `PUA1` ISL69247 to `VDDCR_CORE` and `VDDCR_GFX`, and separate `PUS1` RT8237EZQW to `VDDCR_SOC`; the public copy is **not independent corroboration**, not a board-revision-matched OEM schematic, not a primary teardown, and not a PMBus `PAGE=0/1` assignment.

## Question and bound

Search only for a public BC-250 schematic/boardview/net-labelled source or a primary teardown that links controller outputs to CPU/core, GFX, or SoC. Do not infer from component proximity, re-inspect the already documented `mothenjoyer69` annotated photo, use paywalled/leaked material, inspect credentials, or probe the board. The bound is three relevant source identities: the preserved local GenCAD/parse pair, the public copy (counted as the same artifact if byte comparison confirms it), and the already documented `mothenjoyer69` hardware page record; no fourth source was pursued.

Relevant local state was reopened first: `memory/INDEX.md`, `memory/open-questions.md`, `memory/oc-recheck.md`, `memory/evidence-model.md`, applicable evidence/redaction instincts, `docs/research/2026-09-21-voltage-evidence-integration.md`, `docs/research/luna-bc250-rail-evidence-current.md`, and `docs/research/2026-09-21-luna-rail-mapping-gap.md`. The prior board-photo source is not re-inspected here.

## Finding F1 — public mirror found; no independent new netlist

A DuckDuckGo result, retrieved through Agent Reach's Jina Reader route on 2026-09-21, surfaced the `ASRock AMD BC-250 Hub` page:

- Viewer page: <https://bc-250.com/cad.php>
- Public downloadable artifact linked in that page: <https://bc-250.com/public/cad/ASRock_AMD_BC-250_ISL_X5R_r1.00.cad>
- Download page: <https://bc-250.com/downloads.php?lang=en>
- Site self-identification/about: <https://bc-250.com/about.php>
- Public site legal page: <https://bc-250.com/legal>

The viewer HTML calls itself a `GenCAD 1.4 Boardview`, describes 2,163 components and net tracing, and exposes a link to `ASRock_AMD_BC-250_ISL_X5R_r1.00.cad` labelled “Download Original .CAD (1.83 MB)”; Agent Reach/Jina fetched the linked artifact without authentication (no login was attempted). Its meta author is “Communauté Open-Source BC-250 & Kaws”; the download-page footer says “Dev By Kaws,” links GitHub user `Takiios`, and calls the project independent and not affiliated with ASRock or AMD. The site's general footer says “Licence MIT / Open Hardware,” but I found no file-specific license, source revision, or attribution for this CAD file. Treat the site as an **external community host**, not manufacturer authority. A DuckDuckGo search-result snippet for the downloads page mentioned `ISL69269`, but the fetched download-page body did not expose that claim; do not use that snippet for component identity.

The GenCAD body is structured netlist evidence, not just an annotated component photo. Local reconciliation changes its provenance classification:

- It begins `GENCAD 1.4`, but the header says `DRAWING X`, `REVISION "NA"`, and `USER "NA"`; filename `r1.00` is the file label, not evidence of the actual PCB revision. No matching physical-board revision is supplied.
- `DEVICE PUA1` is listed as `PWM CON. ISL69247IRAZ-T-C51 RENESAS/QFN52/AMD/4+2` (Jina-rendered body lines 68434–68435). `PUA11`, `PUA12`, and `PUA21`–`PUA24` are listed as ISL99360 power stages (lines 68436–68447).
- The net `+VDDCR_CORE_PWM1` joins `PUA1` pin 48 to `PUA11` pin 28; `+VDDCR_CORE_PWM2` joins `PUA1` pin 49 to `PUA12` pin 28 (lines 78171–78175). `PUA11/12` outputs are named `+VCORE_CS1/2`, and their switch nodes `CORE_SW1/2` join inductors `PLA11/12`; those inductors' opposite nodes are members of `APU_VDDCR_CORE_RUN`, which also connects to `U25` APU pins (signal block beginning line 72911). This is a boardview-listed PUA1 → two core phases → `APU_VDDCR_CORE_RUN` connectivity path.
- The nets `+VDDCR_GFX_PWM1`–`PWM4` join `PUA1` pins 3, 2, 1, and 52 to `PUA21`–`PUA24` pin 28 (lines 78162–78179). The corresponding output nets `+VGFX_CS1`–`CS4` and switch nodes `GFX_SW1`–`SW4` route through inductors `PLA21`–`PLA24` into `APU_VDDCR_GFX_RUN`, which also connects to `U25` APU pins (signal block beginning line 74515). This is a boardview-listed PUA1 → four GFX phases → `APU_VDDCR_GFX_RUN` connectivity path.
- SoC is shown as a different path, not PUA1: `PUS1` is listed as `PWM CONTROLLER RT8237EZQW(2)` (lines 68462–68463); `SOC_PHASE` connects PUS1 pin 8, `PLS1` pin 1, and associated power-stage nodes (line 77634), while `+VDDCR_SOC` connects `PLS1` pin 2 and the `U25` SoC pins (line 75000). `VDDCR_SOC_RUN_PG` connects to `PUS1` pin 1 (line 77776). Thus the file maps the named SoC supply path through PUS1/PLS1, **not** to PUA1.
- `PUIO1` is listed as ISL95712 (lines 68458–68459); its nearby named nets include `+VMEMIO_UGATE1/2`, `+VMEMIO_LGATE1/2`, and `+VMEMIO_*` controller signals. This does not support assigning PUIO1 to SoC/core/GFX on this file. The earlier community photo table's description “Core supply PMIC” remains potentially ambiguous/in conflict with these signal names; no component-proximity inference is made.

## Exact local-source reconciliation

Before finalizing this finding, the identical-named local import was checked rather than treating the public copy as a new boardview:

- Preserved source: `archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad`, 1,923,019 bytes, SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`.
- Preserved parse output: `archives/imported/recon-evidence/legacy-tmp-bc250-recon/boardview-parse.json`, 294,507 bytes, SHA-256 `cf11baa257b81ae26b6288162b49f436d50fe0f4ad1a59c2c9703b4527fa8caf`; it contains 2,163 device records and 1,437 signal records, including the rail paths summarized above.
- `cmp -n 1923019 <local CAD> /tmp/bc250-genccad-source.cad` exited 0. The extracted public body is 1,923,020 bytes; the final byte is one LF after all 1,923,019 local bytes. This proves the retrieved public payload is a mirror of the preserved import, not an independently authored netlist.
- The local JSON parse was loaded and queried read-only; it reports top-level `devices` (2,163 entries) and `signals` (1,437 entries), including PUA1 `ISL69247`, PUIO1 `ISL95712`, PUS1 `RT8237EZQW(2)`, `APU_VDDCR_CORE_RUN`, `APU_VDDCR_GFX_RUN`, `+VDDCR_SOC`, and the PWM nets cited above. This is an existing parse of the same imported CAD, not an independent parser/source validation.
- The historical imported analysis `archives/imported/codex-workspaces/legacy-Documents-Codex/2026-08-30/x20/bc250-uefi-capture/analysis/bios-breakdown-phase23/boardview-hardware-findings.md` was reopened. Its report covers connector/chip-identification leads and does not document this voltage-page mapping. It is historical evidence, not an instruction or proof of current live-board identity.

Therefore F1 adds public hosting/discoverability and an observed remote/local byte-identity edge; the static electrical connectivity was already present in the import and must not be counted twice as corroboration.

The netlist names provide an output-to-net trace, but **do not state that ISL69247 PMBus `PAGE=0` means core and `PAGE=1` means GFX (or vice versa)**. Firmware paths and net names cannot supply that missing PAGE-value join on their own.

## Provenance and conflict

The source is self-described as a community site and says it is not affiliated with ASRock/AMD. A DuckDuckGo search snippet (not confirmed in the retrieved downloads-page body) describes the VRM as `ISL69269`, whereas the retrieved GenCAD `DEVICE PUA1` part string says `ISL69247IRAZ-T-C51`; that search snippet is weak, conflicting metadata, not a verified site claim. The file header's `REVISION "NA"`, unspecified upstream origin, generic site license statement, and lack of an independent source materially limit its authority. The local prior record for `mothenjoyer69/bc250-documentation/hardware.md` independently records PUA1 as ISL69247, but its annotated-photo image was not reopened or relied on anew in this follow-up.

## Bounded search and execution record

- `agent-reach doctor --json` exited 0: Jina Reader was the available general-web route; Exa was unavailable. GitHub `gh CLI` was listed but Doctor did not perform credential-touching `gh auth status`. No credential values were read or printed.
- Agent Reach's GitHub read-only search route: repository queries `AMD BC-250 board schematic`, `AMD BC250 boardview`, and `BC-250 PUA1 ISL69247` returned `[]`, exit 0; code queries `PUA1 ISL69247`, `BC-250 ISL69247 page`, and `BC250 boardview` returned `[]`, exit 0. The first repo-query invocation used unsupported JSON field `nameWithOwner` and exited 1 with “Unknown JSON field”; corrected to supported `fullName`, after which all three repo searches completed with no rows. No credentials were printed.
- Agent Reach Jina Reader over the public DuckDuckGo HTML endpoint found `bc-250.com/cad.php`, the matching `downloads.php` page, and the public `.cad` URL. A targeted index query `site:bc-250.com/cad PUA1 ISL69247 VDDCR_SOC` returned no indexed results; no independent search-index hit exposed the rail labels. The first relevant result list also contained unrelated Bearcat BC-250 manuals; those were not opened or used.
- Jina Reader of `cad.php` returned HTML capture `/tmp/bc250-cad-jina.html`, 154,289 bytes, SHA-256 `185bcb52e26a01e8db6ae6a677ddb3e085e03c0a37eb97904ac25c6de14fd299`. It names the linked `.cad` file and component/net viewer behavior. Jina's rendered text capture is `/tmp/bc250-cad-jina.txt`, 1,004 bytes, SHA-256 `24880b32a46777624966b1de612f9270907e77004a1fd8604be7e0191ee88d7c`.
- Jina Reader of the public `.cad` endpoint returned 1,923,173 bytes including Jina's wrapper (SHA-256 `28f3004c7378856d996459e3edd6e04c298a1bca9e65290b06f1006d89572463`). Removing only the leading seven Jina metadata lines through the first `$HEADER` produced a 1,923,020-byte GenCAD body in `/tmp/bc250-genccad-source.cad`, SHA-256 `d60c6389af8d476accf2bf0ff0315f8e239bf7516d0cbdb02aeaff9f48ebcb30`. This is the hash of the body returned through Jina, **not an independently obtained origin-file hash**. Selected source lines and `SIGNAL`/`NODE` joins were reread from that local body and matched against the existing parse JSON; no independent CAD parser or independently authored netlist was used.
- Direct origin `curl https://bc-250.com/cad?lang=en` exited 7 (`Could not connect to bc-250.com:443`); resolver returned `0.0.0.0`. I did not attempt to route around that restriction; Agent Reach's Jina route supplied the public content. `cua.createBrowserTab("iab", ...)` returned `Browser is not available: iab`, so interactive website rendering was unrun. The raw text artifact was parsed locally without executing the site's JavaScript.
- Google via Jina returned HTTP 403 `AbuseAlleviationError` attributed by Jina to prior abuse; it was not retried. Prior OpenCLI Google/DuckDuckGo failures in the existing rail-source log were not retried. No login, paywall, private/leaked source, board, firmware, NVRAM, register, or hardware operation was used.

## Result and exact remaining link

**Found:** a publicly retrievable community-hosted copy of the existing imported GenCAD source. The public copy makes the earlier static boardview available at a pinned URL, but it adds no independent netlist evidence. The imported GenCAD connectivity maps the file's PUA1 pins through named power stages to `APU_VDDCR_CORE_RUN` and `APU_VDDCR_GFX_RUN`, and maps a separate PUS1/inductor path to `+VDDCR_SOC`.

**Not established:** the CAD file's true PCB revision/provenance or fidelity to the operator's board; a revision-matched primary schematic/teardown; which physical `PAGE` value selects the core versus GFX output; electrical/PMBus semantics; applied voltage; live hardware behavior; or any safe voltage limit. The exact missing join for firmware-to-physical page mapping is `ISL69247 PAGE value 0/1 → boardview-listed VDDCR_CORE / VDDCR_GFX net` on the operator's identified board revision. A primary revision-matched schematic/netlist or independently authenticated boardview that states that mapping is still required. No hardware measurement is proposed here.

Evidence classes: `observed-bytes` for the extracted public GenCAD text and its recorded body hash; `static-analysis` for `SIGNAL`/`NODE` connectivity as represented in that file; `external-community-source` for the site and its claims. Hardware verification: **unrun**.
