## 2026-10-01 intent

Before write: application did not enumerate after approved UF2, while BOOTSEL/readback matched. Static comparison with TinyUSB HID example found main.c omits board_init() and board_init_after_tusb(). Prepare minimal candidate-only fix; no hardware write authorized by this step.

## Result

- Exact previously approved image readback verified by `picotool verify`: OK.
- Application still did not enumerate after reboot.
- Compared the candidate `main.c` with the Pico TinyUSB HID example. The candidate omitted `board_init()` and `board_init_after_tusb()` while claiming the unified main owned board/USB initialization. This is a concrete startup defect, not a proven sole root cause.
- Minimal fix built as `Waveshare-RP2350B-Plus-W-USB-init-fix-TEST.uf2`, SHA-256 `4ffac696aee995d250b6c0762e05d599811892de348e7111aa50159d236d8d13`; UF2 structural validation passed and six focused tests passed. No new image was flashed.

## Authorized upload attempt

Operator authorized exact 4ffac696 image. Hash matched. picotool load -v exited 249: No accessible RP-series devices in BOOTSEL mode were found. No flash write observed. Authorization retained. Intent: append observed execution to existing verification ledger.

## Hardware result of board-init candidate

Approved 4ffac696 image loaded and picotool verify returned 100% OK. Reboot acknowledged. No application USB or serial appeared after 5 seconds. Board-init hypothesis did not fix observed failure. Original previously working main.c also omitted these calls: absence alone was not proof of root cause. Do not describe them as mandatory cause of this fault.
