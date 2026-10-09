# Git storage policy

Active authored text is intended for version control: the current AGENTS.md contract, archived contract records, focused skills, memory, research/action logs, specifications, scripts, tests, tool launchers/manifests, and candidate build sources. Existing paths are preserved.

Local evidence is preserved outside Git: original dumps, evidence captures, raw imports and import manifests, built firmware/EFI/FFS/sections, build logs, installed external tools, public-source mirrors, and archived session exports. Git is not a backup of these local inputs. A clone needs separately supplied authorized evidence at the paths cited by reports.

Never use blanket `git add -f`. AGENTS.md is the current contract. CLAUDE.md and AGENT_CONTRACT.md are no longer active compatibility copies; their historical content is retained in docs/agents-contract-backup.md. A placement policy does not mean every authored file is already tracked. Generated outputs and sensitive exports must not be forced into history.

Remote publication is authorized ONLY for the curated public repository
`kalpakprod/amd-bc250-bios-unlock` (owner decision 2026-09-24): release
attachments (ladder images, driver FFS blobs, scrubbed manifests) plus the
vetted tree (scripts, driver sources, docs). Everything else stays local-only:
original dumps, `evidence/` captures, `import/`, full `candidates/` and
`firmware-flash-pkg/` trees, session exports. No other remote publication is
authorized by local version control.

Flash packages (`firmware-flash-pkg/`): README.md and SHA256SUMS are versioned
text; staged `.bin`/`.rom` stay local-only like other built firmware (see
`.gitignore`). A package is reproducible from its README (source path + sha256)
plus the local candidates tree.
