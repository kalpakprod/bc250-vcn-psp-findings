# V12 sources mined: CCC 39C3 "Opening pAMDora's box" (tihmstar)

> Статус на 2026-09-27: ИСТОРИЧЕСКИЙ ОБЗОР ВНЕШНЕГО ИССЛЕДОВАНИЯ. Чужой результат не подтверждает работу нашего v001. Указанные ниже первоочередные действия, порядок чтений и аппаратные требования не являются актуальным планом или разрешением на подключение.
> Реестр расхождений: `docs/research/2026-09-27-toctou-document-audit.md`.

Date: 2026-09-23. Source: english subtitles of the 39C3 talk (guid
3aa9e859-d4b0-5e7d-8f5c-7741e6c9856e), preserved at
`evidence/donor/ccc-39c3-20260923/pamdora-talk-eng.vtt.txt` (fetched
2026-09-23 from static.media.ccc.de). Speaker: tihmstar, collaborative
work. Target board = our family (spinoff desktop mainboard, same SoC,
"exact same ROM, very similar boot flow").

## What the talk establishes for our lanes

1. **TOCTOU (our V7') is confirmed and simplified.** The off-chip
   bootloader reads each module body TWICE from SPI: first read is copied
   into SRAM and executed, second read is hashed in-flight by the CCP and
   verified. The speaker's PRODUCTION exploit = ONE RP2040 Pico proxying
   the SPI chip-select with ONE lifted pin on the flash; no second flash
   chip, no desoldering. This upgrades our V7' serve-map rig: the 320 B
   root-key window stays the target, the hardware is simpler than assumed.
2. **The ROM dump recipe (V12 core):**
   - code exec as early as possible (their context: replace Secure OS
     image -> EL1; or ABL0 -> EL0, which on OLD BIOS can write CCP MMIO
     directly; newer BIOS maps MMIO out of EL0 but adds peek/poke
     syscalls that cannot write blacklisted EL1 code, and CCP MMIO is NOT
     blacklisted; EL1 -> EL3 = overwrite exception vector, trigger an
     EL3 exception; EL3 turns out unnecessary);
   - CCP pass-through mode: point CCP config into attacker memory,
     program a CHAINED DMA: transfer 1 = a dummy copy (delays until the
     CPU is dead), transfer 2 = DMA the ROM into SRAM;
   - the CPU must be in reset/dead when the DMA reads the ROM (the ROM
     re-locks itself after execution; warm reset re-enables reads while
     the CPU cannot execute anything but ROM - per the Q&A). The self-
     reset register was found by brute-force writing 0xFFFFFFFF over the
     MMIO space from EL1 (two alive hits; the second accepts 1 = reset);
   - after the dump, reset the whole board: SRAM SURVIVES the reset;
     second boot reads SRAM via the SPI-injection primitive and streams
     it out over USB serial to the Pico;
   - the dump tail: ALWAYS strip the last 30 bytes - per-board random.
3. **ROM reversing results (what the ROM contains):**
   - boot flow: hardware init -> wait for EXTERNAL boot address over I2C
     -> key derivation -> load/decrypt/verify off-chip bootloader ->
     "clear regs and stack, then boot" -> jump to SRAM address 0.
   - **ROM bug (presented, unexploited):** the "clear regs and stack then
     boot or hang(panic)" helper takes (boot address, panic flag) in
     R11/R12, but both are BANKED registers in FIQ mode: entered in FIQ
     mode, the bank-switch zeroes them -> panic=0, boot address=0. Any
     non-watchdog FIQ = boot to address 0 (payload must be stashed at
     SRAM 0 behind filesystem encryption). They could NOT find a
     non-watchdog FIQ trigger; "if you have ideas, feel free to try".
   - **Alternate boot path in ROM main():** a fuse-decided branch into a
     path with NO decryption and NO signature checks, only basic header
     parsing ("some kind of test mode"). Glitch target; payload format
     reversible from the ROM dump.
4. **I2C boot trigger (NEW board fact):** a separate I2C chip on the
   board sends the boot address + boot command to the PSP. Observed
   writes: reg A0 = FF 80 (+zeros), reg A4 = 00 21 00 00, reg A8 = 03.
   Registers A0/A4 concatenate into boot address `FF821000`; the A8
   write triggers the boot. The IC was REMOVED and I2C driven from the
   Pico: manual boot command after reset-button release = the timing
   primitive for glitching. This chip/lines are a NEW observation
   surface for our board (compare with our J5/UART notes).
5. **Keys:** CCP Local Storage Blocks (8 blocks x 16 slots x 32 B);
   slot protection prevents reading but not USING a key; byte-offset
   shift across slot boundary + 1-byte brute force = full key recovery.
   All dumped keys = USELESS: the off-chip-bootloader-decrypting key is
   OVERWRITTEN before the bootloader runs. With the ROM dumped, the key
   derivation is reversible; the only missing piece = fuses (silicon
   decap attempt by their friends failed so far - equipment broke).
6. **Open-sourced by the talk (to mine next):** ROM dumping payload
   (Pico firmware), modchip PCB, modchip firmware (glitch attempts),
   X-ray images. Speaker's github = tihmstar. PT (Habr 979470) dump
   provenance remains separate; the 4700S bootrom repos checked earlier
   do not cover our family.

## Impact on our plan

- V7' rig: simplify to single-Pico CS proxy (one lifted pin), same
  serve-map window (root key t50 entry 0x9DB560..0x9DB6A0).
- V12: the recipe needs (a) early PSP code exec - our board's PSP runs
  the same ROM but OUR attack surface is the DXE carrier, NOT PSP code
  exec; the PT route (CCP-DMA-after-reset from a PSP-context primitive)
  stays the closest match for us; the talk's ABL0/secure-OS replacement
  requires replacing PSP-loaded SPI modules - on OUR board these are
  inside the PSP region we already rebuild (fletcher-only, unsigned
  dir) - a NEW possible lane: swap the Secure OS module body in the PSP
  dir itself (V4-adjacent), giving EL1 without any rig. Needs its own
  decode round before any hardware.
- V2/V2b/V10: the ROM bug list above is the reference for what the
  verifier does NOT catch (the alt boot path, the banked-register bug);
  our op1005 consumer-absent conclusion stays consistent with "the
  consumer lives in ROM".
- The I2C boot trigger: check our board for the same chip/behavior
  before any glitching session (one more probe for the next board-up
  window).

## V14 decode round (same day): swap a Secure-OS-shaped body in our PSP dir

Hypothesis from the talk ("replace the Secure OS image -> EL1 for free"):
our PSP directory is fletcher-only and rebuildable, so point a secure-OS
entry at our own body and get PSP-EL1 without any rig.

Result: **CLOSED-NEGATIVE, offline-decidable.**

- PSP dir of the v003 base (19 entries) enumerated; every loadable body
  is a signed `$PS1` container, verified by `scripts/psp_ps1_verify.py`
  (14 PASS, RSA PSS/SHA256): secure-OS candidates type 0x02 (`$PS1PA`,
  82 768 B, kid `5a3587b5…`) and type 0x28 (`$PS1p`, 108 400 B, the SAME
  kid) - i.e. one signer owns both; ABL0..ABL4 = types 0x30..0x34, all
  kid `663ca522…`; SMU 0x08/0x12 kid `8b8df41e…`; locks 0x24/0x45 kid
  `96ea7cfe…`; 0x44 kid `9ace85d9…` (signed part = 0x10 B only).
- Non-container entries are not usable as payload slots: type 0x01 =
  the encrypted off-chip bootloader (ROM decrypts it; key derivation
  needs the ROM + fuses), type 0x09 = the raw root-key blob (the trust
  anchor), type 0x4F = the AMD public-key region (raw key material,
  memory/firmware-audit.md:1299), types 0x50/0x51 = the KDB carriers
  (kid-not-in-KDB relative to the dir-level chain, by design).
- We can rebuild the DIRECTORY (fletcher) but not sign a BODY: every
  body the ROM/off-chip-bootloader loads must pass its $PS1 signature
  check against KDB-accepted keys. That is the campaign's C1 root, restated.
- The talk's own Secure-OS replacement worked because of the TOCTOU rig
  (serve patched bytes on read 1 = executed, original on read 2 =
  verified). Without a rig, a swapped body = signature fail = the ROM's
  panic path ("clear regs and stack, then hang").
- The ONLY unsigned code surface in the PSP region stays the type-0x44
  tail (V2b): the signed table is 0x10 B, the ~0x3200-B code blobs are
  unsigned, and the consumer is on-die ROM (unproven whether it executes
  them; the talk's ROM dump confirms ROM-side consumers exist but does
  not name 0x44).

Conclusion: on OUR board the talk's "free EL1" route does not exist
without either (a) the V7' TOCTOU rig (now simplified: one Pico, one
lifted pin, per the talk) or (b) a V12-style ROM dump. The V11 in-image
mailbox chain remains the only rig-free product path; V14 closes.

## Evidence class

Talk transcript (public, self-published research) + our own verifier run
on the v003 base (2026-09-23, `psp_ps1_verify.py`, output quoted above).
Classification for V14: OUR MEASUREMENT (verifier output) + EXTERNAL
REPORT (talk). Nothing on hardware was changed.
