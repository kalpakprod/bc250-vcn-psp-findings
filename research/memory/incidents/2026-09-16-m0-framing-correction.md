# G7 correction: board-alive wrongly framed as hypothesis (2026-09-16)

## Wrong claim
Root framed the post-M0 rollback as "prove the board is alive", implying
board death was an open hypothesis needing a control experiment.

## Measurement that disproved it
Operator: the board was UP and gaming on its native BIOS immediately before
the M0 flash (user-observed fact). Flash procedure separately proven
(flashrom VERIFIED + readback hash match). Board-alive-on-native was never
in doubt; the sole unknown was why the M0 image does not start.

## Correction
Board-alive on native BIOS = observed fact. Rollback reframed as
restoring a known-good state / isolating image-vs-procedure, and deferred
per operator order ("find a working BIOS"). No procedure change needed
beyond the framing: do not re-litigate user-observed hardware state.

Source: `docs/action-logs/2026-09-16-m0-window.md` (G7 block).
