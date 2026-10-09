# Action log: 7-agent mining of Telegram 6-month export + Discord recon

Date: 2026-09-22. Actor: root (this session). Operator order: maximum
subagents, deep research, visible tasks. Harness delivered the export
(/tmp/bc250_6mo.jsonl, 38972 msgs, verified n/dates/schema by root).

## Worker registry (all read-only, shared checkout, default model/effort)

| Task             | Track                           | Return artifact | Root check                    |
| ---------------- | ------------------------------- | --------------- | ----------------------------- |
| T1-VRAM-dig      | UMA/VRAM/memcfg/ttm             | /tmp/fin-T1.md  | read full, ids spot-plausible |
| T2-OC-dig        | SCLK/V/cores/stability          | /tmp/fin-T2.md  | read full                     |
| T3-kernel-dig    | kernels/Mesa/CU/ROCm/VCN        | /tmp/fin-T3.md  | read full                     |
| T4-swap-dig      | swap/OOM/MangoHud/Proton        | /tmp/fin-T4.md  | read full                     |
| T5-games-dig     | per-game FPS/FG/Proton          | /tmp/fin-T5.md  | read full                     |
| T6-discord-recon | OpenTabs guild/channel scope    | /tmp/fin-T6.md  | read full, no writes made     |
| T7-place-QA      | digest QA + secrets + placement | /tmp/fin-T7.md  | read full, plan followed      |

Note: subagent_spawn supports no model/effort options; G8
model-routing recorded as session default. Harness session
(speckled-thebe) credited as export producer; its TG MCP servers
maxim_kukuruza/second died on heavy scans (limit<=20000 rule).

## Placement (executed by root)

- `dump/telegram-bc250-20260322-20260920.jsonl` (gitignored, sha256
  26cbe87d...889ce92) + `evidence/telegram-bc250-6mo/` (gitignored).
- `docs/research/telegram-bc250-6mo/*.md` (13 digests) + README-PROVENANCE.md.
- Verified via `git status --ignored`. No commit (not requested).
- Single-source marks still TODO inline (listed in README-PROVENANCE).

## Result

Synthesis delivered to operator in chat. Discord export scope handed
to harness (guild 1315924807128449065, window 2025-09-22..2026-03-22).
