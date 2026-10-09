# BC-250 programmer and candidate recovery gates

## Purpose

This runbook separates harmless SPI readback from any future firmware write. It does not authorize a write. The project works only on the owned/authorized BC-250 and preserves the original image.

## Current verified baseline

- `read-a.bin`: `evidence/programmer/reads/20260911/read-a.bin`
- `read-b.bin`: `evidence/programmer/reads/20260911/read-b.bin`
- Both size: `16,777,216` bytes
- Both SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`
- Both are byte-identical to immutable `dump/2.bin`
- Chip probe: Winbond `W25Q128.V`, 16 MiB, `flashrom v1.8.0`, `ch347_spi`, `1.875M`
- Read manifest: `evidence/programmer/reads/20260911/manifest.json`

## Read-only prerequisites

Stop unless all are true:

1. The exact board is identified as the authorized BC-250.
2. The board is fully disconnected from its power supply and no `+3.3V_SB` is present.
3. The BIOS battery and other unintended power paths are disconnected as appropriate.
4. The physical chip marking, package, pin 1, and clip orientation are checked.
5. CH347T output voltage matches the chip requirement and no board rail is back-powering the board.
6. The read output path is new and distinct from all source images.
7. A signed/pinned flashrom binary is identified. Never use GUI Auto or an unpinned binary for the first capture.

### Allowed read-only commands

```text
flashrom --version
flashrom -p ch347_spi:spispeed=1.875M --flash-name
flashrom -p ch347_spi:spispeed=1.875M -r <new-read-a.bin>
flashrom -p ch347_spi:spispeed=1.875M -r <new-read-b.bin>
sha256sum <new-read-a.bin> <new-read-b.bin>
cmp <new-read-a.bin> <new-read-b.bin>
```

`-w`, erase, write-protection changes, status-register writes, and automatic write actions are not allowed in this phase.

## Candidate gate

A candidate can be called **statically verified** only if:

- source is one of the matching verified reads;
- source/output hashes and size are recorded;
- exact changed offsets and old/new bytes are independently computed;
- relevant NVAR/APCB/FV/FFS/PSP/BHD checks pass;
- signed-region boundaries are documented;
- an independent reviewer checks the actual candidate and failure path;
- hardware, boot, signature acceptance, and runtime behavior are still labelled unrun unless tested.

Current offline candidates:

- VCN/APCB: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`
- Memory clock: `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin`, SHA-256 `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`
- SoC voltage: no candidate; value is not selected because units/encoding/consumer/training/telemetry are unresolved.

## Write gate (not passed)

Do not write unless all prerequisites below are separately evidenced:

1. Complete current recovery dump and at least two matching reads.
2. Known programmer/chip identity and correct voltage.
3. Exact board identifier and physical recovery path.
4. Independent review of the actual candidate, diff, signed boundaries, and failure modes.
5. Exact candidate path and SHA-256 supplied in the operator approval.
6. User explicitly approves that exact image and exact board with this text:

   `Подтверждаю запись файла <exact path> SHA-256: <exact hash> на плату <identifier>`

A general approval, a candidate filename without a hash, or a clean parser result is not sufficient.

## Post-write gate (if separately approved later)

- Record the exact command and timestamp before the write.
- Preserve the pre-write dump and programmer readback.
- Read back the complete chip after writing and compare it with the approved candidate.
- Verify chip ID, image size, hashes, PSP/BHD/APCB/FV/FFS structure, and any available signature status.
- Perform cold boot only after readback passes.
- Record boot behavior, recovery access, thermal/power observations, and rollback decision.
- If any readback, boot, or recovery check fails, stop and restore only through the verified recovery method.

## JTAG separation

J2 is only a CAD-derived candidate CPU-JTAG header. Before an optional read-only attach, verify physical population, pin 1, +1.8 V, reset behavior, debug-security state, adapter/protocol, and target isolation. No JTAG target-memory or register write is permitted without a separate per-call approval and action log.

## Status

The two-read baseline and two offline candidate static validations are complete. No firmware write, erase, register write, JTAG target-memory write, or flash has occurred.

## Stock-boot read-only telemetry gate

This is the next runtime evidence step. It must not be performed while the CH347T clip is attached.

### Preconditions

- Remove the programmer and clip from the SPI chip.
- Confirm no external programmer remains connected to the board.
- Restore normal board power and recovery access.
- Boot the immutable stock baseline; do not flash a candidate.
- Record board revision, BIOS string, kernel release, amdgpu module hash/version, PMFW/VCN firmware names and hashes where available.

### Read-only collection

Capture commands and outputs into a new dated evidence directory. Suggested read-only sources:

```text
uname -a
cat /sys/module/amdgpu/version
journalctl -k -b --no-pager
find /sys/class/drm -path '*gpu_metrics' -type f -print -exec cat {} \;
find /sys -path '*ip_discovery*' -type f -print -exec cat {} \;
find /sys -path '*ip_blocks*' -type f -print -exec cat {} \;
find /sys -path '*pp_dpm_mclk' -o -path '*pp_dpm_fclk' -o -path '*pp_dpm_socclk' -type f -print -exec cat {} \;
```

Use only read operations. Do not use `pp_od_clk_voltage`, SMU write helpers, mailbox setters, debugfs writes, or module parameters that change hardware state.

### Acceptance and stop conditions

- Acceptance requires exact target identity, reproducible logs, and a stock control baseline.
- Record VCN firmware discovery, ring creation, ring-test result, codec node availability, MCLK/UCLK/FCLK/SOCCLK, SoC/GFX voltage metrics, training/fallback messages, and thermal/throttle state separately.
- Stop on unexpected reset, thermal/power fault, missing recovery access, or any command that requires a write.
- Historical imported logs remain historical until this procedure is repeated on the current target.

JTAG readiness inventory: `evidence/boardview/jtag-readiness-20260911.json`. It is CAD/host evidence only; it does not authorize an attach.

### Deferred imported helper

The imported `archives/imported/recon-evidence/legacy-tmp-bc250-recon/a1_readonly.sh` is retained as historical procedure evidence, not the first runtime route. Although its header says read-only, it instantiates an imported SMU transport under `sudo -n`; constructor/transport side effects and exact target compatibility are not independently proven. Do not execute it until that code path has been reviewed. Start with direct kernel/sysfs reads and journal collection instead.

### SMU helper classification correction

Static inspection confirms that the imported `bc250_smu` transport is not read-only: `transport.py` opens PCI config with `O_RDWR`, selects SMN/SMU registers by writing the index at `0xB8`, and mailbox `send_message()` writes command/argument registers. Do not execute any `bc250_smu` query helper in a read-only session. Use kernel/sysfs metrics only until a separate, proven read-only transport is designed and reviewed.

Safe collector: `scripts/collect_stock_runtime_readonly.py` (SHA-256 `ea128ffe4f7fb7151fd63575722e570c7920547c6b8251f923227a447d4571a9`). Its synthetic fixture test summary is `evidence/firmware-audit/collector-fixture-test.json`; no real board was accessed by the test.
