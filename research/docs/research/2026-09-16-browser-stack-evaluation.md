# Browser stack evaluation (external tools for bot-blocked pages)

> Historical tool evaluation, not current browser/session availability. OpenCLI is recorded as working in section 3; the later request to load its extension again is not a fresh prerequisite. Current capabilities must be checked without restarting or modifying the user browser.

Date: 2026-09-16. Need: fetch bot-protected pages (e.g. TechPowerUp CPU specs,
which 403s plain HTTP clients) for donor-BIOS research. Existing capability:
`web_fetch`/`web_search` only; no in-project browser driver (see
`memory/tools.md`). All trials below are read-only page fetches.

## Probe results that frame every verdict

- `web_fetch` of the TechPowerUp 4700S spec page: HTTP 403 (own run).
- Stock headless Chromium 152 (`--headless=new --dump-dom`): identical styled
  "403 - Access Denied" page (own run). Blocking is fingerprint/behavior based,
  not User-Agent based.
- Obscura 0.2.2 `--stealth fetch`: server returns the real page HEAD
  (`<title>AMD Ryzen 4700S Specs...</title>`, og:description "Cardinal, 8
  Cores, 16 Threads, 3.6 GHz, 65 W") but the BODY is an interactive slider
  CAPTCHA ("Automated bot check in progress / Drag the handle to the target").
  So: hard-403 beaten, anonymous full-content still CAPTCHA-gated. Partial PASS.

## 1. obscura (h4ckf0r0day/obscura) — ADOPT (fetch path only)

- Source/revision: GitHub `h4ckf0r0day/obscura`, HEAD `4b70288` (2026-09-16);
  installed artifact = prebuilt release v0.2.2 `obscura-x86_64-linux-stealth`.
- License: Apache-2.0. Inspected: README, Cargo.toml (9-crate Rust workspace,
  V8 JS, CDP, MCP crate), `fetch --help`, release asset list.
- Installed: `~/.local/bin/obscura` sha256
  `0e30b1ee35e3f3f291fed3cc55f7284964c8c741dcc24de1b171fcefa3444cdf`,
  `~/.local/bin/obscura-worker` sha256
  `34edfd3c79c45f04e86a8bae6994956b06d611cb5951d9b497ef91f449541321`
  (user-local, on PATH; NOT in git — 114 MB binary).
- Evidence: control fetch of example.com PASS; TPU stealth fetch partial PASS
  (above). `serve`/`mcp` modes NOT trialed; default bind address UNVERIFIED —
  do not serve until bind is confirmed loopback-only.
- Security: prebuilt binary, no reproducible-build check; `--stealth` does TLS
  impersonation + tracker blocking (defensive scraping use here; no credential
  or paywall bypass attempted). Egress-only in fetch mode, no listener.
- STABILITY CAVEAT (2026-09-16 14:37 +05, coredump-evidence): `obscura
--stealth fetch --dump markdown https://www.amd.com/en/desktop-kits/amd-4700s`
  died SIGSEGV (SEGV_MAPERR at 0xfffffffffffffff0) inside
  deno_core/V8 `host_import_module_dynamically_callback` — the page's JS
  dynamic import() crashes obscura 0.2.2. Upstream bug, not Omarchy, not OOM.
  Rule: JS-heavy vendor pages go through the OpenCLI bridge first; obscura
  fallback order = `fetch` then `--dump original` (bypasses the JS layer).
- Unknowns: whether `--obey-robots` should default on for project crawls;
  worker-binary role; CAPTCHA interaction limits.
- Next: use `obscura --stealth fetch --dump markdown` as the first fallback
  when `web_fetch` 403s; record URL/date/claim per research-provenance.

## 2. browser-harness (browser-use/browser-harness) — TRIAL (blocked on browser permission)

- Source/revision: GitHub `browser-use/browser-harness`, HEAD `afbcc38`
  (2026-09-16). License: MIT. Version 0.1.13 (alpha). Inspected: README,
  install.md, SKILL.md (skimmed), pyproject (deps: cdp-use, websockets).
- Installed: `uv tool install --python 3.12 browser-harness` (user-local).
  Doctor: chrome-running OK, daemon FAIL, 0 connections.
- Root cause (own log read): no DevToolsActivePort — the user runs Thorium
  (not in the harness browser-config search list) and remote debugging was
  never authorized. Fix needs a USER action (tick remote debugging in
  chrome://inspect of a supported Chromium/Chrome) or a separately launched
  debug instance with its own profile (agent-side fallback, no user cookies).
- Overlap: same job as the OpenCLI bridge (drive the logged-in browser), but
  via CDP instead of an extension. Keep both through trial; converge later.
- Next: ask operator for the one-time browser tick, then re-run `page_info()`.

## 3. OpenCLI + Browser Bridge (jackwener/opencli) — ADOPT (verified working)

- Source/revision: GitHub `jackwener/opencli`, HEAD `8271afc` (2026-09-16);
  installed v1.8.7 at `/home/OWNER/.agent-reach/tools/opencli` (pre-existing,
  user-managed). License: Apache-2.0. Node 26.8.1 satisfies engines>=20.
- State 2026-09-16 14:1x UTC: operator loaded the bridge extension;
  `opencli doctor` = ALL GREEN (daemon 19825 loopback-only, extension v1.0.24,
  profile `bpdgjwdw` connected).
- Verified end-to-end (own runs): `tab new` + `open` + `state` + `wait` +
  `screenshot` + `eval` on the TechPowerUp 4700S page — full render, no 403,
  no CAPTCHA in the user session. Screenshots viewed by the agent
  (/tmp/tpu-4700s.png, /tmp/tpu-4700s-specs.png).
- Limitation found: `extract` returns near-empty on TPU's table-heavy layout
  (55 chars); use `eval document.body.innerText` for such pages.
- Working tab left open in the user browser (targetId
  `ABFA212016CE78A9FE02DB0EB9121C5F`); close with
  `opencli browser main tab close <id>` when done.
- Primary-source data captured: 4700S = 8C/16T, 65 W, 3.6/4.0 GHz, codename
  Cardinal, BGA 2197, Zen 2, 8 MB L3, TSMC 7 nm, 10.6B transistors, GDDR6,
  external PCIe Gen 2, no iGPU, locked multiplier, launched June 2021.
  NOTE: TPU labels architecture "Zen 2 (Renoir)" while press reports PS5
  Ariel salvage — taxonomy discrepancy preserved, not resolved.

## What the agent still needs (for real-browser rendering)

1. Either (a) user loads the OpenCLI bridge extension, or (b) user ticks
   remote debugging for browser-harness — exactly one manual browser action
   unlocks the logged-in session (cookies solve CAPTCHAs like TPU's slider).
2. Nothing else software-side: chromium, node, uv pythons 3.11-3.14, cargo,
   and all three tools are present and verified working.
3. Open questions for the operator: what "dontsetch" refers to (no such tool
   found — possibly a transcription of "don't search/fetch"?); confirmation
   that `.agent-reach` is the "Richu/reach agent" meant.

## Rollback

- `uv tool uninstall browser-harness`; delete `~/.local/bin/obscura*`;
  OpenCLI untouched (pre-existing). No repo files depend on any of this yet.
