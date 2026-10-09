# Historical voltage and DF-clock evidence from ChatExport_2026-09-20

## Conclusion

The chat partner's report describes a **physical VRM feedback adjustment**, not a BIOS voltage-offset setting: on 2026-09-05 they wrote that they had abandoned BIOS voltage configuration, raised voltage “by hand,” and adjusted feedback (messages `772341`/`772342`). The next messages report SoC voltage “1.2-something” and DF Clock `1800 MHz` (`772343`/`772344`). This is historical secondhand participant evidence, not the operator's own measurement, an instrumented rail measurement, or proof that a BIOS field caused the result.

The useful reported curve is bounded but internally inconsistent: DF `1000 -> 1400` was first said to show no gain (`772015`), while a later report says `900 -> 1400` lowered/raised observed speeds (`772239`). `1500` reportedly initialized but did not boot the OS (`772237`); another message says values above `1400` bricked/no-init (`772015`, `772183`). After the manual feedback change, a prior sanitized report records photo 16 at `131.4 ns` and DF `1800`, with less improvement than expected and residual asynchrony. This does **not** establish `MCLK=UCLK=FCLK` or a safe voltage.

## Source and handling

- Source: `/home/OWNER/Downloads/AyuGram Desktop/ChatExport_2026-09-20/result.json`
- Source metadata: JSON object, `messages` count `208`; date range observed `2026-09-04T03:38..2026-09-05T22:12 +05` in the prior sanitized provenance.
- Raw export contains an access-bearing URL; it was not printed, copied, hashed, or promoted. Matching text was parsed selectively and URLs/access-like values were redacted before excerpts.
- Existing sanitized route reused: `docs/research/2026-09-17-chat-export-20260904-05.md`; it independently records provenance, photo 16, and the same historical curve.
- No raw messages, full export, access URL, or private material is reproduced here.

## Direct participant excerpts (short, sanitized)

The participant named `алло, это сервис по ремонту стиральных машин?` was misidentified as the operator in the earlier sanitized report. Its 2026-09-24 correction identifies this participant as the chat partner and hardware experimenter. Excerpts below are short and limited to the requested evidence.

|  Message | Date (+05)          | Evidence class      | Short exact quote / sanitized excerpt                                                                |
| -------: | ------------------- | ------------------- | ---------------------------------------------------------------------------------------------------- |
| `772015` | 2026-09-04 03:52:10 | chat-partner report | `df clock я поднимал с 1000 до 1400, но прироста не увидел. выше 1400 кирпич`                        |
| `772183` | 2026-09-04 14:21:47 | chat-partner report | `df не поднимается выше 1400, а mclk не опускается до этих 1400. Оба значения дают отсутствие инита` |
| `772237` | 2026-09-05 00:50:05 | chat-partner report | `1400 берет стабильно, 1500 инит есть, но в ос не грузит`                                            |
| `772239` | 2026-09-05 00:50:31 | chat-partner report | `Я понизил до 900 и они упали, повысил до 1400 - поднялись`                                          |
| `772341` | 2026-09-05 22:03:04 | chat-partner report | `Я забил на настройку напруги в биосе и поднял напругу ручками`                                      |
| `772342` | 2026-09-05 22:03:21 | chat-partner report | `Фидбек отрегулировал`                                                                               |
| `772343` | 2026-09-05 22:03:27 | chat-partner report | `1.2 с чем-то щас на soc`                                                                            |
| `772344` | 2026-09-05 22:03:32 | chat-partner report | `1800мгц DF CLOCK`                                                                                   |
| `772074` | 2026-09-04 04:17:42 | chat-partner report | `задержки 150 (140 после настройки)`                                                                 |
| `772090` | 2026-09-04 04:37:31 | chat-partner report | `142нс, фигня`                                                                                       |
| `772094` | 2026-09-04 04:41:23 | chat-partner report | `все еще 140+`                                                                                       |
| `772376` | 2026-09-05 22:12:20 | chat-partner report | `Единственное, я ожидал большего прироста`                                                           |

The replies in the same exchange were not treated as measurements: operator messages `772345` and `772348` say `1.2 перебор` and `1.15 край, 1.10 стандарт`; `772349` counters `Soc 1.4 максимум же`. These conflict and are participant opinions, not electrical evidence.

## Method attribution: BIOS versus physical modification

1. **Voltage method — bounded positive attribution:** direct chat-partner wording says BIOS voltage configuration was abandoned, voltage was raised manually, and feedback was adjusted (`772341`/`772342`). The corrected sanitized report interprets this as a hardware VRM feedback adjustment. No schematic, resistor value, probe trace, instrument log, or board photo is used here to infer the exact circuit.
2. **DF frequency method — unresolved attribution in direct messages:** the messages report DF values `900`, `1000`, `1400`, `1500`, and `1800`, but do not consistently identify whether each was a BIOS/NVRAM request, another firmware image, or a runtime control. The attached SYNC image family was structurally reconciled separately against pinned CLV in `evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.md`; that reconciliation found NVRAM variants, unchanged executable module bodies, and no proof that stored requests applied.
3. **No 1:1:1 proof:** the prior sanitized report records DF `1800` against MCLK `1750` and residual asynchrony; the direct chat excerpts do not provide an independent UCLK measurement or divider readback.

## Baseline, after-state, and conflicts

| Phase                      | Reported values                                                                                                   | What is actually supported                                                                        |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Stock-ish / early testing  | DF `1000`; latency around `140–150 ns`; chat partner says `1000 -> 1400` initially gave no gain                   | Historical participant report; no instrument log or exact current-board identity                  |
| DF-only exploration        | DF `900 -> 1400` later said to lower/raise observed speeds; `1500` init/no OS; above `1400` no-init/brick wording | Conflicting participant reports; exact workload, image, boot state, and metric provenance missing |
| Manual feedback adjustment | BIOS voltage setting abandoned; feedback adjusted; SoC `~1.2`; DF `1800`                                          | Chat-partner-reported physical modification and voltage; not a measured rail trace                |
| Post-adjustment photo      | Prior sanitized report links photo 16 to `131.4 ns` and DF `1800`; chat partner expected more gain                | Photo/report evidence, not proof of synchronization; asynchrony reportedly remained               |

The `DF 1000 -> 1400 no gain` statement and later `900 -> 1400 speed increase` statement are not safely merged: they may reflect different settings, workloads, images, or measurement conditions. The conflict remains open.

## Version and artifact qualification

- The chat export includes firmware attachment files, but a chat message alone does not establish the exact currently installed BIOS or board NVRAM.
- The separate stage-1 structural report reconciles the attached SYNC/ULTIMATE images to the pinned plain CLV base (`ea578104...`) at the executable-module/APCB level. It finds NVRAM/default-store variants and unchanged UEFI module bodies, but not applied hardware behavior.
- Photo 9 establishes historical UMC Common menu access only; it does not identify exact CLV or prove that a setting was applied.
- Photo 16 is historical participant evidence; it does not prove a physical clock source or voltage safety.

## Safety and project decision

- Current project limit `1.15 V` is an operator ceiling/constraint, not a validated safe rating. The reported `~1.2 V` and collaborator `1.4 V` statements are historical/conflicting and must not be converted into BIOS values or a hardware recipe.
- Existing exact-clv static evidence classifies `VDDCR_VDD` as an unresolved offset/command field; rail identity, sign, units, conversion, consumer, and physical voltage remain unknown.
- No BIOS/ROM/NVRAM/hardware operation was performed in this review. No candidate is recommended.
- The historical secondhand result can be used only as a hypothesis: manual feedback modification may have raised the achievable DF ceiling, but the causal chain and electrical margin require an instrumented board experiment with recovery and explicit approval.

## Checks

- **PASS:** selective current-export parse; message IDs/dates/authors; URL/access-value redaction at source; cross-check against prior sanitized report and stage-1 attachment reconciliation.
- **OBSERVED-BYTES/STATIC:** attached image identity and NVRAM/APCB distinctions from the existing stage-1 report.
- **PARTICIPANT-REPORT:** manual feedback adjustment, self-reported SoC, DF values, latency, and boot outcomes.
- **INCONCLUSIVE:** exact firmware version at each message, exact BIOS/NVRAM path for DF changes, causal effect of feedback adjustment, physical rail voltage, UCLK value/divider, and 1:1:1 synchronization.
- **UNRUN:** board probe, rail measurement, live NVRAM readback, clock counters, training replay, latency A/B, and hardware acceptance.

## Rollback

No source, firmware, BIOS, NVRAM, hardware, or candidate artifact changed. Rollback is deletion of this sanitized report and its action log only; the user export remains untouched outside the project.

> Correction 2026-09-24: the "~1.2 V / 1800 DF" self-report is the chat
> PARTNER's (msgs 772343/772344), not the operator's. The operator's
> statements in that chat were the limits: 1.2 V over, 1.15 V край,
> 1.10 V стандарт, 1.05 V golden standard (msgs 772345/772348/772361).
