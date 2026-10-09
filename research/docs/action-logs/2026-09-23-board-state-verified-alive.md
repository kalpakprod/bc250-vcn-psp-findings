# 2026-09-23: board state live-verified — ALIVE on P3.00; revive step retracted

Intent: the operator challenged the restore talk («ты это сам придумал или
тебе кто-то напел? Какое восстановление? Я сейчас сижу, у меня с Тим
запущен»). Verify the board state live before answering instead of arguing
from records.

Live verification (read-only, via scripts/board_liveness.sh and direct
ping/SSH/dmidecode):

- ping 127.0.0.1: 1/1 received, 0% loss, 0.66 ms.
- SSH (BatchMode, steammachine@, id_ed25519): host up since 2026-09-23
  09:25:46, kernel 7.2.6-1.206-cachyos-bc250, hostname cachyos.
- sudo dmidecode: BIOS `P3.00`, release `12/09/2021` — af531026 is NOT on
  the chip.
- Commit timeline reconciled: flash af531026 = 2026-09-17 04:57 (66b9c92),
  P0 observation = 2026-09-17 05:03 (d83c041). The board was already UP on
  P3.00 by 2026-09-21 (memory/project-state.md: operator's empirical OC
  track on a live P3.00 board). The plan's "chip currently holds af531026,
  P0 fail" line (written 2026-09-23) was six days stale on arrival.

Corrections (repo writes, this log is the record):

- `.procoder/plans/psp-breach.md` Re-ranking section: revive-flash step
  removed; "chip holds af531026" retracted with the live evidence; sequence
  back to Probe2 -> bake -> rebuild -> flash the rebuilt v003b.
- `MISTAKES.md`: new top entry, third instance of the stale-source class;
  per the file's repeat rule the prevention is escalated to a script:
  `scripts/board_liveness.sh` (read-only ping + SSH uptime/kernel +
  dmidecode BIOS check; exit 1 when ping fails).
- D1/D2 (revive-image choice) dissolved: no revive flash exists.
- The earlier same-day entry and log (2026-09-23-v003-guard-verified.md)
  are kept for provenance; their revive framing is superseded by this
  correction. The v003 GUARD-driver verification itself stands unchanged
  (extraction-proven).

Queue after correction (V11 NEXT, unchanged from the operator-confirmed
ranking): Probe2 (read-only, ready:
`candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnProbe2.efi`, 2ee54e86)
on the live board -> bake into the driver constant -> rebuild -> re-inject
(v003b) -> flash with exact operator approval, full dump, readback.

Gates: `pytest tests/` 83 passed (17.2 s); `make test` 7/7 OK. Nothing
flashed; nothing written to the board; no candidate or evidence artifact
modified.
