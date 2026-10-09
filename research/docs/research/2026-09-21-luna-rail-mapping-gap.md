# PUA1 / ISL69247 image evidence and remaining rail-mapping gap

Later local-source note: `evidence/hardware/ASRock AMD BC-250_ISL_X5R r1.00.cad` is present in this workspace (SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`). This report inspected the pinned public image, **not** the local CAD's PUA1 nets or applicability to the operator's board revision. The page-to-rail gap remains open until those are checked; do not infer that no local drawing exists.

Current: the pinned BC-250 hardware page has one direct annotated board image. The image/table identify marker 4 as `PUA1` / ISL69247 “Main PMIC,” but the image does not expose a readable controller marking, board revision, rail net, or PMBus page assignment. Do not infer rail identity from component placement.

## Exact pinned source reopened

- Repository: `mothenjoyer69/bc250-documentation`
- Revision: `1cf461b7766d43b22753f136020b304a90d80c61`
- File: `hardware.md`, `https://github.com/mothenjoyer69/bc250-documentation/blob/1cf461b7766d43b22753f136020b304a90d80c61/hardware.md`
- Pinned raw file: `https://raw.githubusercontent.com/mothenjoyer69/bc250-documentation/1cf461b7766d43b22753f136020b304a90d80c61/hardware.md`
- Re-fetched through Agent Reach's GitHub route on 2026-09-21; 6,693 bytes; SHA-256 `23659e162daaac67c07bd9af116e275a6bfab751bbfa3a1fd8831eb21e3f837f` (matches the prior source note).

In this exact file:

- Line 174 is the only Markdown image link: `images/annotated-chip-id.jpg`, captioned “Top of the BC-250 board, with chips numbered.”
- Lines 176–188 give an “Auxiliary Chip ID” table. Row 4 maps image marker `4` to `PUA1`, `Intersil ISL69247`, “Main PMIC.” Row 2 labels `PUIO1` / ISL95712 “Core supply PMIC”; row 3 lists `PUA11, etc` / ISL99360 “Smart Power Stage (phase controller).” Line 188 cautions that some MOSFETs and voltage regulators are omitted.
- The file's other external URLs concern Molex connector parts and an AMD HDT+ debug-connector reference; no PMIC datasheet, schematic, boardview, or rail/page document is linked. A text search for `revision`, `page`, `VOUT`, `CPU`, `SOC`, `GFX`, `schematic`, `boardview`, and `net` finds no PUA1-to-rail/page declaration.

This is direct community board-identification evidence, not a manufacturer schematic or full BOM. The legend identifies the IC model, but no board revision is named in the Markdown.

## Direct inspection of the linked image

- Pinned image URL: `https://raw.githubusercontent.com/mothenjoyer69/bc250-documentation/1cf461b7766d43b22753f136020b304a90d80c61/images/annotated-chip-id.jpg`
- GitHub API metadata: JPEG, 1,374,964 bytes, blob SHA `fc2d8edde944d583c1b215665baaa4ffa17dd887`.
- Raw downloaded bytes: JPEG 3098×1395, SHA-256 `c96660be7407302ebe0c9a79a4659061a1496d0216c8541fb8b18238cd02b4bf`.
- Visual re-open: the full image is a numbered board-top overview. Red marker `4` is placed over an IC package in the PUA1 area; the annotation therefore obscures any legible top-marking text there. The image has no visible board-revision label, PMBus page labels, rail names, or schematic net labels. Its board outlines/traces and nearby parts provide location only; they do not prove electrical connectivity.
- The image metadata contains basic JPEG/EXIF orientation information only; it does not record a board revision. The source file itself does not name one either.

The image corroborates a component location in the author's board illustration; the table supplies the ISL69247 identification. Neither ties `PAGE=0/1` to CPU, SoC, GFX, or any other output. The earlier firmware trace records two page-select values in VCORE/GFX code paths, but those static instructions do not establish physical output nets.

## Minimum non-invasive evidence needed

1. **To establish the operator's actual board and controller marking:** unpowered, in-focus photos showing the full board's model/revision silkscreen or sticker and a close-up of the PUA1 package top marking with its nearby `PUA1` designator visible. If the board identity/revision is on the underside, include that side. These photos verify identity and package marking only; they do not map rails.
2. **To assign PMBus page/output to a rail:** a schematic, boardview, or netlist for that exact board revision showing PUA1's output/channel/page configuration and named output nets through their connected power stages to CPU/SoC/GFX. A documented existing page-to-net table is acceptable if its board revision and provenance are explicit.
3. If no revision-matched electrical drawing exists, an annotated component photo alone is insufficient. Do not infer from proximity and do not probe guessed test points. No live probe is proposed.

## Retrieval and tool record

- `agent-reach doctor --json` exited 0; GitHub was routed through `gh CLI` (doctor status `warn` because it intentionally does not call credential-touching `gh auth status`), and Jina web reading was available. No credential values were read or printed.
- Per the prior stage's recorded OpenCLI browser errors (`BROWSER_CONNECT` followed by three `Navigation rejected` results), this bounded continuation did not retry that method. The source and image were fetched read-only through Agent Reach's documented GitHub CLI route and pinned raw URL.
- The attempted GitHub Contents API base64 path for the image returned `encoding: none` (size 1,374,964; blob SHA above), leaving an empty temporary output; Pillow raised `UnidentifiedImageError`, command exit 1. The API metadata identified its `download_url`; fetching that exact pinned raw URL succeeded and produced the JPEG hash above. No project image was written or changed.
- This check reused `docs/research/luna-bc250-rail-evidence-current.md` and its action log; it did not repeat a global search, Linux-format trace, firmware scan, or board operation.

## Result and limits

**The checked pinned board image/page confirms a table-based PUA1 → ISL69247 component identification but provides no board revision, visible device top-marking, rail/page label, or electrical net mapping.** Public evidence for the page-to-CPU/SoC/GFX relation remains unconfirmed within this source. This is not a claim that no other public source exists. Hardware verification is unrun; no voltage or rail recommendation is made.

Evidence classes: `observed-bytes` for pinned source/image hashes; `external-community-source` for the contributor's board annotation. No hardware access, ROM/NVRAM/register operation, probing, or source-repository modification occurred.
