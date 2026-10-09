# Baseline board-photo ledger — action log

## Intent — 2026-09-21T03:53:17+05:00 (Asia/Almaty)

Actor: subagent `/root/baseline_board_photos`, assigned by root.
Target: new report `docs/research/2026-09-21-baseline-board-photo-ledger.md` and this log only; preserve all imported images, exports, CAD, ROM, NVRAM, and shared memory unchanged.
Question: do retained photos or markings identify the operator's BC-250 model/PCB revision and the populated `PUS1` / `PUA1` packages, rather than merely depicting a public/reference board?
Procedure: confirm project root; read `memory/INDEX.md`, task-relevant memory, `research-provenance` skill, and the existing baseline voltage / OC photo-gate reports; inventory image paths in the imported tree and `evidence/boardview`; inspect selected stored BC-250 candidates with the existing image viewer; record exact image hashes, imported metadata dates where available, visual legibility, board association, and unreviewed scope. Do not fetch external material, probe hardware, inspect private source URLs, or publish chat contents.
Expected effect: a bounded, source-ledger report with a clear distinction between imported GenCAD/community reference imagery and a photo proven to depict board `BC250-01`; name remaining evidence gap before any photo request.
Rollback: remove only this new report and this action log if explicitly requested. Source data is immutable and no source/firmware/board operation is planned.

## Handling correction / scope note

An initial discovery command materialized one imported community Discord JSON export in memory while looking for image-name references. The emitted tool output included some contributor metadata; no export body or URLs were copied into project artifacts. This was broader than required. Stop further export-content review; retain only non-identifying file paths, image bytes, and exact attachment timestamps for the individually selected reference images. Do not repeat a full-export parse for this task.

## Observed result — 2026-09-21T03:56:00+05:00 (Asia/Almaty)

Created, reopened, and hash-checked report `docs/research/2026-09-21-baseline-board-photo-ledger.md`, SHA-256 `dffe8ecaa355e170ada7db7e0460427e03663b036275f746741ea8727e767cb4`. Selected-image view calls show only board-layout annotations/renderings or unrelated game UI, not a legible physical operator-board photo. Fresh source hashes remain: GenCAD `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`; selected community layout JPEG `21a2de6c11e59100331e2e14cd74a253990cc3473b429e1181b5f3eeb1366178`; annotated layout PNG `12236dfe9e303e8f6744baecad1da7c0fe1148f877a7fe484d06e7d091242414`; stylized board PNG `b622f643e4a51db586e784e5ce67a2babec4a46a90070fe69ea55161eb2076a2`. Existing boardview JSON hash is `cf11baa257b81ae26b6288162b49f436d50fe0f4ad1a59c2c9703b4527fa8caf`.

Outcome: no physical revision or PUS1/PUA1 package marking is verified for `BC250-01`; CAD `REVISION "NA"` remains reference-only. The report explicitly limits its negative to the reviewed scope and names remaining image/evidence requirements. All inspected source hashes match the pre-report observations; no imported image/CAD, raw export, firmware, board, NVRAM, or shared memory file was modified.
