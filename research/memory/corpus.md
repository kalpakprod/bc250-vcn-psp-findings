# Corpus and provenance

## Imported corpus

The original Windows source tree under `import/from-windows/Users/kukuruza/` now contains no files. Its BIOS, temporary working corpus, agent context, Codex workspaces, WorkBuddy material, downloads and upstream repositories were preserved by topic under `archives/imported/`. `docs/import-catalog.md` maps the paths.

The import was verified in three passes:

- Phase 1: 149,890 SHA-256 records.
- Phase 2: 68,716 SHA-256 records.
- Phase 3: 10 additional documentation records found by destination/manifest reconciliation.

Initial import reconciliation: 218,616 records, no source-manifest omissions or destination extras at that time. By 2026-09-28, all original paths and 1,305 later files were routed; six current bytes differ from the original manifests. `reports/repository-audit-20260927/phase33-global-route-metadata-audit.json` and `phase33-global-live-hash-audit.json` verify current routing and hashes. Semantic content review remains open.

## Boundaries

The import deliberately did not copy credentials, tokens, private keys, raw security material, `.pem` or `.env` files, unrelated CVE work, PS5-only bulk trees, or an unreadable NTFS symlink. The excluded source data remains outside the project and is not authority.

## Promotion

Before promotion, record source-relative path, artifact type, hash, generated or original status, license/provenance, duplicate relationship, and the target canonical location.
