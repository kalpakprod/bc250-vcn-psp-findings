# Understand Anything in BC250

Status: TRIAL for pinned project-local deterministic analysis; full semantic graph and adoption remain open. The older NEEDS-EVIDENCE checkpoint below is historical.
Request: «https://github.com/Egonex-AI/Understand-Anything здесь нужен!!!».
Reading: integrate the useful capability into this BC250 workspace if source review supports it, rather than assume the README is proof.
Target: /home/OWNER/orca/projects/bc250.
Existing open repository audit and TOCTOU tasks remain open; this is a separate topic.

## Outcome and gates

- Identify what Understand Anything actually does and which BC250 workflow it improves over existing memory/docs/code-index tools.
- Pin source revision, license and relevant files; classify external-stack decision as KEEP/ADOPT/ADAPT/TRIAL/DEFER/REJECT/NEEDS-EVIDENCE.
- Inspect install/runtime permissions, data destinations, network, secrets, command execution, rollback, compatibility and cost.
- If safe and useful, make only a project-local reversible integration and run its exact test plus make test, procoder test/check. Preserve original bytes and record limitations.
- No global install, account/paid-service use, firmware/hardware action or commit without the corresponding user instruction.

Next: fetch repository metadata and primary files through agent-reach/GitHub read-only; inspect local overlap, then choose the smallest action.

## Checkpoint 2026-09-27

Local `understand-explain` consumer exists, but `.ua/knowledge-graph.json`, legacy graph and `/understand` generator are absent. Upstream GitHub retrieval failed through agent-reach/gh, curl, git and unavailable browser; no commit/license/code review is possible. Bounded evaluation: `docs/research/2026-09-27-understand-anything-evaluation.md`. Decision NEEDS-EVIDENCE, not ADOPT. Next input: pinned upstream ZIP at `scratch/understand-anything-upstream.zip` or working read-only GitHub route; then source audit and project-local trial. Existing audit/TOCTOU tasks stay open.

## Communication correction 2026-09-27
User asked what input is needed in simpler words. Ask for one thing only: attach the GitHub repository ZIP in chat; no path, commit, installation or other setup required from the user. I will handle source review and integration after receipt.

## GitHub CLI correction 2026-09-27
The first `gh` on PATH is a mise shim, but `/usr/bin/gh` exists and starts. Direct `/usr/bin/gh api repos/Egonex-AI/Understand-Anything` still cannot connect, and DNS for `api.github.com` fails in this sandbox. `gh auth status` says invalid token, but network failure prevents treating that as a reliable judgment of the operator's host login. No CLI installation or re-login is needed on the current evidence. Keep NEEDS-EVIDENCE until a readable source route or ZIP is available.

## Network-restored trial 2026-09-27
The access blocker was removed by the changed execution environment. Pinned GitHub source `6df3065f1d8ddc2ce3615314d1d493f36d6b1c80` was fetched into scratch, not globally installed. MIT root license verified. Static audit identified a home-mutating installer, optional auto-update hooks, LLM/token-intensive full graph and a read-all-scanned-files deterministic stage. `pnpm install --ignore-scripts --frozen-lockfile` in scratch, core build and 1013 core tests passed. Bundled `/understand` scanner/import/structure scripts ran with import/evidence/scratch/tools/binary exclusions: 1372 scanned, 1216 parsed, 156 skipped, 0 unreadable. This is structural coverage only; no `.ua/knowledge-graph.json`, no model-based summaries, no claim of full repo understanding. Next: cost/scope gate for semantic graph, then connect verified findings to the latest full-image firmware acceptance branch. Preserve earlier audit and all source bytes.
