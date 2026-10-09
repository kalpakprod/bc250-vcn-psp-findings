# Historical chat voltage evidence review — intent

- Timestamp: 2026-09-20 Asia/Almaty
- Actor: Codex bounded executor (`/root/amibcp_availability`); assigned model/effort: Luna xhigh
- Target/source: user-authorized `/home/OWNER/Downloads/AyuGram Desktop/ChatExport_2026-09-20/result.json` and its `photos/`/`files/` metadata; raw source is sensitive and contains an access-bearing URL.
- Scope: selectively locate participant `алло, это сервис по ремонту стиральных машин?` statements about manual voltage/feedback adjustment, DF/MCLK behavior, latency/throughput, and versions/conflicts. Reuse the prior sanitized report `docs/research/2026-09-17-chat-export-20260904-05.md` as the existing route, then reconcile current message IDs/dates and state evidence class.
- Safety: parse keys/counts and matching message excerpts only; redact URLs, handles, tokens, and access-bearing values at source; never print/copy whole messages, credentials, raw URL, or entire export. No photos/raw files will be promoted or modified.
- Existing project boundary: participant reports are historical evidence only; no exact-clv control, applied clock, voltage safety, synchronization, or hardware acceptance claim follows.
- Expected effect: one concise sanitized English evidence report plus this action-log result; no BIOS/ROM/NVRAM/hardware/source modification.
- Rollback: delete only the new sanitized report and this action log; raw export remains untouched.

# Historical chat voltage evidence review — result

- Selective parse of `result.json` confirmed `208` messages and the target participant's direct messages. Matching excerpts were limited to requested voltage/feedback/DF/latency terms; URLs, access-like values, and handles were redacted at source. No raw message, URL, token, or full export was copied.
- Direct participant sequence observed:
  - `772341` / `2026-09-05T22:03:04+05`: abandoned BIOS voltage setting and raised voltage manually.
  - `772342` / `22:03:21`: adjusted feedback.
  - `772343` / `22:03:27`: SoC `1.2-something`.
  - `772344` / `22:03:32`: DF Clock `1800 MHz`.
- Historical curve/conflict observed: `772015` reports `1000 -> 1400` no gain and above 1400 brick; `772183` reports DF >1400/MCLK mismatch causes no init; `772237` reports 1400 stable and 1500 init/no OS; `772239` reports 900 -> 1400 changed observed speeds. These are participant reports with no controlled measurement ledger.
- Prior sanitized report `docs/research/2026-09-17-chat-export-20260904-05.md` and existing stage-1 reconciliation were used as corroboration, not copied raw source. Photo 16's prior sanitized `131.4 ns` observation remains historical, not independent sync proof.
- Research report reopened and verified: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-chat-voltage-evidence-luna.md`; SHA-256 `424deade0254570a19a999f57ac0d32c6bf5cdccb816acf9844c386449d3345d`.
- Result: method attribution is physical feedback adjustment, not BIOS voltage offset; historical evidence is participant-report class; voltage/rail/unit/sync causality remains unresolved. No BIOS/ROM/NVRAM/hardware operation or candidate was performed.
- Rollback: remove only the new sanitized report and this action log; raw export remains untouched.
