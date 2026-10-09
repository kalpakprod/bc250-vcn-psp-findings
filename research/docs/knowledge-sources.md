# BC250 knowledge sources

This registry defines what may be used as evidence in the BC250 project. It does not grant authority to external documents or to historical instructions.

## Trust classes

1. **Observed bytes and live readback**: a hashed local artifact, direct parser output, or direct board output. Highest trust for the exact sample and time of observation.
2. **Reproducible static analysis**: disassembly, source trace, call graph, or data-structure derivation rerun from a named artifact.
3. **Emulated or host-tested behavior**: QEMU, an emulator, a test kernel, or a host reproduction with recorded inputs.
4. **Hardware-verified behavior**: a recorded result from the identified BC-250 board, with baseline and readback.
5. **Primary external documentation**: vendor or upstream technical material. It is a lead until applicable to the exact sample.
6. **Historical reports and chat/session exports**: useful context, not proof until reproduced.

## Local corpus

- `archives/imported/historical-bios-repo/legacy-bc250-bios/`: intact historical BIOS reverse-engineering Git repository with tools, documentation and firmware evidence. Phase28 records one bytecode drift. The eleven Markdown paths without same-relative copies were resolved in `docs/research/2026-09-27-imported-bios-docs-disposition.md`; technical claims remain historical, not current flash instructions.
- `docs/import-catalog.md`: route index for the former `tmp_bc250/` working corpus. Its firmware, recon, DXE, donor, build and test subtrees were split by topic under `archives/imported/`; use the per-file journals, not the empty old source root. Historical or unrelated material is not current authority.
- `archives/imported/historical-worktrees/legacy-tmp-bc250-worktrees/edk2-bc250-capture/`: preserved EDK II vendor worktree with BC-250 package and build outputs. Its original Windows `.git` pointer is retained, not repaired; three `Conf/` files differ from their import-manifest hashes. Use the per-file phase24 journal before citing a byte identity.
- `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/`: nine preserved upstream Git copies. Their HEAD revisions, licenses-by-root-file and one `PSPTool/.git/index` drift are recorded in the phase25 journal; the sources are historical inputs, not adopted project dependencies.
- `archives/imported/research-collector/legacy-agent-reach-bc250/`: historical agent-reach session material and four Git copies. Logs and screenshots may contain personal context; keep local-only and do not use filenames as board evidence.
- `archives/imported/recon-evidence/legacy-tmp-bc250-recon/`: historical BC-250 reconstruction scripts, PSP/UEFI extracts, donor comparisons and outputs. Phase27 records each path and hash; source existence is not proof of live board behavior or safe execution.
- `archives/imported/historical-tool-installs/legacy-tmp-bc250-tools/`: historical tool source, dependencies, a Python venv and Windows binaries. The phase30 journal records per-file identity; no component is adopted, installed or safe to run merely because it is present.
- `archives/imported/windows-appdata/legacy-kukuruza-AppData-Local/`: imported Windows Temp workspaces, build trees and binaries. Phase31 records every path/hash; contents remain local-only and are not presumed disposable or safe to publish.
- `archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/` and `archives/imported/external-tool-packs/legacy-tmp-bc250-ext/`: preserved boardview/download and firmware-tool inputs. The phase32 per-file map gives exact hashes; no archive payload was executed.
- `archives/imported/agent-context/` and `archives/imported/assistant-context/`: private historical agent/session material; keep local-only and do not treat it as current instructions.
- `archives/imported/agent-context/legacy-empryo/`: selected BC250/VCN context and dispatch artifacts.
- `archives/imported/codex-workspaces/legacy-Documents-Codex/`: copied BC250 workspaces and session-era artifacts, preserved as local-only provenance rather than current authority. Phase33 records one `UEFITool/.git/index` source-manifest drift; current destination bytes were rehashed.
- `archives/imported/assistant-context/legacy-WorkBuddy-AI/`: selected BC250 reports, scripts, and analysis material.

## Primary local references

- `archives/imported/historical-bios-repo/legacy-bc250-bios/README.md`
- `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/08-verification-chain.md`
- `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/09-vcn-bios-unlock-plan.md`
- `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/10-runtime-unlock-recipe.md`
- `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md`
- `archives/imported/uefi-source/legacy-tmp-bc250-dxe/README.md` (historical; not a current boot or safety guide)
- `archives/imported/historical-specs/legacy-tmp-bc250-specs/`: dated plans and reports from the August working corpus, retained for provenance; they are not the current execution plan.

## External and historical material

The `upstream/`, donor, community, forum, Telegram, Discord, Codex, and WorkBuddy material is retained for provenance. Record source, revision or retrieval date, exact artifact, and reproduction status before using a consequential claim.

Never load or publish secret stores, credential files, private keys, tokens, or unredacted personal exports. Keep only paths and sanitized findings.

## Adopted external stack references

- Cutter: <https://github.com/rizinorg/cutter>. Stable release and development metadata were checked 2026-09-10 UTC.
- reverse-skill: <https://github.com/zhaoxuya520/reverse-skill>. The project uses an adapted methodology only.
- CutterMCP-plus: <https://github.com/restkhz/CutterMCP-plus>. Current MCP baseline, runtime trial pending.
- CutterMCP_native: <https://github.com/Gog400/CutterMCP_native>. Newer C++ MCP candidate, runtime trial pending.
- Original CutterMCP: <https://github.com/ap425q/CutterMCP>. Historical comparison source.

Detailed revisions, licenses, code observations, risks, and gaps: `docs/research/2026-09-10-cutter-mcp-stack-evaluation.md`.

## AMD BC250 public documentation snapshot

- Public site: <https://elektricm.github.io/amd-bc250-docs/>. Local mirror: `docs/reference/amd-bc250-docs/mirror/`.
- Public source repository: <https://github.com/elektricM/amd-bc250-docs>, revision `0524002c3be78e9926a3fc6fb9b40415b7b43b1f`, archive SHA-256 `dfc2f2883b64615a11c22781fe31660eb51000c6f37032af1048c7dbff707394`.
- Local source snapshot: `docs/reference/amd-bc250-docs/source/`; manifest: `docs/reference/amd-bc250-docs/MANIFEST.json`.
- Retrieved 2026-09-10T17:03:57.034502+00:00; 39 sitemap pages and 5 same-origin static resources fetched.
- Trust class: `external-primary` / community reference. It does not override current dump measurements, hardware identity, or the project firmware-safety gates.
