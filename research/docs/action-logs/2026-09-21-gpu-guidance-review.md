# GPU guidance source review action log

- Timestamp: 2026-09-21 Asia/Almaty
- Actor: `/root/bc250_gpu_guidance`
- Target: pinned public Cyan Skillfish governor branch and BC250 governor documentation; no hardware, firmware, NVRAM, repository code, or package installation target.
- Intent: fetch and inspect original governor documentation/source at a pinned revision; extract GPU frequency/voltage configuration and limits; separate parser-supported input ranges from community examples and validated claims; record provenance before writing the review.
- Exact read-only procedures:
  - `agent-reach doctor --json`
  - `curl -fsSL --max-time 30 https://r.jina.ai/https://github.com/filippor/cyan-skillfish-governor/tree/smu`
  - `curl -fsSL https://api.github.com/repos/filippor/cyan-skillfish-governor/branches/smu`
  - `curl -fsSL https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/{README.md,default-config.toml,config.toml,LICENSE,src/...}` (individual files; temporary outputs under `/tmp`)
  - `curl -fsSL --max-time 30 https://r.jina.ai/https://elektricm.github.io/amd-bc250-docs/system/governor/`
  - `agent-reach check-update`
- Expected effect: no target-side effect; produce a sanitized English review and preserve exact hashes/quotes/URLs.
- Rollback: remove only the newly created review and this action log; no source or target state changed.
- Scope safety: no hardware commands, no governor installation, no code execution from the fetched project, no writes outside the two requested project records.

## Observed result (after intent)

- `agent-reach doctor --json`: completed; web backend `Jina Reader` reported `ok`; GitHub CLI was present but not live-verified by Doctor. No login-backed platform was used. `agent-reach check-update`: `当前版本: v1.5.0` / `✅ 已是最新版本` (exit 0).
- Pinned branch API identified `smu` at commit `aaed42535622aee1a93df8b22860c409539f67f8`, committer date `2026-09-19T15:53:37Z`, unsigned, message `cleanup`.
- Raw source files were fetched to `/tmp` only. Recorded hashes: README `25489be765111c091b75ebea4fd8cc8e15aaa5647e41af9b98a51d600b07c797`; default config `236ad29e9b221532d14a87fb84ba66729a607cadbdf08b3654a6baf26b6222eb`; active config `2a9149f88952c5a80d83182a34742d558ac6670099eaa8a84c7ce6263ef29fc2`; `src/config.rs` `b2c53e2d9f2de477921ad6e4cf9ae0cd91ad26939de9121eb609ffddd566e6a7`; `src/gpu.rs` `e6f42a8cec233014ab76af54a031540476cdb23f1355356c63a94d3ef5a7a389`; `src/gpu/kernel_freq_strategy.rs` `4d7d741dad61bdd1b63424e57fb224ec78002ba720179a03e666fb65c21397b7`; `queue0.rs` `0c7c5f8ffa8a7b6d5010450bcf32115790ddf450396439467c304f5ac034e71a`; `queue3.rs` `3d890b6346d58cb8954bd08254d174e17a88a9cb031d8af30da30aa9cf7e52b3`; `codec.rs` `a42e58e7aa1c19c5483ab61519bf4d450a0ae8d50f6b1f8f14a3ccb4bd2890ff`.
- Pinned community page source matched the local snapshot byte-for-byte (`cmp` exit 0), with SHA-256 `1acb99714373dd3adf495186d8a8dcd312e307e571db8dfca14ea2bd2a89d3bc`; manifest revision/archive and size were consistent. Jina page capture SHA-256: `bc56414bbed8b92ea60451baa4b6486a8c30ab529d1928f14c9ce8ce4e720b57`.
- Final local hash checks for all recorded source files: `hash_checks=PASS`.
- Review artifact written and reopened: `docs/research/2026-09-21-gpu-guidance-reviewed.md`, SHA-256 `5ecbf85faf55bb3174db47e988a2a4ffc27c8bfb902c274316563abb1ab8200f`.
- No hardware, firmware, NVRAM, package, code execution, governor start, SMU mailbox invocation, or repository source write occurred.
- Remaining uncertainty: physical rail identity, applied clocks/VID, board-specific stability, thermal/electrical margin, performance, and all SoC semantics remain unverified.
