## 2026-09-22 02:55 UTC — Discord wave x12 (operator: max parallelism)

Intent: pull BC250-relevant Discord history (guild 1315924807128449065) via OpenTabs MCP shim to answer "why so slow" + collect BIOS/OC facts.
Model/effort: subagent tool exposes no model/effort selector → default route, standard effort. Permissions: read-only; repo writes forbidden; outputs to /tmp/discord-track-NN.md + /tmp/discord-raw-NN/.
Registry: T1 chat-history, T2 chat-search, T3 help-forum, T4 resources-forum, T5 other-forums, T6 search-A, T7 search-B, T8 search-C, T9 DMs, T10 small-channels-pins, T11 context-me, T12 other-guilds. Acceptance each: artifact exists, every tech claim sourced (author/timestamp/msg+channel+guild IDs + quote), gaps recorded (429s/tool limits).
Risk: 12 workers share one browser-tab rate limit; pacing 4s+jitter + 60/120s backoff on 429 instructed.

## 2026-09-22 03:00 UTC — spawn result: 7 accepted, 5 queued

Accepted: T1..T7 (agent_paths main/discord-t01/33 … main/discord-t07/39). Rejected root_capacity_exhausted (8/8 slots): T8..T12 — briefs on disk at /home/OWNER/.codex/tasks/discord-t08..12.md, respawn with fresh command_ids as slots free.

## 2026-09-22 03:05 UTC — SAFE MODE (operator order)

Ban-risk concern. All running workers (T2..T8) ordered: 10s+jitter pacing, max 2 search pages/term, wrap up at >=200 msgs, 120s backoff single-retry on 429, full stop on 401/403/CF. T9..T12 stay queued.

## 2026-09-22 03:0x UTC — peer note (soft session speckled-asterism, UNVERIFIED by root)

Peer reports live on 7.2.6-1.2: pp_od writes rejected (EINVAL, "Failed to set performance level", "Invalid sclk! Valid sclk range: 350MHz-3000Mhz"); only `r` passes. Claim: our patch raised display ceiling only, enforcement stock (SMU/prot-table); working community path = TOML governors via SMU messages. Peer log: docs/action-logs/2026-09-22-gpu-oc-2200-live.md. Status: peer-reported, not re-run by root; affects max-first OC plan if confirmed.

## 2026-09-22 ~03:50 local — T6 done, safe-mode rendezvous gap

T6 artifact verified (receipt line 3, 300 lines, 56 raw files, 346 msgs deduped). No safe-mode confirmation line; pacing shows queue messages do NOT preempt single-turn workers (order lands only at next turn). No cancel/respawn: observed aggregate rate ~211 req/50min (~1 per 14s) is already below safe-mode target; T9..T12 briefs carry safe mode from start. Lesson: mid-run steering of single-turn workers is impossible — put constraints in the spawn brief.

## 2026-09-22 ~03:5x local — T9 BLOCKED (list_dms 2x429), requeued to end

T9 artifact verified (receipt ok, gaps recorded, no DM content touched). Safe mode confirmed by worker. Decision: T9 requeued after T12 (DM-route bucket needs cooldown); T10 spawned (different routes: read_messages/list_pinned).

## 2026-09-22 ~04:0x local — T2 done, accepted with note

T2: 20/20 terms, 44 pages, 836 unique msgs, 20 ctx, artifact 124 lines + 67 raw JSON. Note: RECEIPT present in child report but missing inside artifact file; no safe-mode confirm (same non-preemption gap as T6). Accepted — content complete, gaps section present.

## 2026-09-22 ~04:30 local — OPERATOR STOP: all pulls halted, account safe

Cancelled T4,T5,T7,T8,T9b,T12 (all accepted) + SIGKILLed 9 orphaned worker shell/python loops (they would have fired after sleep/cooldown). Verified: zero Discord-pull processes remain. At stop: T4 resources threads, T5 forum threads, T7 search-B ctx, T8 search-C offsets, T9b DM reads just starting, T12 guild retries in cooldown. Preserved: 6 complete artifacts (T1,T2,T3,T6,T10,T11) + partial raw T4/T5/T7/T8/T12. No auth failures/captchas ever observed (only 429 throttles). No further Discord API calls without explicit operator order.

## 2026-09-22 ~05:00 local — synthesis done (zero API)

Root read all 6 complete artifacts + T7 draft + mined local 113k export. Report: docs/research/2026-09-22-discord-synthesis.md. Headlines: community lineage timeline; our slow branches were community-closed (P5.00 base, VCN wall, 4700S); pp_od `vc`-recipes existed (peer "zero recipes" claim overstated — retest open); Old Lamer = YouTuber with SMU-OC guide; operator footprint = 4 msgs Jun-17.

## 2026-09-22 ~05:10 local — goal-read wave (operator: goal for 5.00-CLV 1:1:1+OCV BIOS)

Operator demands full 3-day history read (550 files) before goal composition. 15 reader briefs written (/home/OWNER/.codex/tasks/goal-read-NN.md), 2 waves (7+8, root cap 8 slots). Model/effort: default route (no selector). Read-only.

## 2026-09-22 ~05:2x local — STRAY-PROCESS incident + server shutdown

Operator reported fresh 429s after STOP. Found 5 worker loops survived cancel (T4 x2, T8, T12 retry, T4 tail-watch) — subagent_cancel is async, agents launched new loops before termination. SIGKILLed all 5 + killed OpenTabs server (pid 1551629, port 9515 CLOSED). Verified: zero pull processes. Lesson: cancel alone does not stop running bash loops; kill server/processes for a hard stop. Server restarts only on explicit operator order. GR02 digest verified (60 lines); GR11 spawned.

## 2026-09-22 ~05:3x local — resurrection chain broken at launcher

T4/T8/T12 agents still alive (no cancel receipts), kept restarting server (23:57Z, then 2039258) + loops. Hardened: shim renamed .DISABLED + server killed + CLI moved to cli.js.DISABLED (reversible: move back + chmod). All worker calls now fail locally (no file / no server) — Discord unreachable by construction. GR09/GR10 verified; GR11-GR15 running (10/15 digests in).

## 2026-09-22 ~05:4x local — all 15/15 digests in, goal composed, all Discord workers dead

T12 cancel confirmed (last one). Traffic: CLEAN, port CLOSED. Goal text saved: specs/2026-09-22-goal-500-111-ocv.md. Coverage: 583 files via GR01-GR15 digests (all receipts verified) + root-read D-REQ1/matrix/NO-GO/evidence-draft.
